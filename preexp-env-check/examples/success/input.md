# ✅ 成功样例：环境全部就绪

## 输入（用户请求 + 环境）

**用户请求**：
> 我要跑功耗实验了，帮我检查一下环境

**SSH 环境**：
- PEEC_SSH_HOST / USER / KEY 已正确设置
- 服务器可达，SSH 凭据有效

**覆盖参数**（用默认值）：
- lptest: /data/ts-home/p00954667/tool/lptest0d0
- turbocfg 参数: 17 9 50
- NPU: 4

## 可判定预期

Agent 触发本 Skill，依次执行两项检查，产出报告：

1. **检查项 1（固件驱动+pid）** → status=pass
   - 原始输出含 `p[10]i[20]d[300]` 格式 + `cmd turbocfg exec succ`
   - failure_class=none
2. **检查项 2（NPU 可见设备）** → status=pass
   - ASCEND_RT_VISIBLE_DEVICES == `4,5,6,7`
   - failure_class=none
3. **总体结论**：可开跑

## 证明

证明主路径可用：两项检查全过，Agent 给出"可开跑"结论并附每项原始输出。
对应 slide7「成功样例：完整典型输入 → 产物完整、格式正确、证据可反查」。
