# 实验前环境检查报告

> 本模板是 Skill 输出报告的固定格式。Agent 汇总各 check_*.py 的结构化结果后按此格式填充。
> 每一项结论都附「原始命令输出」折叠区，满足 slide10「从结论反查原始证据」。

**检查时间**：{timestamp}
**服务器**：{ssh_user}@{ssh_host}:{ssh_port}
**总体结论**：{overall_conclusion}  <!-- 可开跑 / 不可开跑 -->

---

## 检查项总览

| # | 检查项 | 状态 | 失败分类 | 关键? |
|---|---|---|---|---|
| 1 | 固件驱动 + pid 生效 | {status_1} | {fc_1} | 是 |
| 2 | NPU 可见设备 | {status_2} | {fc_2} | 是 |

状态取值：✅ pass / ❌ fail / ⚠️ warn

---

## 检查项 1：固件驱动 + pid 生效

- **状态**：{status_1}
- **执行命令**：`{command_1}`
- **预期判据**：输出含 `p[...]i[...]d[...]` 格式且 `cmd turbocfg exec succ`
- **实际值**：{actual_1}
- **失败分类**：{fc_1}
- **修复建议**：{fix_hint_1}
- **failed 17 自动重试**：{retry_attempted_1}  <!-- 是/否；若是附重试命令与输出 -->

<details>
<summary>原始命令输出（点击展开）</summary>

```
{stdout_1}
{stderr_1}
{retry_stdout_1}
```
</details>

---

## 检查项 2：NPU 可见设备

- **状态**：{status_2}
- **执行命令**：`echo $ASCEND_RT_VISIBLE_DEVICES`
- **预期判据**：值为预期值（默认 `0`，或 `PEEC_EXPECTED_VISIBLE` 指定）
- **实际值**：{actual_2}
- **失败分类**：{fc_2}
- **修复建议**：{fix_hint_2}

<details>
<summary>原始命令输出（点击展开）</summary>

```
{stdout_2}
{stderr_2}
```
</details>

---

## 总体结论与下一步

{overall_detail}

<!-- 当全部 pass： -->
<!--   当前环境已就绪，可开跑实验。请继续人工执行：拉起 vllm 服务、修改实验脚本日期、运行 HY_PID_run.sh。 -->
<!-- 当任一 fail： -->
<!--   当前环境不可开跑。不通过项见上表，请按各检查项的「修复建议」处理后，重新触发本检查。 -->

---

*本报告由 preexp-env-check Skill 自动生成。原始证据见各检查项折叠区。*
