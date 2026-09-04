# 失败样例 —— 预期报告（以场景 A：failed 7 为例）

# 实验前环境检查报告

**检查时间**：2026-09-01 10:05:00
**服务器**：p00954667@10.x.x.x:22
**总体结论**：❌ 不可开跑

---

## 检查项总览

| # | 检查项 | 状态 | 失败分类 | 关键? |
|---|---|---|---|---|
| 1 | 固件驱动 + pid 生效 | ❌ fail | failed_7 | 是 |
| 2 | NPU 可见设备 | —（因关键项已失败，停止） | — | 是 |

---

## 检查项 1：固件驱动 + pid 生效

- **状态**：❌ fail
- **执行命令**：`/data/ts-home/p00954667/tool/lptest0d0 turbocfg 17 9 50`
- **预期判据**：输出含 `p[...]i[...]d[...]` 格式且 `cmd turbocfg exec succ`
- **实际值**：failed 7
- **失败分类**：failed_7
- **修复建议**：固件驱动版本不支持当前 lptest/lpmi，需升级或回退固件驱动到支持版本，联系环境维护同学。
- **failed 17 自动重试**：否（失败分类非 failed 17，不触发重试）

<details>
<summary>原始命令输出（点击展开）</summary>

```
failed 7
```
</details>

---

## 总体结论与下一步

❌ 当前环境不可开跑。

不通过项：检查项 1（固件驱动 + pid 生效），失败分类 failed_7。
原因：固件驱动版本不支持当前 lptest/lpmi。
建议修复动作：升级或回退固件驱动到支持版本，联系环境维护同学。

修复后请重新对我说「检查环境」触发本检查，全过即可开跑实验。

---

*本报告由 preexp-env-check Skill 自动生成。原始证据见各检查项折叠区。*

---

## 其他失败场景的预期报告差异

- **场景 B（pid 未生效）**：failure_class=pid_not_effective，fix_hint 指向「重新下发 pid」
- **场景 C（failed 17 重试失败）**：evidence.retry_attempted=true，附重试命令与输出；fix_hint 指向「人工启动 lpmi_tool 排查」
- **场景 D（NPU 不符）**：检查项 1 为 pass，检查项 2 为 fail（npu_mismatch），fix_hint 指向「重新 export ASCEND_RT_VISIBLE_DEVICES」
