# C01-SEANet Stage 1 评审整改对照（V7.6）

## 历史评审结论

评审对象是 Stage 1 初始文件 C01_SEANet_initial.pptx，不是后续修复版本。修订后的评分为 **12/24，FAIL**；此前 17/24 PASS 已被评审记录撤销。

主要缺陷：
1. 初始文件只绘制下方 graph-level diagnosis panel，上方 FBG construction 整体缺失。
2. Input 多频带/多子图层次被简化。
3. 两个 pooling 外形与作者实验室图中的倾斜四边形不符。
4. Dense 后五个纵向独立输出方块被简化为一个。
5. 88 个对象缺少有效替代文本和整图阅读顺序。
6. 引用和重大结构性改绘披露不足。
7. 未提供自动化重建脚本/依赖链。

## 整改与交付分层

| 评审要求 | 当前处理 | 对应资产/自动检查 |
|---|---|---|
| 同屏展示完整上下两部分和 Total graph → Input | 完整双面板 composite；独立 SEANet 文件保留为下半部分摘绘并明确披露 | C01_composite_defense_slide_v75；18 条关键路线检查 |
| Input 保留多频带/多子图视觉层次 | composite Input 中增加四组频带子图示意图标、节点群和跨组连接；明确 adjacency schematic | validate_c01_composite_v75.py |
| 两个 pooling 恢复源图倾斜轮廓 | standalone v7.4 与 composite v7.5 均使用可编辑 freeform quadrilateral，具有近竖直侧边和倾斜上下边 | standalone/composite validators |
| Dense 后恢复五个方块 | 五个独立方块，第二个橙色高亮 | composite validator |
| 替代文本与阅读顺序 | 对象级 alt text；整图标题描述；上下 panel 阅读顺序 | PPTX accessibility validators |
| 来源与重绘边界 | 说明作者实验室视觉来源、publisher 高清图未能访问、矢量替代和 schematic graph 边界 | C01_V73_SOURCE.md、C01_V76_SOURCE_CORRECTION.md |
| IR/SR 术语 | 可见图标签保留 IR layer；说明公开摘要使用 SR；差异未解决 | standalone/composite specs 与 validators |
| 可复现构建 | FigureSpec、builder、renderer、validator、CI 和修复历史一起保留 | MANIFEST_V7.json 与 CI |

## 评审状态

- Stage 1 初始版：历史 FAIL，保留原记录，不覆盖。
- Standalone SEANet v7.4：已明确为 lower-panel excerpt，不代表完整双面板。
- Composite v7.5：完整双面板修复候选；本轮新增 pooling 几何与 IR/SR 边界整改。
- CI PASS 只证明自动结构/对象/交付断言通过，不构成独立领域专家 PASS。
- 人工终评、真实投影/印刷尺寸、PowerPoint 2016 主机往返：仍须单独验收。
