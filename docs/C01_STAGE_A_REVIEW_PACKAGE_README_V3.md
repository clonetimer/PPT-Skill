# C01 Image2 Stage-A V3 专家复审材料包

本包包含 C01 FBG-SEANet 修订后的 Image2 目标图，以及完成技术复审所需的源证据、拓扑约束和历史审查意见。

## 文件清单

- C01_Image2_target_v3_1920x1080.png — 本轮目标图（待复审，不是已批准稿）。
- C01_IMAGE2_STAGE_A_CANDIDATE_V3.md — 候选图说明、版本与哈希、修订摘要。
- C01_IMAGE2_TOPOLOGY_AUDIT_V8.md — 18 条方法级有向关系与内部示意连线的区分。
- C01_STAGE_A_TECHNICAL_REVIEW_2026-11-16.md — 原始技术预审意见。
- C01_STAGE_A_REMEDIATION_2026-11-16.md — 逐项整改记录。
- C01_composite_defense_slide_image_first_v8.json — V8 FigureSpec。
- c01_composite_expected_topology_v8.json — V8 Topology Contract。
- C01_V73_SOURCE.md — 原始来源和证据边界记录。

## 本轮关键变化

1. B₁、B₂、B₃、…、Bₙ 明确表示 N 可变；四个可见条目只是代表性展示。
2. B_i 子图与 Total graph 可见层统一为三节点示意；该设计不声称恢复真实数值邻接。
3. Input 保留 12 节点、4×3 和 8 条行内实线；虚线跨行连接仅为示意。
4. 撤销“精确九条虚线”声明；不声称已完成逐边数量核验。
5. 五个输出框标注为示意五类，只高亮 C₂。
6. 保留 IR/SR 未解决的术语差异。

## 验收状态

该材料包用于专家复审。AI 技术预审和 CI 自动化检查不代替项目指定的人类 Stage A 签核。Stage B 在人类批准前保持锁定。
