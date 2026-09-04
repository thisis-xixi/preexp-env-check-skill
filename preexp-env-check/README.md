# preexp-env-check —— 实验前环境检查 Skill

功耗实验（Wan2.2 lptest/lpmi）启动前，通过 SSH 远程检查服务器环境是否就绪。
只做只读检查，全过才放行，任一关键项不通过即停止并报告修复动作。

## 目录结构

```
preexp-env-check/
├── SKILL.md                       # 唯一入口：触发/步骤/判断/停止/反馈
├── scripts/
│   ├── ssh_exec.py                # SSH 封装（连接/执行/取回输出）
│   ├── check_firmware_pid.py      # 检查项1：固件驱动+pid（含 failed 17 自动重试）
│   └── check_npu_visible.py       # 检查项2：NPU 可见设备
├── references/
│   ├── check_items.md             # 检查项清单与判据（审查标准来源）
│   └── ssh_usage.md               # SSH 参数、命令清单、故障分类
├── assets/
│   └── report_template.md         # 检查报告输出模板
└── examples/
    ├── success/                   # ✅ 全通过样例
    ├── boundary/                  # ? 边界样例（输入缺失→澄清）
    └── failure/                   # × 失败样例（failed7/pid未生效/failed17重试失败）
```

## 快速开始（用户使用说明）

### 1. 安装依赖

```bash
pip install paramiko
```

### 2. 配置 SSH 连接（环境变量，安全红线——不硬编码）

SSH 凭据只从本地环境变量读取，绝不写进脚本或仓库。按你的操作系统选一种方式设置。

#### Linux / macOS

在本地 shell 设置（或写入不入库的 `~/.peec.env` 后 `source` 它）：

```bash
export PEEC_SSH_HOST=10.x.x.x
export PEEC_SSH_PORT=22
export PEEC_SSH_USER=p00954667
export PEEC_SSH_KEY=~/.ssh/id_rsa     # 推荐；或用 PEEC_SSH_PASSWORD
```

> 临时设的话只在当前终端有效；要持久化可把上面几行写入 `~/.bashrc` 或 `~/.peec.env`（后者记得 `chmod 600` 且不入库）。

#### Windows

Windows 上有三种常见跑法，按你实际用的 shell 选：

**① PowerShell（推荐用于持久化）**

用 `[Environment]::SetEnvironmentVariable` 设**用户级**持久变量（重开终端后仍有效，且 Python 进程能读到）：

```powershell
[Environment]::SetEnvironmentVariable("PEEC_SSH_HOST", "10.x.x.x", "User")
[Environment]::SetEnvironmentVariable("PEEC_SSH_PORT", "22", "User")
[Environment]::SetEnvironmentVariable("PEEC_SSH_USER", "p00954667", "User")
[Environment]::SetEnvironmentVariable("PEEC_SSH_KEY", "C:\Users\你\.ssh\id_rsa", "User")
# 或用密码：[Environment]::SetEnvironmentVariable("PEEC_SSH_PASSWORD", "你的密码", "User")
```

只对当前会话临时设（重开终端失效）：

```powershell
$env:PEEC_SSH_HOST = "10.x.x.x"
$env:PEEC_SSH_PORT = "22"
$env:PEEC_SSH_USER = "p00954667"
$env:PEEC_SSH_KEY  = "C:\Users\你\.ssh\id_rsa"
```

**② 图形界面（最直观，适合不熟命令行的同学）**

`Win` 键搜「环境变量」→「编辑系统环境变量」→「环境变量…」→ 在「用户变量」里「新建」，逐条加入上面四个变量。确定后**重开**终端生效。

**③ Git Bash / MSYS2（如果用 Claude Code 的 Git Bash 跑脚本）**

和 Linux 一样用 `export`，但有两个 Windows 特有的坑，务必注意：

```bash
export PEEC_SSH_HOST=10.x.x.x
export PEEC_SSH_PORT=22
export PEEC_SSH_USER=p00954667
export PEEC_SSH_KEY=~/.ssh/id_rsa
```

- **坑 1：环境变量不跨 `!` 命令持久**。在 Claude Code 里每个 `! <cmd>` 是独立 shell，`export` 设的变量下一条 `!` 就读不到。解决办法：把所有 `export` 和跑脚本的命令写在**同一条**命令里，例如
  `PEEC_SSH_HOST=... PEEC_SSH_USER=... python scripts/check_firmware_pid.py`；
  或写入一个本地不入库的文件（如 `~/.peec.env`），每次跑前 `source ~/.peec.env` 再跑。
- **坑 2：MSYS 路径转换**。Git Bash 会把以 `/` 开头的值（如远程路径 `/home/...`）自动改成 `C:/Program Files/Git/home/...`，导致传给服务器的路径错误。本 Skill 的脚本已内置**自愈逻辑**（`ssh_exec.py` 的 `_strip_msys_prefix`），会自动把被改写的路径还原成 `/home/...`，正常情况下你无需手动处理；若遇到奇怪的路径报错，可在跑脚本前加 `MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL="*"` 作为兜底。

> 密码方式认证时用 `PEEC_SSH_PASSWORD`（不推荐，密钥优先）。无论哪种方式，**都不要把凭据提交进仓库**。

#### 验证设置是否生效

设好后，在你要跑脚本的同一个终端里自检（应能看到 host/user，密钥/密码隐藏）：

```bash
python scripts/ssh_exec.py
```

#### 可选覆盖（不设则用默认值）

变量名兼容两套：文档名（下方"推荐"列）优先，脚本历史名（"兼容"列）作为回退。

| 用途 | 推荐变量名（文档） | 兼容变量名（历史） | 默认值 |
|---|---|---|---|
| lptest 路径 | `PEEC_LPTEST_PATH` | `PEEC_LPTEST` | `/data/ts-home/p00954667/tool/lptest0d0` |
| lpmi_tool 路径 | `PEEC_LPMI_PATH` | `PEEC_LPMI_TOOL` | `/data/ts-home/p00954667/tool/lpmi_tool` |
| turbocfg 参数 | `PEEC_TURBOCFG` | `PEEC_TURBOCFG_ARGS` | `17 9 50` |
| failed 17 重试用的 NPU 号 | `PEEC_NPU` | — | `4` |
| check #2 预期可见设备 | `PEEC_EXPECTED_VISIBLE` | — | `0`（单卡）；多卡可设 `4,5,6,7` |

Linux/macOS 示例：

```bash
export PEEC_LPTEST_PATH=/data/ts-home/p00954667/tool/lptest0d0
export PEEC_LPMI_PATH=/data/ts-home/p00954667/tool/lpmi_tool
export PEEC_TURBOCFG="17 9 50"
export PEEC_NPU=4
export PEEC_EXPECTED_VISIBLE=4,5,6,7   # 多卡服务器；单卡机器用默认 0 即可不设
```

Windows PowerShell 示例（持久化）：

```powershell
[Environment]::SetEnvironmentVariable("PEEC_LPTEST_PATH", "/data/ts-home/p00954667/tool/lptest0d0", "User")
[Environment]::SetEnvironmentVariable("PEEC_EXPECTED_VISIBLE", "4,5,6,7", "User")
```

> Windows 上 `PEEC_LPTEST_PATH` 这类远程路径值，建议用正斜杠 `/home/...` 或 `/data/...` 形式（**不要**写成 `C:\...`，那是远程 Linux 路径）。脚本的自愈逻辑会处理 Git Bash 的路径转换，PowerShell/cmd 则不存在该问题。

### 3. 触发检查

对 Agent 说：「我要跑功耗实验了，帮我检查一下环境」即可触发本 Skill。

### 4. 单独运行脚本自检（不经过 Agent）

```bash
python scripts/check_firmware_pid.py    # 输出结构化 JSON
python scripts/check_npu_visible.py
python scripts/ssh_exec.py              # 自检 SSH 配置是否加载
```

## 边界（这个 Skill 不做什么）

- 不执行实验本身（不跑 HY_PID_run.sh）
- 不拉起 vllm 服务（run_tp4ep_401.sh 超出检查范围）
- 不修改任何文件（不改实验脚本里的日期等配置）
- 不设置环境变量（只读回核对 ASCEND_RT_VISIBLE_DEVICES，不替你 export）
- 不分析实验后数据

## 安全

- SSH 凭据只从环境变量读取，不进仓库。
- 全部检查命令只读（除 failed 17 的 lpmi_tool try-repair，那是既定修复尝试）。
- 报告原始输出可能含 IP/路径/卡号，外发前自行脱敏。

## 试用指引（slide8 独立试用）

1. 把本目录 + SKILL.md 给一位同组同事，**不口头补充**。
2. 让他自然说「我要跑实验了帮我查环境」触发。
3. 记录：是否成功触发 / 哪里需要补充 / 输出能否直接进入下一步 / 失败反馈能否指导修复 / 是否愿意再用。
4. Baseline（人工逐项检查耗时与漏检率）vs After（用 Skill 后）对比。

## 依赖关系

- `check_firmware_pid.py` 和 `check_npu_visible.py` 都 import `ssh_exec.py`，
  需在同一 scripts/ 目录下运行，或保证 `sys.path` 含该目录（脚本已自动处理）。
