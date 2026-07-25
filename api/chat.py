"""
Vercel Python Serverless Function: /api/chat

診断結果画面のチャットからの質問に、OpenAI APIを使って回答する。
リスク判定(当たると外れるとで実害が出る部分)はLLMの自由な推論に任せず、
compute_risk という決定的なPython関数をtool callingで呼ばせることで、
数字の間違いを防ぐ設計にしている。

必要な環境変数(Vercelダッシュボード側で設定する):
    OPENAI_API_KEY
"""

import json
import os
from http.server import BaseHTTPRequestHandler

from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

MODEL = "gpt-4o-mini"  # コストを抑えるため軽量モデルを使用
MAX_INPUT_CHARS = 300
MAX_TOKENS = 300

SYSTEM_PROMPT = """あなたは「企業型DC・iDeCo自動移換診断ツール」の補助アシスタントです。

ルール:
- 必ず日本語で、3〜4文以内の簡潔な回答をする
- 特定の運用商品・投資信託・銘柄の売買は絶対に推奨しない(制度・手続きの説明に限定する)
- 転職からの経過月数や移換手続きの有無から自動移換リスクを判定する必要がある場合は、
  必ず compute_risk 関数を呼び出し、その結果をもとに回答する(自分で暗算しない)
- 個別の税務・法律相談が必要な内容は、専門家(社会保険労務士・国民年金基金連合会)へ
  相談するよう案内する
"""


def compute_risk(months_since_job_change: int, transferred: bool) -> str:
    """script.js の computeRisk と同じロジック(決定的な判定はここに集約する)"""
    if transferred:
        return "low(手続き済みのため自動移換の心配は基本的にありません)"
    if months_since_job_change >= 6:
        return "high(6ヶ月以上経過・未手続きのため自動移換されている可能性が高い)"
    if months_since_job_change > 0:
        return "mid(6ヶ月以内であればまだ間に合うタイミング)"
    return "unknown(情報が不足しているため断定できません)"


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "compute_risk",
            "description": "転職・退職からの経過月数と移換手続きの有無から、自動移換リスクを判定する",
            "parameters": {
                "type": "object",
                "properties": {
                    "months_since_job_change": {
                        "type": "integer",
                        "description": "転職・退職からの経過月数",
                    },
                    "transferred": {
                        "type": "boolean",
                        "description": "既に移換手続きを完了しているかどうか",
                    },
                },
                "required": ["months_since_job_change", "transferred"],
            },
        },
    }
]


def run_chat(user_message: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
        max_tokens=MAX_TOKENS,
    )
    msg = response.choices[0].message

    if msg.tool_calls:
        messages.append(msg)
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            try:
                result = compute_risk(**args)
            except TypeError:
                result = "unknown(引数が不足しているため判定できません)"
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result,
                }
            )

        response2 = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS,
        )
        return response2.choices[0].message.content

    return msg.content


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            body = json.loads(raw or b"{}")
            user_message = str(body.get("message", "")).strip()[:MAX_INPUT_CHARS]

            if not user_message:
                self._send_json(400, {"error": "message is empty"})
                return

            if not os.environ.get("OPENAI_API_KEY"):
                self._send_json(500, {"error": "OPENAI_API_KEY is not configured"})
                return

            reply = run_chat(user_message)
            self._send_json(200, {"reply": reply})

        except Exception as e:  # noqa: BLE001
            self._send_json(500, {"error": str(e)})
