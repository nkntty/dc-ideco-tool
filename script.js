// ------------------------------------------------------------
// 企業型DC・iDeCo 自動移換リスク診断ロジック
// 全てルールベース(投資助言に該当しないよう、制度・手続きの案内に限定)
// ------------------------------------------------------------

const questions = [
  {
    key: "jobChange",
    title: "直近で転職・退職をしたのはいつ頃ですか?",
    options: [
      { label: "6ヶ月以内", value: "within6m" },
      { label: "6ヶ月〜1年前", value: "6to12m" },
      { label: "1年以上前", value: "over1y" },
      { label: "転職・退職はしていない", value: "none" },
    ],
  },
  {
    key: "hadDC",
    title: "前職(または退職した会社)に企業型DC(企業型確定拠出年金)はありましたか?",
    options: [
      { label: "あった", value: "yes" },
      { label: "なかった", value: "no" },
      { label: "わからない", value: "unknown" },
    ],
  },
  {
    key: "transferred",
    title: "転職・退職後、DC資産の移換手続き(iDeCoや転職先の制度への移換)はしましたか?",
    options: [
      { label: "手続き済み", value: "done" },
      { label: "していない", value: "notdone" },
      { label: "わからない", value: "unknown" },
    ],
  },
  {
    key: "currentDC",
    title: "現在の勤務先(または現在の状況)を教えてください",
    options: [
      { label: "企業型DCがある会社に勤務", value: "hasDC" },
      { label: "企業型DCがない会社に勤務", value: "noDC" },
      { label: "自営業・フリーランス・無職", value: "selfEmployed" },
    ],
  },
];

let currentStep = 0;
const answers = {};

const startBtn = document.getElementById("start-btn");
const quizSection = document.getElementById("quiz-section");
const resultSection = document.getElementById("result-section");
const quizBox = document.getElementById("quiz-box");
const resultBox = document.getElementById("result-box");

startBtn.addEventListener("click", () => {
  currentStep = 0;
  answers.jobChange = null;
  answers.hadDC = null;
  answers.transferred = null;
  answers.currentDC = null;
  quizSection.classList.remove("hidden");
  resultSection.classList.add("hidden");
  renderQuestion();
  quizSection.scrollIntoView({ behavior: "smooth" });
});

function renderQuestion() {
  // 「転職していない」なら以降の質問をスキップして低リスク判定へ
  if (currentStep === 1 && answers.jobChange === "none") {
    showResult();
    return;
  }

  const q = questions[currentStep];
  if (!q) {
    showResult();
    return;
  }

  quizBox.innerHTML = `
    <div class="q-card">
      <div class="q-progress">質問 ${currentStep + 1} / ${questions.length}</div>
      <div class="q-title">${q.title}</div>
      <div class="q-options">
        ${q.options
          .map(
            (opt) =>
              `<button class="q-option" data-key="${q.key}" data-value="${opt.value}">${opt.label}</button>`
          )
          .join("")}
      </div>
    </div>
  `;

  quizBox.querySelectorAll(".q-option").forEach((btn) => {
    btn.addEventListener("click", () => {
      answers[btn.dataset.key] = btn.dataset.value;
      currentStep += 1;
      renderQuestion();
    });
  });
}

function computeRisk() {
  const { jobChange, hadDC, transferred, currentDC } = answers;

  // 転職していない、またはDCがそもそもなかった場合はリスク対象外
  if (jobChange === "none" || hadDC === "no") {
    return {
      level: "low",
      label: "現時点ではリスク低",
      message:
        "今回の回答からは、自動移換の対象になっている可能性は低そうです。ただし今後転職・退職をする際は、6ヶ月以内の移換手続きを忘れずに。",
      steps: [
        "転職・退職時は退職先から届く「移換のお知らせ」を必ず確認する",
        "次の勤務先にDC制度があるか事前に確認しておく",
      ],
    };
  }

  if (transferred === "done") {
    return {
      level: "low",
      label: "手続き済み・リスク低",
      message:
        "移換手続きが完了しているとのことなので、自動移換の心配は基本的にありません。念のため移換先の口座で資産が反映されているか確認しておくと安心です。",
      steps: [
        "iDeCoまたは転職先DCの口座残高が正しく反映されているか確認する",
        "運用商品の配分が現在の方針と合っているか年に一度は見直す",
      ],
    };
  }

  const monthsSince = { within6m: 3, "6to12m": 9, over1y: 18 }[jobChange] ?? 0;

  if (monthsSince >= 6 && (transferred === "notdone" || transferred === "unknown")) {
    return {
      level: "high",
      label: "高リスク:自動移換の可能性が高い",
      message:
        "転職・退職から6ヶ月以上が経過し、移換手続きが未完了(または不明)とのことなので、資産が国民年金基金連合会に自動移換されている可能性が高いです。運用が止まり手数料だけが引かれ続けている状態かもしれません。",
      steps: [
        "国民年金基金連合会のコールセンターまたはウェブサイトで自動移換の有無を確認する",
        "現在の勤務状況(企業型DCの有無・自営業か)に応じて、iDeCoまたは転職先DCへの移換手続きを行う",
        "必要書類(基礎年金番号がわかるものなど)を事前に準備しておく",
      ],
    };
  }

  if (monthsSince > 0 && monthsSince < 6) {
    return {
      level: "mid",
      label: "要注意:今すぐ動けば間に合う",
      message:
        "転職・退職から6ヶ月以内であれば、まだ自動移換される前に手続きができるタイミングです。早めに動きましょう。",
      steps: [
        "現在の勤務先の状況(DCの有無・自営業か)を確認する",
        "iDeCoまたは転職先DCへの移換手続きをできるだけ早く行う",
        "手続き期限(退職から6ヶ月)をカレンダーに登録しておく",
      ],
    };
  }

  return {
    level: "mid",
    label: "状況を確認しましょう",
    message:
      "回答内容から自動移換のリスクを断定できませんでした。念のため国民年金基金連合会で現在の状況を確認することをおすすめします。",
    steps: [
      "国民年金基金連合会に自動移換の有無を問い合わせる",
      "手元の年金関連の通知書類を確認する",
    ],
  };
}

function showResult() {
  quizSection.classList.add("hidden");
  resultSection.classList.remove("hidden");

  const risk = computeRisk();
  const riskClass = { high: "risk-high", mid: "risk-mid", low: "risk-low" }[risk.level];

  resultBox.innerHTML = `
    <div class="result-card">
      <span class="risk-tag ${riskClass}">${risk.label}</span>
      <h2>診断結果</h2>
      <p>${risk.message}</p>
      <ul class="next-steps">
        ${risk.steps.map((s) => `<li>${s}</li>`).join("")}
      </ul>
      <span class="retry-link" id="retry-btn">もう一度診断する</span>
    </div>
  `;

  document.getElementById("retry-btn").addEventListener("click", () => {
    resultSection.classList.add("hidden");
    startBtn.scrollIntoView({ behavior: "smooth" });
  });

  resultSection.scrollIntoView({ behavior: "smooth" });
}

// ------------------------------------------------------------
// ウェイトリスト登録(Formspreeに送信)
// https://formspree.io で無料アカウントを作り、フォームを1つ作成して
// 発行されたエンドポイントURLを下の FORMSPREE_ENDPOINT に貼り替えてください。
// 例: "https://formspree.io/f/abcdwxyz"
// ------------------------------------------------------------
const FORMSPREE_ENDPOINT = "https://formspree.io/f/xrenlrzo";

const waitlistForm = document.getElementById("waitlist-form");
const waitlistMsg = document.getElementById("waitlist-msg");

waitlistForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  if (FORMSPREE_ENDPOINT.includes("YOUR_FORM_ID")) {
    waitlistMsg.textContent = "設定が未完了です(FORMSPREE_ENDPOINTを設定してください)";
    return;
  }

  const formData = new FormData(waitlistForm);

  try {
    const res = await fetch(FORMSPREE_ENDPOINT, {
      method: "POST",
      headers: { Accept: "application/json" },
      body: formData,
    });

    if (res.ok) {
      waitlistMsg.textContent = "登録ありがとうございます!リリース時にご連絡します。";
      waitlistForm.reset();
    } else {
      waitlistMsg.textContent = "送信に失敗しました。時間をおいて再度お試しください。";
    }
  } catch (err) {
    waitlistMsg.textContent = "通信エラーが発生しました。ネットワークをご確認ください。";
  }
});
