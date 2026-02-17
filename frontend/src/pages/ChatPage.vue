<template>
  <PageShell>
  <div class="chat-root">
    <!-- ── Messages ── -->
    <div ref="scrollEl" class="messages-area" @scroll="onScroll">
      <div class="messages-inner">
        <!-- Empty state -->
        <div v-if="messages.length === 0" class="empty-state">
          <div class="empty-logo">RPL</div>
          <h2 class="empty-heading">How can I help?</h2>
          <p class="empty-sub">
            {{ activeModel || "Configure Ollama above to get started" }}
          </p>
        </div>

        <!-- Message list -->
        <template v-for="msg in messages" :key="msg.id">
          <!-- User bubble -->
          <div v-if="msg.role === 'user'" class="msg-row user">
            <div class="user-bubble">
              <p class="user-text">{{ msg.content }}</p>
            </div>
          </div>

          <!-- Assistant message -->
          <div v-else class="msg-row assistant">
            <div class="assistant-avatar">AI</div>
            <div class="assistant-body">
              <!-- Thinking block -->
              <div
                v-if="msg.thinking || msg.streamingThinking"
                class="think-block"
              >
                <button
                  class="think-header"
                  @click="msg.thinkingExpanded = !msg.thinkingExpanded"
                >
                  <span
                    class="think-dot"
                    :class="{ pulsing: msg.streamingThinking }"
                  ></span>
                  <span class="think-label">{{
                    msg.streamingThinking ? "Thinking…" : "Thought for a moment"
                  }}</span>
                  <svg
                    class="think-chevron"
                    :class="{ rotated: msg.thinkingExpanded }"
                    xmlns="http://www.w3.org/2000/svg"
                    width="12"
                    height="12"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </button>
                <Transition name="think-expand">
                  <div v-if="msg.thinkingExpanded" class="think-content">
                    <pre class="think-text">{{ msg.thinking }}</pre>
                  </div>
                </Transition>
              </div>

              <!-- Response content -->
              <div
                v-if="msg.content"
                class="response-content"
                v-html="renderMarkdown(msg.content)"
              ></div>

              <!-- Streaming dots (before first content) -->
              <div
                v-if="msg.streaming && !msg.content && !msg.streamingThinking"
                class="typing-dots"
              >
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </template>

        <!-- Stream error -->
        <div v-if="streamError" class="stream-error">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          {{ streamError }}
        </div>

        <div ref="bottomEl"></div>
      </div>
    </div>

    <!-- ── Input ── -->
    <div class="input-area">

      <!-- Settings panel (slides up above input) -->
      <Transition name="slide-up">
        <div v-if="settingsOpen" class="settings-panel">
          <div class="settings-inner">
            <div class="setting-row">
              <label class="setting-label">Ollama Endpoint</label>
              <div class="setting-input-group">
                <input
                  v-model="endpointDraft"
                  type="url"
                  placeholder="http://localhost:11434"
                  class="setting-input"
                  @keydown.enter="applyEndpoint"
                />
                <button
                  class="connect-btn"
                  @click="applyEndpoint"
                  :disabled="modelsLoading"
                >
                  {{ modelsLoading ? "Connecting…" : "Connect" }}
                </button>
              </div>
            </div>
            <p v-if="modelsError" class="settings-msg error">{{ modelsError }}</p>
            <p v-else-if="models.length > 0" class="settings-msg success">
              Connected · {{ models.length }} model{{ models.length === 1 ? "" : "s" }} available
            </p>
          </div>
        </div>
      </Transition>

      <!-- Input box -->
      <div
        class="input-box"
        :class="{ focused: inputFocused, disabled: isStreaming }"
      >
        <textarea
          ref="inputEl"
          v-model="input"
          placeholder="Message…"
          rows="1"
          class="input-textarea"
          :disabled="isStreaming"
          @keydown.enter.exact.prevent="send"
          @input="autoResize"
          @focus="inputFocused = true"
          @blur="inputFocused = false"
        ></textarea>
        <button
          class="send-btn"
          :class="{ stop: isStreaming, active: input.trim() || isStreaming }"
          @click="isStreaming ? stopStream() : send()"
          :disabled="!input.trim() && !isStreaming"
          :title="isStreaming ? 'Stop' : 'Send'"
        >
          <svg v-if="isStreaming" xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
            <rect x="4" y="4" width="16" height="16" rx="2" />
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
          </svg>
        </button>
      </div>

      <!-- Toolbar: model selector + actions -->
      <div class="input-toolbar">
        <div class="model-selector-wrap">
          <select
            v-model="activeModel"
            class="model-select"
            :disabled="modelsLoading"
            @change="onModelChange"
            title="Select model"
          >
            <option v-if="models.length === 0" value="">
              {{ modelsLoading ? "Loading…" : "No models found" }}
            </option>
            <option v-for="m in models" :key="m.id" :value="m.id">{{ m.id }}</option>
          </select>
          <svg class="select-chevron" xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </div>

        <div class="toolbar-actions">
          <button class="toolbar-btn" @click="clearChat" title="New conversation">
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            <span>New chat</span>
          </button>
          <button
            class="toolbar-btn"
            :class="{ active: settingsOpen }"
            @click="settingsOpen = !settingsOpen"
            title="Settings"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
            <span>Settings</span>
          </button>
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
  return { pendingTag: "", inThink: false, closeTag: "", thinking: "", content: "" };
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
/* ── Layout ───────────────────────────────────────────────────────────────── */

.chat-root {
  position: fixed;
  inset: 0;
  top: 88px; /* clear the fixed AppHeader */
  display: flex;
  flex-direction: column;
  background: transparent;
}

.model-selector-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.model-select {
  appearance: none;
  background: transparent;
  border: 1px solid rgba(12, 17, 24, 0.15);
  border-radius: 10px;
  padding: 0.35rem 2rem 0.35rem 0.75rem;
  font-size: 0.82rem;
  font-weight: 500;
  font-family: inherit;
  color: var(--ink);
  cursor: pointer;
  outline: none;
  transition:
    border-color 0.15s,
    box-shadow 0.15s;
}

.model-select:hover {
  border-color: rgba(12, 17, 24, 0.3);
}

.model-select:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(255, 106, 0, 0.12);
}

.model-select:disabled {
  opacity: 0.5;
  cursor: default;
}

.select-chevron {
  position: absolute;
  right: 0.55rem;
  color: var(--muted);
  pointer-events: none;
}

/* ── Settings panel ───────────────────────────────────────────────────────── */

.settings-panel {
  border-top: 1px solid rgba(12, 17, 24, 0.1);
  padding: 0.75rem 0;
  margin-bottom: 0.5rem;
}

.settings-inner {
  max-width: 720px;
  margin: 0 auto;
}

.setting-row {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.setting-label {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}

.setting-input-group {
  display: flex;
  gap: 0.5rem;
}

.setting-input {
  flex: 1;
  border: 1px solid rgba(12, 17, 24, 0.15);
  border-radius: 10px;
  padding: 0.45rem 0.75rem;
  font-size: 0.85rem;
  font-family: inherit;
  color: var(--ink);
  background: rgba(255, 255, 255, 0.8);
  outline: none;
  transition:
    border-color 0.15s,
    box-shadow 0.15s;
}

.setting-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(255, 106, 0, 0.12);
}

.connect-btn {
  padding: 0.45rem 1rem;
  border-radius: 10px;
  border: none;
  background: var(--ink);
  color: #fff;
  font-size: 0.82rem;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.15s;
  white-space: nowrap;
}

.connect-btn:hover:not(:disabled) {
  background: #1d2a3a;
}

.connect-btn:disabled {
  opacity: 0.5;
  cursor: default;
}

.settings-msg {
  margin: 0.5rem 0 0;
  font-size: 0.78rem;
}

.settings-msg.error {
  color: #dc2626;
}

.settings-msg.success {
  color: #16a34a;
}

/* ── Messages area ────────────────────────────────────────────────────────── */

.messages-area {
  flex: 1;
  overflow-y: auto;
  scroll-behavior: auto;
}

.messages-inner {
  max-width: 720px;
  margin: 0 auto;
  padding: 2rem 1.5rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 5rem 1rem;
  text-align: center;
}

.empty-logo {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: #111722;
  color: #fff;
  display: grid;
  place-items: center;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.2em;
}

.empty-heading {
  margin: 0;
  font-size: 1.6rem;
  font-weight: 600;
  color: var(--ink);
}

.empty-sub {
  margin: 0;
  color: var(--muted);
  font-size: 0.875rem;
}

/* Message rows */
.msg-row {
  display: flex;
  gap: 0.75rem;
}

.msg-row.user {
  justify-content: flex-end;
}

.msg-row.assistant {
  align-items: flex-start;
}

/* User bubble */
.user-bubble {
  max-width: 78%;
  background: rgba(255, 106, 0, 0.09);
  border: 1px solid rgba(255, 106, 0, 0.2);
  border-radius: 20px;
  border-bottom-right-radius: 6px;
  padding: 0.75rem 1rem;
}

.user-text {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

/* Assistant */
.assistant-avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: #111722;
  color: #fff;
  display: grid;
  place-items: center;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  margin-top: 2px;
}

.assistant-body {
  flex: 1;
  min-width: 0;
}

/* ── Thinking block ────────────────────────────────────────────────────────── */

.think-block {
  margin-bottom: 0.75rem;
  border: 1px solid rgba(12, 17, 24, 0.1);
  border-radius: 12px;
  overflow: hidden;
}

.think-header {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.55rem 0.875rem;
  background: rgba(12, 17, 24, 0.04);
  border: none;
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 500;
  font-family: inherit;
  color: var(--muted);
  text-align: left;
  transition: background 0.15s;
}

.think-header:hover {
  background: rgba(12, 17, 24, 0.07);
}

.think-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--teal);
  flex-shrink: 0;
  transition: background 0.3s;
}

.think-dot.pulsing {
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

.think-label {
  flex: 1;
}

.think-chevron {
  transition: transform 0.2s;
  color: var(--muted);
}

.think-chevron.rotated {
  transform: rotate(180deg);
}

.think-content {
  border-top: 1px solid rgba(12, 17, 24, 0.07);
  background: rgba(12, 17, 24, 0.02);
  overflow-y: auto;
}

.think-text {
  margin: 0;
  padding: 0.75rem 0.875rem;
  font-size: 0.75rem;
  font-family: "Space Mono", "Menlo", "Monaco", monospace;
  color: var(--muted);
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.65;
}

/* ── Response content ─────────────────────────────────────────────────────── */

.response-content {
  font-size: 0.9rem;
  line-height: 1.7;
  color: var(--ink);
  word-break: break-word;
}

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

/* ── Typing dots ──────────────────────────────────────────────────────────── */

.typing-dots {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 0.3rem 0;
}

.typing-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--muted);
  animation: bounce 1.2s ease-in-out infinite;
}

.typing-dots span:nth-child(2) {
  animation-delay: 0.2s;
}
.typing-dots span:nth-child(3) {
  animation-delay: 0.4s;
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

/* ── Stream error ─────────────────────────────────────────────────────────── */

.stream-error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.82rem;
  color: #dc2626;
  background: rgba(220, 38, 38, 0.07);
  border: 1px solid rgba(220, 38, 38, 0.2);
  border-radius: 10px;
  padding: 0.6rem 0.875rem;
}

/* ── Input toolbar ────────────────────────────────────────────────────────── */

.input-toolbar {
  max-width: 720px;
  margin: 0.35rem auto 0;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  margin-left: auto;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.55rem;
  border-radius: 8px;
  border: none;
  background: transparent;
  font-size: 0.75rem;
  font-family: inherit;
  color: var(--muted);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.toolbar-btn:hover,
.toolbar-btn.active {
  background: rgba(12, 17, 24, 0.07);
  color: var(--ink);
}

/* ── Input area ───────────────────────────────────────────────────────────── */

.input-area {
  flex-shrink: 0;
  padding: 0.75rem 1.5rem 1rem;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  border-top: 1px solid rgba(12, 17, 24, 0.08);
}

.input-box {
  max-width: 720px;
  margin: 0 auto;
  display: flex;
  align-items: flex-end;
  gap: 0.5rem;
  border: 1.5px solid rgba(12, 17, 24, 0.15);
  border-radius: 16px;
  background: #fff;
  padding: 0.6rem 0.6rem 0.6rem 1rem;
  box-shadow: 0 2px 8px rgba(12, 17, 24, 0.06);
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
}

.input-box.focused {
  border-color: rgba(255, 106, 0, 0.5);
  box-shadow:
    0 0 0 3px rgba(255, 106, 0, 0.1),
    0 2px 8px rgba(12, 17, 24, 0.06);
}

.input-box.disabled {
  opacity: 0.7;
}

.input-textarea {
  flex: 1;
  resize: none;
  background: transparent;
  border: none;
  outline: none;
  font-size: 0.9rem;
  font-family: inherit;
  color: var(--ink);
  line-height: 1.6;
  max-height: 200px;
  overflow-y: auto;
}

.input-textarea::placeholder {
  color: var(--muted);
}

.send-btn {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 12px;
  border: none;
  display: grid;
  place-items: center;
  cursor: pointer;
  background: rgba(12, 17, 24, 0.12);
  color: var(--muted);
  transition:
    background 0.15s,
    color 0.15s,
    transform 0.1s;
}

.send-btn.active {
  background: var(--ink);
  color: #fff;
}

.send-btn.stop {
  background: #dc2626;
  color: #fff;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.05);
}

.send-btn:disabled {
  cursor: default;
}

.input-hint {
  max-width: 720px;
  margin: 0.4rem auto 0;
  text-align: center;
  font-size: 0.68rem;
  color: var(--muted);
  letter-spacing: 0.03em;
}

/* ── Transitions ──────────────────────────────────────────────────────────── */

.think-expand-enter-active,
.think-expand-leave-active {
  transition: max-height 0.3s ease, opacity 0.2s ease;
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
    opacity 0.2s ease;
  max-height: 200px;
  overflow: hidden;
}

.slide-up-enter-from,
.slide-up-leave-to {
  max-height: 0;
  opacity: 0;
}

/* ── Scrollbar (webkit) ───────────────────────────────────────────────────── */

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
