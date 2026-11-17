# P1 — Dataset contract adoption assessment

**Date:** 2026-11-17  
**Status:** Existing implementation reused; schema hardening queued after P0 renderer gates.

## Decision

Do **not** introduce a second, parallel dataset-manifest format. The repository already has a substantial dataset/chart contract in `specs/iris_charts_v76.json`, a FigureSpec lineage pointer, and independent recomputation/audit tooling. P1 should strengthen these existing contracts and generalize them, rather than duplicate their fields in a new registry.

## Existing implementation verified in the current branch

| Requirement from the P2P-inspired proposal | Existing implementation | Assessment |
|---|---|---|
| Dataset URI / provenance | `data.source_url`, DOI, license and local `data.file` in `iris_charts_v76.json` | Present; source URL currently identifies the dataset landing page, not necessarily the exact downloadable byte artifact |
| Dataset content hash | `data.sha256`; `chart_data.load_rows` recomputes SHA-256 before parsing | Present and enforced |
| Row semantics | `row_count`, `row_unit`, stable source-row index | Present |
| Selected columns and units | `data.columns` with type, unit and source position; chart x/y/group and axis declarations | Present |
| Missing-value policy and transforms | `missing_value_policy`, `transforms` | Present; transforms are currently free-text declarations |
| Filtering and aggregation | Chart `filter`, `sample_size`, `derived_fields`, `statistics.display` and chart-specific recomputation | Present, but aggregation semantics are partly expressed in prose and code rather than one generic typed record |
| Bootstrap configuration | Interval name, resample count, seed and resampling unit in Q03/Q06 | Present; Python validator checks these fields |
| Figure-to-dataset binding | FigureSpec `data_lineage` includes data file/hash/source URL/DOI/row count plus chart-spec path and canonical digest | Present and checked by `scientific_ir.validate_spec` |
| Independent numeric verification | `validate_quantitative_examples.py` reloads source rows, recomputes intervals/derived values and checks plotted geometry | Present |
| Source-row-to-mark audit | `export_quantitative_reproduction_audit.py` exports row-to-object traceability CSV and a reproduction report | Present |

Relevant implementation:
- `specs/iris_charts_v76.json`
- `specs/chart_spec_v76.schema.json`
- `tools/chart_data.py`
- `tools/chart_contract.py`
- `tools/validate_quantitative_examples.py`
- `tools/export_quantitative_reproduction_audit.py`
- `tools/scientific_ir.py`

## Remaining gaps

1. **Exact source artifact URI.** `source_url` points to the UCI dataset page. Add an optional immutable `artifact_url` or `download_url` when the upstream host exposes a stable direct file; keep `source_url` as the human-readable provenance page. Never synthesize a direct URL where the source does not provide one.
2. **Structured transforms.** Replace or supplement free-text transform strings with typed operations containing operation name, input fields, output fields, parameters and implementation/version. Preserve the human-readable explanation.
3. **Typed aggregation contract.** Add a generic aggregation object (group-by, measure, statistic, output field and missing-value handling) so a checker can understand the calculation without interpreting the chart claim or Python source.
4. **Schema-level bootstrap requirements.** The current Python validator checks bootstrap resamples, seed and resampling unit, but `chart_spec_v76.schema.json` does not fully require/type these fields for every bootstrap interval. Move these requirements into JSON Schema as well as retaining semantic recomputation.
5. **Dataset identity in FigureSpec.** Add a stable dataset ID and a canonical dataset-record digest to `data_lineage`; keep the full record in the ChartSpec rather than duplicating all column definitions in every FigureSpec.

## P1 acceptance gates

- Mutating the source file without updating its hash fails before parsing.
- Mutating selected columns, units, filter, aggregation, bootstrap seed/resamples/unit or confidence interval fails schema or semantic validation.
- Recomputed statistics match stored values within declared numeric tolerances.
- Every plotted mark resolves to a source row or an explicitly declared aggregate group.
- A FigureSpec resolves to one immutable dataset/chart contract by ID and digest.
- The existing Q01–Q08 quantitative examples and the 15-figure V7.6 regression remain green.

## Sequencing

P0-A AST, P0-B canonical LibreOffice, and P0-C calibrated text fit remain the active engineering priority. P1-A begins after the cross-paper AST/text calibration gate is green. The existing Iris contract is the first migration test, not a reason to create a duplicate contract system.
