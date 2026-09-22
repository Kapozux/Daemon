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



DANGEROUS = ["rm -rf", "rm -r","git push --force","mkfs", "> /dev/"]
def execute_action(command: str) -> str: #本地python -> bash执行指令
    #执行，得到结果
    for d in DANGEROUS:
        if d in command:
            while True:
                user_input = input("目前的代码中有存在对于危险指令，回复y/n是否确认执行？")
                if(user_input =="y"):
                    break
                elif(user_input =="n"):
                    return "用户决定不执行该指令，你的bash action被退回，重新和用户达成一致后再继续执行其他指令"
                else:
                    print("输入格式错误")
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
    # if("plan-finish" in lm_output):
    #     return True
    # else:
    #     return False
    for line in lm_output.strip().split("\n"):
        if "plan-finish" in line and len(line.strip()) < 30:
            return True
        
    return False
    
def parse_plan_needed(lm_output):
    if("plan-needed" in lm_output):
        return True
    elif("plan-unwanted" in lm_output):
        return False



