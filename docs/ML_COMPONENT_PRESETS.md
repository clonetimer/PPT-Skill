# 科研插图基础组件预置（V7.6 开发版）

## 定位

`specs/ml_source_grammar_patterns_v76.json` 列出一类论文图应核查的科学状态与标记；`tools/ml_figure_components.py` 提供可参数化的原生 PowerPoint/SVG **基础组件**。使用者先核对原文，再选择组件和版式。组件不替论文确定层数、数值、颜色或连线，也不验证张量类型是否相容。

| 组件 | 主要参数 | 返回的连接端口 | 本次复用证据 |
|---|---|---|---|
| `feature_map_strip` | 通道、空间尺寸、宽高、颜色、尺寸标注带 | 上/下/左/右/中心 | U-Net 原图构建代码已调用；提取前后元素清单一致 |
| `crop_concat_pair` | 两半的通道、共同空间尺寸、白/蓝条宽与间距 | `crop_in`、`upsample_in`、`conv_out` | U-Net 四处拼接已调用；白色复制与蓝色上采样保持独立 |
| `addition_junction` | 位置、直径、线色 | 上/左/右输入、输出 | ResNet 已调用；提取前后元素清单一致 |
| `residual_variant` | 面板内可容纳的有序层列表、各层宽度/颜色、背景身份箭头 | 输入、主路、求和、输出 | Wide Residual Networks Figure 1 四个变体共用此组件，图面经一次修订后通过 |
| `encoder_wedge` | 标签、轮廓、填充、渐缩量 | 输入、输出、顶/底 | CLIP 四个编码器已调用；提取前后元素清单一致 |
| `similarity_matrix` | 行列索引、格尺寸、正配对色、行列模态色 | 每一行/列/格端口及组端口 | CLIP 已调用；展示图另以四个可见成员运行 |
| `vector_fanout` | 来源、成员目标、干线位置、方向、省略项 | 每个显示成员端口 | 参数变化展示图包含文字/图像向量扇出 |
| `token_strip` | 成员数、格尺寸、省略项、可见组外框 | 组端口及每格上下端口 | DETR 测试中修复了“只接首／末 token”的歧义 |
| `multihead_neighbor_bundle` | 两节点、半径、头颜色、波形幅度 | 起点与终点；逐头 `head_id` | GAT 邻域多头边，逐束逐头校验 |
| `multihead_self_loop` | 节点中心、半径、头颜色 | 回环两端；逐头 `head_id` | GAT 的自贡献从缺失变为可见且可变异检查 |
| `vector_math_label` | 数学文本、矢量箭头相对位置、字号 | 标签中心 | GAT 的节点、系数和权重向量记号统一；避免组合 Unicode 字形在 PowerPoint 中散开 |

接口以英寸为坐标单位，接受实现 `rect/text/line/polygon/ellipse` 的画布对象，并返回 `Component` 的命名端口。`bounds` 是主体几何外框，`visual_bounds` 还包含可见标签区域，排版时应使用后者预留间距。需要可追溯的 FigureSpec 与 PowerPoint 时，可使用 `dist/skill_tests/ml_fidelity/figurelib.py` 中的 `Figure` 作为画布。一个最小调用：

```python
from ml_figure_components import crop_concat_pair

pair = crop_concat_pair(
    figure, sid="decoder2", x=4.2, y=2.0, h=1.1,
    channels_per_half=128, spatial_size="104×104",
    fill="#74A0CE", stroke="#38669A", label_color="#767676",
)
up_input = pair.port("upsample_in")
copy_input = pair.port("crop_in")
```

在仓库中运行示例：

```powershell
.testtmp\venv\Scripts\python.exe tools\test_ml_figure_components.py
.testtmp\venv\Scripts\python.exe tools\build_ml_component_gallery.py
.testtmp\venv\Scripts\python.exe dist\skill_tests\ml_component_heldout\build.py
.testtmp\venv\Scripts\python.exe dist\skill_tests\ml_component_heldout\validate_heldout.py
.testtmp\venv\Scripts\python.exe dist\skill_tests\ml_cross_family\validate_revision.py
```

预览：[组件参数变化展示图](../dist/skill_tests/ml_component_gallery/ml_component_gallery.png)；[Wide Residual Networks Figure 1 试画](../dist/skill_tests/ml_component_heldout/MLH01_wide_resnet_variants.png)。后者源自 [Zagoruyko 与 Komodakis 的论文](https://arxiv.org/pdf/1605.07146)，PDF 第 2 页 Figure 1。原图、原文 PDF、FigureSpec、PPTX、PDF、PNG 和[独立评审](../dist/skill_tests/ml_component_heldout/CRITIC_REVIEW.md)留在 `dist/skill_tests/ml_component_heldout/`。首版因末层到求和节点的空段过长未通过；修订版 **21/24**，达到本轮图面门槛。该图与 ResNet 同属残差图族，且 `residual_variant` 为此次试画开发，不能算冻结组件后的独立留出验证。

## 使用限制

- `crop_concat_pair` 表示裁剪特征与上采样特征的**拼接**；源方法使用求和或无裁剪时应选其他构件，不能改名后套用。
- `residual_variant` 仅适用于有身份旁路与加法汇合的变体；BN/ReLU 是否显示、卷积顺序、层宽、dropout 位置必须按源图设定。
- `similarity_matrix` 对可见的批成员、行图像/列文本与对角正配对作图。省略号只表示未展示的中间成员，不能把可见的最后一个成员断开。
- 组件端口是生成和验证时的语义坐标。PPTX 中的连接线仍是独立原生对象，尚无 PowerPoint 节点端点绑定；移动形状后要重新导出并审图。
- `residual_variant` 的面板宽、层高、层宽与间距有可渲染范围；它不是任意层数的自适应排版器。标签较长时仍应检查实际导出图。普通画布若没有 `route` 接口，组件画出的线不携带语义连线记录。
- 参数变化展示图是合成示例，没有论文证据资格。本轮证明组件在受控参数下可调用、已知反例被拒绝，及一张同族新图在批评和迭代后达到门槛。**“快速准确泛化”尚无证据**：需冻结组件版本，再由独立评审选不同图族和多实例组合样本，记录首次导出评分、调整轮次和实际耗时。
- GAT/DETR 跨图族试验的首版均未通过，暴露了空拓扑清单、注意力头不完整、token 组端口缺位等问题；经多轮修订，两图最终均获 **21.5/24**。详见 [试验与差异分类](ML_CROSS_FAMILY_TRIAL_2026-11.md)。逐头 `head_id` 是生成和验证用的语义记录，不会让 PowerPoint 连接线随节点拖动。
