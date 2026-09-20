from openai import OpenAI
from dotenv import load_dotenv



import os






load_dotenv()
# print(os.environ.get("MOONSHOT_API_KEY"))


client = OpenAI(
    api_key=(os.environ["MOONSHOT_API_KEY"]), #用来自虚拟环境... 的apikey
    base_url="https://api.moonshot.cn/v1"
)

client_ds = OpenAI(
    api_key=(os.environ["DEEPSEEK_API_KEY"]),
    base_url="https://api.deepseek.com"
)



def compression(messages): # 压缩上下文（对message做处理

   messages.append({"role": "user", "content": "目前token amount已经超标,执行压缩程序。你目前现在需要根据我完整的上下文进行如下的信息保留。对于用户信息尽可能保留原始信息，对模型的输出（非代码部分）进行保留，以及对bash/python 的返回结果做大部分的压缩。最后你将三者按比例返回给我一个完整的新上下文结果。"})  # 进行压缩命令的输入
   lm_output,token_amount_temp,state_lm = query_lm(messages,True)
   new_messages = [{
        "role": "system", 
        "content": "你是一个代码编写的agent, 你需要根据用户的初步指令去完成目标，并且根据你代码出现的错误进行自我修正知道完成用户目标。如果你需要跑一个指令（一次只有一个bash指令），请用以下方式包装： ```bash-action\n<command>\n```. 如果你认为任务已经完成，请运行exit 指令。 记住，只做符合任务目的的一切行动，不许经过用户同意后擅自查看，修改，创建新文件。输出规范：不许使用md的语法。当程序运行成功且输出符合预期时，必须立即运行 exit 命令，不要再做额外的验证或优化。"
    }]
   new_messages.append({"role": "assistant", "content": lm_output})
   return new_messages


def query_lm(messages,isCompression=False):
    cnt = 1
    state = True
    full_response = ""
    token_amount=0
    while True:
        try:
            
            response = client_ds.chat.completions.create(
                model="deepseek-chat",
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
                    token_amount = chunk.usage.total_tokens
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




