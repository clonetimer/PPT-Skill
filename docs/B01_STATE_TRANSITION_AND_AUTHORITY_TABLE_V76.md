# B01 状态转换与控制权限边界（V7.6）

## 证据范围

B01 是根据用户提供的答辩视觉参考（slide 213）整理的工程概念示意，不是某一型号卫星的完整 FDIR 状态机，也不是时序性能证明。原始 PPT 未在仓库中重新分发。

本表只转录图中明确出现的状态、箭头标签和控制权限措辞。未在来源中明确的守卫谓词、角色身份、指令接口和任务时序均保持未定义，不作推断。

## 图中可见的状态与条件

| 状态 | 图中可见说明 | 解释边界 |
|---|---|---|
| NORMAL | Nominal control；No active fault | 正常控制且没有活动故障；未定义进入该状态的完整条件 |
| RECONFIG | Fault confirmed；Reconfig. authorized | 故障确认且重构获得授权；图中未定义确认阈值、授权主体或授权协议 |
| DEGRADED | Reduced capability；Resources available | 能力降级且资源可用；这是状态说明，不单独等同于完整转换守卫 |
| SAFE | Safe response；Safety boundary hit | 触及安全边界时进入安全响应；图中未给出全部安全阈值或恢复逻辑 |

## 图中可见的转换关系

| 图示路径 | 可见标签 | 可以作出的陈述 | 不应扩展的陈述 |
|---|---|---|---|
| NORMAL → RECONFIG | fault | 故障事件路径触发后续重构流程 | 不推断具体故障检测阈值、隔离算法或确认时限 |
| RECONFIG → DEGRADED | rec. | 图中显示重构流程继续进入降级运行状态 | 不推断所有重构都会导致降级，也不推断自动切换条件 |
| guarded path → SAFE | safety / resource guard | 图中存在安全/资源守卫关联的 SAFE 路径 | 不推断具体守卫公式、优先级或 SAFE 恢复路径 |
| SAFE → NORMAL | 未显示 | 不作声明 | 不补画自动复位或任务恢复箭头 |

## 控制权限边界

- 图中明确使用 authorized reconfiguration，因此重构不是无条件动作。
- 图中涉及控制分配重构，并列出通信、推进和 ADCS 授权范围。
- 图中没有给出授权主体、权限矩阵、命令确认协议、拒绝/超时策略或不同分系统的完整控制权交接表。
- 0.1 s 原时序标记已删除，因为当前来源材料没有提供可核查的任务时序依据。
- 图件现标注 Engineering concept schematic · no mission-specific timing is asserted.

## 验收方式

1. 对照 B01 PPTX，确认四个状态和可见箭头标签一致。
2. 检查 0.1 s 不再出现。
3. 将本表作为伴随说明；若未来取得型号级状态机、权限矩阵或时序规范，再以独立来源补全，不以本示意推定具体型号实现。
