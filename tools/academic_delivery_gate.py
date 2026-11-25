#!/usr/bin/env python3
"""Source-bound, final-size academic figure delivery gate (not a science oracle).

All renderers may produce drafts. Only this gate publishes a reviewed candidate.
The source inventory is authored from inspected source evidence BEFORE drawing.
Object bindings are authored separately from the actual PPTX, not inferred truth.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
import unicodedata
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.oxml.ns import qn

RULES = ("R01", "R02", "R03", "R04", "R05", "R06", "R07", "R08")
EMU_PT = 12700
RENDERER = "LibreOffice Impress -> PDF -> PyMuPDF"


class GateError(ValueError):
    pass


def require(test, message):
    if not test:
        raise GateError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")


def norm(text):
    return "".join(unicodedata.normalize("NFKC", text).split())


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def keyed(items, label):
    require(isinstance(items, list), f"{label}: expected list")
    result = {}
    for item in items:
        require(isinstance(item, dict) and nonempty(item.get("id")) and item["id"] not in result,
                f"{label}: missing/duplicate id")
        result[item["id"]] = item
    return result


def read_contract(path):
    path = Path(path)
    c = load(path)
    require(c.get("version") == 1 and nonempty(c.get("claim")), "R01: missing version/claim")
    require(c.get("mode") in {"source_matched", "mechanism_redraw", "scientific_slide"},
            "R01: choose source-matched, redraw, or scientific slide")
    evidence = keyed(c.get("evidence"), "R01 evidence")
    require(evidence, "R01: no source evidence")
    for e in evidence.values():
        require(nonempty(e.get("path")) and nonempty(e.get("locator")),
                "R01: source file and precise locator required")
        source = path.parent / e["path"]
        require(source.is_file() and sha(source) == e.get("sha256"),
                "R01: missing/changed source evidence: " + e["id"])
    require(any(e.get("kind") == "visual_reference" for e in evidence.values()),
            "R02: inspect and retain actual visual reference")
    require(any(e.get("kind") in {"paper", "code", "data", "user_spec"} for e in evidence.values()),
            "R01: visual reference alone does not establish scientific content")
    marks = keyed(c.get("marks"), "R02 marks")
    edges = keyed(c.get("relations"), "R04 relations")
    require(marks, "R02: source inventory is empty")
    for item in list(marks.values()) + list(edges.values()):
        require(item.get("evidence") in evidence and nonempty(item.get("locator"))
                and nonempty(item.get("meaning")), "R01: missing source locator/meaning: " + item["id"])
    for m in marks.values():
        require(nonempty(m.get("form")) and isinstance(m.get("labels"), list),
                "R02/R03: source visual form and label inventory required")
        require(all(nonempty(t) for t in m["labels"]), "R03: invalid required label")
        require(isinstance(m.get("native_kinds"), list) and m["native_kinds"]
                and all(nonempty(t) for t in m["native_kinds"]), "R02/R07: declare required shape types")
        if "operator" in m:
            require(nonempty(m["operator"]) and m["labels"], "R04: operator requires explicit visible label")
            require(isinstance(m.get("operands"), list) and len(m["operands"]) >= 2
                    and len(set(m["operands"])) == len(m["operands"]),
                    "R04: operator requires distinct operand edges in source order")
            require(all(i in edges and edges[i]["target"] == m["id"] for i in m["operands"]),
                    "R04: operator operand must reach its own node")
            require(set(m["operands"]) <= {i for i, e in edges.items() if e["target"] == m["id"]},
                    "R04: invalid operand binding")
    for e in edges.values():
        require(e.get("source") in marks and e.get("target") in marks
                and nonempty(e.get("role")) and nonempty(e.get("target_port"))
                and isinstance(e.get("directed"), bool), "R04: incomplete typed relation: " + e["id"])
    # Every aggregation operand is tied to an explicit source/planned geometric
    # anchor, independent of the rendered connector's metadata. Relative coordinates
    # remain stable when the operator moves or scales. Exact curve geometry is reviewed.
    for m in marks.values():
        if "operator" not in m:
            continue
        for operand in m["operands"]:
            anchor = edges[operand].get("target_anchor")
            require(isinstance(anchor, list) and len(anchor) == 2 and
                    all(isinstance(v, (int, float)) and not isinstance(v, bool)
                        and math.isfinite(v) and 0 <= v <= 1 for v in anchor),
                    "R04: missing/invalid planned operand port anchor: " + operand)
    p = c.get("placement", {})
    require(p.get("profile") in {"presentation", "publication"} and
            all(isinstance(p.get(k), (float, int)) and not isinstance(p[k], bool)
                and math.isfinite(p[k]) and p[k] > 0 for k in ("width_in", "height_in")),
            "R05: explicit final placement dimensions required")
    if p["profile"] == "presentation":
        # Conservative provisional engineering floors, not a claim of legibility at any distance.
        require(p.get("min_span_pt", 11) >= 11 and p.get("min_core_pt", 14) >= 14,
                "R05: presentation minimums cannot be silently lowered")
    else:
        require(nonempty(p.get("venue")) and all(isinstance(p.get(k), (int, float))
                and math.isfinite(p[k]) and p[k] > 0 for k in ("min_span_pt", "min_core_pt")),
                "R05: publication requires named venue and explicit final-size thresholds")
    require(p.get("min_core_pt", 14) >= p.get("min_span_pt", 11), "R05: invalid font hierarchy")
    return c, marks, edges, evidence


def shape_kind(s):
    k = s.shape_type.name
    return k + ":" + s.auto_shape_type.name if k == "AUTO_SHAPE" else k


def shape_index(pptx):
    deck = Presentation(pptx)
    require(len(deck.slides) == 1, "R06: audit exactly one final figure/slide")
    # Group geometry has nested coordinate transforms. Do not pretend to resolve it.
    # Bind group as a top-level mark, review its children visually.
    return deck, {str(s.shape_id): s for s in deck.slides[0].shapes}


def bbox(shapes):
    return (min(s.left for s in shapes), min(s.top for s in shapes),
            max(s.left + s.width for s in shapes), max(s.top + s.height for s in shapes))


def near_box(point, box, tol=3 * EMU_PT):
    x, y = point
    a, b, c, d = box
    return a - tol <= x <= c + tol and b - tol <= y <= d + tol


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def get_bound(index, ids, owner):
    require(isinstance(ids, list) and ids and len(set(map(str, ids))) == len(ids)
            and all(str(i) in index for i in ids), owner + ": missing or duplicate PPTX shape binding")
    return [index[str(i)] for i in ids]


def verify_mapping(pptx, contract_path, mapping_path):
    c, marks, edges, evidence = read_contract(contract_path)
    mapping = load(mapping_path)
    deck, index = shape_index(pptx)
    bound_marks = mapping.get("marks", {})
    bound_edges = mapping.get("relations", {})
    require(set(bound_marks) == set(marks), "R02/R03: source/realization mark inventory mismatch")
    require(set(bound_edges) == set(edges), "R04: source/realization relation inventory mismatch")
    native = {}
    custom_routes = []
    for key, m in marks.items():
        b = bound_marks[key]
        shapes = get_bound(index, b.get("shape_ids"), "R02 " + key)
        require(b.get("form") == m["form"], "R02: visual encoding changed: " + key)
        kinds = {shape_kind(s) for s in shapes} | {s.shape_type.name for s in shapes}
        require(set(m["native_kinds"]) <= kinds, "R02/R07: missing required geometry: " + key)
        content = norm(" ".join(s.text for s in shapes if s.has_text_frame))
        require(all(norm(t) in content for t in m["labels"]),
                "R03: required visible label absent in mapped objects: " + key)
        if "operator" in m:
            require(b.get("operator") == m["operator"] and b.get("operands") == m["operands"],
                    "R04: wrong aggregation operation or operand order: " + key)
        native[key] = shapes
    operand_ends = {}
    for key, e in edges.items():
        b = bound_edges[key]
        require(all(b.get(k) == e[k] for k in ("source", "target", "role", "target_port", "directed")),
                "R04: relation endpoints/role/port/direction changed: " + key)
        route = get_bound(index, b.get("shape_ids"), "R04 " + key)
        require(all(s.shape_type in {MSO_SHAPE_TYPE.LINE, MSO_SHAPE_TYPE.FREEFORM,
                                    MSO_SHAPE_TYPE.AUTO_SHAPE} for s in route),
                "R04: relation is not editable line/path geometry: " + key)
        if all(s.shape_type == MSO_SHAPE_TYPE.LINE for s in route):
            starts = [(s.begin_x, s.begin_y) for s in route]
            ends = [(s.end_x, s.end_y) for s in route]
            require(all(distance(a, b) <= 3 * EMU_PT for a, b in zip(ends, starts[1:])),
                    "R04: disconnected line segments: " + key)
            require(near_box(starts[0], bbox(native[e["source"]])) and
                    near_box(ends[-1], bbox(native[e["target"]])),
                    "R04: line misses source or destination: " + key)
            if e["directed"]:
                tail = route[-1]._element.spPr.find(".//" + qn("a:tailEnd"))
                marker = b.get("arrow_shape_id")
                if marker is not None:
                    arr = get_bound(index, [marker], "R04 arrow " + key)[0]
                    require(arr.shape_type in {MSO_SHAPE_TYPE.AUTO_SHAPE, MSO_SHAPE_TYPE.FREEFORM}
                            and near_box(ends[-1], bbox([arr])), "R04: arrow marker misses endpoint: " + key)
                else:
                    require(tail is not None and tail.get("type", "none") != "none",
                            "R04: missing directed arrow: " + key)
            if e.get("target_anchor") is not None:
                a, b_, c_, d = bbox(native[e["target"]])
                u, v = e["target_anchor"]
                planned = (a + u * (c_ - a), b_ + v * (d - b_))
                # Cap tolerance in physical and local operator coordinates so
                # two nearby input ports cannot be accepted interchangeably.
                tolerance = min(3 * EMU_PT, .10 * min(c_ - a, d - b_))
                require(distance(ends[-1], planned) <= tolerance,
                        "R04: connector misses planned operand port: " + key)
            operand_ends[key] = ends[-1]
        else:
            # Curves and imported freeforms remain supported. Geometry/direction require
            # the actual source-to-render inspection under R04, never a machine topology pass.
            custom_routes.append(key)
    for key, m in marks.items():
        if "operator" in m:
            endpoints = [operand_ends[i] for i in m["operands"] if i in operand_ends]
            require(all(distance(a, b) >= 2 * EMU_PT for i, a in enumerate(endpoints)
                        for b in endpoints[i+1:]), "R04: distinct operands collapse before operator: " + key)
    # Every retained raster must have a declared scientific reason and exact bytes.
    # Nested pictures also need a record, even inside editable groups.
    def descendants(shapes):
        for s in shapes:
            yield s
            if s.shape_type == MSO_SHAPE_TYPE.GROUP:
                yield from descendants(s.shapes)
    pictures = {str(s.shape_id): s for s in descendants(deck.slides[0].shapes)
                if s.shape_type == MSO_SHAPE_TYPE.PICTURE}
    assets = mapping.get("assets", {})
    require(set(assets) == set(pictures), "R07: missing/extra retained image provenance")
    for key, s in pictures.items():
        a = assets[key]
        require(a.get("category") in {"photo", "measured_data", "spatial_reference", "illustrative_art"}
                and a.get("evidence") in evidence and nonempty(a.get("locator"))
                and hashlib.sha256(s.image.blob).hexdigest() == a.get("sha256"),
                "R07: unsupported raster or provenance mismatch: " + key)
    if c.get("all_native"):
        require(not pictures, "R07: all-native request contains pictures")
    revision = mapping.get("revision")
    if revision is not None:
        baseline = Path(mapping_path).parent / revision["baseline"]
        require(baseline.is_file() and sha(baseline) == revision["sha256"],
                "R08: missing/changed frozen baseline")
        _, old = shape_index(baseline)
        changed = set(map(str, revision.get("mutable_shape_ids", [])))
        require(changed and changed <= (set(old) | set(index)), "R08: invalid local change scope")
        require(set(old) - changed == set(index) - changed,
                "R08: objects outside revision scope added/removed")
        for key in set(old) - changed:
            require(old[key]._element.xml == index[key]._element.xml,
                    "R08: object outside revision scope changed: " + key)
    return c, {"mark_count": len(marks), "relation_count": len(edges),
               "manual_geometry_routes": custom_routes, "picture_count": len(pictures),
               "top_level_shape_count": len(index), "local_revision": revision is not None}


def audit_render(pptx, pdf, c, preview=None):
    import fitz
    deck, index = shape_index(pptx)
    with fitz.open(pdf) as doc:
        require(len(doc) == 1, "R06: rendered output not exactly one page")
        page = doc[0]
        require(abs(page.rect.width / page.rect.height - deck.slide_width / deck.slide_height) < .02,
                "R06: PDF aspect ratio differs from PPTX")
        p = c["placement"]
        scale = min(p["width_in"] * 72 / page.rect.width, p["height_in"] * 72 / page.rect.height)
        minimum = p.get("min_span_pt", 11)
        core_minimum = p.get("min_core_pt", 14)
        errors, spans = [], []
        lines = []
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                line_id = len(lines)
                line_spans = []
                for s in line["spans"]:
                    if not s["text"].strip():
                        continue
                    rect = fitz.Rect(s["bbox"])
                    size = s["size"] * scale
                    entry = {"text": s["text"], "size_pt": round(size, 3), "bbox_pdf_pt": list(rect),
                             "line": line_id}
                    spans.append(entry)
                    line_spans.append(entry)
                    if size + .05 < minimum:
                        errors.append("R05: undersize rendered span: " + repr(s["text"]) + f" ({size:.2f} pt)")
                    if not (page.rect + (-.5, -.5, .5, .5)).contains(rect):
                        errors.append("R06: rendered text outside canvas: " + repr(s["text"]))
                if line_spans:
                    lines.append(line_spans)
        require(spans, "R05/R07: no extractable rendered text")
        # Match whole visible labels over spans, including mixed font runs.
        for m in c["marks"]:
            for label in m["labels"]:
                target = norm(label)
                # Labels may wrap over consecutive lines; exact text remains required.
                matching = []
                for i in range(len(lines)):
                    combined = []
                    for j in range(i, min(i+4, len(lines))):
                        combined.extend(lines[j])
                        text = norm(" ".join(s["text"] for s in combined))
                        if target == text or (i == j and target in text):
                            matching.append(combined)
                            break
                if not matching:
                    errors.append("R03: required label not found in PDF: " + label)
                elif m.get("core", False) and not any(
                        all(s["size_pt"] + .05 >= core_minimum for s in seq) for seq in matching):
                    errors.append("R05: core rendered label below floor: " + label)
        # Conservative overlap proxy: use inset text boxes, not line-height padding.
        # Same-line script runs are not treated as colliding. Intentional overlaps and
        # figure/text interactions must still be inspected on the actual render.
        rects = []
        for s in spans:
            r = fitz.Rect(s["bbox_pdf_pt"])
            inset = min(r.height*.16, 2)
            rects.append(fitz.Rect(r.x0, r.y0+inset, r.x1, r.y1-inset))
        for i, a in enumerate(rects):
            for j in range(i+1, len(rects)):
                if spans[i]["line"] == spans[j]["line"]:
                    continue
                b = rects[j]
                area = min(a.get_area(), b.get_area())
                if area > 0 and (a & b).get_area() > area*.25:
                    errors.append("R06: significant text intersection: " + repr(spans[i]["text"])
                                  + " / " + repr(spans[j]["text"]))
        if preview is not None:
            # Preview occupies the same effective pixels as the final physical placement
            # on a 1280px-wide 13.333-inch slide, not an enlarged figure-only screenshot.
            pixels_per_pt = 1280 / (13.333 * 72)
            page.get_pixmap(matrix=fitz.Matrix(scale*pixels_per_pt, scale*pixels_per_pt),
                            alpha=False).save(preview)
        return {"passed": not errors, "errors": errors, "scale": scale,
                "placement_in": [p["width_in"], p["height_in"]],
                "min_rendered_span_pt": min(s["size_pt"] for s in spans),
                "span_count": len(spans), "spans": spans,
                "limitations": "PDF extraction and bounding boxes are conservative proxies. "
                               "No OCR of raster labels, scientific proof, physical projection, "
                               "or Microsoft PowerPoint host claim."}


def prepare(pptx, contract, mapping, output):
    pptx, contract, mapping, output = map(Path, (pptx, contract, mapping, output))
    c, inventory = verify_mapping(pptx, contract, mapping)
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="academic-gate-") as temp:
        root = Path(temp)
        # Never overwrite a previous coherent receipt with an unsuccessful render.
        subprocess.run(["libreoffice", "-env:UserInstallation=" + (root/"profile").as_uri(),
                        "--headless", "--convert-to", "pdf", "--outdir", str(root),
                        str(pptx.resolve())], check=True, timeout=120, capture_output=True)
        pdf = root / (pptx.stem + ".pdf")
        require(pdf.is_file(), "R05/R06: actual PPTX render missing")
        preview = root / "final_size.png"
        report = audit_render(pptx, pdf, c, preview)
        shutil.copyfile(pdf, output/"render.pdf")
        shutil.copyfile(preview, output/"final_size.png")
    receipt = {"version": 1, "renderer": RENDERER, "inventory": inventory, "render_audit": report,
               "hashes": {"pptx": sha(pptx), "contract": sha(contract), "mapping": sha(mapping),
                          "pdf": sha(output/"render.pdf"), "preview": sha(output/"final_size.png")},
               "status": "review_pending" if report["passed"] else "blocked"}
    save(output/"receipt.json", receipt)
    return receipt


def finalize(pptx, contract, mapping, output, review_path, destination):
    output, destination = Path(output), Path(destination)
    receipt = load(output/"receipt.json")
    require(receipt["hashes"] == {"pptx": sha(pptx), "contract": sha(contract), "mapping": sha(mapping),
            "pdf": sha(output/"render.pdf"), "preview": sha(output/"final_size.png")},
            "R08: stale or changed source, artifact or render; prepare again")
    c, inventory = verify_mapping(pptx, contract, mapping)
    actual = audit_render(pptx, output/"render.pdf", c)
    require(receipt["renderer"] == RENDERER and actual["passed"],
            "R05/R06: final-size render failed; revise, do not publish")
    review = load(review_path)
    require(review.get("receipt_sha256") == sha(output/"receipt.json"),
            "R08: review does not refer to this exact prepared render")
    require(review.get("reviewer_role") in {"author_agent", "independent_agent", "human", "user"},
            "reviewer role required; no implied independence")
    checks = review.get("checks", {})
    require(set(checks) == set(RULES), "missing mandatory R01-R08 review")
    for rule in RULES:
        entry = checks[rule]
        require(entry.get("status") == "pass" and nonempty(entry.get("observation"))
                and nonempty(entry.get("locator")), rule + ": failed/unreviewed or no concrete evidence")
    require(not destination.exists() and not destination.with_suffix(".acceptance.json").exists(),
            "R08: candidate already exists; use a new revision name")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(pptx, destination)
    record = {"status": "reviewed_candidate", "user_accepted": False,
              "pptx_sha256": sha(destination), "receipt_sha256": sha(output/"receipt.json"),
              "review_sha256": sha(review_path), "reviewer_role": review["reviewer_role"],
              "inventory": inventory, "renderer": RENDERER,
              "limitations": actual["limitations"]}
    save(destination.with_suffix(".acceptance.json"), record)
    return record


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["prepare", "finalize"])
    ap.add_argument("--pptx", type=Path, required=True)
    ap.add_argument("--contract", type=Path, required=True)
    ap.add_argument("--mapping", type=Path, required=True)
    ap.add_argument("--review-dir", type=Path, required=True)
    ap.add_argument("--review", type=Path)
    ap.add_argument("--destination", type=Path)
    args = ap.parse_args()
    try:
        if args.command == "prepare":
            result = prepare(args.pptx, args.contract, args.mapping, args.review_dir)
            print(json.dumps({"status": result["status"], "errors": result["render_audit"]["errors"]},
                             ensure_ascii=False, indent=2))
            if result["status"] == "blocked":
                return 2
        else:
            require(args.review and args.destination, "finalize requires review and destination")
            result = finalize(args.pptx, args.contract, args.mapping, args.review_dir,
                              args.review, args.destination)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (GateError, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        ap.exit(2, "Academic delivery blocked: " + str(error) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
