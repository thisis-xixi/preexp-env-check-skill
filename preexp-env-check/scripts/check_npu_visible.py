# -*- coding: utf-8 -*-
"""检查项 2：NPU 可见设备。

远程读回 ASCEND_RT_VISIBLE_DEVICES 环境变量（只读，不设置），核对是否为预期值。
预期值从环境变量 PEEC_EXPECTED_VISIBLE 读取，未设置时默认 "0"（单卡机器）；
多卡服务器可 export PEEC_EXPECTED_VISIBLE=4,5,6,7 覆盖。
  - pass：值 == 预期值
  - npu_not_set：值为空
  - npu_mismatch：值非预期值

注：本脚本不执行 export（越界），只读回核对。判据详见 references/check_items.md。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ssh_exec import connect, run, emit, _strip_msys_prefix

EXPECTED = _strip_msys_prefix(os.environ.get("PEEC_EXPECTED_VISIBLE", "0"))


def main():
    client, err = connect()
    if err:
        emit(err)
        return

    # 只读读回，不设置
    cmd = "echo $ASCEND_RT_VISIBLE_DEVICES"
    _, out, err = run(client, cmd, timeout=15)
    val = out.strip()

    evidence = {
        "command": cmd,
        "stdout": out,
        "stderr": err,
        "retry_attempted": False,
    }

    if val == EXPECTED:
        emit({
            "item": "npu_visible",
            "status": "pass",
            "actual": val,
            "expected": EXPECTED,
            "failure_class": "none",
            "evidence": evidence,
            "fix_hint": "",
            "critical": True,
        })
    elif val == "":
        emit({
            "item": "npu_visible",
            "status": "fail",
            "actual": "(空，未设置)",
            "expected": EXPECTED,
            "failure_class": "npu_not_set",
            "evidence": evidence,
            "fix_hint": f"在服务器对应 shell/容器内执行 export ASCEND_RT_VISIBLE_DEVICES={EXPECTED}，"
                        f"确认实验用 NPU（可见设备应为 {EXPECTED}）可见。本 Skill 不替你执行 export，"
                        "请手动设置后重新触发检查。",
            "critical": True,
        })
    else:
        emit({
            "item": "npu_visible",
            "status": "fail",
            "actual": val,
            "expected": EXPECTED,
            "failure_class": "npu_mismatch",
            "evidence": evidence,
            "fix_hint": f"ASCEND_RT_VISIBLE_DEVICES 当前为 {val}，应为 {EXPECTED}。"
                        f"在服务器对应 shell/容器内重新 export ASCEND_RT_VISIBLE_DEVICES={EXPECTED} 后重新触发检查。",
            "critical": True,
        })
    client.close()


if __name__ == "__main__":
    main()
