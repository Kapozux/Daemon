from openai import OpenAI
from dotenv import load_dotenv
import os
import re
import subprocess
import os







load_dotenv()
# print(os.environ.get("MOONSHOT_API_KEY"))


client = OpenAI(
    api_key=(os.environ["MOONSHOT_API_KEY"]), #用来自虚拟环境... 的apikey
    base_url="https://api.moonshot.cn/v1"
)

def query_lm(messages,isCompression=False):
    cnt = 1
    state = True
    full_response = ""
    token_amount=0
    while True:
        try:
            
            response = client.chat.completions.create(
                model="kimi-k2.7-code",
                messages=messages,
                stream = True
            )   
            full_response = ""
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    if(isCompression==False):
                        print(content,end="",flush=True)
                    full_response += content

                #token_amount = chunk.choices[0].usage["total_token"]
                if(hasattr(chunk,"usage")and (chunk.usage is not None)):
                    token_amount = chunk.choices[0].usage["total_token"]
                if hasattr(chunk.choices[0].delta,'reasoning_content') and chunk.choices[0].delta.reasoning_content: #如果在思考的话就输出....
                    print(".",end="",flush=True)
            if(isCompression==False):
                print()
            
            return full_response, token_amount,state
        
        except Exception as e:
            print(f"API调用失败: {e}")

            cnt+=1
            state = False
            if(cnt>5):
                return full_response, token_amount,state
            continue

        break


def parse_action(lm_output: str) -> str:
    #找要干啥的指令
    matches = re.findall(
        r"```bash-action\s*\n(.*?)\n```",
        lm_output,
        re.DOTALL
    )
    return matches[0].strip() if matches else ""


env_vars = {
    "PAGER": "cat",
    "MANPAGER": "cat",
    "LESS": "-R",
    "PIP_PROGRESS_BAR": "off",
    "TQDM_DISABLE": "1",
}

# ...


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
            timeout=30,
        )
        return result.stdout    
    except subprocess.TimeoutExpired as e:
        raise OurTimeoutError("TIMEOUT, try a new approach") from e




def compression(messages): # 压缩上下文（对message做处理

   messages.append({"role": "user", "content": "目前token amount已经超标,执行压缩程序。你目前现在需要根据我完整的上下文进行如下的信息保留。对于用户信息尽可能保留原始信息，对模型的输出（非代码部分）进行保留，以及对bash/python 的返回结果做大部分的压缩。最后你将三者按比例返回给我一个完整的新上下文结果。"})  # 进行压缩命令的输入
   lm_output,token_amount_temp,state_lm = query_lm(messages,True)
   new_messages = [{
        "role": "system", 
        "content": "你是一个代码编写的agent, 你需要根据用户的初步指令去完成目标，并且根据你代码出现的错误进行自我修正知道完成用户目标。如果你需要跑一个指令（一次只有一个bash指令），请用以下方式包装： ```bash-action\n<command>\n```. 如果你认为任务已经完成，请运行exit 指令。 记住，只做符合任务目的的一切行动，不许经过用户同意后擅自查看，修改，创建新文件。输出规范：不许使用md的语法。当程序运行成功且输出符合预期时，必须立即运行 exit 命令，不要再做额外的验证或优化。"
    }]
   new_messages.append({"role": "assistant", "content": lm_output})
   return new_messages

# input = [{"role": "user", "content": "Roll a d20"}]
# print(query_lm(input))


# test_output = """I'll list the files in the current directory.

# ```bash-action
# ls -la
# ```
# """
# print(parse_action(test_output))


def save_chat(messages): #对聊天记录做导出
    temp = ""
    for i in range(len(messages)):
        if(messages[i]["role"]!="system"):
            temp += "## "
            temp += (messages[i]["role"])
            temp += ":\n"
            temp += messages[i]["content"]
            temp += "\n"
            temp += "---"
            temp += "\n"
    with open("agent_chat_history.md","w") as f:
        f.write(temp)


def parse_plan_finished(lm_output):
    return ("````plan-finished``` `" in lm_output)
    




content_input = ""

messages = [{
    "role": "system", 
    "content": "你是一个代码编写的agent, 你需要根据用户的初步指令去完成目标，并且根据你代码出现的错误进行自我修正知道完成用户目标。如果你需要跑一个指令，请用以下方式包装（一次回答只给一个！）： ```bash-action\n<command>\n```. 如果你认为任务已经完成，请运行exit 指令（不要陷入死循环）。 记住，只做符合任务目的的一切行动，不许经过用户同意后擅自查看，修改，创建新文件。输出规范：不许使用md的语法。当程序运行成功且输出符合预期时，必须立即运行 exit 命令，不要再做额外的验证或优化。"
}]

if(os.path.exists("DAEMON.md")):
    with open("DAEMON.md","r") as f:
        content_d = f.read()
    messages.append({"role":"system","content":"这个是你在这项目里应该做什么，应该怎么干，有什么要注意，有什么初始信息的文件，需要仔细理解"+content_d})
    save_chat(messages)
class NonterminatingException(RuntimeError): ...
class OurTimeoutError(NonterminatingException): ...


token_amount_temp = 0
state_lm=True
while True: #第一层循环，用户提要求，agent自己去试试试
    content_input = input("请输入你的指令，纯语言就可以哈: ")
    messages.append({"role": "user", "content": content_input+"请你先输出你根据这个代码的思路，不要立刻执行。"})
    save_chat(messages)








    cnt = 0
    while True:
        cnt+=1
        
        if cnt>10:
            print("agent 跑了10次了,太废物了没完成退出了")
            messages.append({"role": "assistant", "content": "你任务没完成(10轮)强制退出了"})  # remember what the LM said
            save_chat(messages)
            break
        
        try:
            token_amount_temp = 0
            lm_output,token_amount_temp,state_lm = query_lm(messages)
            if(token_amount_temp>256000*0.8):
                messages = compression(messages)
                continue
            if(state_lm == False):
                print("有bug 崩了")
                break
            # print("当前输出",lm_output) 被在query_lm 里面的flush替代了
            action = parse_action(lm_output)

            messages.append({"role": "assistant", "content": lm_output})  # remember what the LM said
            save_chat(messages)
            if action == "exit":
                break
            if action == "":
                break
            output = execute_action(action)
            split_output = output.split("\n")
            filter_output=""
            for x in split_output:
                if("Warning" in x):
                    continue
                else:
                    filter_output+=x
                    filter_output+="\n"

            if filter_output == "":
                print("命令执行成功，无输出")
                messages.append({"role": "user", "content": "此时运行无输出，执行成功"}) # 给总上下文此时python运行无结果
                save_chat(messages)
                continue
            print("executing输出",filter_output)
            
            messages.append({"role": "user", "content": filter_output})  # send command output back
            save_chat(messages)

        except NonterminatingException as e:
            messages.append({"role": "user", "content": str(e)})        
            save_chat(messages)
        
        
        
        
