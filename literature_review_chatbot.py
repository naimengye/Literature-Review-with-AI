import os
import yaml
import json
from copilot import Copilot
# Load OpenAI API key from config.yaml
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)
openai_api_key = config.get('openai_api_key')
if not openai_api_key:
    raise ValueError("OpenAI API key not found in config.yaml")
copilot = Copilot()
messages = []
while True:
    question = input("Please ask a question: ")
    retrived_info, answer = copilot.ask(question, messages=messages, openai_key=openai_api_key)
    ### answer can be a generator or a string

    #print(retrived_info)
    if isinstance(answer, str):
        print(answer)
    else:
        answer_str = ""
        for chunk in answer:
            content = chunk.choices[0].delta.content
            if content:
                answer_str += content
                print(content, end="", flush=True)
        print()
        answer = answer_str

    messages.append({"role": "user", "content": question})
    messages.append({"role": "assistant", "content": answer})

    # save the messages to a file
    with open('messages.txt', 'w', encoding='utf-8') as f:
        for message in messages:
            f.write(f"{message['role']}: {message['content']}\n")

