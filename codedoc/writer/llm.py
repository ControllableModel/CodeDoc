from openai import OpenAI
import json
import time

from codedoc.writer.usage import RECORDER


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
        #: Optional per-call tag so concurrent callers can attribute usage to
        #: themselves. Without it, a thread that snapshots the recorder cannot tell
        #: its own records from its siblings', and batch accounting inflates.
        self.label = ""

    def create_socket(self):
        self.client = OpenAI(api_key=self.LLM_key, base_url=self.LLM_url)

    def process(self, msg, mode="solo", stream=False):
        if mode == "solo":
            messages = msg if isinstance(msg, list) else [{"role": "user", "content": msg}]
        else:
            messages = msg

        started = time.time()
        try:
            r = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=stream,
                temperature=self.temperature
            )
        except Exception as exc:
            RECORDER.record(phase="generation", model=self.model,
                            seconds=time.time() - started, ok=False,
                            error=f"{type(exc).__name__}: {exc}",
                            label=getattr(self, "label", ""))
            raise
        if not stream:
            RECORDER.record_response("generation", self.model, r, time.time() - started,
                                     label=getattr(self, "label", ""))

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
