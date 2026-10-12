#!/usr/bin/python3
# _*_ coding: utf-8 _*_
#
# @Time    : 2025/8/25 上午12:31
# @Author  : 单子叶蚕豆_DzyCd
# @File    : __init__.py.py
# @IDE     : PyCharm
from openai import OpenAI
import time

class LLM_Remote_query:
    def __init__(self, api_key='<>', api_url='', model='gpt-5-mini'):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.MESSAGE_HISTORY = [{"role": "system", "content": "You are a professional reviewer"}]
        self.temperature = 0.5
        self.max_token = 1024

    def multi_query(self, question):
        self.MESSAGE_HISTORY.append({"role": "user", "content": question})
        self.client = OpenAI(api_key=self.api_key, base_url=self.api_url)
        answer = self.client.chat.completions.create(
                model=self.model,
                messages=self.MESSAGE_HISTORY,
                stream=False,
                temperature=self.temperature,
                max_tokens=self.max_token,
            )
        ans = answer.choices[0].message.content
        self.MESSAGE_HISTORY.append({"role": "assistant", "content": ans})

        return ans
    def solo_query(self, question, write=False):
        self.MESSAGE_HISTORY.append({"role": "user", "content": question})
        self.client = OpenAI(api_key=self.api_key, base_url=self.api_url)
        count = 5
        while count > 0:
            time.sleep(2)
            try:
                answer = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.MESSAGE_HISTORY,
                    stream=False,
                    temperature=1,
                    max_tokens=self.max_token,
                )
                count = 0
            except:
                count -= 1
                print(f"Request Try Left: {count}")
        ans = answer.choices[0].message.content
        self.MESSAGE_HISTORY.append({"role": "assistant", "content": ans})
        return ans

    def load_judgeContent(self, name, behavior, example=''):
        judge = f"A good document should have the quality of {name}, which means to {behavior}."
        if example != "":
            judge += f"Here is A good document example: {example}."
        judge += f"Please view the following document and judge the quality of {name},  you can choose from 1 score(Not Mention) to 5 score (excellent), and give your evidence."
        judge += ("your output must be a JSON, which have two attribute, 'judge' include your choice, 'evidence' include your evidence. "
                  "You should output like {judge: ..., evidence: ...}")
        self.MESSAGE_HISTORY = [{"role": "system", "content": judge}]

    def load_JudgeContent_Once(self, judge, example=''):
        judge = f"A good document should have the following quality: {judge}."
        if example != "":
            judge += f"Here is A good document example: {example}."
        judge += f"Please view the following document and judge its quality, you can choose from 1 score(Not Mention) to 5 score (excellent), and give your evidence."
        judge += ("your output must be a JSON, the key is the attribute you view, the value which have two attribute, "
                  "'judge' include your choice, 'evidence' include your evidence. "
                  "You should output like {judgeName : {judge: ..., evidence: ...}, judgeName : {judge: ..., evidence: ...}}")
        self.MESSAGE_HISTORY = [{"role": "system", "content": judge}]

