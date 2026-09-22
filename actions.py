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


def handle_read(command):
    parts = command.split() # 按空格拆成多个string的list ["xxx", "aaaa"]
    filename= parts[1]

    if len(parts) == 4:
        # read file.py 10 20 空格的情况
        start, end = int(parts[2]), int(parts[3])
    elif "-" in parts[2]:
        # read file.py 10-20 
        start,end = parts[2].split("-")
        start,end = int(start),int(end)
    else:
        return "请重新给出合理的bash指令。 目前无法匹配"

    with open(filename,"r") as f:
        lines = f.readlines() # 返回一个列表，索引对应不同行    
    
    result = lines[start-1:end]
    return "".join(result)



def handle_write(command):
    parts = command.split(maxsplit=3) # 前3个token是命令/文件/行号，剩余为内容(可含空格)
    filename = parts[1]
    specific_line = parts[2]
    new_content = parts[3]

    if not os.path.exists(filename):

        with open(filename,"w") as f: #纯没有文件
            f.write(new_content + "\n")
        return "新文件已创建"

    with open(filename,"r") as f:
        lines = f.readlines()

    lines[int(specific_line)-1] =  new_content + "\n" #将读出来的lines 然后根据命令的行数修改
    with open(filename, "w") as f:
        f.writelines(lines)
    return "已修改成功"

def handle_search(command):
    # command: "search error ./src"
    parts = command.split(maxsplit=2) # keyword 后的剩余全部作为目录(可含空格)
    keyword = parts[1]
    directory = parts[2] if len(parts) > 2 else "."

    results = ""
    for root, dirs, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root,file)
            if not os.path.isfile(filepath):
                continue
            try:
                with open(filepath,"r", encoding="utf-8", errors="replace") as f:
                    for i,line in enumerate(f.readlines()):
                        if keyword in line:
                            results += f"{filepath}:{i+1}: {line}"
            except (OSError, PermissionError):
                continue

    return results




def parse_action(lm_output: str) -> str:
    #找要干啥的指令
    matches = re.findall(
        r"```bash-action\s*\n(.*?)\n```",
        lm_output,
        re.DOTALL
    )
    return matches[0].strip() if matches else ""



DANGEROUS = ["rm -rf", "rm -r","git push --force","mkfs", "> /dev/","My_agent.py","actions.py","llm.py","chat_export.py","system_prompt.txt",".env"]
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
        if command.startswith("read "):
            return handle_read(command)
        if command.startswith("write "):
            return handle_write(command)
        if command.startswith("search "):
            return handle_search(command)


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



