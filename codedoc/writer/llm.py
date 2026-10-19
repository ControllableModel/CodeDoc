from openai import OpenAI
import json


class LinguisticCore:
    def __init__(self):
        self.client = None
        self.LLM_url = ""
        self.LLM_key = ""
        self.model = ""
        self.template = ""
        self.web_search = False
        self.call_robot = True
        self.temperature = 1
        self.history = []
        self.round = 10

    def create_socket(self):
        self.client = OpenAI(api_key=self.LLM_key, base_url=self.LLM_url)

    def process(self, msg, mode="solo", stream=False):
        if mode == "solo":
            messages = msg if isinstance(msg, list) else [{"role": "user", "content": msg}]
        else:
            messages = msg

        r = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=stream,
            temperature=self.temperature
        )

        if stream:
            def gen():
                content = ""
                for chunk in r:
                    if chunk.choices[0].delta.content:
                        content += chunk.choices[0].delta.content
                        yield chunk.choices[0].delta.content
                return content
            return gen()

        return r.choices[0].message.content
