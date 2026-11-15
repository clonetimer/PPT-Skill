# 首次复现质量门禁（源图 PDF → 原生可编辑 PPTX）

本流程与原有 FigureSpec 科学语义检查互补：针对作者提供的**矢量 PDF**，自动检测源图风险、逐对象导入质量和最终渲染差异，尽早把不可信的“结构 PASS”转为显式复核任务。它并不推断科学结论或自动认证期刊质量。

## 1. 标准执行

```bash
python -m pip install python-pptx PyMuPDF Pillow numpy reportlab
python tools/figure_first_pass_gate.py source.pdf \
  --pptx out/source_editable.pptx \
  --report out/first_pass.json \
  --auto-export \
  --preview out/source_vs_candidate_vs_diff.png
```

使用 `--inspect-only` 时仅分析源图，不执行转换。使用 `--exported-pdf` 可指定从**目标 PowerPoint 宿主**导出的 PDF；`--auto-export` 在系统安装 LibreOffice 时使用该宿主。没有可用渲染器时保留结构报告，状态为 `NEEDS_REVIEW`，不得伪称视觉验收通过。

## 2. 问题出现之前就预警

| 源图特征 | 首轮风险 | 自动处理与边界 |
|---|---|---|
| 4 段闭合 Bézier 构成标准椭圆 | 雷达圆环采样后出现缺口 | 严格切线/四端点识别后转换成原生 PowerPoint 椭圆；非规则超图回环不替换 |
| PDF 图表裁剪路径 | 雷达线/柱图溢出或斜线纹理丢失 | 标记 `CLIPPED_PLOTS` 并审视最终面板；复杂非矩形裁剪不冒充完整支持 |
| 异常线宽（>1584 pt） | 转换器无法表示或直接遗漏 | 标记 `UNREPRESENTABLE_STROKE`，要求源图渲染对照确认 |
| PUA、替代字符、数学字体 | 公式语义乱码 | `SUSPICIOUS_UNICODE`/`MATH_FONT`；必须根据论文原文核对，不从字形猜测公式 |
| 源图仅有嵌入图像 | 整图无法原生编辑 | `RASTER_ONLY`，不得以图片对象数掩盖编辑性不足 |
| 高密度路径与小字号 | 图例、统计曲线、数字密集造成失真 | `DENSE_VECTORS`/`TINY_LABELS`；终尺寸单独检查 |

## 3. 双层质量约束

**结构层**检查：源 PDF 的文字对象、独立图片、矢量保留量、画布尺寸、整图替代、越界。原生 `AUTO_SHAPE` 椭圆计入矢量对象，避免正确的几何简化被误判为路径丢失。

**渲染层**检查：将源 PDF 与 PowerPoint/LibreOffice 导出的 PDF 在同一像素尺寸渲染。输出全图 SSIM 风格相似度、标准化平均像素差、4×4 空间分区的最低相似度和并排差异图。当前默认*复核触发阈值*：全图 <0.88，或任一分区 <0.70。它是保守工程筛查线，**不是论文视觉保真合格分**；不同字体替代会影响分数，需要实际观察差异面板。

| 状态 | 含义 | 处理 |
|---|---|---|
| `FAIL` | 结构损失、整图扁平化或越界 | 停止交付，修复后从同一源图重新构建 |
| `NEEDS_REVIEW` | 存在字体/裁剪/视觉风险，或缺实际渲染对照 | 人工核对原图、公式、统计数值与标注，再单独记录验收 |
| `TECHNICAL_PASS` | 结构与渲染前检未发现门槛问题 | **仍不代表**科学准确、Office 2016 实机通过、无版权风险或最终发布合格 |

## 4. 冻结陌生图件首次结果

首次复现的评价不能使用已用于调参的 Mamba、Swin、MMGraph-Agent 样本直接宣称泛化能力。每一轮开始先冻结**模型/脚本版本、从未参与开发的源 PDF、文献页码、关键边/公式/标签、目标 PPTX 宿主及评分规则**。对每份源图保留：

1. 第一次生成的 PPTX/PDF/PNG、SHA-256、结构报告、风险区域和初次独立评分；
2. 逐次修复的修改记录与第二轮结果，不能覆盖首轮文件；
3. 原论文科学语义 4/4、其余五维每项至少 3/4、总计至少 21/24 的独立验收；
4. Office 2016（如为目标）的实际打开、保存、再导出记录。

首次复现成功率口径：

`通过首次科学语义 + 视觉 + 编辑性验收的独立留出源图数 / 独立留出源图总数`

这是待测指标；**本轮的合成回归测试不能替代真实独立论文样本评分**。

## 5. 回归

```bash
python tools/test_pdf_figure_import.py
python tools/test_audit_imported_pdf_figure.py
python tools/test_figure_first_pass_gate.py
```

测试包含闭合圆环识别/超图回环反例、图表裁剪、不可表示线宽、纯图片来源、局部图表抹除对照、原生椭圆编辑性以及包含节点和圆环的独立样例。GitHub Actions 执行上述检查；Linux 工作流不能等同于 Office 2016 实机试验。
