# 机器学习论文插图复刻压力测试（2026-11-07）

本次选了三种不同的科学视觉语法，而不是继续增加统一版式模板：

| 原图 | 原文与定位 | 本次可编辑重绘 | 为什么有测试价值 |
|---|---|---|---|
| U-Net | [Ronneberger et al. 2015](https://arxiv.org/pdf/1505.04597)，Figure 1，PDF 第 2 页 | `dist/skill_tests/ml_fidelity/unet/MLU01_unet_architecture.pptx` | 特征图空间大小、通道、池化、裁剪拼接必须同时正确。 |
| ResNet | [He et al. 2016](https://openaccess.thecvf.com/content_cvpr_2016/papers/He_Deep_Residual_Learning_CVPR_2016_paper.pdf)，Figure 2，PDF 第 2 页 | `dist/skill_tests/ml_fidelity/resnet/MLR01_resnet_residual_block.pptx` | 简单方框也可承载高精度语义；分叉、相加、ReLU 位置和内部比例决定保真度。 |
| CLIP | [Radford et al. 2021](https://proceedings.mlr.press/v139/radford21a/radford21a.pdf)，Figure 1，PDF 第 2 页 | `dist/skill_tests/ml_fidelity/clip/MLC01_clip_overview.pptx` | 同图含照片、文本卡片、梯形编码器、N×N 矩阵和类别向量到预测得分的一一对应。 |

原论文 PDF、原图渲染、`source_style.json`、FigureSpec、SVG、PPTX、PDF、PNG 均保存在 `dist/skill_tests/ml_fidelity/` 对应目录。CLIP 使用有记录的 [CC0 替代照片](../dist/skill_tests/ml_fidelity/clip/ASSET_PROVENANCE.md)，没有把原论文整图作为栅格嵌入。

## 独立评审

`figure_critic` 在查看成品前冻结了 [基线](../dist/skill_tests/ml_fidelity/CRITIC_BASELINE.md)：六维各 0–4 分，科学语义必须 4，其余每维至少 3，总分至少 21/24，并以关键关系、数值错误、文字遮挡作硬失败。第一轮只看原文与导出的 PNG/PDF，结论见 [盲评](../dist/skill_tests/ml_fidelity/CRITIC_FIRST_REVIEW.md)。三张第一版均未通过。第二轮须先再次盲看修订成品，再检查实现、许可证与可编辑性；自动检查不代替这一复评。

第一轮发现的关键差异及已采取的修复：

| 图 | 原因 | 修订措施 | 通用能力变化 |
|---|---|---|---|
| U-Net | 初版省去了 284²/64、140²/128、68²/256 池化后状态；白色复制条被错误地当作全部拼接对象；尺寸字被线穿过 | 补齐池化状态与卷积箭头；四处并排画白色复制与蓝色上采样特征图，绿色箭头进入蓝色半部；重排尺寸与通道标注 | 独立 fixture 加入关键状态与通道/空间尺寸校验；旋转文字的 PowerPoint 重叠审计改用实际旋转包围盒 |
| ResNet | 主支路底段过长，层间箭头断开，旁路折点可见 | 按原图压缩第二层到相加的间距；用连续箭头标中间 ReLU；旁路采样更密 | 结构检查必须有内部比例与锚点距离，而不仅是节点/边存在 |
| CLIP | 初版把整个批向量组压成指向 T₃/I₃ 的单点；右侧类别向量与得分行分离 | 文本、图像及类别向量对可见各格扇出；类别向量与得分逐列对齐；预测从选中蓝格中心引出 | FigureSpec/PPTX 新增可编辑 `polygon`；修复了自由多边形坐标取整导致梯形在 PPTX 变矩形的实际渲染缺陷；组端口需要与单元素端口区别 |

## 对 SKILL 与预置模板的决定

1. 高保真任务先从原图和图注冻结可证伪的**状态、关系、数值、视觉标记、内部比例**检查项，再绘图。对比应使用最终 PowerPoint 导出的 PDF/PNG；SVG 正确并不保证 PPTX 正确。
2. 预置模式提供可变的科学语法构件：特征图状态与拼接、分叉与相加、矩阵行列与正配对、向量组分发。不得把任一论文的固定坐标或配色当作所有机器学习图的模板。
3. 素材可使用许可明确的照片或图标，但记录替换、作者、许可、来源 URL 和哈希；数值、箭头、运算和标注仍保持可编辑。
4. 将 `expected_topology.json` 与作图代码分开，并运行 `python dist/skill_tests/ml_fidelity/validate_trial.py`。这个脚本检查本次样本的关键关系、尺寸、通道和 CLIP 矩阵对角线；它是样本检查，不是对任意论文图保真的通用证明。
5. 用 `python tools/audit_pptx.py <figure.pptx> --strict` 检查 ResNet/U-Net；CLIP 使用 `--strict --allow-raster`，因为五个图片对象是已披露的 CC0 照片。还需人工查看文字与箭线交叉及实际查看尺寸。

## 后续升级的验收顺序

| 优先级 | 可复用能力 | 本次样本的验收点 | 范围边界 |
|---|---|---|---|
| P0 | 状态与操作分开建模 | U-Net 池化后保持通道，随后卷积改变通道；四处解码都有白色裁剪部和蓝色上采样部；ResNet 分叉发生在首层前 | 不能用“有 U 形/有旁路”替代逐边核对 |
| P0 | 组端口与成员端口 | CLIP 的 I₁、I₂、I₃、Iₙ 与 T₁、T₂、T₃、Tₙ 均能从编码器追踪到矩阵；类别向量与评分格逐列对应 | 不能只检查组级 `semantic_edges` 自声明 |
| P1 | 来源数据驱动几何 | U-Net 的左右特征图高度随空间尺寸变化，ResNet 的层间距和求和位置接近原图内部比例 | 几何值针对论文图定标，不固化成通用布局 |
| P1 | 导出后的路径与标注检查 | 红色池化向下、绿色上采样自蓝条底部向上；尺寸不被箭线穿越；通道数字各归其对象 | PPTX 对象重叠和 FigureSpec 路径审计仍需人眼复看 PDF |
| P2 | 更易维护的原生曲线及连接端点 | 减少 ResNet 旁路碎线数量，移动节点后连接可追踪 | 当前只证实对象级可编辑，未证实自动跟随 |

第二轮 [独立评审](../dist/skill_tests/ml_fidelity/CRITIC_SECOND_REVIEW.md)记录了中间版本 ResNet 21/24、U-Net 17/24、CLIP 19/24。之后又修正了 U-Net 的上采样入口、左右高度和图例方向，以及 CLIP 的 Iₙ 干线，并给替换照片建立独立 `asset_1` 证据记录。第二轮分数不适用于这些再修订文件，最终结论以新的独立复评为准。

## 最终受审结果

| 图 | 独立评审 | 六维总分 | 冻结门槛 |
|---|---|---:|---|
| ResNet Figure 2 | [第三轮完整复评](../dist/skill_tests/ml_fidelity/CRITIC_FINAL_REVIEW.md) | 21.5/24 | 通过 |
| CLIP Figure 1 | [第三轮完整复评](../dist/skill_tests/ml_fidelity/CRITIC_FINAL_REVIEW.md) | 21/24 | 通过 |
| U-Net Figure 1 | [第四轮专项复评](../dist/skill_tests/ml_fidelity/CRITIC_UNET_FINAL_REVIEW.md) | 21/24 | 通过 |

评审保留了早期失败版本和每轮受审文件哈希。通过表示这三个指定原图在本次结构、视觉语法、导出可读性和对象级可编辑性门槛下合格；不延伸为像素一致、实际投影/印刷合格、期刊接收或 V7.6 稳定版验收。CLIP 的照片是许可明确的替换素材。连接线虽为原生 PowerPoint 对象，但没有绑定节点端点，移动节点后不会自动跟随；ResNet 旁路由多个小线段构成，后续可改进编辑维护性。
