# C01 FBG-SEANet — V8 拓扑核验与证据边界

**用途：** 对 2026-11-16 Stage A 技术预审意见作工程化响应，并为下一轮 Image2 目标图与后续 PPTX 重建提供可审计约束。  
**状态：** V8 修订基线；不构成 Stage A 人工批准。

## 1. 必须区分的两类“边”

### A. 方法流程的 18 条关键有向关系

以下关系作为方法级流程约束保留，必须在目标图和 PPTX 中表达，方向不得颠倒：

1. Input → GCN₁
2. GCN₁ → pooling₁
3. pooling₁ → GCN₂
4. GCN₂ → pooling₂
5. pooling₂ → IR₁
6. IR₁ → Σ
7. Input → Energy-assisted module
8. Energy-assisted module → GCN₁
9. pooling₁ → IR₂
10. IR₂ → Σ
11. Σ → Dense
12. OCF/notch → band-pass / band-subgraph construction
13. Total graph → Input
14. B₁ → Total graph
15. B₂ → Total graph
16. B₃ → Total graph
17. Bₙ → Total graph
18. Dense → class outputs

这 18 条是流程/数据路径的语义约束，不是 Total graph 或 Input 图内部虚线连接的数量。

## 2. 图内部节点与连线的处理

| 区域 | V8 表达 | 证据性质 |
|---|---|---|
| B_i 子图 | 每个可见子图采用 3 节点、2 条实线的简单图标 | 为与 Total graph / Input 图保持视觉一致而采用的示意性设计，不声称恢复真实子图邻接 |
| Total graph | 显示 B₁、B₂、B₃、Bₙ 四个代表性层，每层 3 节点 | 四个可见层仅为布局示例，实际频带总数为可变 N |
| Input 图 | 12 节点，4 行×3 列，8 条行内实线 | 作者实验室示意图中的可见结构；节点位置和连线不代表数值邻接矩阵 |
| 跨频带/跨行虚线 | 只保留少量稀疏虚线，明确标注 schematic | 具体条数不作声明，不作为科学拓扑事实，不计入 18 条流程关系 |

**撤销“精确九条虚线”这一未获来源逐边证据支持的表述。** V8 不再设置 inter_band_link_count=9 或 inter_row_link_count=9。渲染图中实际画出的少量虚线仅服务于示意表达，不代表算法真实邻接数量。

## 3. 频带数量 N

可见标签采用：

B₁, B₂, B₃, …, Bₙ

- N 为可变频带数；
- 画面可显示四个代表性条目 B₁、B₂、B₃、Bₙ；
- 不得将“四个可见条目”表述成“算法固定四频带”；
- Total graph 的四个可见层同样是展示样例，不代表总层数恒为四。

## 4. 分类输出

- 画面保留五个方形输出示例；
- 仅 C₂ 使用橙色高亮；
- 明确标注 “5-class illustrative output” 或等义文字；
- 五个输出框不构成算法对所有数据集固定五类的声明。

## 5. IR / SR 术语

- 保留作者实验室示意图中可见的两个 “IR layer” 标签；
- 说明公开摘要使用 “SR”；
- 术语对应关系仍未解决，不擅自扩写、替换或宣称等价。

## 6. Stage A 复审检查项

- [ ] B₁/B₂/B₃/Bₙ 标注完整，N 可变性明确；
- [ ] B_i、Total graph 可见层采用一致的三节点示意；
- [ ] Input 图为 12 节点、4×3，8 条行内实线；
- [ ] 不出现“精确九条”或其它未证实的虚线数量声明；
- [ ] 18 条方法级有向关系完整、方向正确；
- [ ] Frequency 箭头向下；
- [ ] 两条 IR 分支在 Σ 汇合后进入 Dense；
- [ ] 五类输出明确为示例，只高亮 C₂；
- [ ] IR/SR 术语差异仍披露；
- [ ] 右侧说明和图中小节点适合 1080p 投影。

Stage A 复审通过后，才允许 Stage B 开始原生 PPTX 重建。
