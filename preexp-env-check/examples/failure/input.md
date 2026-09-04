# × 失败样例：关键项不通过 → 停止并报告

本目录含三个失败场景，每个都应触发「停止 + 报告修复动作」，证明 Skill 不该继续时会停止
（slide7 失败样例：缺关键证据/越界/无权限 → 停止并解释，反馈能指导修复）。

---

## 失败场景 A：failed 7（固件驱动版本不对）

**输入**：用户请求检查环境，SSH 信息齐全，服务器可达。
**远程命令输出**：
```
failed 7
```
**预期**：
- 检查项 1 status=fail，failure_class=failed_7
- **停止**（不继续检查项 2 也可，或继续但总体结论已是不可开跑）
- 报告 fix_hint：「固件驱动版本不支持当前 lptest/lpmi，需升级或回退固件驱动到支持版本，联系环境维护同学。」
- 总体结论：❌ 不可开跑
- 证据：原始输出 `failed 7` 可反查

## 失败场景 B：pid 未生效（输出无 p[]i[]d[] 格式）

**输入**：用户请求检查环境，SSH 信息齐全。
**远程命令输出**：
```
cmd:turbocfg exec succ
```
（有 succ 但没有 p[]i[]d[] 格式）
**预期**：
- 检查项 1 status=fail，failure_class=pid_not_effective
- **停止**
- 报告 fix_hint：「pid 参数未写入生效，检查 pid 下发流程是否执行、turbocfg 是否成功落盘，重新下发 pid 后再触发检查。」
- 总体结论：❌ 不可开跑

## 失败场景 C：failed 17 重试仍失败

**输入**：用户请求检查环境，SSH 信息齐全。
**首次命令输出**：`failed 17`
**自动重试**：脚本拉起 lpmi_tool try-repair → 等 5 秒 → pkill -INT → 重跑 turbocfg
**重试后输出**：`failed 17`（仍未恢复）
**预期**：
- 检查项 1 status=fail，failure_class=failed_17_retry_failed
- evidence.retry_attempted=true，附重试命令与重试输出
- **停止**
- 报告 fix_hint：「failed 17 自动重试仍失败，需人工登录服务器手动启动 lpmi_tool 排查，或检查 NPU 卡状态。」
- 总体结论：❌ 不可开跑

## 失败场景 D：NPU 可见设备不符

**输入**：用户请求检查环境，SSH 信息齐全，检查项 1 通过。
**检查项 2 命令输出**：`4,5,6`（少一张卡）
**预期**：
- 检查项 2 status=fail，failure_class=npu_mismatch
- **停止**
- 报告 fix_hint：「ASCEND_RT_VISIBLE_DEVICES 当前为 4,5,6，应为 4,5,6,7。在服务器对应 shell/容器内重新 export ASCEND_RT_VISIBLE_DEVICES=4,5,6,7 后重新触发检查。」
- 总体结论：❌ 不可开跑

---

## 证明

四个场景覆盖所有 failure_class，每个都满足 slide7 失败样例三要素：
1. ✅ 停止（不继续跑实验）
2. ✅ 解释原因（failure_class + actual vs expected）
3. ✅ 反馈能指导修复（fix_hint 给出具体动作）
4. ✅ 证据可反查（原始命令输出）

现场演示建议：故意把 pid 设错或断开网络，演示场景 A 或 D，最能直观证明「会停」。
