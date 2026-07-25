"""
転職・退職から5〜6ヶ月経過した登録者に、自動移換のリマインドメールを送るスクリプト。
Gmail SMTP(アプリパスワード)を使用。同じ相手には二重送信しないよう
reminded_log.csv に送信履歴を記録する。

事前準備:
    1. pip install -r requirements.txt
    2. .env.example を .env にコピーし、GMAIL_ADDRESS / GMAIL_APP_PASSWORD を設定
       (Googleアカウントで2段階認証を有効化した上で「アプリパスワード」を発行する)
    3. Formspreeダッシュボードから submissions.csv をエクスポートしてこのフォルダに置く

使い方:
    python3 send_reminders.py [CSVファイルパス]
    (省略時は ./submissions.csv を読みにいく)

注意:
    submissions.csv と reminded_log.csv には個人のメールアドレスが含まれるため、
    このリポジトリが公開GitHubリポジトリの場合は絶対にcommitしないこと
    (.gitignoreで除外済み)。
"""

import os
import smtplib
import ssl
import sys
from datetime import datetime
from email.mime.text import MIMEText

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
LOG_FILE = "reminded_log.csv"
TOOL_URL = "https://dc-ideco-tool.vercel.app"

SUBJECT = "【リマインド】企業型DCの自動移換、そろそろ期限です"

BODY_TEMPLATE = """{email} 様

企業型DC・iDeCo移換診断ツールにご登録いただきありがとうございます。

ご入力いただいた転職・退職の時期から計算すると、そろそろ「自動移換」の期限(6ヶ月)が
近づいている可能性があります。まだ移換手続きがお済みでない場合は、お早めに以下をご確認ください。

・国民年金基金連合会で自動移換の有無を確認する
・iDeCoまたは転職先の企業型DCへの移換手続きを行う

診断ツール: {tool_url}

※本メールは一度きりの自動リマインドです。既に手続き済みの場合は、
本メールは無視していただいて構いません。
"""


def find_col(df: pd.DataFrame, keyword: str):
    matches = [c for c in df.columns if keyword in c]
    return matches[0] if matches else None


def send_email(to_email: str, body: str):
    msg = MIMEText(body)
    msg["Subject"] = SUBJECT
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = to_email

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())


def load_already_sent() -> set:
    if os.path.exists(LOG_FILE):
        return set(pd.read_csv(LOG_FILE)["email"].tolist())
    return set()


def append_log(email: str):
    row = pd.DataFrame([{"email": email, "sent_at": datetime.now().isoformat()}])
    header = not os.path.exists(LOG_FILE)
    row.to_csv(LOG_FILE, mode="a", header=header, index=False)


def main(csv_path: str):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("GMAIL_ADDRESS / GMAIL_APP_PASSWORD が .env に設定されていません。処理を中止します。")
        sys.exit(1)

    df = pd.read_csv(csv_path)
    df.columns = [c.strip().lower() for c in df.columns]

    email_col = find_col(df, "email")
    job_col = find_col(df, "job_change_month")

    if not email_col or not job_col:
        print("email または job_change_month の列が見つかりませんでした。CSVの内容を確認してください。")
        sys.exit(1)

    job_dates = pd.to_datetime(df[job_col], errors="coerce", format="%Y-%m")
    now = pd.Timestamp.now()
    months_since = (now.year - job_dates.dt.year) * 12 + (now.month - job_dates.dt.month)

    target = df[(months_since >= 5) & (months_since <= 6)]
    already_sent = load_already_sent()

    sent_count = 0
    for idx in target.index:
        email = df.loc[idx, email_col]
        if pd.isna(email) or email in already_sent:
            continue

        body = BODY_TEMPLATE.format(email=email, tool_url=TOOL_URL)
        try:
            send_email(email, body)
            append_log(email)
            sent_count += 1
            print(f"送信済み: {email}")
        except Exception as e:
            print(f"送信失敗: {email} ({e})")

    print(f"\n合計 {sent_count} 件のリマインドを送信しました。")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "submissions.csv"
    main(path)
