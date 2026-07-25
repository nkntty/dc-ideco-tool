"""
Formspreeからエクスポートした submissions.csv を読み込み、
登録数の推移とリマインド対象者(転職から5〜6ヶ月)を集計するスクリプト。

使い方:
    python3 analyze_submissions.py [CSVファイルパス]
    (省略時は ./submissions.csv を読みにいく)

CSVの取得方法:
    Formspreeダッシュボード → 対象フォーム → Submissions →
    右上あたりの Export / Download ボタンからCSVをダウンロードし、
    このスクリプトと同じフォルダに submissions.csv として保存する。
"""

import sys
import pandas as pd


def find_col(df: pd.DataFrame, keyword: str):
    matches = [c for c in df.columns if keyword in c]
    return matches[0] if matches else None


def load(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def main(csv_path: str):
    df = load(csv_path)

    email_col = find_col(df, "email")
    date_col = find_col(df, "date") or find_col(df, "created")
    job_col = find_col(df, "job_change_month")

    total = len(df)
    print(f"総登録数: {total}件")

    if date_col:
        parsed_dates = pd.to_datetime(df[date_col], errors="coerce")
        daily = parsed_dates.dt.date.value_counts().sort_index()
        print("\n日別登録数:")
        print(daily.to_string())
    else:
        print("\n(日付列が見つからなかったため、日別集計はスキップしました)")

    if job_col:
        job_dates = pd.to_datetime(df[job_col], errors="coerce", format="%Y-%m")
        now = pd.Timestamp.now()
        months_since = (now.year - job_dates.dt.year) * 12 + (now.month - job_dates.dt.month)

        near_deadline = df[(months_since >= 5) & (months_since <= 6)]
        print(f"\nリマインド送信対象(転職・退職から5〜6ヶ月経過): {len(near_deadline)}件")

        if email_col and len(near_deadline) > 0:
            for idx in near_deadline.index:
                m = months_since.loc[idx]
                email = df.loc[idx, email_col]
                print(f"  - {email} (経過 {int(m)}ヶ月)")
    else:
        print("\n(job_change_month列が見つからなかったため、リマインド対象の集計はスキップしました)")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "submissions.csv"
    main(path)
