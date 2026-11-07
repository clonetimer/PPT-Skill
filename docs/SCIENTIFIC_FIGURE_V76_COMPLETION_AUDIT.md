# V7.6 科研绘图方案验收审计（2026-11-07）

审计对象为 `docs/SCIENTIFIC_FIGURE_GAP_AND_UPGRADE_PLAN_2026.md` 的 A–D 阶段。此处的“自动通过”只说明列出的机器检查在当前提交上通过；不代表科研解释、实际投影可读性或期刊接收已获认可。审计应在图件、来源或评审表变化后重新执行。

| 方案条款 | 当前证据 | 判定 |
|---|---|---|
| A：统一 FigureSpec、稳定元素 ID、来源与绘制拓扑 | `specs/figure_spec_v76.schema.json`；15 个 `figure_specs/`；`tools/migrate_figure_specs.py`；`tools/validate_scientific_ir.py` 独立核对 C01 复合图 14 条关键可见关系；`tools/test_scientific_ir.py` 包含删边、反向、错标和来源哈希突变 | 自动通过 |
| A：文档状态与新旧输出科学标签 | `README.md` 区分开发版；`tools/validate_render_semantics.py` 核对当前 SVG/PPTX/PDF 科学标签；`tools/validate_legacy_label_parity.py` 将五张迁移前 FigureSpec 和 SVG 的文字多重集逐项与当前版对照，三张 C01 另对照历史 PPTX；`tools/validate_c01_v73.py` 和 `tools/validate_c01_v74.py` 核对固定内容 | 已提交的五张旧图标签自动通过；B01/F07 历史 PPTX 未入库，当前 PPTX 与迁移前 FigureSpec 对照通过。此项仅证明标签，不证明全部语义或视觉等价 |
| B：数据、单位、变换、统计与轴契约 | `specs/iris_charts_v76.json`、`specs/wine_charts_v76.json` 和 ChartSpec Schema；`tools/chart_data.py` 共用来源哈希与逐行解析；`tools/chart_contract.py` 在两个数据集上校验样本数、轴类型/单位/范围、类别覆盖及 bootstrap 定义；FigureSpec Schema 强制定量数据链字段，验证器将嵌入的图表定义及来源元数据与哈希锁定的 ChartSpec 逐项比对，独立评审模板另锁定原始配置文件哈希；Iris 验证器检查六类统计图；`tools/validate_wine_scatter.py` 独立核对 UCI Wine 两张图各 178 行、坐标、双编码及未报告单位；负向测试拒绝来源、数值、坐标、单位、配置哈希及嵌入统计定义突变 | Iris 六类与 Wine 散点/分布图自动通过；跨数据集的散点和分布通道有实证，其余四类仍只在 Iris 验证 |
| B：原始点可见、SVG/PPTX/PDF 可复现 | Q01/Q02/Q03/Q06/Q07/Q08 的原始点分离有几何检查；Q03/Q06 汇总标记避让；`dist/render_record_v76.json` 锁定 PowerPoint PDF；独立评审包解压后已重建两张 Wine 图并通过规范化哈希和数据行核对 | 自动通过；最终观看尺寸仍需人工复核 |
| C：图像完整性 | I01 的 CC0 原图、哈希、处理日志、0.107 µm/像素校准、10 µm 比例尺与像素直方图由 `tools/validate_image_quant_example.py` 核对 | 单图示例自动通过；不代表生物学重复或细胞分割 |
| C：可访问性与双载体 | `tools/check_scientific_accessibility.py` 检查文字、关键图形标记、线和示意箭头对比度，生成灰度及近似色觉差异预览；`tools/validate_output_profiles.py` 检查 14 个演示规格和 1 个 Nature 主图示例；PDF 字体、尺寸、矢量层由渲染及出版示例验证器核对 | 自动预检通过；实际投影和 183 × 100 mm 印刷尺寸未复核 |
| D：固定基准与发布硬门槛 | `specs/research_figure_benchmark_v76.json` 有 15 项、5 个学科、6 维评分和 4 类硬失败；`tools/validate_release_readiness.py` 锁定来源、FigureSpec、ChartSpec 配置、图件与 Q03P 图注哈希，要求领域匹配、先评后核对、逐维至少 2 分及终尺寸证据；`tools/test_release_readiness.py` 的通过数据仅为合成测试 | 基准和门槛已实现；仓库内真实独立评审记录 0/15 |

## 未完成的验收证据

1. **独立领域复核：**当前没有已填写的真实评审表。15 项任务分别需要具备航空系统、机械故障诊断、应用统计、分析化学或细胞成像相应经验的未参与制图人员；同一人可覆盖其实际专业范围内的多项任务。使用 `tools/prepare_scientific_review_bundle.py` 生成的两阶段材料包，先看来源与图件，再看规格、预期和已知陷阱。
2. **实际终尺寸：**演示图需要记录设备、投影距离和读不清的具体元素；Q03P 需要在 183 × 100 mm 的物理印刷尺寸或经校准的等效显示尺寸检查，并记录尺寸证据。现有 PNG/PDF 尺寸与字体检查不能代替这一步。
3. **外部来源边界：**C01 仍缺对作者原图的高分辨率逐区叠图复核；其输出继续标为结构性重绘。Q03P 是 Nature 主图尺寸示例，尚未进行投稿前的目标期刊最终核验。

上述三项缺少实际证据时，`tools/validate_release_readiness.py --review` 不应通过；不得将开发版称为已发布稳定版。
