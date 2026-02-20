<template>
  <PageShell>
    <div class="fixed inset-0 top-22 flex flex-col bg-transparent">
      <!-- ── Messages ── -->
      <div ref="scrollEl" class="messages-area flex-1 overflow-y-auto" @scroll="onScroll">
        <div class="max-w-180 mx-auto px-6 pt-8 pb-6 flex flex-col gap-6">
          <!-- Empty state -->
          <div v-if="messages.length === 0"
            class="flex flex-col items-center justify-center gap-3 py-20 px-4 text-center">
            <div
              class="w-14 h-14 rounded-2xl bg-[#111722] text-white grid place-items-center text-[0.7rem] font-bold tracking-[0.2em]">
              RPL
            </div>
            <h2 class="m-0 text-[1.6rem] font-semibold text-(--ink)">
              How can I help?
            </h2>
            <p class="m-0 text-(--muted) text-sm">
              {{ activeModel || "Configure Ollama above to get started" }}
            </p>
          </div>

          <!-- Message list -->
          <template v-for="msg in messages" :key="msg.id">
            <!-- User bubble -->
            <div v-if="msg.role === 'user'" class="flex gap-3 justify-end">
              <div
                class="max-w-[78%] bg-[rgba(255,106,0,0.09)] border border-[rgba(255,106,0,0.2)] rounded-[20px] rounded-br-md px-4 py-3">
                <p class="m-0 text-[0.9rem] leading-relaxed whitespace-pre-wrap wrap-break-word">
                  {{ msg.content }}
                </p>
              </div>
            </div>

            <!-- Assistant message -->
            <div v-else class="flex gap-3 items-start">
              <div
                class="shrink-0 w-8 h-8 rounded-[10px] bg-[#111722] text-white grid place-items-center text-[0.65rem] font-bold tracking-[0.05em] mt-0.5">
                AI
              </div>
              <div class="flex-1 min-w-0">
                <!-- Thinking block -->
                <div v-if="msg.thinking || msg.streamingThinking"
                  class="mb-3 border border-[rgba(12,17,24,0.1)] rounded-xl overflow-hidden">
                  <button
                    class="w-full flex items-center gap-2 px-3.5 py-[0.55rem] bg-[rgba(12,17,24,0.04)] border-none cursor-pointer text-[0.78rem] font-medium font-[inherit] text-(--muted) text-left transition-colors duration-150 hover:bg-[rgba(12,17,24,0.07)]"
                    @click="msg.thinkingExpanded = !msg.thinkingExpanded">
                    <span class="w-1.75 h-1.75 rounded-full bg-(--teal) shrink-0 transition-colors duration-300"
                      :class="{ 'think-dot-pulsing': msg.streamingThinking }"></span>
                    <span class="flex-1">{{
                      msg.streamingThinking
                        ? "Thinking…"
                        : "Thought for a moment"
                    }}</span>
                    <svg class="transition-transform duration-200 text-(--muted)"
                      :class="{ 'rotate-180': msg.thinkingExpanded }" xmlns="http://www.w3.org/2000/svg" width="12"
                      height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
                      stroke-linecap="round" stroke-linejoin="round">
                      <polyline points="6 9 12 15 18 9" />
                    </svg>
                  </button>
                  <Transition name="think-expand">
                    <div v-if="msg.thinkingExpanded"
                      class="think-content border-t border-[rgba(12,17,24,0.07)] bg-[rgba(12,17,24,0.02)] overflow-y-auto">
                      <pre
                        class="m-0 px-3.5 py-3 text-[0.75rem] font-mono text-(--muted) whitespace-pre-wrap wrap-break-word leading-[1.65]">{{ msg.thinking }}</pre>
                    </div>
                  </Transition>
                </div>

                <!-- Response content -->
                <div v-if="msg.content"
                  class="response-content text-[0.9rem] leading-[1.7] text-(--ink) wrap-break-word"
                  v-html="renderMarkdown(msg.content)"></div>

                <!-- Streaming dots (before first content) -->
                <div v-if="msg.streaming && !msg.content && !msg.streamingThinking"
                  class="flex gap-1 items-center py-[0.3rem]">
                  <span class="typing-dot"></span>
                  <span class="typing-dot [animation-delay:0.2s]"></span>
                  <span class="typing-dot [animation-delay:0.4s]"></span>
                </div>
              </div>
            </div>
          </template>

          <!-- Stream error -->
          <div v-if="streamError"
            class="flex items-center gap-2 text-[0.82rem] text-red-600 bg-[rgba(220,38,38,0.07)] border border-[rgba(220,38,38,0.2)] rounded-[10px] px-3.5 py-[0.6rem]">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            {{ streamError }}
          </div>

          <div ref="bottomEl"></div>
        </div>
      </div>

      <!-- ── Input Card ── -->
      <div class="shrink-0 px-6 pt-4 pb-5 bg-transparent">
        <div
          class="max-w-180 mx-auto border-[1.5px] rounded-[18px] bg-white px-4 py-[0.85rem] shadow-[0_2px_12px_rgba(12,17,24,0.08)] transition-[border-color,box-shadow] duration-200"
          :class="inputFocused
            ? 'border-[rgba(255,106,0,0.5)] shadow-[0_0_0_3px_rgba(255,106,0,0.1),0_2px_12px_rgba(12,17,24,0.08)]'
            : 'border-[rgba(12,17,24,0.15)]'
            ">
          <!-- Settings panel (inside card) -->
          <Transition name="slide-up">
            <div v-if="settingsOpen" class="pb-3 mb-2 border-b border-[rgba(12,17,24,0.08)]">
              <div class="flex flex-col gap-[0.4rem]">
                <label class="text-[0.7rem] font-semibold tracking-[0.08em] uppercase text-(--muted)">Ollama
                  Endpoint</label>
                <div class="flex gap-2">
                  <input v-model="endpointDraft" type="url" placeholder="http://localhost:11434"
                    class="flex-1 border border-[rgba(12,17,24,0.15)] rounded-[10px] px-3 py-[0.45rem] text-[0.85rem] text-(--ink) bg-[rgba(255,255,255,0.8)] outline-none transition-[border-color,box-shadow] duration-150 focus:border-(--accent) focus:shadow-[0_0_0_3px_rgba(255,106,0,0.12)]"
                    @keydown.enter="applyEndpoint" />
                  <button
                    class="px-4 py-[0.45rem] rounded-[10px] border-none bg-(--ink) text-white text-[0.82rem] font-semibold cursor-pointer transition-colors duration-150 whitespace-nowrap hover:bg-[#1d2a3a] disabled:opacity-50 disabled:cursor-default"
                    @click="applyEndpoint" :disabled="modelsLoading">
                    {{ modelsLoading ? "Connecting…" : "Connect" }}
                  </button>
                </div>
              </div>
              <p v-if="modelsError" class="mt-2 m-0 text-[0.78rem] text-red-600">
                {{ modelsError }}
              </p>
              <p v-else-if="models.length > 0" class="mt-2 m-0 text-[0.78rem] text-green-700">
                Connected · {{ models.length }} model{{
                  models.length === 1 ? "" : "s"
                }}
                available
              </p>
            </div>
          </Transition>

          <!-- Input textarea -->
          <textarea ref="inputEl" v-model="input" placeholder="Message…" rows="1"
            class="w-full resize-none bg-transparent border-none outline-none text-[0.9rem] text-(--ink) leading-relaxed max-h-50 overflow-y-auto placeholder:text-(--muted) disabled:opacity-60"
            :disabled="isStreaming" @keydown.enter.exact.prevent="send" @input="autoResize" @focus="inputFocused = true"
            @blur="inputFocused = false"></textarea>

          <!-- Bottom toolbar -->
          <div class="flex items-center justify-between pt-2 mt-2 border-t border-[rgba(12,17,24,0.08)]">
            <div class="flex items-center gap-2">
              <button
                class="flex items-center justify-center w-8 h-8 rounded-lg border-none bg-transparent text-(--muted) cursor-pointer transition-colors duration-150 hover:bg-[rgba(12,17,24,0.07)] hover:text-(--ink)"
                @click="clearChat" title="New conversation">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="12" y1="5" x2="12" y2="19" />
                  <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
              </button>
            </div>

            <div class="flex items-center gap-1">
              <button
                class="flex items-center justify-center w-8 h-8 rounded-lg border-none bg-transparent text-(--muted) cursor-pointer transition-colors duration-150 hover:bg-[rgba(12,17,24,0.07)] hover:text-(--ink)"
                :class="{
                  'bg-[rgba(12,17,24,0.07)] text-(--ink)!': settingsOpen,
                }" @click="settingsOpen = !settingsOpen" title="Settings">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="3" />
                  <path
                    d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
                </svg>
              </button>
              <div class="relative flex items-center">
                <select v-model="activeModel"
                  class="appearance-none bg-[rgba(12,17,24,0.05)] border-none rounded-lg py-[0.35rem] pl-[0.65rem] pr-7 text-[0.78rem] font-medium text-(--ink) cursor-pointer outline-none transition-colors duration-150 hover:bg-[rgba(12,17,24,0.08)] focus:bg-[rgba(12,17,24,0.1)] disabled:opacity-50 disabled:cursor-default"
                  :disabled="modelsLoading" @change="onModelChange" title="Select model">
                  <option v-if="models.length === 0" value="">
                    {{ modelsLoading ? "Loading…" : "No models" }}
                  </option>
                  <option v-for="m in models" :key="m.id" :value="m.id">
                    {{ m.id }}
                  </option>
                </select>
                <svg class="absolute right-2 text-(--muted) pointer-events-none" xmlns="http://www.w3.org/2000/svg"
                  width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
                  stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="6 9 12 15 18 9" />
                </svg>
              </div>
              <button
                class="flex items-center justify-center w-8 h-8 rounded-[10px] border-none cursor-pointer bg-[rgba(12,17,24,0.1)] text-(--muted) transition-[background,color,transform] duration-150 hover:scale-105 disabled:cursor-default disabled:opacity-50"
                :class="{
                  'bg-[#C96040] text-white!': !isStreaming && input.trim(),
                  'bg-red-600 text-white!': isStreaming,
                }" @click="isStreaming ? stopStream() : send()" :disabled="!input.trim() && !isStreaming"
                :title="isStreaming ? 'Stop' : 'Send'">
                <svg v-if="isStreaming" xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24"
                  fill="currentColor">
                  <rect x="4" y="4" width="16" height="16" rx="2" />
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="12" y1="19" x2="12" y2="5" />
                  <polyline points="5 12 12 5 19 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </PageShell>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from "vue";
import { settings, persistSettings } from "../stores/chat.js";
import PageShell from "../components/PageShell.vue";

// ── State ────────────────────────────────────────────────────────────────────

const messages = ref([]);
const input = ref("");
const inputFocused = ref(false);
const isStreaming = ref(false);
const streamError = ref("");

const models = ref([]);
const modelsLoading = ref(false);
const modelsError = ref("");

const settingsOpen = ref(false);
const activeModel = ref(settings.model);
const endpointDraft = ref(settings.endpoint);

const scrollEl = ref(null);
const bottomEl = ref(null);
const inputEl = ref(null);

let abortController = null;
let userScrolledUp = false;

// ── Think-tag stream parser ───────────────────────────────────────────────────
// Parses <think>...</think> blocks out of streamed content in real time.

// Both <think> and <thinking> are used by different models.
const OPEN_TAGS = ["<think>", "<thinking>"];
const CLOSE_TAG = { "<think>": "</think>", "<thinking>": "</thinking>" };

function createThinkState() {
  return {
    pendingTag: "",
    inThink: false,
    closeTag: "",
    thinking: "",
    content: "",
  };
}

function processDelta(state, chunk) {
  for (const ch of chunk) {
    if (!state.inThink) {
      state.pendingTag += ch;
      const couldMatch = OPEN_TAGS.some((t) => t.startsWith(state.pendingTag));
      const fullMatch = OPEN_TAGS.find((t) => t === state.pendingTag);
      if (fullMatch) {
        state.inThink = true;
        state.closeTag = CLOSE_TAG[fullMatch];
        state.pendingTag = "";
      } else if (!couldMatch) {
        state.content += state.pendingTag;
        state.pendingTag = "";
      }
    } else {
      state.pendingTag += ch;
      if (state.closeTag.startsWith(state.pendingTag)) {
        if (state.pendingTag === state.closeTag) {
          state.inThink = false;
          state.closeTag = "";
          state.pendingTag = "";
        }
      } else {
        state.thinking += state.pendingTag;
        state.pendingTag = "";
      }
    }
  }
}

function flushThinkState(state) {
  if (state.inThink) {
    state.thinking += state.pendingTag;
  } else {
    state.content += state.pendingTag;
  }
  state.pendingTag = "";
}

function extractReasoningDelta(delta) {
  const parts = [];
  for (const key of ["thinking", "reasoning_content", "reasoning"]) {
    const value = delta?.[key];
    if (typeof value === "string" && value.length > 0) {
      parts.push(value);
    }
  }
  return parts.join("");
}

function shouldRetryWithoutThink(status, errText) {
  if (status < 400 || status >= 500) return false;
  return /think|unknown|unexpected|additional|invalid|unrecognized|schema/i.test(
    errText,
  );
}

// ── Model loading ─────────────────────────────────────────────────────────────

async function loadModels() {
  modelsLoading.value = true;
  modelsError.value = "";

  try {
    const res = await fetch(`${settings.endpoint}/v1/models`, {
      signal: AbortSignal.timeout(8000),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    models.value = (data.data || []).sort((a, b) => a.id.localeCompare(b.id));

    // Validate or pick default model
    if (models.value.length > 0) {
      const exists = models.value.some((m) => m.id === activeModel.value);
      if (!exists) {
        // Prefer name containing "think" if available
        const preferred = models.value.find((m) =>
          m.id.toLowerCase().includes("think"),
        );
        activeModel.value = preferred ? preferred.id : models.value[0].id;
        settings.model = activeModel.value;
        persistSettings();
      }
    }
  } catch (err) {
    modelsError.value = `Cannot connect to ${settings.endpoint} — ${err.message}`;
    settingsOpen.value = true;
  } finally {
    modelsLoading.value = false;
  }
}

// ── Chat actions ──────────────────────────────────────────────────────────────

function onModelChange() {
  settings.model = activeModel.value;
  persistSettings();
}

function applyEndpoint() {
  settings.endpoint = endpointDraft.value.trim().replace(/\/+$/, "");
  endpointDraft.value = settings.endpoint;
  persistSettings();
  loadModels();
}

function clearChat() {
  if (isStreaming.value) stopStream();
  messages.value = [];
  streamError.value = "";
  nextTick(() => inputEl.value?.focus());
}

function stopStream() {
  abortController?.abort();
  abortController = null;
}

// ── Send ──────────────────────────────────────────────────────────────────────

async function send() {
  const text = input.value.trim();
  if (!text || isStreaming.value) return;

  const userMsg = { id: crypto.randomUUID(), role: "user", content: text };
  messages.value.push(userMsg);
  input.value = "";
  nextTick(autoResize);

  const assistantMsg = reactive({
    id: crypto.randomUUID(),
    role: "assistant",
    content: "",
    thinking: "",
    streamingThinking: false,
    thinkingExpanded: false,
    streaming: true,
  });
  messages.value.push(assistantMsg);
  scrollToBottom();

  isStreaming.value = true;
  streamError.value = "";
  abortController = new AbortController();

  const thinkState = createThinkState();
  let hasExplicitThinking = false;

  try {
    // Build conversation history (exclude current streaming placeholder)
    const history = messages.value
      .filter((m) => m.id !== assistantMsg.id)
      .map((m) => ({ role: m.role, content: m.content }));

    const baseBody = {
      model: activeModel.value,
      messages: history,
      stream: true,
    };

    const runRequest = (includeThink) =>
      fetch(`${settings.endpoint}/v1/chat/completions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          includeThink ? { ...baseBody, think: true } : baseBody,
        ),
        signal: abortController.signal,
      });

    let res = await runRequest(true);
    if (!res.ok) {
      const errText = await res.text().catch(() => `HTTP ${res.status}`);
      if (shouldRetryWithoutThink(res.status, errText)) {
        res = await runRequest(false);
      } else {
        throw new Error(errText || `HTTP ${res.status}`);
      }
    }

    if (!res.ok) {
      const errText = await res.text().catch(() => `HTTP ${res.status}`);
      throw new Error(errText || `HTTP ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buf += decoder.decode(value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop(); // keep incomplete line

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith("data:")) continue;
        const dataStr = trimmed.slice(5).trim();
        if (dataStr === "[DONE]") continue;

        let parsed;
        try {
          parsed = JSON.parse(dataStr);
        } catch {
          continue;
        }

        const delta = parsed.choices?.[0]?.delta;
        if (!delta) continue;

        const reasoningDelta = extractReasoningDelta(delta);
        if (reasoningDelta) {
          hasExplicitThinking = true;
          assistantMsg.thinking += reasoningDelta;
          assistantMsg.streamingThinking = true;
        }

        if (delta.content != null) {
          if (hasExplicitThinking) {
            // Thinking phase ended — content is the pure response.
            if (delta.content.length > 0) {
              assistantMsg.streamingThinking = false;
              assistantMsg.content += delta.content;
            }
          } else {
            // Parse <think>/<thinking> tags out of the content stream.
            processDelta(thinkState, delta.content);
            assistantMsg.thinking = thinkState.thinking;
            assistantMsg.content = thinkState.content;
            assistantMsg.streamingThinking = thinkState.inThink;
          }
        }

        if (!userScrolledUp) scrollToBottom();
      }
    }

    // Flush any remaining buffered tag characters
    if (!hasExplicitThinking) {
      flushThinkState(thinkState);
      assistantMsg.thinking = thinkState.thinking;
      assistantMsg.content = thinkState.content;
    }
  } catch (err) {
    if (err.name !== "AbortError") {
      streamError.value = err.message || "Stream failed";
      messages.value = messages.value.filter((m) => m.id !== assistantMsg.id);
    }
  } finally {
    assistantMsg.streaming = false;
    assistantMsg.streamingThinking = false;
    if (assistantMsg.thinking) assistantMsg.thinkingExpanded = false;
    isStreaming.value = false;
    abortController = null;
    scrollToBottom(true);
  }
}

// ── UI helpers ────────────────────────────────────────────────────────────────

function onScroll() {
  if (!scrollEl.value) return;
  const { scrollTop, scrollHeight, clientHeight } = scrollEl.value;
  userScrolledUp = scrollHeight - scrollTop - clientHeight > 120;
}

function scrollToBottom(smooth = false) {
  nextTick(() => {
    bottomEl.value?.scrollIntoView({ behavior: smooth ? "smooth" : "instant" });
  });
}

function autoResize() {
  const el = inputEl.value;
  if (!el) return;
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 200) + "px";
}

// ── Markdown renderer ─────────────────────────────────────────────────────────
// Lightweight renderer — no external dependency needed for a chat interface.

function escHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderMarkdown(text) {
  if (!text) return "";

  // Split into code blocks vs. normal text first so we don't process code internals
  const parts = text.split(/(```[\s\S]*?```)/g);

  const rendered = parts.map((part, i) => {
    if (i % 2 === 1) {
      // Code block
      const match = part.match(/```(\w*)\n?([\s\S]*?)```/);
      if (match) {
        const lang = match[1]
          ? `<span class="code-lang">${escHtml(match[1])}</span>`
          : "";
        return `<pre class="chat-code-block">${lang}<code>${escHtml(match[2].trim())}</code></pre>`;
      }
      return escHtml(part);
    }

    let html = escHtml(part);

    // Inline code
    html = html.replace(
      /`([^`\n]+)`/g,
      '<code class="chat-inline-code">$1</code>',
    );

    // Bold
    html = html.replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>");

    // Italic (not inside **)
    html = html.replace(/(?<!\*)\*(?!\*)([^*\n]+)\*(?!\*)/g, "<em>$1</em>");

    // Headers
    html = html.replace(/^#### (.+)$/gm, "<h4>$1</h4>");
    html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
    html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
    html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");

    // Horizontal rule
    html = html.replace(/^---+$/gm, "<hr>");

    // Unordered list
    html = html.replace(/((?:^[ \t]*[-*•] .+(?:\n|$))+)/gm, (block) => {
      const items = block
        .trim()
        .split("\n")
        .map((l) => `<li>${l.replace(/^[ \t]*[-*•] /, "")}</li>`)
        .join("");
      return `<ul>${items}</ul>`;
    });

    // Ordered list
    html = html.replace(/((?:^[ \t]*\d+\. .+(?:\n|$))+)/gm, (block) => {
      const items = block
        .trim()
        .split("\n")
        .map((l) => `<li>${l.replace(/^[ \t]*\d+\. /, "")}</li>`)
        .join("");
      return `<ol>${items}</ol>`;
    });

    // Paragraphs
    html = html.replace(/\n{2,}/g, "</p><p>");
    html = html.replace(/\n/g, "<br>");

    return `<p>${html}</p>`;
  });

  return rendered.join("");
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────

onMounted(() => {
  loadModels();
  nextTick(() => inputEl.value?.focus());
});
</script>

<style scoped>
/* ── Thinking dot pulse ───────────────────────────────────────────────────── */

.think-dot-pulsing {
  animation: think-pulse 1.2s ease-in-out infinite;
}

@keyframes think-pulse {

  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.35;
  }
}

/* ── Typing dots ──────────────────────────────────────────────────────────── */

.typing-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--muted);
  animation: bounce 1.2s ease-in-out infinite;
}

@keyframes bounce {

  0%,
  80%,
  100% {
    transform: translateY(0);
    opacity: 0.4;
  }

  40% {
    transform: translateY(-5px);
    opacity: 1;
  }
}

/* ── Response content (rendered markdown) ────────────────────────────────── */

.response-content :deep(p) {
  margin: 0 0 0.75em;
}

.response-content :deep(p:last-child) {
  margin-bottom: 0;
}

.response-content :deep(h1),
.response-content :deep(h2),
.response-content :deep(h3),
.response-content :deep(h4) {
  margin: 1.1em 0 0.4em;
  font-weight: 600;
  line-height: 1.3;
}

.response-content :deep(h1) {
  font-size: 1.25em;
}

.response-content :deep(h2) {
  font-size: 1.1em;
}

.response-content :deep(h3) {
  font-size: 1em;
}

.response-content :deep(h4) {
  font-size: 0.95em;
  color: var(--muted);
}

.response-content :deep(ul),
.response-content :deep(ol) {
  margin: 0.5em 0 0.75em;
  padding-left: 1.4em;
}

.response-content :deep(li) {
  margin-bottom: 0.25em;
}

.response-content :deep(strong) {
  font-weight: 600;
}

.response-content :deep(em) {
  font-style: italic;
}

.response-content :deep(hr) {
  border: none;
  border-top: 1px solid rgba(12, 17, 24, 0.12);
  margin: 1em 0;
}

.response-content :deep(.chat-inline-code) {
  font-family: "Menlo", "Monaco", "Consolas", monospace;
  font-size: 0.82em;
  background: rgba(12, 17, 24, 0.07);
  padding: 0.15em 0.4em;
  border-radius: 5px;
}

.response-content :deep(.chat-code-block) {
  margin: 0.75em 0;
  background: #1a2030;
  border-radius: 10px;
  overflow: hidden;
}

.response-content :deep(.code-lang) {
  display: block;
  padding: 0.45rem 0.875rem 0;
  font-family: "Menlo", "Monaco", "Consolas", monospace;
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.4);
  letter-spacing: 0.05em;
}

.response-content :deep(.chat-code-block code) {
  display: block;
  padding: 0.75rem 0.875rem;
  font-family: "Menlo", "Monaco", "Consolas", monospace;
  font-size: 0.8rem;
  line-height: 1.6;
  color: #e2e8f0;
  white-space: pre;
  overflow-x: auto;
}

/* ── Vue transitions ──────────────────────────────────────────────────────── */

.think-expand-enter-active,
.think-expand-leave-active {
  transition:
    max-height 0.3s ease,
    opacity 0.2s ease;
  overflow: hidden;
  max-height: 320px;
}

.think-expand-enter-from,
.think-expand-leave-to {
  max-height: 0;
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition:
    max-height 0.25s ease,
    opacity 0.2s ease,
    padding 0.25s ease,
    margin 0.25s ease;
  max-height: 200px;
  overflow: hidden;
}

.slide-up-enter-from,
.slide-up-leave-to {
  max-height: 0;
  opacity: 0;
  padding-top: 0;
  padding-bottom: 0;
  margin-bottom: 0;
}

/* ── Scrollbars ───────────────────────────────────────────────────────────── */

.messages-area::-webkit-scrollbar,
.think-content::-webkit-scrollbar {
  width: 5px;
}

.messages-area::-webkit-scrollbar-track,
.think-content::-webkit-scrollbar-track {
  background: transparent;
}

.messages-area::-webkit-scrollbar-thumb,
.think-content::-webkit-scrollbar-thumb {
  background: rgba(12, 17, 24, 0.15);
  border-radius: 10px;
}
</style>
