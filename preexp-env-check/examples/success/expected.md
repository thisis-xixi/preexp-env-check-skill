# 成功样例 —— 预期报告

# 实验前环境检查报告

**检查时间**：2026-09-01 10:00:00
**服务器**：p00954667@10.x.x.x:22
**总体结论**：✅ 可开跑

---

## 检查项总览

| # | 检查项 | 状态 | 失败分类 | 关键? |
|---|---|---|---|---|
| 1 | 固件驱动 + pid 生效 | ✅ pass | none | 是 |
| 2 | NPU 可见设备 | ✅ pass | none | 是 |

---

## 检查项 1：固件驱动 + pid 生效

- **状态**：✅ pass
- **执行命令**：`/data/ts-home/p00954667/tool/lptest0d0 turbocfg 17 9 50`
- **预期判据**：输出含 `p[...]i[...]d[...]` 格式且 `cmd turbocfg exec succ`
- **实际值**：cmd:turbocfg p[10]i[20]d[300] p[10]i[20]d[300] cmd turbocfg exec succ
- **失败分类**：none
- **修复建议**：（无）
- **failed 17 自动重试**：否

<details>
<summary>原始命令输出（点击展开）</summary>

```
cmd:turbocfg p[10]i[20]d[300] p[10]i[20]d[300] cmd turbocfg exec succ
```
</details>

---

## 检查项 2：NPU 可见设备

- **状态**：✅ pass
- **执行命令**：`echo $ASCEND_RT_VISIBLE_DEVICES`
- **预期判据**：值为 `4,5,6,7`
- **实际值**：4,5,6,7
- **失败分类**：none
- **修复建议**：（无）

<details>
<summary>原始命令输出（点击展开）</summary>

```
4,5,6,7
```
</details>

---

## 总体结论与下一步

当前环境已就绪，可开跑实验。请继续人工执行：拉起 vllm 服务、修改实验脚本日期、运行 HY_PID_run.sh。

---

*本报告由 preexp-env-check Skill 自动生成。原始证据见各检查项折叠区。*
