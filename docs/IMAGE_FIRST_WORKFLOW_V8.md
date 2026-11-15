# V8：Image-first 双阶段幻灯片生成工作流

**状态：开发中（8.0.0-dev）**

V8 为高视觉复杂度的答辩页、研究框架页、技术路线页和多模块信息页增加一条 Image-first 路线：

1. **Stage A — Image2 目标视觉稿**：先生成单页 16:9 幻灯片效果图，审查科学内容、文字、版式和投影可读性。
2. **Stage B — 可编辑 PPTX 复现**：只以已批准并冻结的目标图为视觉基准，将页面重建为原生 PowerPoint 文本、形状、连接线和图表，再做对象审计和视觉对照。

V8 不替换 V7.6 的 FigureSpec、ChartSpec 或 PDF 导入路线。定量图表、统计图、公式精度优先的页面仍走 spec-first；视觉布局复杂、需要先收敛构图的页面走 image-first。一个 DeckSpec 可以按页选择路线。

## 1. 工作流边界

### Stage A：目标视觉稿

输入：
- DeckSpec / SlideSpec 的页面主张、准确可见文字、演讲备注和证据来源；
- 论文图、原始 PPT、手绘草图或风格参考；
- Image2 prompt。

输出：
- 一张 1920 × 1080 的 16:9 目标图；
- 生成 prompt、参考素材 SHA-256、模型与迭代记录；
- 人工视觉审查记录。

Image2 生成是独立的图像生成步骤。仓库中的 prompt builder 负责根据 DeckSpec 生成可复用提示词和工作流清单，不伪称自己调用了 Image2 服务。

Stage A 必须由人工批准后才能进入 Stage B。批准检查：
- scientific_content：科学内容与来源一致；
- exact_text：所有必需可见文字准确；
- source_fidelity：关系、方向、公式、数值和证据边界符合来源；
- visual_hierarchy：标题、主体、辅助信息层级清晰；
- projection_readability：在演示尺寸下可读；
- reconstruction_feasibility：布局可用原生 PPT 对象复现。

任何科学语义或文字错误都应在 Stage A 修正，不允许把错误视觉稿冻结后再在 PPTX 阶段“悄悄纠正”。

### Stage B：PPTX 复现

重建目标：
- 标题、标签、说明和图注使用可编辑文本框；
- 模块、背景、边框、节点、箭头和连接线使用原生形状；
- 数据图表使用可编辑图表或 FigureSpec / ChartSpec；
- 照片和确需保留的复杂源图可作为独立图片对象；
- 不允许把整张目标图作为全页图片背景交付。

重建后必须：
1. 导出对应页的 PNG 预览；
2. 检查必需文字覆盖率、对象数量、越界、文本框重叠和整页栅格背景；
3. 比较目标图与 PPTX 渲染图；
4. 完成独立人工视觉审查；
5. 对最终交付执行 PowerPoint 2016 主机往返测试。

## 2. 目录与数据契约

| 文件 | 用途 |
|---|---|
| `specs/image_first_workflow_v8.schema.json` | 单页两阶段工作流 JSON Schema |
| `specs/image_first_workflow_v8.example.json` | FBG-SEANet 方法页的 Stage A 计划示例 |
| `prompts/image2_slide_prompt_template.md` | Image2 提示词规则模板 |
| `tools/build_image2_slide_prompt.py` | 从 DeckSpec 生成目标图提示词 |
| `tools/create_image_first_manifest.py` | 创建单页 prompt 与工作流 manifest |
| `tools/audit_image_first_reconstruction.py` | 审计 PPTX 原生对象、文字覆盖与布局 |
| `tools/compare_image_first_renders.py` | 计算目标图与渲染图的图像差异指标 |
| `tools/validate_image_first_workflow.py` | 校验状态迁移、来源锁定、文件哈希和验收门槛 |

每页一个 manifest。它通过 `deck_spec_ref`、`slide_id` 和 `slide_index` 绑定既有 DeckSpec，并复制一份不可随意漂移的 `content_lock`。验证器会逐项比对 claim、on-slide 文案、speaker notes 和 evidence；内容锁不一致时直接失败。

## 3. 开始 Stage A

以现有 FBG-SEANet 方法页为例：

```bash
python tools/create_image_first_manifest.py \
  specs/deck_spec_v76.example.json s02 \
  --output-dir dist/image_first/fbg-seanet-s02
```

生成：
- `dist/image_first/fbg-seanet-s02/image2_prompt.md`
- `dist/image_first/fbg-seanet-s02/workflow.json`

将 prompt 提交给 Image2，生成一张 1920 × 1080 PNG，保存为例如：

`dist/image_first/fbg-seanet-s02/target_image.png`

然后在 manifest 中记录：
- Stage A 状态为 `generated`；
- target_image 的相对路径、SHA-256、像素宽高和媒体类型；
- 生成迭代、参考图和 prompt 哈希。

人工检查并修正后，将状态设为 `approved`，填写人工 reviewer、时间戳，并把六项 checks 全部置为 true。未通过审查的图像保持 `generated` 或 `needs_revision`，不得启动 Stage B。

## 4. 执行 Stage B 与审计

将目标图重建为 PPTX。PPTX 可以包含整套 deck，manifest 的 `slide_index` 指向本次审计页。

用 PowerPoint 或 LibreOffice 导出该页预览。LibreOffice 示例（13.333 × 7.5 英寸、144 dpi 对应 1920 × 1080）：

```bash
mkdir -p dist/image_first/fbg-seanet-s02/render
libreoffice --headless --convert-to pdf \
  --outdir dist/image_first/fbg-seanet-s02/render \
  dist/image_first/fbg-seanet-s02/reconstructed.pptx
pdftoppm -f 2 -l 2 -r 144 -png -singlefile \
  dist/image_first/fbg-seanet-s02/render/reconstructed.pdf \
  dist/image_first/fbg-seanet-s02/render/slide
```

生成结构审计：

```bash
python tools/audit_image_first_reconstruction.py \
  dist/image_first/fbg-seanet-s02/workflow.json \
  --output dist/image_first/fbg-seanet-s02/pptx_audit.json
```

生成目标图与渲染图对照指标：

```bash
python tools/compare_image_first_renders.py \
  dist/image_first/fbg-seanet-s02/target_image.png \
  dist/image_first/fbg-seanet-s02/render/slide.png \
  --output dist/image_first/fbg-seanet-s02/parity.json
```

将两个报告中的对象清单、审计字段和图像指标写回 manifest，再执行：

```bash
python tools/validate_image_first_workflow.py \
  dist/image_first/fbg-seanet-s02/workflow.json
```

## 5. 视觉一致性指标的解释

对照工具记录：
- `global_ssim`：整张灰度图的全局 SSIM；
- `mean_absolute_error`：归一化 RGB 平均绝对误差；
- `dhash_hamming_distance`：64 位差分哈希汉明距离。

这些指标用于快速发现整体偏差，不等价于局部布局 IoU，也不能代替人工逐区审查。特别是全局 SSIM 可能掩盖小字、箭头和局部科学标记的错误。阈值由 manifest 明确记录；最终通过仍要求人工审查。

## 6. 状态机与硬门槛

Stage A：
- `planned` → `generated` → `approved` → `locked`
- `generated` → `needs_revision` → 再次生成与审查
- 只有人工批准的 `approved/locked` 可以启动 Stage B。

Stage B：
- `not_started` → `in_progress` → `reconstructed` → `audited` → `accepted`

`audited` 至少要求：
- 必需可见文字覆盖率为 100%；
- 无越界、无文本框重叠；
- 无全页栅格背景；
- 目标图、PPTX、预览图哈希一致；
- 图像指标达到 manifest 中记录的阈值。

`accepted` 还要求：
- 独立人工视觉审查批准；
- PowerPoint 2016 主机往返测试通过；
- 保存往返测试证据文件及 SHA-256。

机器检查通过不等于科学验收通过。Stage A 图像与 Stage B PPTX 均需保留，禁止覆盖历史轮次。

## 7. 路线选择

| 页面类型 | 默认路线 | 原因 |
|---|---|---|
| 答辩研究背景、研究方案、技术路线 | image-first | 先收敛视觉构图和信息层级 |
| 多模块框架图、复杂综合页 | image-first | 先确认页面阅读路径，再重建对象 |
| 柱状图、折线图、散点图、统计区间 | spec-first | 数据、坐标、单位和统计定义必须可计算验证 |
| 数学公式、精确网络结构、关键科学拓扑 | spec-first 或 hybrid | 不能让图像生成模型决定公式或关系 |
| 复杂页面中的局部装饰插图 | image-first 局部素材 + 原生 PPTX | 插图可作为独立素材，文字与关系仍保持可编辑 |

V8 首批以 C01 的 FBG-SEANet 方法页作为试点：先生成一张 Image2 目标效果图，经人工确认后再重建 PPTX。试点通过后再扩展到研究背景、总体技术路线和结果页。
