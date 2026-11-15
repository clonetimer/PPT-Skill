# C01-FBG 逐区来源对照记录（V7.4）

## 来源与术语边界

- 作者实验室原图页面：https://hai.snu.ac.kr/bbs/board.php?bo_table=sub4_1_a&wr_id=251
- 作者页面图像：https://hai.snu.ac.kr/data/editor/2606/78d439b23291567a99c14c62e0bbf0a6_1780552979_7277.jpg
- 论文/DOI：https://doi.org/10.1016/j.engappai.2026.115273

- 图形摘要：Seoul National University Hyperautonomy AI Lab 作者发布图，原图上方标题为 **Graph Construction (Time-Frequency Graph)**。
- 论文方法术语：Lee et al. (2026) 正文/摘要称该构建方法为 **frequency-band graph (FBG)**。
- 本版处理：保留原图标题，并在副标题标明论文术语“Frequency-band graph (FBG) construction”。不再用论文术语替换原图标题。
- 论文来源：Engineering Applications of Artificial Intelligence 179 (2026), 115273；DOI 10.1016/j.engappai.2026.115273。
- 原图仅作内部来源比对；本仓库交付可编辑结构重绘，不重新分发出版社或作者图片。

## 逐区核对

| 区域 | 原图可见内容 | V7.4 保留内容 | 证据边界 |
|---|---|---|---|
| 标题 | Graph Construction (Time-Frequency Graph) | 原标题逐字保留；副标题补充论文术语 FBG | 图题与正文方法术语不同层级，不互相覆盖 |
| Sensor signals | Sensor #1、#2、#M-1、#M及对应波形 | 保留四个传感器位置和波形示意 | 传感器照片由矢量符号替代；波形为示意，不是测量数据 |
| OCF | OCF框、Notch filter、上下两组波形、两处 Fault sensitivity 标识及方向提示 | 保留Notch filter、上下波形、两处Fault sensitivity标签，并明确“qualitative” | 不添加滤波参数、幅值、灵敏度数值或故障检测性能 |
| OCF效果 | 图中标注operational component removed，并显示故障敏感性线索 | 保留operational component removed，并标注Fault sensitivity cues clearer (qualitative) | 只保留定性线索，不声称定量增益 |
| 频带子图 | Sub graph 1: 1st band；Sub graph 2: 2nd band；Sub graph 3: 3rd band；…；Sub graph N: Nth band | 用相同序号语义标注四个代表频带，并保留省略号 | 不虚构具体频率区间、带宽或截止频率 |
| 频率方向 | 原图有Frequency方向箭头，频带子图沿频率方向排列 | 增加明确的Frequency方向箭头 | 方向为来源可见；具体频率数值未提供 |
| Total graph | 频带子图连接形成Total graph | 保留Total graph及四组代表层 | 图边与节点坐标仍为示意，不代表数值邻接矩阵 |
| 连接关系 | 子图之间以可见连线/虚线表达关联 | 保留跨频带连接，并在图注明确inter-band links schematic | 不推断每条边的物理含义或精确拓扑 |

## 当前验收断言

- 原图标题存在且未被论文术语替换。
- 副标题包含Frequency-band graph (FBG) construction。
- 四个频带标签、ellipsis和Frequency方向箭头均存在。
- OCF/notch filter、operational component removed、两处Fault sensitivity及定性效果说明均存在。
- 图中没有数值频带截止值、波形幅值或邻接矩阵声明。
- PPTX为原生可编辑对象；每个对象有替代文本；不包含整图栅格化图片。

## 仍需专家判断

1. OCF前后故障敏感性视觉提示是否足以表达原图的定性含义。
2. 代表频带的数量和“…”是否在目标演示尺寸下清晰。
3. 原图结构重绘与答辩版式之间的抽象程度是否合适。

CI通过只证明上述结构断言和对象检查通过，不替代机械故障诊断领域专家终评或投影可读性测试。
