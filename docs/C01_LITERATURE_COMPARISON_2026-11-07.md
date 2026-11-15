# C01 生成 PPT 与作者实验室图形摘要的差异审查（2026-11-15 修订）

## 审查范围与证据来源

直接视觉比对来源为 Lee 等（2026）作者实验室发布的图形摘要：

https://hai.snu.ac.kr/data/editor/2606/78d439b23291567a99c14c62e0bbf0a6_1780552979_7277.jpg

论文公开摘要/Highlights 页面：

https://www.sciencedirect.com/science/article/pii/S0952197626015575

**出版社高清 graphical abstract 直接访问失败，未完成出版社原图核验。** 先前文档中“已检查出版社 1198 × 886 原图”及其下载哈希均已撤回，详见 C01_V76_SOURCE_CORRECTION.md。

本审查按是否改变观众对方法步骤、信息流、科学作用或输出的理解分级。图件为答辩用结构重绘，不以像素一致为目标。没有获得足以恢复精确邻接矩阵、实测波形、数值频率边界或全文内部细节的来源。

| 比较项 | 作者实验室图形摘要可见内容 | 当前整改要求 | 判断与影响 |
|---|---|---|---|
| 上下两部分 | 上方 Graph Construction (Time-Frequency Graph)；下方 Graph-level fault diagnosis framework；Total graph 连至 Input | 完整双面板 composite 同屏呈现上下两部分及跨面板输入连接；单独 SEANet 图须明确标为下半部分摘绘 | 不得将下半部分摘绘冒充完整 graphical abstract |
| OCF 与频带构建 | Sensor signals → OCF/notch filter → band subgraphs → Total graph；上方含频率方向及第 1、2、3、N 频带标识 | 保留 OCF、band-pass、频带顺序、频率方向和 Total graph；数值 cutoffs 不作推断 | 保留方法步骤，不伪造滤波参数 |
| OCF 效果 | 图中呈现滤波前后波形和定性 fault-sensitivity 线索 | 保留定性线索，不声称数值增益 | 不添加无来源的灵敏度指标 |
| Input 图结构 | 下方 Input 是多层堆叠图表示，不是单个扁平小网络 | 用可编辑多子图/多群结构保留视觉层次；明确 adjacency schematic | 结构层次必须保留，但不能推断逐边数值拓扑 |
| Pooling | 两个 pooling 均为左右近竖直、上下边倾斜的四边形轮廓 | 两处均使用可编辑 freeform quadrilateral；箭头端点对齐 | 矩形或常规对称梯形均不符合来源轮廓 |
| Readout 标签 | 作者实验室图中两处小字视觉上似为 IR layer | 图件保留来源可见 IR layer，同时说明公开摘要使用 SR 表述 sensitivity-aware readout；差异未解决 | 不得把公开摘要术语静默替换为来源图标签，也不作最终术语裁决 |
| Readout 路径 | Main route 的 pooling2 → 上方 readout → summation；pooling1 另分支至下方 readout → summation；EA 由 Input 输入并馈入首个 GCN | 保留两条 readout 分支及 EA→first GCN，禁止 EA→lower-readout 捷径 | 路径方向属于关键科学信息 |
| 分类输出 | Dense 后有五个纵向独立方块，第二个橙色高亮 | 保留五个独立可编辑方块和第二方块高亮 | 不能简化为一个橙色方块 |
| 传感器和图节点外观 | 使用传感器照片、波形及节点/连边图 | 可用矢量符号替代照片；波形与图拓扑示意必须披露 | 不声称是真实传感器型号、遥测波形或数值邻接矩阵 |

## 当前验收边界

- C01-SEANet v7.4 是下半部分摘绘，已明确标注 excerpt；完整上下两部分由 C01-composite 提供。
- C01-composite 需要通过 pooling 几何、五方块输出、Input 多子图层次、跨面板 Total graph → Input、替代文本和阅读顺序检查。
- 作者实验室图形摘要是本轮直接视觉来源；出版社高清图未核验。
- IR/SR 标签差异保持未决；如需最终裁定，必须取得出版社原图或可核验全文。
- 投影/印刷终尺寸检查、领域专家终评及 PowerPoint 2016 主机往返均不能由 CI 代替。
