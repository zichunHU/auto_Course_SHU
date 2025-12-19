import time
import os
import json
import signal
import datetime
from loguru import logger
from typing import Dict, List, Any, Optional, Callable

INTERRUPT_FLAG = False

def format_time() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def setup_interrupt_handler():
    def handler(signum, frame):
        global INTERRUPT_FLAG
        print(f"\n[{format_time()}] 接收到中断信号，准备退出...")
        INTERRUPT_FLAG = True
    signal.signal(signal.SIGINT, handler)

def is_interrupted() -> bool:
    return INTERRUPT_FLAG

def clear_interrupt_flag():
    global INTERRUPT_FLAG
    INTERRUPT_FLAG = False

def print_status(message: str, status: str = "info"):
    timestamp = format_time()
    status_icons = {
        "info": "ℹ️",
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "attempt": "🔄"
    }
    icon = status_icons.get(status, "ℹ️")
    print(f"[{timestamp}] {icon} {message}")

def countdown(seconds: int, message: str = "等待中", cancel_check: Callable[[], bool] = None):
    for i in range(seconds, 0, -1):
        if cancel_check and cancel_check():
            return False
        print(f"\r{message}... {i}秒 ", end="", flush=True)
        time.sleep(1)
    print(f"\r{message}... 完成!     ")
    return True