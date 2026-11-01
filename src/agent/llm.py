"""LLM 호출. 기본은 이 PC 의 Claude Code CLI(`claude -p`) — API 키를 쓰지 않는다.

도구는 하나도 주지 않고(--tools ""), 빈 폴더에서, 대화 기록을 남기지 않게 부른다.
시험에서는 FakeLLM 으로 바꿔 끼운다.
"""
import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field

MODEL = os.environ.get("AGENT_MODEL", "sonnet")
TIMEOUT_S = 300


class LLMError(Exception):
    pass


def claude_cli(system: str, prompt: str, timeout: int = TIMEOUT_S) -> str:
    cmd = ["claude", "-p", "--tools", "", "--model", MODEL, "--output-format", "json",
           "--no-session-persistence", "--setting-sources", "project", "--system-prompt", system]
    with tempfile.TemporaryDirectory(prefix="agent-sandbox-") as cwd:
        try:
            p = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=timeout, cwd=cwd)
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            raise LLMError(f"Claude CLI 호출 실패: {e}") from e
    try:
        out = json.loads(p.stdout)
    except json.JSONDecodeError as e:
        raise LLMError(f"CLI 출력이 JSON 이 아님: {p.stdout[:200]!r} {p.stderr[:200]!r}") from e
    if out.get("is_error"):
        raise LLMError(f"CLI 오류: {str(out.get('result'))[:200]}")
    return out.get("result", "")


def parse_json(text: str) -> dict:
    """답에서 JSON 객체 하나를 꺼낸다(코드 울타리가 있어도)."""
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    body = m.group(1) if m else text[text.find("{"): text.rfind("}") + 1]
    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        raise LLMError(f"답에서 JSON 을 읽지 못함: {text[:200]!r}") from e


@dataclass
class FakeLLM:
    """시험용: 미리 정한 답을 차례로 돌려주고, 받은 프롬프트를 기록한다."""
    replies: list[str]
    prompts: list[str] = field(default_factory=list)

    def __call__(self, system: str, prompt: str, timeout: int = TIMEOUT_S) -> str:
        self.prompts.append(prompt)
        return self.replies.pop(0)
