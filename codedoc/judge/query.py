#!/usr/bin/python3
# _*_ coding: utf-8 _*_
#
# @Time    : 2025/8/25 上午12:31
# @Author  : 单子叶蚕豆_DzyCd
# @File    : __init__.py.py
# @IDE     : PyCharm
from openai import OpenAI
import time

from codedoc.writer.usage import RECORDER

class LLM_Remote_query:
    def __init__(self, api_key='<>', api_url='', model='gpt-5-mini'):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.MESSAGE_HISTORY = [{"role": "system", "content": "You are a professional reviewer"}]
        self.temperature = 0.5
        #: Judging temperature. 0 by default: a scoring instrument should not add
        #: sampling variance, and at temperature 1 the model intermittently emits
        #: unparseable JSON (observed: 2/38 documents in the first benchmark run).
        self.judge_temperature = 0.0
        self.max_token = 1024
        #: See writer.llm: newer models need ``max_completion_tokens`` via extra_body.
        self.use_max_completion_tokens = False
        #: Models such as gpt-6-luna accept only the default temperature (1). When such
        #: a model is used the judge records the temperature it actually ran at, because
        #: a scoring instrument at temperature 1 needs replicated runs to control
        #: variance and may emit unparseable verdicts more often.
        self.temperature_forced = False
        self.effective_temperature = None

    def multi_query(self, question):
        self.MESSAGE_HISTORY.append({"role": "user", "content": question})
        self.client = OpenAI(api_key=self.api_key, base_url=self.api_url)
        _t0 = time.time()
        _kwargs = dict(model=self.model, messages=self.MESSAGE_HISTORY, stream=False,
                       temperature=self.temperature)
        if self.use_max_completion_tokens:
            _kwargs["extra_body"] = {"max_completion_tokens": int(self.max_token)}
        else:
            _kwargs["max_tokens"] = int(self.max_token)
        answer = self.client.chat.completions.create(**_kwargs)
        RECORDER.record_response("judge_multi", self.model, answer, time.time() - _t0)
        ans = answer.choices[0].message.content
        self.MESSAGE_HISTORY.append({"role": "assistant", "content": ans})

        return ans
    def solo_query(self, question, write=False):
        self.MESSAGE_HISTORY.append({"role": "user", "content": question})
        self.client = OpenAI(api_key=self.api_key, base_url=self.api_url)
        count = 5
        answer = None
        last_error: Exception | None = None
        while count > 0:
            time.sleep(2)
            try:
                _t0 = time.time()
                _kwargs = dict(model=self.model, messages=self.MESSAGE_HISTORY, stream=False,
                               temperature=self.judge_temperature)
                if self.use_max_completion_tokens:
                    _kwargs["extra_body"] = {"max_completion_tokens": int(self.max_token)}
                else:
                    _kwargs["max_tokens"] = int(self.max_token)
                answer = self.client.chat.completions.create(**_kwargs)
                self.effective_temperature = _kwargs.get("temperature")
                RECORDER.record_response("judge_solo", self.model, answer, time.time() - _t0)
                count = 0
            except Exception as exc:  # noqa: BLE001 - retried, then surfaced
                last_error = exc
                message = str(exc)
                if "temperature" in message and "does not support" in message:
                    # Fixed-temperature models: drop the parameter rather than fail, and
                    # remember that this judge could not run at the configured value.
                    self.temperature_forced = True
                    self.judge_temperature = 1.0
                    count = 5
                    continue
                count -= 1
                print(f"Request Try Left: {count} ({type(exc).__name__}: {message[:160]})")
        if answer is None:
            # A bare `except` here used to swallow the real cause and fail later with
            # UnboundLocalError, which hid provider errors entirely.
            raise RuntimeError(f"judge request failed: {type(last_error).__name__}: {last_error}"
                               if last_error else "judge request failed")
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



# ---------------------------------------------------------------------------
# Parsing helper (added during the refactor)
# ---------------------------------------------------------------------------
import json as _json
import re as _re


def parse_verdict(text):
    """Parse a judge response into {dimension: {"judge": int, "evidence": str}}.

    The archived judge output format is *not* valid JSON: keys are unquoted
    (`{judge: 4, evidence: ...}`).  A tolerant parser is therefore required, and
    it must never silently invent a score.
    """
    if not text:
        return {}
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = _re.sub(r"^```[a-zA-Z]*\s*|```$", "", cleaned).strip()
    try:
        data = _json.loads(cleaned)
        return _normalize(data)
    except Exception:
        pass
    quoted = _re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_ .&/-]*?)\s*:', r'\1"\2":', cleaned)
    try:
        return _normalize(_json.loads(quoted))
    except Exception:
        return {}


def _normalize(data):
    out = {}
    if not isinstance(data, dict):
        return out
    if "judge" in data:
        return {"overall": {"judge": _as_int(data.get("judge")), "evidence": str(data.get("evidence", ""))}}
    for name, value in data.items():
        if isinstance(value, dict) and "judge" in value:
            out[name] = {"judge": _as_int(value.get("judge")), "evidence": str(value.get("evidence", ""))}
    return out


def _as_int(value):
    try:
        return int(float(str(value).strip()))
    except Exception:
        m = _re.search(r"\d+", str(value))
        return int(m.group()) if m else None


def judge_with_retry(judge, text, attempts=3):
    """Score one document, retrying when the verdict JSON cannot be parsed.

    A malformed verdict is not an API failure: the call succeeds and returns prose
    or truncated JSON. Silently recording an empty verdict loses the document from
    the analysis, so the scoring path retries and reports the cost of doing so.
    """
    last = ""
    for attempt in range(1, attempts + 1):
        raw = judge.solo_query(text)
        verdict = parse_verdict(raw)
        if verdict:
            return verdict, attempt, ""
        last = raw or ""
        if attempt < attempts:
            judge.MESSAGE_HISTORY = judge.MESSAGE_HISTORY[:1]
    return {}, attempts, last[:400]
