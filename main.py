import openai
from config import OPENAI_KEY
from speech_assistant import get_speech_instance
from utils import get_logger

openai.api_key = OPENAI_KEY
logger = get_logger("chat")


def chat(prompt):  # 定义一个函数，以便后面反复调用
    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            temperature=0.9,
            max_tokens=2500,
            top_p=1,
            frequency_penalty=0.0,
            presence_penalty=0.6,
            stop=[" Human:", " AI:"]
        )

        answer = response["choices"][0]["text"].strip()
        return answer
    except Exception as exc:
        logger.warning(f"Failed to chat: {exc}", exc_info=exc)


def loop():
    text = ""  # 设置一个字符串变量
    turns = []  # 设置一个列表变量，turn指对话时的话轮
    prompt = "hello 我来咯"
    tts = get_speech_instance()
    tts.play_sound(prompt)
    while True:  # 能够连续提问
        question = tts.get_hear_text()
        if question is None:
            logger.info("No text detected")
            continue
        if question.startswith("退出"):
            tts.play_sound("bye bye")
            break
        if len(question.strip()) == 0:  # 如果输入为空，提醒输入问题
            print("please input your question")
        elif question == "quit":  # 如果输入为"quit"，程序终止
            print("\nAI: See You Next Time!")
            break
        else:
            prompt = text + "\nHuman: " + question
            result = chat(prompt)
            print(result)
            while result == "退出":  # 问不出结果会自动反复提交上一个问题，直到有结果为止。
                result = chat(prompt)  # 重复提交问题
            else:
                turns += [question] + [result]  # 只有这样迭代才能连续提问理解上下文
            if len(turns) <= 10:  # 为了防止超过字数限制程序会爆掉，所以提交的话轮语境为10次。
                text = " ".join(turns)
            else:
                text = " ".join(turns[-10:])
            role_index = result.find(":")
            if role_index > 0:
                result = result[role_index + 2:]
            tts.play_sound(result)


if __name__ == "__main__":
    loop()
