const API_URL = "http://localhost:8010/predict";

async function getCurrentTabUrl() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab?.url || "";
}

async function analyze(url, model) {
  const res = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, model }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

function render(data) {
  const resultEl = document.getElementById("result");
  const verdictClass = data.is_phishing ? "risky" : "safe";
  const verdictText = data.is_phishing ? "LIKELY PHISHING" : "LOOKS SAFE";
  const explanationHtml = data.explanation.length
    ? `<ul>${data.explanation.map((e) => `<li>${e}</li>`).join("")}</ul>`
    : "<div style='color:#9aa4ab'>No strong risk signals detected.</div>";

  resultEl.innerHTML = `
    <div class="verdict ${verdictClass}">${verdictText}</div>
    <div class="prob">probability: ${(data.probability * 100).toFixed(1)}%  ·  model: ${data.model}</div>
    ${explanationHtml}
  `;
}

async function run() {
  const url = await getCurrentTabUrl();
  document.getElementById("url").textContent = url;
  const model = document.getElementById("model").value;

  if (!url || !url.startsWith("http")) {
    document.getElementById("result").innerHTML = `<div class="err">No analyzable URL on this tab.</div>`;
    return;
  }

  try {
    const data = await analyze(url, model);
    render(data);
  } catch (e) {
    document.getElementById("result").innerHTML =
      `<div class="err">Could not reach the detector API at localhost:8010.<br>Start it with: uvicorn api.main:app --port 8010</div>`;
  }
}

document.getElementById("model").addEventListener("change", run);
run();
