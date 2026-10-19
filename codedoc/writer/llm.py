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
        #: Newer OpenAI-family models reject ``max_tokens`` and require
        #: ``max_completion_tokens``; the installed SDK (1.3.0) has no typed kwarg for
        #: it, so it is sent through ``extra_body``.
        self.max_output_tokens = 0
        self.use_max_completion_tokens = False
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

        kwargs = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "temperature": self.temperature,
        }
        if self.max_output_tokens:
            if self.use_max_completion_tokens:
                kwargs["extra_body"] = {"max_completion_tokens": int(self.max_output_tokens)}
            else:
                kwargs["max_tokens"] = int(self.max_output_tokens)
        started = time.time()
        try:
            r = self.client.chat.completions.create(**kwargs)
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
