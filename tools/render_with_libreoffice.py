#!/usr/bin/env python3
"""Canonical headless LibreOffice PPTX -> PDF/PNG renderer with an auditable environment record."""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess, tempfile
from pathlib import Path
from typing import Any
from pptx import Presentation


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_command(args: list[str], env: dict[str, str] | None = None,
                timeout: int = 180, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, capture_output=True, text=True, env=env, timeout=timeout)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"COMMAND_FAILED:{args[0]}:{result.returncode}\n"
            f"stdout={result.stdout[-3000:]}\nstderr={result.stderr[-3000:]}"
        )
    return result


def command_version(command: str, args: list[str]) -> str:
    result = run_command([command, *args], check=False)
    text = result.stdout or result.stderr
    return text.strip().splitlines()[0] if text.strip() else "unknown"


def read_os_release() -> dict[str, str]:
    path = Path("/etc/os-release")
    if not path.exists():
        return {}
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            result[key] = value.strip().strip('"')
    return result


def installed_package_versions(packages: list[str]) -> dict[str, str]:
    if not shutil.which("dpkg-query"):
        return {}
    result = {}
    for package in packages:
        query = run_command(["dpkg-query", "-W", package], check=False)
        if query.returncode == 0 and query.stdout.strip():
            fields = query.stdout.strip().split()
            result[package] = fields[-1]
    return result


def collect_requested_fonts(pptx_path: Path) -> list[str]:
    deck = Presentation(pptx_path)
    fonts: set[str] = set()
    for slide in deck.slides:
        for shape in slide.shapes:
            if not getattr(shape, "has_text_frame", False):
                continue
            for paragraph in shape.text_frame.paragraphs:
                for run in paragraph.runs:
                    if run.font.name:
                        fonts.add(run.font.name)
    return sorted(fonts)


def resolve_fonts(font_names: list[str]) -> dict[str, dict[str, str]]:
    resolved = {}
    for family in font_names:
        match = run_command(["fc-match", "-f", "%{family}\\n%{file}\\n", family], check=False)
        lines = [line.strip() for line in match.stdout.splitlines() if line.strip()]
        actual_family = lines[0] if lines else "unresolved"
        file_name = lines[1] if len(lines) > 1 else ""
        item = {"resolved_family": actual_family, "file": file_name}
        file_path = Path(file_name) if file_name else None
        if file_path and file_path.is_file():
            item["sha256"] = sha256_file(file_path)
        resolved[family] = item
    return resolved


def pdf_page_count(pdf_path: Path) -> tuple[int, str]:
    result = run_command(["pdfinfo", "-box", str(pdf_path)])
    match = re.search(r"^Pages:\\s+(\\d+)", result.stdout, re.MULTILINE)
    if not match:
        raise RuntimeError("PDFINFO_PAGE_COUNT_NOT_FOUND")
    page_size = re.search(r"^Page size:\\s+(.+)$", result.stdout, re.MULTILINE)
    return int(match.group(1)), page_size.group(1).strip() if page_size else "unknown"


def pdf_font_report(pdf_path: Path) -> list[str]:
    result = run_command(["pdffonts", str(pdf_path)], check=False)
    return result.stdout.splitlines()[2:] if result.stdout else []


def load_profile(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"profile_id":"ad-hoc-lo-headless","profile_version":"0","lock_status":"capture",
                "dpi":144,"locale":"C.UTF-8","timezone":"UTC","required_packages":[],"expected":{}}
    return json.loads(path.read_text(encoding="utf-8"))


def validate_lock(profile: dict[str, Any], observed: dict[str, Any]) -> list[str]:
    if profile.get("lock_status") != "enforce":
        return []
    expected = profile.get("expected", {})
    mismatches = []
    for key in ("libreoffice_version", "poppler_version", "fontconfig_version"):
        value = expected.get(key)
        if value and value != observed.get(key):
            mismatches.append(f"{key}:expected={value}:actual={observed.get(key)}")
    for key, value in expected.get("package_versions", {}).items():
        if observed.get("package_versions", {}).get(key) != value:
            mismatches.append(f"package:{key}:expected={value}:actual={observed.get('package_versions', {}).get(key)}")
    for family, value in expected.get("font_files", {}).items():
        actual = observed.get("font_files", {}).get(family, {})
        if actual.get("sha256") != value:
            mismatches.append(f"font:{family}:expected={value}:actual={actual.get('sha256')}")
    return mismatches


def render_pptx(input_pptx: str | Path, output_dir: str | Path,
                profile_path: str | Path | None = None, dpi: int | None = None) -> dict[str, Any]:
    source = Path(input_pptx).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"INPUT_PPTX_NOT_FOUND:{source}")
    for tool in ("soffice", "pdftoppm", "pdfinfo", "pdffonts", "fc-match"):
        if not shutil.which(tool):
            raise RuntimeError(f"RENDER_TOOL_NOT_FOUND:{tool}")
    profile = load_profile(Path(profile_path) if profile_path else None)
    render_dpi = int(dpi or profile.get("dpi", 144))
    if render_dpi < 72 or render_dpi > 600:
        raise ValueError("DPI_OUT_OF_RANGE:72..600")
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / f"{source.stem}.pdf"
    if pdf_path.exists():
        pdf_path.unlink()
    env = os.environ.copy()
    env.update({
        "LANG": str(profile.get("locale", "C.UTF-8")),
        "LC_ALL": str(profile.get("locale", "C.UTF-8")),
        "TZ": str(profile.get("timezone", "UTC")),
        "SAL_USE_VCLPLUGIN": "gen",
    })
    with tempfile.TemporaryDirectory(prefix="ppt-skill-lo-profile-") as user_profile:
        profile_uri = Path(user_profile).resolve().as_uri()
        run_command([
            "soffice", f"-env:UserInstallation={profile_uri}",
            "--headless", "--nologo", "--nodefault", "--nofirststartwizard",
            "--convert-to", "pdf", "--outdir", str(out_dir), str(source),
        ], env=env, timeout=240)
    if not pdf_path.is_file():
        raise RuntimeError(f"LIBREOFFICE_PDF_NOT_CREATED:{pdf_path}")
    page_count, page_size = pdf_page_count(pdf_path)
    prefix = out_dir / f"{source.stem}-slide"
    run_command(["pdftoppm","-png","-r",str(render_dpi),"-f","1","-l",str(page_count),str(pdf_path),str(prefix)], timeout=240)
    png_paths = sorted(out_dir.glob(f"{source.stem}-slide-*.png"))
    if len(png_paths) != page_count:
        raise RuntimeError(f"PNG_PAGE_COUNT_MISMATCH:expected={page_count}:actual={len(png_paths)}")
    requested_fonts = collect_requested_fonts(source)
    font_files = resolve_fonts(requested_fonts)
    packages = installed_package_versions(profile.get("required_packages", []))
    observed = {
        "profile_id": profile.get("profile_id"),
        "profile_version": profile.get("profile_version"),
        "renderer": "LibreOffice headless",
        "libreoffice_version": command_version("soffice", ["--version"]),
        "poppler_version": command_version("pdftoppm", ["-v"]),
        "pdfinfo_version": command_version("pdfinfo", ["-v"]),
        "fontconfig_version": command_version("fc-match", ["--version"]),
        "package_versions": packages,
        "font_files": font_files,
        "requested_fonts": requested_fonts,
        "pdf_fonts": pdf_font_report(pdf_path),
        "os_release": read_os_release(),
        "locale": env["LC_ALL"],
        "timezone": env["TZ"],
        "dpi": render_dpi,
        "pdf_page_size": page_size,
    }
    mismatches = validate_lock(profile, observed)
    record = {
        "schema_version": "1.0.0",
        "render_profile": profile.get("profile_id"),
        "render_profile_sha256": hashlib.sha256(json.dumps(profile,sort_keys=True,separators=(",",":")).encode("utf-8")).hexdigest(),
        "input": {"path": str(source), "sha256": sha256_file(source)},
        "renderer": observed,
        "outputs": {
            "pdf": {"path": str(pdf_path), "sha256": sha256_file(pdf_path)},
            "pages": [{"page":i+1,"path":str(path),"sha256":sha256_file(path)} for i,path in enumerate(png_paths)],
        },
        "lock_status": profile.get("lock_status", "capture"),
        "lock_mismatches": mismatches,
        "powerpoint_host_round_trip": {
            "status": "not_tested",
            "note": "LibreOffice render success is not a Microsoft PowerPoint host compatibility test."
        },
    }
    record_path = out_dir / "render_record.json"
    record_path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\\n",encoding="utf-8")
    if mismatches:
        raise RuntimeError("RENDER_PROFILE_LOCK_MISMATCH:" + ";".join(mismatches))
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_pptx", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--dpi", type=int)
    args = parser.parse_args()
    record = render_pptx(args.input_pptx,args.output_dir,args.profile,args.dpi)
    print(json.dumps({
        "status":"PASS","input_sha256":record["input"]["sha256"],
        "renderer":record["renderer"]["libreoffice_version"],
        "page_count":len(record["outputs"]["pages"]),
        "png_sha256":[p["sha256"] for p in record["outputs"]["pages"]],
        "record":str(Path(args.output_dir)/"render_record.json")
    },ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
