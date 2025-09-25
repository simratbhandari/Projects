const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

const chatLog = $("#chatLog");
const chatForm = $("#chatForm");
const chatInput = $("#chatInput");
const micBtn = $("#micBtn");
const ttsToggle = $("#ttsToggle");
const clearChat = $("#clearChat");

const planForm = $("#planForm");
const planOut = $("#planOut");
const printBtn = $("#printPlan");
const dlBtn = $("#downloadJSON");

// Utilities
const store = {
  load() {
    return JSON.parse(localStorage.getItem("mp_history") || "[]");
  },
  save(items) {
    localStorage.setItem("mp_history", JSON.stringify(items));
  },
};

// Streaming TTS (Web Speech API)
class TTSStreamer {
  constructor(toggleEl, { lang, rate = 1.0, pitch = 1.0, minChunk = 45 } = {}) {
    this.toggleEl = toggleEl;
    this.lang = lang || document.documentElement.lang || "en-US";
    this.rate = rate;
    this.pitch = pitch;
    this.minChunk = minChunk;
    this.buf = "";
  }
  get enabled() {
    return !!this.toggleEl?.checked;
  }

  // Add new text; speak completed sentences if enabled
  ingest(delta) {
    this.buf += delta || "";
    if (!this.enabled) return;
    this.#emitChunksFromBuffer();
  }

  // Try speaking whatever is already buffered (e.g., when toggle turned on)
  drain() {
    if (!this.enabled) return;
    this.#emitChunksFromBuffer();
  }

  flush() {
    if (!this.enabled) {
      this.buf = "";
      return;
    }
    const tail = this.buf.trim();
    if (tail) this.#speak(tail);
    this.buf = "";
  }

  cancel() {
    try {
      window.speechSynthesis.cancel();
    } catch {}
    this.buf = "";
  }

  #emitChunksFromBuffer() {
    // Speak complete sentences, and avoid tiny fragments
    const out = [];
    let last = 0;
    const re = /([.!?…])(\s|$)/g;
    let m;
    while ((m = re.exec(this.buf)) !== null) {
      const end = m.index + m[1].length;
      const sentence = this.buf.slice(last, end).trim();
      if (sentence.length >= this.minChunk) {
        out.push(sentence);
        last = end + (m[2] ? 1 : 0);
      }
    }
    if (out.length) {
      this.buf = this.buf.slice(last);
      out.forEach((chunk) => this.#speak(chunk));
    }
  }

  #speak(text) {
    // Light markdown cleanup so TTS sounds natural
    const cleaned = text
      .replace(/[`*_#>~\-]+/g, " ")
      .replace(/\[(.*?)\]\((.*?)\)/g, "$1")
      .replace(/\s{2,}/g, " ")
      .trim();

    if (!cleaned) return;
    const u = new SpeechSynthesisUtterance(cleaned);
    u.lang = this.lang;
    u.rate = this.rate;
    u.pitch = this.pitch;
    window.speechSynthesis.speak(u);
  }
}

const ttsStreamer = new TTSStreamer(ttsToggle);

// If user turns TTS on mid-reply, speak from current buffer
ttsToggle?.addEventListener("change", () => {
  if (!ttsToggle.checked) ttsStreamer.cancel();
  else ttsStreamer.drain();
});

function addMessage(role, content) {
  const wrap = document.createElement("div");
  wrap.className = `flex ${
    role === "user" ? "justify-end" : "justify-start"
  } mb-3`;
  const bubble = document.createElement("div");
  bubble.className = `max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow ${
    role === "user"
      ? "bg-gradient-to-tr from-blueberry to-mint text-white"
      : "bg-white/80 ring-1 ring-white/70"
  }`;
  bubble.innerHTML = content;
  wrap.appendChild(bubble);
  chatLog.appendChild(wrap);
  chatLog.scrollTop = chatLog.scrollHeight;
}

// Stream AI Response
async function streamChat(messages) {
  const res = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
  });
  if (!res.ok || !res.body) throw new Error("Network error");

  // Fresh reply: stop any previous speech & clear internal buffer
  ttsStreamer.cancel();

  let buffer = "";
  const reader = res.body.getReader();
  const decoder = new TextDecoder();

  // placeholder assistant bubble
  const holder = document.createElement("div");
  holder.className = "flex justify-start mb-3";
  const bubble = document.createElement("div");
  bubble.className =
    "max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow bg-white/80 ring-1 ring-white/70";
  bubble.innerHTML = '<em class="text-slate-500">Typing…</em>';
  holder.appendChild(bubble);
  chatLog.appendChild(holder);

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";

    for (const chunk of parts) {
      if (!chunk.startsWith("data:")) continue;
      const data = chunk.replace(/^data:\s*/, "");
      if (data === "[DONE]") {
        buffer = "";
        break;
      }
      try {
        const obj = JSON.parse(data);
        if (obj.error) {
          bubble.innerHTML = `<span class="text-rose-600">${obj.error}</span>`;
          continue;
        }
        if (obj.delta) {
          const safe = obj.delta.replace(/</g, "&lt;").replace(/>/g, "&gt;");
          bubble.innerHTML =
            (bubble.textContent === "Typing…" ? "" : bubble.innerHTML) + safe;

          // Speak the stream as it arrives (sentence-by-sentence)
          ttsStreamer.ingest(obj.delta);
        }
      } catch {
        /* ignore bad chunks */
        console.log(error);
      }
    }
  }

  // Speak whatever partial text remains
  ttsStreamer.flush();
  chatLog.scrollTop = chatLog.scrollHeight;
}

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  // Stop any ongoing TTS before starting a fresh request
  ttsStreamer.cancel();

  const text = chatInput.value.trim();
  if (!text) return;

  const history = store.load();
  history.push({ role: "user", content: text });
  store.save(history);

  addMessage("user", text.replace(/</g, "&lt;"));
  chatInput.value = "";

  const messages = [
    { role: "system", content: "You are a helpful nutrition assistant." },
    ...history,
  ];

  try {
    await streamChat(messages);
  } catch (err) {
    addMessage(
      "assistant",
      `<span class="text-rose-600">${err.message}</span>`
    );
  }
});

clearChat.addEventListener("click", () => {
  ttsStreamer.cancel(); // stop speaking immediately
  localStorage.removeItem("mp_history");
  chatLog.innerHTML = "";
});

// Voice input (Web Speech API)
let recognizer = null;
let recognizing = false;

function setupVoice() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return null;
  const rec = new SR();
  rec.lang = document.documentElement.lang || "en-US";
  rec.continuous = false;
  rec.interimResults = true;
  rec.onresult = (e) => {
    let final = "";
    for (let i = e.resultIndex; i < e.results.length; ++i) {
      const t = e.results[i][0].transcript;
      if (e.results[i].isFinal) final += t;
      else chatInput.value = t;
    }
    if (final) chatInput.value = final;
  };
  rec.onstart = () => {
    recognizing = true;
    micBtn.classList.add("ring-2", "ring-lime");
    // Avoid feedback loop while mic is open
    ttsStreamer.cancel();
  };
  rec.onend = () => {
    recognizing = false;
    micBtn.classList.remove("ring-2", "ring-lime");
  };
  rec.onerror = (e) => {
    console.warn("SpeechRecognition error", e);
  };
  return rec;
}

micBtn.addEventListener("click", async () => {
  if (!recognizer) recognizer = setupVoice();
  if (!recognizer) {
    alert("Voice input not supported in this browser.");
    return;
  }
  if (recognizing) recognizer.stop();
  else recognizer.start();
});

function renderPlan(data) {
  if (!planOut) return;
  if (!data.days) {
    planOut.innerHTML = '<div class="p-3">No plan.</div>';
    return;
  }
  planOut.innerHTML = "";
  data.days.forEach((d, idx) => {
    const card = document.createElement("div");
    card.className =
      "rounded-2xl overflow-hidden ring-1 ring-white/70 bg-white/80 shadow";
    card.innerHTML = `
      <div class="px-4 py-3 bg-gradient-to-r from-mango via-guava to-rose-400 text-white font-semibold">
        ${d.label || `Day ${idx + 1}`}
      </div>
      <div class="p-4 space-y-3">
        <div class="text-xs text-slate-500">
          Totals: ${d.totals?.calories ?? "?"} kcal · P ${
      d.totals?.protein_g ?? "?"
    }g · C ${d.totals?.carbs_g ?? "?"}g · F ${d.totals?.fat_g ?? "?"}g
        </div>
        ${(d.meals || [])
          .map(
            (m) => `
          <div class="p-3 rounded-xl ring-1 ring-slate-200 bg-white/70">
            <div class="font-medium">${escapeHtml(m.name || "")}</div>
            <div class="text-xs text-slate-500">
              ${m.calories || "?"} kcal · P ${m.protein_g || "?"}g · C ${
              m.carbs_g || "?"
            }g · F ${m.fat_g || "?"}g · ⏱ ${m.prep_time_min || "?"} min
            </div>
            <details class="mt-2">
              <summary class="cursor-pointer text-sm text-slate-700">Ingredients & Steps</summary>
              <div class="mt-2 text-sm">
                <div class="font-semibold">Ingredients</div>
                <ul class="list-disc ml-5 text-slate-700">
                  ${(m.ingredients || [])
                    .map((i) => `<li>${escapeHtml(i)}</li>`)
                    .join("")}
                </ul>
                <div class="font-semibold mt-2">Instructions</div>
                <p class="whitespace-pre-wrap">${escapeHtml(
                  m.instructions || ""
                )}</p>
              </div>
            </details>
          </div>
        `
          )
          .join("")}
      </div>
    `;
    planOut.appendChild(card);
  });
  if (data.shopping_list?.length) {
    const list = document.createElement("div");
    list.className =
      "rounded-2xl overflow-hidden ring-1 ring-white/70 bg-white/80 shadow";
    list.innerHTML = `
      <div class="px-4 py-3 bg-gradient-to-r from-mint to-blueberry text-white font-semibold">Shopping List</div>
      <ul class="p-4 grid grid-cols-1 md:grid-cols-2 gap-2 list-disc ml-5">
        ${data.shopping_list.map((i) => `<li>${escapeHtml(i)}</li>`).join("")}
      </ul>
    `;
    planOut.appendChild(list);
  }
  if (data.notes) {
    const n = document.createElement("div");
    n.className =
      "rounded-2xl overflow-hidden ring-1 ring-white/70 bg-white/80 shadow";
    n.innerHTML = `
      <div class="px-4 py-3 bg-slate-900 text-white font-semibold">Notes</div>
      <div class="p-4 text-sm text-slate-700">${escapeHtml(data.notes)}</div>
    `;
    planOut.appendChild(n);
  }
}

function escapeHtml(s) {
  return (s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}


// Startup
if (APP_WARN) {
  addMessage("assistant", `<span class="text-rose-600">${APP_WARN}</span>`);
}
