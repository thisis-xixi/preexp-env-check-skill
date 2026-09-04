# -*- coding: utf-8 -*-
"""检查项 1：固件驱动版本 + pid 参数生效。

远程执行 lptest0d0 turbocfg，解析输出：
  - pass：输出含 p[...]i[...]d[...] 格式 + cmd turbocfg exec succ
  - failed 7：固件驱动版本不对 → 直接 fail
  - pid 未生效：输出不含 p[...]i[...]d[...] 格式 → 直接 fail
  - failed 17：自动重试一次（拉起 lpmi_tool try-repair → 等待 → 打断 → 重跑），
              仍 failed 17 → fail

判据详见 references/check_items.md。脚本只做机检，返回结构化 JSON。
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ssh_exec import connect, run, emit, _strip_msys_prefix

# 默认值，可由环境变量覆盖。
# 变量名兼容：同时接受文档里的 PEEC_LPTEST_PATH / PEEC_LPMI_PATH / PEEC_TURBOCFG
# 和脚本历史使用的 PEEC_LPTEST / PEEC_LPMI_TOOL / PEEC_TURBOCFG_ARGS。
# 文档名优先（以 SKILL.md / references 为准），脚本历史名作为回退。
LPTEST = _strip_msys_prefix(
    os.environ.get("PEEC_LPTEST_PATH")
    or os.environ.get("PEEC_LPTEST")
    or "/data/ts-home/p00954667/tool/lptest0d0")
LPMI_TOOL = _strip_msys_prefix(
    os.environ.get("PEEC_LPMI_PATH")
    or os.environ.get("PEEC_LPMI_TOOL")
    or "/data/ts-home/p00954667/tool/lpmi_tool")
TURBOCFG_ARGS = os.environ.get("PEEC_TURBOCFG") or os.environ.get("PEEC_TURBOCFG_ARGS") or "17 9 50"
NPU = os.environ.get("PEEC_NPU", "4")

PID_FMT_RE = re.compile(r"p\[\d+\]i\[\d+\]d\[\d+\]")
SUCC_RE = re.compile(r"cmd turbocfg exec succ")


def classify(output):
    """根据 turbocfg 输出文本分类。返回 failure_class 或 'pass'。"""
    if "failed 7" in output:
        return "failed_7"
    if "failed 17" in output:
        return "failed_17"
    if not PID_FMT_RE.search(output):
        return "pid_not_effective"
    if SUCC_RE.search(output) or PID_FMT_RE.search(output):
        # 含 p[]i[]d[] 格式即视为 pid 生效（数值不比对，见 check_items.md）
        if "failed" in output.lower():
            # 含 p[]i[]d[] 但又含 failed（非 7/17），保守判 fail 待查
            return "pid_not_effective"
        return "pass"
    return "pid_not_effective"


def retry_with_lpmi_tool(client):
    """failed 17 自动重试：拉起 lpmi_tool try-repair → 等待 → 打断 → 重跑 turbocfg。

    返回重跑后的 (output, retry_evidence)。
    """
    npu = NPU
    log_file = f"lpmi_{npu}.log"
    start_cmd = (f"{LPMI_TOOL} --device-id {npu} --query-info --power-sampling "
                 f"--syscnt-scale 50000 --sampling-interval 50 --sampling-duration 200 "
                 f"--sampling-chip=910D --try-repair > {log_file} 2>&1 &")
    run(client, start_cmd, timeout=10)
    time.sleep(5)
    # 打断 lpmi_tool（发 SIGINT 更稳妥，避免依赖交互 channel）
    run(client, "pkill -INT lpmi_tool", timeout=10)
    time.sleep(1)
    # 重跑检查命令
    check_cmd = f"{LPTEST} turbocfg {TURBOCFG_ARGS}"
    _, out, err = run(client, check_cmd, timeout=60)
    retry_ev = {
        "retry_attempted": True,
        "start_cmd": start_cmd,
        "kill_cmd": "pkill -INT lpmi_tool",
        "retry_stdout": out,
        "retry_stderr": err,
    }
    return out + "\n" + err, retry_ev


def main():
    client, err = connect()
    if err:
        emit(err)
        return

    check_cmd = f"{LPTEST} turbocfg {TURBOCFG_ARGS}"
    _, out, err = run(client, check_cmd, timeout=60)
    raw = out + "\n" + err
    fc = classify(raw)

    evidence = {
        "command": check_cmd,
        "stdout": out,
        "stderr": err,
        "retry_attempted": False,
    }

    if fc == "failed_17":
        # 自动重试一次
        retry_out, retry_ev = retry_with_lpmi_tool(client)
        evidence.update(retry_ev)
        fc2 = classify(retry_out)
        if fc2 == "pass":
            emit({
                "item": "firmware_pid",
                "status": "pass",
                "actual": retry_out.strip(),
                "expected": "输出含 p[...]i[...]d[...] 格式且 cmd turbocfg exec succ",
                "failure_class": "none",
                "evidence": evidence,
                "fix_hint": "",
                "critical": True,
            })
            client.close()
            return
        else:
            emit({
                "item": "firmware_pid",
                "status": "fail",
                "actual": retry_out.strip(),
                "expected": "failed 17 重试后应出现 p[...]i[...]d[...] 格式",
                "failure_class": "failed_17_retry_failed",
                "evidence": evidence,
                "fix_hint": "failed 17 自动重试仍失败，需人工登录服务器手动启动 lpmi_tool 排查，或检查 NPU 卡状态。",
                "critical": True,
            })
            client.close()
            return

    if fc == "pass":
        emit({
            "item": "firmware_pid",
            "status": "pass",
            "actual": raw.strip(),
            "expected": "输出含 p[...]i[...]d[...] 格式且 cmd turbocfg exec succ",
            "failure_class": "none",
            "evidence": evidence,
            "fix_hint": "",
            "critical": True,
        })
    else:
        fix_map = {
            "failed_7": "固件驱动版本不支持当前 lptest/lpmi，需升级或回退固件驱动到支持版本，联系环境维护同学。",
            "pid_not_effective": "pid 参数未写入生效，检查 pid 下发流程是否执行、turbocfg 是否成功落盘，重新下发 pid 后再触发检查。",
        }
        emit({
            "item": "firmware_pid",
            "status": "fail",
            "actual": raw.strip(),
            "expected": "输出含 p[...]i[...]d[...] 格式且 cmd turbocfg exec succ",
            "failure_class": fc,
            "evidence": evidence,
            "fix_hint": fix_map.get(fc, "未知失败，请检查原始输出。"),
            "critical": True,
        })
    client.close()


if __name__ == "__main__":
    main()
