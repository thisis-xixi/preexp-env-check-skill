# SSH 远程检查使用说明

> 本文件说明 scripts/ 如何通过 SSH 连服务器执行检查命令、连接参数从哪来、
> 以及各类故障如何分类。脚本开发与答辩演示时参考本文件。

## 依赖

- Python 3.8+
- paramiko：`pip install paramiko`

## SSH 连接参数（从环境变量读取，安全红线）

脚本通过 `scripts/ssh_exec.py` 统一封装连接。参数一律从环境变量读取，
**绝不硬编码**到脚本或 skill 仓库：

| 环境变量 | 含义 | 示例 |
|---|---|---|
| `PEEC_SSH_HOST` | 服务器 IP/主机名 | `10.x.x.x` |
| `PEEC_SSH_PORT` | SSH 端口 | `22` |
| `PEEC_SSH_USER` | 登录用户 | `p00954667` |
| `PEEC_SSH_KEY` | 私钥路径（推荐） | `~/.ssh/id_rsa` |
| `PEEC_SSH_PASSWORD` | 密码（不推荐，密钥优先） | 仅在无密钥时用 |

> 用户使用前在本地 shell 设置这些变量，或写入本地不入库的 `.env`。
> skill 仓库中只有占位符与读取逻辑，没有任何真实凭据。

## 检查命令清单

| 检查项 | 远程命令 | 脚本 |
|---|---|---|
| 固件驱动+pid | `/data/ts-home/p00954667/tool/lptest0d0 turbocfg 17 9 50` | `check_firmware_pid.py` |
| failed 17 重试 | `lpmi_tool --device-id 4 --query-info --power-sampling --syscnt-scale 50000 --sampling-interval 50 --sampling-duration 200 --sampling-chip=910D --try-repair > lpmi_4.log 2>&1 &` | `check_firmware_pid.py` |
| NPU 可见设备 | `echo $ASCEND_RT_VISIBLE_DEVICES` | `check_npu_visible.py` |

## 脚本返回结构（统一 JSON）

所有 `check_*.py` 脚本以相同结构输出 JSON 到 stdout，供 Agent 解析：

```json
{
  "item": "firmware_pid",
  "status": "pass | fail | warn",
  "actual": "命令原始 stdout+stderr",
  "expected": "通过判据的文字描述",
  "failure_class": "failed_7 | pid_not_effective | failed_17_retry_failed | npu_not_set | npu_mismatch | none",
  "evidence": {
    "command": "实际执行的命令",
    "stdout": "...",
    "stderr": "...",
    "retry_attempted": false,
    "retry_stdout": "..."
  },
  "fix_hint": "不通过时给用户的修复建议（通过时为空）",
  "critical": true
}
```

Agent 只读 `status` / `failure_class` / `fix_hint` / `evidence` 来组织报告，
**不自行重新判断**命令输出（判断逻辑全在脚本里，可测可复现）。

## 故障分类总表

| failure_class | 触发条件 | 关键? | 处理 |
|---|---|---|---|
| `failed_7` | turbocfg 输出含 `failed 7` | 是 | 停止 |
| `pid_not_effective` | turbocfg 输出不含 `p[...]i[...]d[...]` 格式 | 是 | 停止 |
| `failed_17_retry_failed` | failed 17 自动重试后仍 failed 17 | 是 | 停止 |
| `npu_not_set` | ASCEND_RT_VISIBLE_DEVICES 为空 | 是 | 停止 |
| `npu_mismatch` | ASCEND_RT_VISIBLE_DEVICES != 预期值（默认 `0`，或 `PEEC_EXPECTED_VISIBLE` 指定） | 是 | 停止 |
| `ssh_unreachable` | SSH 连不上 / 命令执行超时 | 是 | 停止（前置条件失败） |
| `pass` | 满足通过判据 | — | 继续 / 放行 |

## failed 17 重试的 SSH 实现要点

paramiko 重试 lpmi_tool 的关键步骤：

1. 用 `exec_command` 后台启动 lpmi_tool（命令末尾 `&`，立即返回）
2. `time.sleep(5)` 等待 query/repair 完成
3. 打开一个新 channel，`exec_command` 执行 `kill` 或向 lpmi_tool 进程发 SIGINT；
   也可用交互 channel `invoke_shell` 后发送 `\x03`。脚本里用 `pkill -INT lpmi_tool` 更稳妥。
4. 重新 `exec_command` 执行 turbocfg 检查命令，解析输出。

> 实现细节见 `scripts/check_firmware_pid.py` 的 `retry_with_lpmi_tool()` 函数。

## 安全注意事项

- 脚本只执行「检查命令清单」里列出的命令，不接受用户任意命令注入。
- lpmi_tool 的 try-repair 是既定修复尝试，参数固定，不从用户输入拼接。
- 原始输出可能含 IP/路径/卡号等，报告外发前由用户自行脱敏。
