from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import os
import re
import subprocess
import os



curr_date = datetime.now().strftime("%Y_%m_%d_%H_%M_%s")



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
    with open("agent_chat_history"+curr_date+".md","w") as f:
        f.write(temp)


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



content_input = ""

messages = [{
    "role": "system", 
    "content": "你是一个代码编写的agent, 你需要根据用户的初步指令去是否选择计划而去完成目标，并且根据你代码出现的错误进行自我修正知道完成用户目标。如果你需要跑一个指令，请用以下方式包装（一次回答只给一个！）： ```bash-action\n<command>\n```. 如果你认为任务已经完成，请运行exit 指令（不要陷入死循环）。 记住，只做符合任务目的的一切行动，不许经过用户同意后擅自查看，修改，创建新文件。输出规范：不许使用md的语法。当程序运行成功且输出符合预期时，必须立即运行 exit 命令，不要再做额外的验证或优化。目前agent的步骤分为三个：1. listening stage 2. plan stage 3. Execution and correction stage  Plan的时候只说计划，不给代码。 Plan的时候用户说ok，说确认才给finished.，没说的时候不可以给，不可以给计划的时候同时给finish"}]

if(os.path.exists("DAEMON.md")):
    with open("DAEMON.md","r") as f:
        content_d = f.read()
    messages.append({"role":"system","content":"这个是你在这项目里应该做什么，应该怎么干，有什么要注意，有什么初始信息的文件，需要仔细理解"+content_d})
    save_chat(messages)
class NonterminatingException(RuntimeError): ...
class OurTimeoutError(NonterminatingException): ...


token_amount_temp = 0
state_lm=True
while True: #第一层循环，用户提要求
    content_input = input("请输入你的指令，纯语言就可以哈: ")

    routing_messages = [
        {"role":"system","content":"你只需要判断用户的任务是否需要先做计划。回复只能是plan-needed 或 plan-unwanted 其中一个词。 不允许任何其他内容。 需要多步骤、写代码、创建文件的任务回复 plan-needed。查看文件、简单查询回复 plan-unwanted。"},
        {"role":"user","content":content_input}
    ]
    lm_output, _, _ = query_lm(routing_messages) # 请求模型个旁枝看看要不要plan

    # messages.append({"role": "user", "content": content_input+"你的回复只能包含 plan-needed 或 plan-unwanted 两个词之一，不允许输出任何其他内容"})
    # save_chat(messages)
    # lm_output,token_amount_temp,state_lm = query_lm(messages) # 拿第一个回答 看是否需要planning or not
    needed = parse_plan_needed(lm_output)
    if(needed):
        messages.append({"role":"user","content":"我提的plan:"+content_input})
        messages.append({"role": "assistant", "content": "目前planning 已经开启，请输出你的plan"})

        cnt_plan=0
        while True: # PLAN LOOP
            token_amount_temp = 0
            lm_output,token_amount_temp,state_lm = query_lm(messages) # 拿一个回答
            messages.append({"role": "assistant", "content": lm_output})
            if(parse_plan_finished(lm_output)):
                break
            if(token_amount_temp>256000*0.8):
                messages = compression(messages)
                continue
            if(state_lm == False):
                print("有bug 崩了")
                break
            content_input = input("Planning:你看看当前计划如何，纯语言就可以哈: ") #获得用户对plan对回答
            messages.append({"role": "user", "content": content_input+"指令部分（不需要回复）：根据用户的完善进一步给出计划，如果用户认为当前计划可以执行，那你在你的下一步回答中要包括````plan-finish```` 以及当你输出 plan-finish 时，不要同时输出任何 bash-action 代码块。plan-finish 的回答只包含 plan-finish 标记本身。以及你绝对不能自行输出 plan-finish。只有当用户的消息中明确包含'确认'、'可以'、'ok'等同意词时，你才能在下一条回复中输出 plan-finish。否则你必须等待用户反馈。"})
            if(cnt_plan>20):
                print("Plan 崩了，回家咯，直接继续")
                messages.append({"role": "assistant", "content": "目前planning结束（由于plan次数太多)，结束了"})
                break
            cnt_plan+=1
    else:
        messages.append({"role":"user","content":"我提的你要直接做的任务:"+content_input})
    messages.append({"role": "assistant", "content": "开始执行你的代码吧"})
    cnt = 0
    while True:
        cnt+=1
        
        if cnt>30:
            print("agent 跑了30次了,太废物了没完成退出了")
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
        
        
        
        
