#!/usr/bin/env python3
"""FontTools-based text measurement, binary-search fit solvers and WCAG contrast helpers."""
from __future__ import annotations
from dataclasses import dataclass
import math, re, shutil, subprocess, unicodedata
from pathlib import Path
from typing import Callable
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTCollection, TTFont


class MissingGlyphError(ValueError):
    pass


def resolve_font_face(family_or_path: str) -> tuple[Path, int, str]:
    """Resolve a font family to an exact file and TTC face index via fontconfig."""
    candidate = Path(family_or_path)
    if candidate.is_file():
        return candidate.resolve(), 0, ""
    if not shutil.which("fc-match"):
        raise FileNotFoundError(f"FONT_NOT_FOUND_AND_FC_MATCH_UNAVAILABLE:{family_or_path}")
    result = subprocess.run(
        ["fc-match", "-f", "%{family[0]}\\n%{index}\\n%{file}\\n", family_or_path],
        capture_output=True, text=True, check=True,
    )
    lines = [line.strip() for line in result.stdout.splitlines()]
    if len(lines) < 3 or not lines[2] or not Path(lines[2]).is_file():
        raise FileNotFoundError(f"FONT_RESOLUTION_FAILED:{family_or_path}")
    try:
        face_index = int(lines[1] or "0")
    except ValueError as error:
        raise ValueError(f"INVALID_FONT_FACE_INDEX:{family_or_path}:{lines[1]}") from error
    return Path(lines[2]).resolve(), face_index, lines[0]


def resolve_font_file(family_or_path: str) -> Path:
    """Compatibility wrapper returning the resolved font file only."""
    return resolve_font_face(family_or_path)[0]


class FontMetrics:
    def __init__(self, font_path: str | Path, face_index: int = 0,
                 fallback_enabled: bool = True):
        self.path = Path(font_path).resolve()
        self.face_index = int(face_index)
        self.fallback_enabled = bool(fallback_enabled)
        self._fallback_metrics: dict[str, FontMetrics] = {}
        self.fallback_fonts: dict[str, dict[str, str | int]] = {}
        self._glyph_ink_bounds: dict[int, tuple[float, float, float, float] | None] = {}
        if self.path.suffix.lower() == ".ttc":
            self.collection = TTCollection(str(self.path), lazy=True)
            if self.face_index < 0 or self.face_index >= len(self.collection.fonts):
                self.collection.close()
                raise ValueError(f"FONT_FACE_INDEX_OUT_OF_RANGE:{self.face_index}:{self.path.name}")
            self.font = self.collection.fonts[self.face_index]
        else:
            if self.face_index != 0:
                raise ValueError(f"FONT_FACE_INDEX_REQUIRES_TTC:{self.face_index}:{self.path.name}")
            self.collection = None
            self.font = TTFont(str(self.path), lazy=True)
        names = self.font["name"].names
        self.family_name = ""
        for record in names:
            if record.nameID in (16, 1):
                try:
                    value = record.toUnicode()
                except Exception:
                    continue
                if value:
                    self.family_name = value
                    if record.nameID == 16:
                        break
        self.units_per_em = int(self.font["head"].unitsPerEm)
        self.cmap = self.font.getBestCmap() or {}
        self.hmtx = self.font["hmtx"].metrics
        os2 = self.font["OS/2"]
        if getattr(os2, "sTypoAscender", 0) or getattr(os2, "sTypoDescender", 0):
            ascender = int(os2.sTypoAscender)
            descender = int(os2.sTypoDescender)
            line_gap = int(getattr(os2, "sTypoLineGap", 0))
        else:
            hhea = self.font["hhea"]
            ascender, descender, line_gap = int(hhea.ascent), int(hhea.descent), int(hhea.lineGap)
        self.ascender_units = ascender
        self.descender_units = descender
        self.line_height_units = max(1, ascender - descender + line_gap)

    def _fallback_for_char(self, char: str) -> "FontMetrics | None":
        if not self.fallback_enabled:
            return None
        key = f"U+{ord(char):04X}"
        if key in self._fallback_metrics:
            return self._fallback_metrics[key]
        family = self.family_name or self.path.stem
        try:
            path, face_index, resolved_family = resolve_font_face(
                f"{family}:charset={ord(char):x}"
            )
        except (FileNotFoundError, ValueError):
            return None
        if path == self.path and face_index == self.face_index:
            return None
        fallback = FontMetrics(path, face_index=face_index, fallback_enabled=False)
        if ord(char) not in fallback.cmap:
            fallback.close()
            return None
        self._fallback_metrics[key] = fallback
        self.fallback_fonts[key] = {
            "requested_family": family,
            "resolved_family": resolved_family or fallback.family_name,
            "font_file": str(path),
            "font_face_index": face_index,
        }
        return fallback

    def close(self) -> None:
        for fallback in self._fallback_metrics.values():
            fallback.close()
        self._fallback_metrics.clear()
        if self.collection is not None:
            self.collection.close()
        else:
            self.font.close()

    def _font_for_char(self, char: str) -> "FontMetrics":
        codepoint = ord(char)
        if codepoint in self.cmap or unicodedata.category(char).startswith("M"):
            return self
        fallback = self._fallback_for_char(char)
        if fallback is not None:
            return fallback
        raise MissingGlyphError(f"MISSING_GLYPH:U+{codepoint:04X}:{char!r}:{self.path.name}")

    def glyph_vertical_offsets_pt(self, char: str, font_size_pt: float) -> tuple[float, float]:
        """Return (top, bottom) offsets from the rendered baseline using the selected glyph face."""
        metrics = self._font_for_char(char)
        top = -float(metrics.ascender_units) / metrics.units_per_em * float(font_size_pt)
        bottom = -float(metrics.descender_units) / metrics.units_per_em * float(font_size_pt)
        return top, bottom

    def glyph_ink_offsets_pt(
        self, char: str, font_size_pt: float
    ) -> tuple[float, float, float, float] | None:
        """Return exact glyph-outline offsets (left, bottom, right, top) from its baseline."""
        metrics = self._font_for_char(char)
        codepoint = ord(char)
        if codepoint not in metrics._glyph_ink_bounds:
            glyph_name = metrics.cmap.get(codepoint)
            if glyph_name is None:
                metrics._glyph_ink_bounds[codepoint] = None
            else:
                glyph_set = metrics.font.getGlyphSet()
                pen = BoundsPen(glyph_set)
                glyph_set[glyph_name].draw(pen)
                metrics._glyph_ink_bounds[codepoint] = pen.bounds
        bounds = metrics._glyph_ink_bounds[codepoint]
        if bounds is None:
            return None
        scale = float(font_size_pt) / metrics.units_per_em
        x_min, y_min, x_max, y_max = bounds
        return (
            float(x_min) * scale,
            float(y_min) * scale,
            float(x_max) * scale,
            float(y_max) * scale,
        )

    def glyph_advance_pt(self, char: str, font_size_pt: float) -> float:
        if char in "\r\n":
            return 0.0
        if unicodedata.category(char).startswith("M") and ord(char) not in self.cmap:
            return 0.0
        metrics = self._font_for_char(char)
        glyph_name = metrics.cmap.get(ord(char))
        if glyph_name is None:
            return 0.0
        advance = metrics.hmtx.get(glyph_name, (0, 0))[0]
        return float(advance) / metrics.units_per_em * float(font_size_pt)

    def text_width_pt(self, text: str, font_size_pt: float) -> float:
        return sum(self.glyph_advance_pt(char, font_size_pt) for char in text)

    def line_height_pt(self, font_size_pt: float, line_spacing: float = 1.0) -> float:
        return self.line_height_units / self.units_per_em * float(font_size_pt) * float(line_spacing)

    def wrap(self, text: str, font_size_pt: float, max_width_pt: float) -> list[str]:
        if max_width_pt <= 0:
            raise ValueError("TEXT_WIDTH_MUST_BE_POSITIVE")
        lines: list[str] = []
        for paragraph in str(text).split("\n"):
            if paragraph == "":
                lines.append("")
                continue
            current = ""
            for token in re.findall(r"\s+|\S+", paragraph):
                if token.isspace():
                    if current and self.text_width_pt(current + token, font_size_pt) <= max_width_pt:
                        current += token
                    continue
                if current and self.text_width_pt(current + token, font_size_pt) <= max_width_pt:
                    current += token
                    continue
                if current:
                    lines.append(current.rstrip())
                    current = ""
                for char in token:
                    candidate = current + char
                    if current and self.text_width_pt(candidate, font_size_pt) > max_width_pt:
                        lines.append(current)
                        current = char
                    else:
                        current = candidate
            lines.append(current.rstrip())
        return lines

    def measure(self, text: str, font_size_pt: float, width_in: float,
                height_in: float,
                margins_pt: tuple[float, float, float, float] = (1.44, 1.44, .576, .576),
                line_spacing: float = 1.0) -> dict:
        left, right, top, bottom = margins_pt
        available_width = float(width_in) * 72.0 - left - right
        available_height = float(height_in) * 72.0 - top - bottom
        lines = self.wrap(text, font_size_pt, available_width)
        line_height = self.line_height_pt(font_size_pt, line_spacing)
        required_height = len(lines) * line_height
        return {
            "font_path": str(self.path),
            "font_size_pt": float(font_size_pt),
            "lines": lines,
            "line_count": len(lines),
            "max_line_width_pt": max((self.text_width_pt(line, font_size_pt) for line in lines), default=0.0),
            "line_height_pt": line_height,
            "required_height_pt": required_height + top + bottom,
            "available_height_pt": float(height_in) * 72.0,
            "fits": required_height <= available_height + 1e-6,
        }


@dataclass(frozen=True)
class FitResult:
    fits: bool
    selected_font_size_pt: float | None
    required_height_pt: float
    available_height_pt: float
    line_count: int
    iterations: int
    reason: str


def fit_font_size(metrics: FontMetrics, text: str, width_in: float, height_in: float,
                  preferred_size_pt: float, min_size_pt: float,
                  margins_pt: tuple[float, float, float, float] = (1.44, 1.44, .576, .576),
                  line_spacing: float = 1.0, iterations: int = 24) -> FitResult:
    """Find the largest fitting font size; applying the shrink remains an explicit caller policy."""
    if min_size_pt <= 0 or preferred_size_pt < min_size_pt:
        raise ValueError("INVALID_FONT_SIZE_BOUNDS")
    preferred = metrics.measure(text, preferred_size_pt, width_in, height_in, margins_pt, line_spacing)
    if preferred["fits"]:
        return FitResult(True, preferred_size_pt, preferred["required_height_pt"],
                         preferred["available_height_pt"], preferred["line_count"], 0,
                         "preferred_size_fits")
    smallest = metrics.measure(text, min_size_pt, width_in, height_in, margins_pt, line_spacing)
    if not smallest["fits"]:
        return FitResult(False, None, smallest["required_height_pt"],
                         smallest["available_height_pt"], smallest["line_count"], 0,
                         "minimum_size_does_not_fit")
    low, high, last = float(min_size_pt), float(preferred_size_pt), smallest
    used = 0
    for used in range(1, iterations + 1):
        mid = (low + high) / 2.0
        measured = metrics.measure(text, mid, width_in, height_in, margins_pt, line_spacing)
        if measured["fits"]:
            low, last = mid, measured
        else:
            high = mid
    return FitResult(True, low, last["required_height_pt"], last["available_height_pt"],
                     last["line_count"], used, "binary_search_max_fitting_size")


def binary_search_min_height(probe: Callable[[float], bool], min_height_pt: float,
                             max_height_pt: float, tolerance_pt: float = .25,
                             iterations: int = 24) -> dict:
    """Find minimum textbox height accepted by a render/overflow probe.

    The probe may use fast font metrics or a calibrated LibreOffice render check.
    """
    if min_height_pt <= 0 or max_height_pt < min_height_pt:
        raise ValueError("INVALID_HEIGHT_BOUNDS")
    if not probe(max_height_pt):
        return {"fits": False, "height_pt": None, "iterations": 0, "reason": "max_height_overflows"}
    low, high, used = float(min_height_pt), float(max_height_pt), 0
    for used in range(1, iterations + 1):
        if high - low <= tolerance_pt:
            break
        mid = (low + high) / 2.0
        if probe(mid):
            high = mid
        else:
            low = mid
    return {"fits": True, "height_pt": high, "iterations": used, "reason": "binary_search_minimum_height"}


def fit_textbox_height(metrics: FontMetrics, text: str, font_size_pt: float,
                       width_in: float, min_height_pt: float, max_height_pt: float,
                       margins_pt: tuple[float, float, float, float] = (1.44, 1.44, .576, .576),
                       line_spacing: float = 1.0, tolerance_pt: float = .25) -> dict:
    """Binary-search the minimum height using a font-metric overflow probe.

    The same probe interface can be replaced by a calibrated LibreOffice render probe.
    """
    def probe(height_pt: float) -> bool:
        result = metrics.measure(
            text, font_size_pt, width_in, height_pt / 72.0, margins_pt, line_spacing
        )
        return bool(result["fits"])
    return binary_search_min_height(
        probe, min_height_pt, max_height_pt, tolerance_pt=tolerance_pt
    )


def luminance(hex_color: str) -> float:
    value = hex_color.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError(f"INVALID_HEX_COLOR:{hex_color}")
    channels = [int(value[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in channels]
    return .2126 * linear[0] + .7152 * linear[1] + .0722 * linear[2]


def contrast_ratio(foreground: str, background: str) -> float:
    a, b = luminance(foreground), luminance(background)
    lighter, darker = max(a, b), min(a, b)
    return (lighter + .05) / (darker + .05)


def resolve_font_path(family_or_path: str) -> Path:
    return resolve_font_file(family_or_path)
