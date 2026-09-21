from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import sys
import os
import re
import subprocess
import os

class NonterminatingException(RuntimeError): ...
class OurTimeoutError(NonterminatingException): ...


env_vars = {
    "PAGER": "cat",
    "MANPAGER": "cat",
    "LESS": "-R",
    "PIP_PROGRESS_BAR": "off",
    "TQDM_DISABLE": "1",
}

def parse_action(lm_output: str) -> str:
    #找要干啥的指令
    matches = re.findall(
        r"```bash-action\s*\n(.*?)\n```",
        lm_output,
        re.DOTALL
    )
    return matches[0].strip() if matches else ""




def execute_action(command: str) -> str: #本地python -> bash执行指令
    #执行，得到结果
    try:
        result = subprocess.run(
            command,
            shell=True,
            text=True,
            env=os.environ | env_vars,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        return result.stdout    
    except subprocess.TimeoutExpired as e:
        raise OurTimeoutError("TIMEOUT, try a new approach") from e





    

def parse_plan_finished(lm_output):
    if("plan-finish" in lm_output):
        return True
    else:
        return False
    
def parse_plan_needed(lm_output):
    if("plan-needed" in lm_output):
        return True
    elif("plan-unwanted" in lm_output):
        return False



