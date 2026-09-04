# -*- coding: utf-8 -*-
"""SSH 远程执行封装。

所有检查脚本通过本模块连接服务器、执行命令、取回输出。
连接参数一律从环境变量读取，绝不硬编码（安全红线，见 references/ssh_usage.md）。

依赖：pip install paramiko
"""
import os
import sys
import json
import time
import paramiko


# ---- Windows MSYS 路径转换自愈 ----
# 在 Windows 的 Git Bash (MSYS) 下，以 "/" 开头的环境变量值或命令参数会被
# 自动 prepend 上 MSYS 安装根目录（如 "C:/Program Files/Git"），导致传给远程
# 服务器的 Linux 绝对路径变成 "C:/Program Files/Git/home/..."。
# 这个改写发生在 python 进程启动 *之前*，所以在脚本里设 MSYS_NO_PATHCONV 已来不及。
# 这里做的是事后自愈：把被改写过的路径前缀剥掉，还原成原始的 "/..." 路径。
_MSYS_ROOTS = []
if sys.platform == "win32":
    for _env_name in ("MSYSTEM_PREFIX", "MSYS2_PATH"):
        _root = os.environ.get(_env_name)
        if _root:
            _MSYS_ROOTS.append(os.path.normpath(_root))
    # 常见安装根：Git for Windows 默认 + MSYS2 默认
    for _guess in ("C:/Program Files/Git", "C:/Program Files/Git/usr",
                   "C:/msys64", "C:/msys64/usr"):
        _MSYS_ROOTS.append(os.path.normpath(_guess))
    # git-bash 通常把 INSTALL_ROOT 暴露在 _ 或类似变量；兜底再扫一遍 PATH 里的根
    _mingw = os.environ.get("MINGW_PREFIX")
    if _mingw:
        _MSYS_ROOTS.append(os.path.normpath(_mingw))
    # 去重，保持顺序
    _seen = set()
    _MSYS_ROOTS = [r for r in _MSYS_ROOTS if not (r in _seen or _seen.add(r))]


def _strip_msys_prefix(value):
    """剥离 MSYS 错误 prepend 的本地路径前缀，还原远程 Linux 绝对路径。

    只处理形如 "<msys_root>/home/..." 或 "<msys_root>/tmp/..." 这类本应是
    远程绝对路径、被 MSYS 改写过的值。其它值原样返回。
    """
    if not value or not isinstance(value, str):
        return value
    if sys.platform != "win32" or not _MSYS_ROOTS:
        return value
    norm = os.path.normpath(value)
    for root in _MSYS_ROOTS:
        # 形如 "C:\\Program Files\\Git\\home\\p00954667\\tool\\lptest"
        root_norm = os.path.normpath(root)
        if norm == root_norm:
            continue
        if norm.startswith(root_norm + os.sep):
            rest = norm[len(root_norm) + 1:]
            # 只还原那些原本应该是远程绝对路径的顶层目录。
            # 注意：不放 "usr" —— 本地 MSYS 的 /usr/bin 等路径会因此被误还原。
            # 当前检查涉及的远程路径都在 /home、/data 下；如以后用到 /usr/... 远程路径再增补。
            top = rest.split(os.sep, 1)[0].lower()
            if top in ("home", "tmp", "etc", "opt", "data", "var", "root", "proc", "sys", "dev", "mnt", "srv"):
                return "/" + rest.replace(os.sep, "/")
    return value


def _load_ssh_config():
    """从环境变量读取 SSH 连接参数。缺失则返回错误结构。

    路径类变量（PEEC_SSH_KEY）经 _strip_msys_prefix 还原，避免 Windows MSYS
    把本地私钥路径错误改写。
    """
    host = os.environ.get("PEEC_SSH_HOST")
    port = int(os.environ.get("PEEC_SSH_PORT", "22"))
    user = os.environ.get("PEEC_SSH_USER")
    key = _strip_msys_prefix(os.environ.get("PEEC_SSH_KEY"))
    password = os.environ.get("PEEC_SSH_PASSWORD")
    if not host or not user:
        return None, {
            "item": "ssh_config",
            "status": "fail",
            "failure_class": "ssh_unreachable",
            "actual": "缺少 SSH 配置环境变量 PEEC_SSH_HOST / PEEC_SSH_USER",
            "expected": "需设置 PEEC_SSH_HOST、PEEC_SSH_USER（及 PEEC_SSH_KEY 或 PEEC_SSH_PASSWORD）",
            "evidence": {"command": "", "stdout": "", "stderr": "",
                         "env": {k: ("***" if "PASS" in k or "KEY" in k else os.environ.get(k, ""))
                                 for k in ("PEEC_SSH_HOST", "PEEC_SSH_PORT", "PEEC_SSH_USER",
                                           "PEEC_SSH_KEY", "PEEC_SSH_PASSWORD")}},
            "fix_hint": "在本地 shell 设置 PEEC_SSH_HOST、PEEC_SSH_USER、PEEC_SSH_KEY 等环境变量后重新触发检查。",
            "critical": True,
        }
    return {"hostname": host, "port": port, "username": user,
            "key_filename": key, "password": password}, None


def connect():
    """建立 SSH 连接，返回 (client, None) 或 (None, error_json)。"""
    cfg, err = _load_ssh_config()
    if err:
        return None, err
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connect_kwargs = {"hostname": cfg["hostname"], "port": cfg["port"],
                          "username": cfg["username"], "timeout": 15}
        if cfg.get("key_filename"):
            connect_kwargs["key_filename"] = cfg["key_filename"]
        elif cfg.get("password"):
            connect_kwargs["password"] = cfg["password"]
        client.connect(**connect_kwargs)
        return client, None
    except Exception as e:
        return None, {
            "item": "ssh_connect",
            "status": "fail",
            "failure_class": "ssh_unreachable",
            "actual": f"SSH 连接失败：{type(e).__name__}: {e}",
            "expected": "服务器可达且 SSH 凭据有效",
            "evidence": {"command": f"ssh {cfg['username']}@{cfg['hostname']} -p {cfg['port']}",
                         "stdout": "", "stderr": str(e), "retry_attempted": False},
            "fix_hint": "确认服务器网络可达、SSH 服务运行、凭据有效；检查 PEEC_SSH_* 环境变量。",
            "critical": True,
        }


def run(client, command, timeout=60):
    """执行远程命令，返回 (exit_code, stdout, stderr)。

    对 command 做一次 _strip_msys_prefix 防御：即使调用方拼命令时用到了被
    MSYS 改写过的路径变量，这里也能在发到远程之前还原成 "/..." 形式。
    """
    command = _strip_msys_prefix(command) or command
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    return exit_code, out, err


def emit(result):
    """把检查结果 JSON 输出到 stdout，供 Agent 解析。统一出口。"""
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    # 自检：打印 SSH 配置加载结果（不实际连接）
    cfg, err = _load_ssh_config()
    if err:
        print("SSH 配置缺失：", err["actual"])
        sys.exit(1)
    print("SSH 配置已加载：", {k: v for k, v in cfg.items()
                              if k not in ("password", "key_filename")})
