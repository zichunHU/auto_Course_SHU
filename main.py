import sys
import time
from functions.app_orchestrator import AppOrchestrator

def run():
    base_url = "https://jwxt.shu.edu.cn"

    sid =
    pwd = ""
    year = 2025
    term = 2
    debug_flag = True
    orchestrator = AppOrchestrator(base_url, sid, pwd, year, term, debug_flag)
    orchestrator.run_assistant()

if __name__ == "__main__":
    run()
