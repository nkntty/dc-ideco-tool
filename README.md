# DC・iDeCo移換診断ツール(スターター)

企業型DC・iDeCoの「自動移換問題」に気づいてもらうための、診断+ウェイトリスト機能付きランディングページのMVPです。フレームワーク不要のプレーンなHTML/CSS/JSなので、GitHub Pages や Vercel にそのままデプロイできます。

## ファイル構成

```
dc-ideco-tool/
├── index.html   # ランディングページ本体
├── style.css    # スタイル
├── script.js    # 診断クイズのロジック + ウェイトリスト登録
└── README.md    # このファイル
```

## ローカルで確認する

ビルド不要です。`index.html` をブラウザで直接開くか、簡易サーバーを立てて確認してください。

```bash
cd dc-ideco-tool
python3 -m http.server 8000
# http://localhost:8000 を開く
```

## GitHubへのpush

```bash
cd dc-ideco-tool
git init
git add .
git commit -m "Initial commit: DC/iDeCo diagnosis MVP"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

## デプロイ(無料・数分でできる方法)

**GitHub Pages を使う場合**
1. GitHubのリポジトリ設定 → Pages
2. Source を `main` ブランチ / ルートディレクトリに設定
3. 数分で `https://<your-username>.github.io/<repo-name>/` が公開される

**Vercel を使う場合(推奨・カスタムドメインも楽)**
1. https://vercel.com にGitHubアカウントでログイン
2. 「New Project」からこのリポジトリを選択
3. フレームワーク設定は不要(Other/Staticのままでよい)、そのままDeploy

## 今のMVPでできること / できないこと

**できること**
- 4問の質問から自動移換リスクを判定するルールベース診断
- 診断結果に応じた次のアクション(手続き案内)の表示
- メールアドレスのウェイトリスト登録(現状はブラウザのconsole.logのみ)

**まだできないこと(今後の実装対象)**
- ウェイトリストの実データ保存(下記「次にやること」参照)
- 転職・退職時期の自動リマインド通知(LINE/メール)
- 実際の移換手続きの代行・自動化

## 次にやること(優先順位順)

1. **ウェイトリスト送信先を本物にする**
   `script.js` の `waitlistForm` の送信処理を、Google Forms・Tally・ConvertKitなどのエンドポイントに差し替える。無料枠で十分。

2. **X / note で発信を始める**
   「企業型DC 自動移換」「転職 年金 放置」などのキーワードで悩んでいる人に向けて、診断ページのリンク付きで投稿。転職系ハッシュタグとの相性が良い。

3. **リマインド機能(次のマイルストーン)**
   退職日を入力してもらい、6ヶ月後にメール/LINE通知を送る仕組み。バックエンドが必要になるので、Supabase(無料枠)+ Resend(メール送信)や、Zapier連携などが低コストで実装しやすい。

4. **マネタイズ:iDeCo口座開設のアフィリエイト**
   診断結果の「iDeCoへの移換をおすすめします」の下に、SBI証券・楽天証券などのiDeCo口座開設アフィリエイトリンクを設置。特定の商品(投資信託など)を名指しで推奨しないよう、あくまで「口座開設先の選択肢」として提示する。

5. **法人向け展開の布石**
   ある程度ユーザーが集まったら、退職者への案内義務がある企業(特に人事労務SaaSを使っている中小企業)向けに、同じ診断ロジックをコンプライアンスツールとして提供する展開も検討。

## リマインド機能(Pythonスクリプト)

`scripts/` フォルダに、登録者へのリマインドメールを送るための2本のスクリプトがあります。

- `analyze_submissions.py` : Formspreeの登録データを集計し、リマインド対象者(転職・退職から5〜6ヶ月経過)を表示する
- `send_reminders.py` : 対象者にGmail経由でリマインドメールを送信する(二重送信防止のログ付き)

### セットアップ

```bash
cd scripts
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env` を開き、`GMAIL_ADDRESS` に自分のGmailアドレス、`GMAIL_APP_PASSWORD` にアプリパスワードを設定してください。アプリパスワードは、Googleアカウントで2段階認証を有効にした上で https://myaccount.google.com/apppasswords から発行できます(通常のGoogleパスワードとは別物です)。

### 実行の流れ

1. Formspreeダッシュボード → 対象フォーム → Submissions → CSVをエクスポートし、`scripts/submissions.csv` として保存する
2. 集計だけ確認したい場合: `python3 analyze_submissions.py`
3. リマインドメールを実際に送る場合: `python3 send_reminders.py`

現時点では手動でCSVをダウンロードして実行する運用ですが、慣れてきたら GitHub Actions の scheduled workflow(`cron`)で `send_reminders.py` を毎日自動実行するように発展させられます(その場合、CSV取得部分をFormspreeの有料プランのAPI、またはGoogle Sheets連携に置き換える必要があります)。

### 重要な注意

`submissions.csv` と `reminded_log.csv` には登録者の個人のメールアドレスが含まれます。このリポジトリは公開GitHubリポジトリなので、**これらのファイルは絶対にcommit・pushしないでください**(`.gitignore` で既に除外設定済みですが、念のため `git status` で確認する習慣をつけてください)。

## 規制まわりの注意

- このツールは制度・手続きに関する一般的な情報提供であり、特定の運用商品や銘柄を推奨するものではありません(投資助言業の登録が不要な範囲に留めています)。
- 実際のリリース前に、内容が現行の確定拠出年金法・関連通知に沿っているか、可能であれば社会保険労務士やFPに一度レビューしてもらうことを推奨します。
