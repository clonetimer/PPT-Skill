#!/usr/bin/env python3
"""Package all 15 final candidates, including every companion artifact, with SHA-256."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from validate_research_benchmark import OUTPUTS, artifact_paths
from fifteen_figure_review_packet import TASK_SUPPLEMENTARY_FILENAMES
from scientific_ir import ROOT


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def archive_path(task_id: str, relative: str) -> str:
    if task_id == "Q07":
        if relative.startswith("dist/Q07_") or relative.startswith("examples/Q07_"):
            return "02_最终候选版/Q07/01_散点/" + Path(relative).name
        if relative.startswith("dist/Q08_") or relative.startswith("examples/Q08_"):
            return "02_最终候选版/Q07/02_分布/" + Path(relative).name
    return f"02_最终候选版/{task_id}/{Path(relative).name}"


def build(output: Path, root: Path = ROOT) -> dict:
    root, output = Path(root), Path(output)
    if output.exists():
        raise FileExistsError(f"REFUSE_TO_OVERWRITE_FINAL_CANDIDATE_PACKAGE:{output}")
    entries = []
    missing = []
    for task_id in OUTPUTS:
        for relative in artifact_paths(task_id):
            source = root / relative
            if not source.is_file():
                missing.append(relative)
                continue
            entries.append({
                "task_id": task_id,
                "source": relative,
                "archive_path": archive_path(task_id, relative),
                "size_bytes": source.stat().st_size,
                "sha256": sha256(source),
            })
    if missing:
        raise FileNotFoundError("FINAL_CANDIDATE_ARTIFACTS_MISSING:" + ",".join(missing))
    for relative in ("dist/quantitative_reproduction_audit_v76.json",
                     "dist/quantitative_point_traceability_v76.csv"):
        source=root/relative
        if not source.is_file():
            raise FileNotFoundError(f"QUANTITATIVE_AUDIT_ARTIFACT_MISSING:{relative}")
        entries.append({"task_id":"QUANTITATIVE_AUDIT","source":relative,
                        "archive_path":"03_审计证据/"+Path(relative).name,
                        "size_bytes":source.stat().st_size,"sha256":sha256(source)})
    for task_id, filenames in TASK_SUPPLEMENTARY_FILENAMES.items():
        for filename in filenames:
            source=root/"dist/accepted_repairs"/filename
            if not source.is_file():
                raise FileNotFoundError(f"SUPPLEMENTARY_FINAL_CANDIDATE_MISSING:{task_id}:{filename}")
            entries.append({"task_id":task_id,"source":str(source.relative_to(root)),
                            "archive_path":f"02_最终候选版/{task_id}/02_两页演示版/{filename}",
                            "size_bytes":source.stat().st_size,"sha256":sha256(source)})
    q07_files = [item for item in entries if item["task_id"] == "Q07"]
    q07_scatter = [item for item in q07_files if "/01_散点/" in item["archive_path"]]
    q07_distribution = [item for item in q07_files if "/02_分布/" in item["archive_path"]]
    required = {"Q08_wine_strip.pptx",
                "Q08_wine_strip.svg", "Q08_wine_strip.pdf",
                "Q08_wine_strip.preview.png"}
    actual = {Path(item["source"]).name for item in q07_distribution}
    if not required.issubset(actual):
        raise AssertionError(f"Q07_COMPANION_DELIVERY_INCOMPLETE:{sorted(required-actual)}")
    if not any(Path(item["source"]).name == "Q07_wine_scatter.pptx" for item in q07_scatter):
        raise AssertionError("Q07_SCATTER_PPTX_MISSING")

    manifest = {
        "schema_version": "1.0.0",
        "release": "PPT-Skill V7.6 final candidate set",
        "population": len(OUTPUTS),
        "artifact_count": len(entries),
        "tasks": sorted(OUTPUTS),
        "q07_delivery": {
            "primary": "Wine scatter",
            "companion": "Wine categorical alcohol distribution",
            "sample_count_each": 178,
            "cultivar_counts": {"1": 59, "2": 71, "3": 48},
            "required_pair_present": True,
        },
        "artifacts": entries,
        "acceptance": "Candidate package only; independent human final review and host/final-size checks remain pending.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("README_CN.md", (
            "# PPT-Skill V7.6 最终候选文件包\n\n"
            "包含 15 项任务的可编辑 PPTX、SVG/PDF/PNG 预览及任务要求的配套材料。\n"
            "**Q07 已按成套交付：散点图 Q07 + 分类分布图 Q08**，两图均对应 UCI Wine 的 178 条原始样本。\n\n"
            "本包是最终候选，不代表专家 PASS；独立领域评审、实际终尺寸和 PowerPoint 2016 主机往返仍需完成。\n"
        ))
        archive.writestr("SHA256_MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        archive.writestr("SHA256SUMS.txt", "".join(
            f"{item['sha256']}  {item['archive_path']}\n" for item in entries
        ))
        for item in entries:
            archive.write(root / item["source"], item["archive_path"])
    return {
        "status": "PASS",
        "population": len(OUTPUTS),
        "artifact_count": len(entries),
        "q07_scatter_artifacts": len(q07_scatter),
        "q07_distribution_artifacts": len(q07_distribution),
        "output": str(output),
        "sha256": sha256(output),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/PPT-Skill_15_final_candidates_v76.zip")
    args = parser.parse_args()
    print(json.dumps(build(args.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
