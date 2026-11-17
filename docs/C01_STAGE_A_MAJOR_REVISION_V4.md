# C01 Image2 V4 — Major Revision 整改记录与复审门槛

**版本：** V4 presentation Stage-A candidate  
**评审依据：** 2026-11-16 学术编辑 Major Revision 评审报告（用户提供）  
**上一候选：** C01_Image2_target_v3_1920x1080.png  
**新候选：** C01_Image2_target_v4_1920x1080.png  
**V4 图像 SHA-256：** f463c28b5a45a2bbb0f0d220819c52ac8ba3170d5fd6ba539636aea9d514293f  
**状态：** 尚未获得独立专家 Stage A 批准；Stage B 未开始。

## 1. 已执行的 P1 整改

| 评审事项 | V4 处理 | 证据与未解决边界 |
|---|---|---|
| 频带内/频带间图连接抽象过度 | 在 Total graph 中明确展示斜向跨频带虚线实例；新增实线=频带内、虚线=频带间小图例 | 三节点 motif 与虚线仍属示意，不是完整真实数值邻接矩阵 |
| 传感器数量 M 缺失 | 增加 Sensor #1、Sensor #2、Sensor #M−1、Sensor #M 和 M variable | M 真实值不在公开框架图中给定；三节点图示不代表 M=3 |
| 融合运算符不一致 | 强制使用圆形 +，并为 FigureSpec/Topology/回归测试添加精确符号校验 | 原作者实验室图为 +；V3 Image2 曾错误生成 Σ |
| IR/SR 尚待核实 | 保留原作者实验室图中两个 IR layer，另标注论文摘要和 Highlights 使用 SR | 尚未确认全文图注/术语定义一致，禁止声称两者等价 |

## 2. P2 改进

| 评审事项 | V4 处理 | 仍需验收 |
|---|---|---|
| 期刊版式不适宜 | 保留答辩用 slide 模式，另列独立 publication profile 规范 | 期刊双子图排版、图注、单/双栏最小字号仍待独立实现 |
| OCF 过程不直观 | 以 Before / After 两条独立示意波形补充滤波机制说明 | 波形仅为示例，不是测量数据或滤波性能证据 |
| 跨面板线干扰标题 | Total graph → Input 沿左外侧空白布线，避开下半区标题 | 需对 Image2 PNG 和后续 PPTX 进行人工阅读路径审查 |

## 3. 科学证据边界

- 论文作者实验室公开页面：https://hai.snu.ac.kr/bbs/board.php?bo_table=sub4_1_a&wr_id=251
- 论文出版社页面：https://www.sciencedirect.com/science/article/pii/S0952197626015575
- 作者实验室图可见 Sensor #1、#2、#M−1、#M、圆形 + 与两个 IR layer。
- 出版社摘要与 Highlights 写明 SR。现有证据不足以证明 IR 和 SR 的技术定义完全等价。
- 18 条有向方法链路约束继续保留，但内部频带图的具体邻接矩阵并未恢复。
- M 与 N 均为可变维度，示意节点和五个分类框均不代表固定算法参数。
- OCF 机制示意不对应实验信号或定量性能。

## 4. Stage A 冻结条件

1. 科学内容与作者实验室图的可见模块、方向、运算符一致。
2. 所有必需文字准确，无 Image2 将 + 变成 Σ 或漏掉 Sensor #M 等错误。
3. 所有示意关系明确标注，不把示意图当作真实邻接矩阵或测量结果。
4. 演示尺寸下标题、流程箭头、证据说明可读。
5. 布局可用可编辑 PPTX 原生对象复现。
6. 指定人类审核人完成六项审查并明确批准。

未满足任一项，保持 Stage A `needs_revision` 或 `generated`；不得将 V4 标为 `approved`，不得宣称 Stage B 已完成。

## 5. V4 与期刊版的边界

V4 是答辩/学术汇报用的高保真方法说明页。对期刊图仍需另行生成紧凑的 (a) FBG construction 和 (b) Graph-level diagnosis 双子图，长说明放入图注，字体与最终排版目标栏宽匹配，并交付可编辑矢量格式。未经正文和图注核验，不将这种图称作严格复现或期刊定稿。
