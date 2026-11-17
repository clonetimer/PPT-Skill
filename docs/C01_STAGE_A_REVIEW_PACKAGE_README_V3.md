# C01 Image2 Stage-A V3 专家复审材料包

**候选文件：** `C01_Image2_target_v3_1920x1080.png`  
**尺寸：** 1920 × 1080  
**格式：** PNG  
**大小：** 266,044 bytes  
**SHA-256：** `0a1d079218cc73d87d5045f0c3cd1303d0bc53237670271dfacb61919fb58337`

## 文件清单

- `C01_Image2_target_v3_1920x1080.png` — Image2 目标图 V3（待人工复审，不是已批准稿）。
- `C01_IMAGE2_STAGE_A_CANDIDATE_V3.md` — 候选图版本、哈希、视觉检查记录。
- `C01_STAGE_A_TECHNICAL_REVIEW_2026-11-16.md` — 对 V2 的技术预审意见。
- `C01_IMAGE2_TOPOLOGY_AUDIT_V8.md` — 18 条方法级有向关系与内部示意连线的区分。
- `C01_STAGE_A_REMEDIATION_2026-11-16.md` — 逐项整改记录。
- `C01_V73_SOURCE.md` — 论文与作者实验室图来源、证据边界。
- `C01_composite_defense_slide_image_first_v8.json` — V8 FigureSpec。
- `c01_composite_expected_topology_v8.json` — V8 Topology Contract。
- `deck_spec_v8.example.json` 与 `image_first_workflow_v8.example.json` — 单页内容锁与双阶段工作流示例。

上述工程源文件以 PR #17 的分支提交为准：
https://github.com/clonetimer/PPT-Skill/tree/feature/image-first-v8-20261115

## V3 修订重点

1. B₁、B₂、B₃、Bₙ 与 Total graph 可见层统一为三节点示意。
2. 明确频带数 N 可变；四个可见条目只是代表性示例。
3. 撤销精确九条虚线声明；跨频带与跨行虚线仅作示意。
4. Input 保留 12 节点、4×3、8 条行内实线。
5. 五个分类输出仅为示例，只高亮 C₂。
6. 保留 Total graph → Input、Input → GCN 及 Input → EA → GCN 两条路径。
7. 保留向下 Frequency 轴、两个 IR readout 分支及 IR/SR 未解决说明。

## 视觉预检

- 1920 × 1080 文件尺寸核验：PASS
- PNG 可解码：PASS
- 主要方法路径与分支可见：PASS（视觉预检）
- 变量 N、示意虚线、示意五类说明：PASS（视觉预检）
- 人工科学内容/原图一致性/投影可读性签核：待完成

**重要：** AI 视觉预检与 CI 通过不等于人类 Stage A 批准。Stage B 在指定人类审查人完成六项检查并批准前保持锁定。
