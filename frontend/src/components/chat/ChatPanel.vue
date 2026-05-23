<template>
  <div class="flex flex-col h-full bg-transparent min-h-0">
    <!-- ── Messages ── -->
    <div
      ref="scrollEl"
      class="messages-area flex-1 overflow-y-auto min-h-0"
      @scroll="onScroll"
      @click="handleMessageClick"
    >
      <div class="max-w-250 mx-auto px-6 pt-6 pb-6 flex flex-col gap-6">
        <!-- Empty state -->
        <div
          v-if="messages.length === 0"
          class="flex flex-col items-center justify-center gap-3 py-16 px-4 text-center"
        >
          <div
            class="w-14 h-14 rounded-2xl bg-[#111722] text-white grid place-items-center text-[0.7rem] font-bold tracking-[0.2em]"
          >
            RPL
          </div>
          <h2 class="m-0 text-[1.4rem] font-semibold text-(--ink)">
            How can I help?
          </h2>
          <p class="m-0 text-(--muted) text-sm">
            {{ activeModel || "Configure Ollama above to get started" }}
          </p>
        </div>

        <!-- Message list -->
        <template v-for="(msg, idx) in messages" :key="msg.id">
          <!-- User bubble -->
          <div v-if="msg.role === 'user'" class="flex gap-3 justify-end group">
            <div class="flex flex-col items-end gap-1 max-w-[78%]">
              <div
                v-if="editingId !== msg.id"
                class="bg-[rgba(255,106,0,0.09)] border border-[rgba(255,106,0,0.2)] rounded-[20px] rounded-br-md px-4 py-3"
              >
                <p
                  class="m-0 text-[0.9rem] leading-relaxed whitespace-pre-wrap wrap-break-word"
                >
                  {{ msg.content }}
                </p>
              </div>
              <div
                v-else
                class="w-full border border-[rgba(255,106,0,0.4)] rounded-[16px] bg-white p-2 flex flex-col gap-2"
              >
                <textarea
                  v-model="editDraft"
                  rows="3"
                  class="w-full resize-none border-none outline-none text-[0.9rem] text-(--ink) leading-relaxed"
                ></textarea>
                <div class="flex justify-end gap-2">
                  <button
                    class="px-3 py-1 text-[0.78rem] rounded-md bg-transparent border border-[rgba(12,17,24,0.15)] cursor-pointer hover:bg-[rgba(12,17,24,0.04)]"
                    @click="cancelEdit"
                  >
                    Cancel
                  </button>
                  <button
                    class="px-3 py-1 text-[0.78rem] rounded-md bg-(--ink) text-white border-none cursor-pointer hover:bg-[#1d2a3a]"
                    @click="commitEdit(idx)"
                  >
                    Save & resend
                  </button>
                </div>
              </div>
              <button
                v-if="editingId !== msg.id && !isStreaming"
                class="opacity-0 group-hover:opacity-100 text-[0.7rem] text-(--muted) hover:text-(--ink) cursor-pointer bg-transparent border-none transition-opacity"
                title="Edit and resend"
                @click="beginEdit(msg)"
              >
                Edit
              </button>
            </div>
          </div>

          <!-- Tool result -->
          <div
            v-else-if="msg.role === 'tool'"
            class="flex gap-3 items-start"
          >
            <div
              class="shrink-0 w-8 h-8 rounded-[10px] bg-(--teal) text-white grid place-items-center text-[0.6rem] font-bold mt-0.5"
              title="Tool result"
            >
              ⚙
            </div>
            <div
              class="flex-1 min-w-0 border border-[rgba(12,17,24,0.1)] rounded-xl bg-[rgba(12,17,24,0.02)] px-3 py-2"
            >
              <div
                class="text-[0.7rem] font-semibold tracking-[0.05em] uppercase text-(--muted) mb-1"
              >
                {{ msg.name }}
              </div>
              <pre
                class="m-0 text-[0.78rem] text-(--ink) font-mono whitespace-pre-wrap wrap-break-word leading-[1.55] max-h-72 overflow-y-auto"
                >{{ msg.content }}</pre
              >
            </div>
          </div>

          <!-- Assistant message -->
          <div v-else class="flex gap-3 items-start group">
            <div
              class="shrink-0 w-8 h-8 rounded-[10px] bg-[#111722] text-white grid place-items-center text-[0.65rem] font-bold tracking-[0.05em] mt-0.5"
            >
              AI
            </div>
            <div class="flex-1 min-w-0">
              <!-- Tool call chips -->
              <div
                v-if="msg.toolCalls && msg.toolCalls.length > 0"
                class="flex flex-wrap gap-1.5 mb-2"
              >
                <span
                  v-for="tc in msg.toolCalls"
                  :key="tc.id || tc.name"
                  class="inline-flex items-center gap-1.5 px-2 py-[0.25rem] rounded-full text-[0.72rem] font-medium border"
                  :class="
                    tc.status === 'running'
                      ? 'border-[rgba(255,106,0,0.3)] bg-[rgba(255,106,0,0.08)] text-(--accent)'
                      : 'border-[rgba(12,17,24,0.12)] bg-[rgba(12,17,24,0.04)] text-(--ink)'
                  "
                >
                  <span
                    class="w-1.5 h-1.5 rounded-full"
                    :class="
                      tc.status === 'running'
                        ? 'bg-(--accent) think-dot-pulsing'
                        : 'bg-(--teal)'
                    "
                  ></span>
                  {{ tc.name }}
                </span>
              </div>
              <!-- Thinking block -->
              <div
                v-if="msg.thinking || msg.streamingThinking"
                class="mb-3 border border-[rgba(12,17,24,0.1)] rounded-xl overflow-hidden"
              >
                <button
                  class="w-full flex items-center gap-2 px-3.5 py-[0.55rem] bg-[rgba(12,17,24,0.04)] border-none cursor-pointer text-[0.78rem] font-medium font-[inherit] text-(--muted) text-left transition-colors duration-150 hover:bg-[rgba(12,17,24,0.07)]"
                  @click="msg.thinkingExpanded = !msg.thinkingExpanded"
                >
                  <span
                    class="w-1.75 h-1.75 rounded-full bg-(--teal) shrink-0 transition-colors duration-300"
                    :class="{ 'think-dot-pulsing': msg.streamingThinking }"
                  ></span>
                  <span class="flex-1">{{
                    msg.streamingThinking
                      ? "Thinking…"
                      : "Thought for a moment"
                  }}</span>
                  <svg
                    class="transition-transform duration-200 text-(--muted)"
                    :class="{ 'rotate-180': msg.thinkingExpanded }"
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
                  <div
                    v-if="msg.thinkingExpanded"
                    class="think-content border-t border-[rgba(12,17,24,0.07)] bg-[rgba(12,17,24,0.02)] overflow-y-auto"
                  >
                    <pre
                      class="m-0 px-3.5 py-3 text-[0.75rem] font-mono text-(--muted) whitespace-pre-wrap wrap-break-word leading-[1.65]"
                      >{{ msg.thinking }}</pre
                    >
                  </div>
                </Transition>
              </div>

              <!-- Response content -->
              <div
                v-if="msg.content"
                class="response-content text-[0.9rem] leading-[1.7] text-(--ink) wrap-break-word"
                v-html="renderMarkdown(msg.content)"
              ></div>

              <!-- Streaming dots -->
              <div
                v-if="msg.streaming && !msg.content && !msg.streamingThinking"
                class="flex gap-1 items-center py-[0.3rem]"
              >
                <span class="typing-dot"></span>
                <span class="typing-dot [animation-delay:0.2s]"></span>
                <span class="typing-dot [animation-delay:0.4s]"></span>
              </div>

              <!-- Regenerate (only on last assistant message) -->
              <button
                v-if="
                  !msg.streaming && !isStreaming && idx === lastAssistantIndex
                "
                class="mt-2 inline-flex items-center gap-1 text-[0.72rem] text-(--muted) hover:text-(--ink) cursor-pointer bg-transparent border-none opacity-0 group-hover:opacity-100 transition-opacity"
                @click="regenerate"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <polyline points="23 4 23 10 17 10" />
                  <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
                </svg>
                Regenerate
              </button>
            </div>
          </div>
        </template>

        <!-- Stream error -->
        <div
          v-if="streamError"
          class="flex items-center gap-2 text-[0.82rem] text-red-600 bg-[rgba(220,38,38,0.07)] border border-[rgba(220,38,38,0.2)] rounded-[10px] px-3.5 py-[0.6rem]"
        >
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

    <!-- ── Input Card ── -->
    <div 
      class="shrink-0 bg-white border-t transition-colors duration-200 px-6 py-4"
      :class="
        inputFocused
          ? 'border-t-(--accent)'
          : 'border-t-[rgba(12,17,24,0.08)]'
      "
    >
        <!-- Settings -->
        <Transition name="slide-up">
          <div
            v-if="settingsOpen"
            class="pb-3 mb-2 border-b border-[rgba(12,17,24,0.08)]"
          >
            <div class="flex flex-col gap-[0.4rem]">
              <label
                class="text-[0.7rem] font-semibold tracking-[0.08em] uppercase text-(--muted)"
                >Ollama Endpoint</label
              >
              <div class="flex gap-2">
                <input
                  v-model="endpointDraft"
                  type="url"
                  placeholder="http://localhost:11434"
                  class="flex-1 border border-[rgba(12,17,24,0.15)] rounded-[10px] px-3 py-[0.45rem] text-[0.85rem] text-(--ink) bg-[rgba(255,255,255,0.8)] outline-none transition-[border-color,box-shadow] duration-150 focus:border-(--accent) focus:shadow-[0_0_0_3px_rgba(255,106,0,0.12)]"
                  @keydown.enter="applyEndpoint"
                />
                <button
                  class="px-4 py-[0.45rem] rounded-[10px] border-none bg-(--ink) text-white text-[0.82rem] font-semibold cursor-pointer transition-colors duration-150 whitespace-nowrap hover:bg-[#1d2a3a] disabled:opacity-50 disabled:cursor-default"
                  @click="applyEndpoint"
                  :disabled="modelsLoading"
                >
                  {{ modelsLoading ? "Connecting…" : "Connect" }}
                </button>
              </div>
            </div>
            <p
              v-if="modelsError"
              class="mt-2 m-0 text-[0.78rem] text-red-600"
            >
              {{ modelsError }}
            </p>
            <p
              v-else-if="models.length > 0"
              class="mt-2 m-0 text-[0.78rem] text-green-700"
            >
              Connected · {{ models.length }} model{{
                models.length === 1 ? "" : "s"
              }}
              available
            </p>
          </div>
        </Transition>

        <!-- Attachment chips -->
        <div
          v-if="attachments.length > 0"
          class="flex flex-wrap gap-1.5 pb-2 mb-2 border-b border-[rgba(12,17,24,0.08)]"
        >
          <span
            v-for="att in attachments"
            :key="`${att.kind}:${att.id}`"
            class="inline-flex items-center gap-1.5 px-2 py-[0.25rem] rounded-full text-[0.72rem] font-medium bg-[rgba(0,150,136,0.08)] border border-[rgba(0,150,136,0.2)] text-(--teal)"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="11"
              height="11"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path
                d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"
              />
            </svg>
            {{ att.name }}
            <button
              type="button"
              class="ml-0.5 cursor-pointer bg-transparent border-none text-(--teal) opacity-70 hover:opacity-100 leading-none p-0"
              @click="$emit('detach', att)"
              title="Remove attachment"
            >
              ×
            </button>
          </span>
        </div>

        <!-- Input -->
        <div class="relative">
          <textarea
            ref="inputEl"
            v-model="input"
            placeholder="Message… (type @ for workflows)"
            rows="1"
            class="w-full resize-none bg-transparent border-none outline-none text-[0.9rem] text-(--ink) leading-relaxed max-h-50 overflow-y-auto placeholder:text-(--muted) disabled:opacity-60"
            :disabled="isStreaming"
            @keydown="onInputKeydown"
            @input="onInputEvent"
            @click="updateMention"
            @keyup="updateMention"
            @focus="inputFocused = true"
            @blur="inputFocused = false"
          ></textarea>
          <MentionMenu
            :open="mentionOpen"
            :items="mentionItems"
            :active-index="mentionIndex"
            @select="selectMention"
            @hover="(i) => (mentionIndex = i)"
          />
        </div>

        <!-- Toolbar -->
        <div
          class="flex items-center justify-between pt-2 mt-2 border-t border-[rgba(12,17,24,0.08)]"
        >
          <div class="flex items-center gap-2">
            <button
              class="flex items-center justify-center w-8 h-8 rounded-lg border-none bg-transparent text-(--muted) cursor-pointer transition-colors duration-150 hover:bg-[rgba(12,17,24,0.07)] hover:text-(--ink)"
              @click="clearChat"
              title="New conversation"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path d="M8 12h5" />
                <path d="M10.5 9.5v5" />
                <path
                  d="M17 14a4 4 0 0 0 1-2.65C18 7.29 14.87 4 11 4s-7 3.29-7 7.35S7.13 18.7 11 18.7c.8 0 1.58-.14 2.31-.4L18 20l-1.24-4.23A7.6 7.6 0 0 0 17 14z"
                />
              </svg>
            </button>
          </div>

          <div class="flex items-center gap-1">
            <button
              class="flex items-center justify-center w-8 h-8 rounded-lg border-none bg-transparent text-(--muted) cursor-pointer transition-colors duration-150 hover:bg-[rgba(12,17,24,0.07)] hover:text-(--ink)"
              :class="{
                'bg-[rgba(12,17,24,0.07)] text-(--ink)!': settingsOpen,
              }"
              @click="settingsOpen = !settingsOpen"
              title="Settings"
            >
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
                <circle cx="12" cy="12" r="3" />
                <path
                  d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"
                />
              </svg>
            </button>
            <div class="relative flex items-center">
              <select
                v-model="activeModel"
                class="appearance-none bg-[rgba(12,17,24,0.05)] border-none rounded-lg py-[0.35rem] pl-[0.65rem] pr-7 text-[0.78rem] font-medium text-(--ink) cursor-pointer outline-none transition-colors duration-150 hover:bg-[rgba(12,17,24,0.08)] focus:bg-[rgba(12,17,24,0.1)] disabled:opacity-50 disabled:cursor-default"
                :disabled="modelsLoading"
                @change="onModelChange"
                title="Select model"
              >
                <option v-if="models.length === 0" value="">
                  {{ modelsLoading ? "Loading…" : "No models" }}
                </option>
                <option v-for="m in models" :key="m.id" :value="m.id">
                  {{ m.id }}
                </option>
              </select>
              <svg
                class="absolute right-2 text-(--muted) pointer-events-none"
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
            </div>
            <button
              class="flex items-center justify-center w-8 h-8 rounded-[10px] border-none cursor-pointer bg-[rgba(12,17,24,0.1)] text-(--muted) transition-[background,color,transform] duration-150 hover:scale-105 disabled:cursor-default disabled:opacity-50"
              :class="{
                'bg-[#C96040] text-white!': !isStreaming && input.trim(),
                'bg-red-600 text-white!': isStreaming,
              }"
              @click="isStreaming ? stopStream() : send()"
              :disabled="!input.trim() && !isStreaming"
              :title="isStreaming ? 'Stop' : 'Send'"
            >
              <svg
                v-if="isStreaming"
                xmlns="http://www.w3.org/2000/svg"
                width="13"
                height="13"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <rect x="4" y="4" width="16" height="16" rx="2" />
              </svg>
              <svg
                v-else
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2.5"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <line x1="12" y1="19" x2="12" y2="5" />
                <polyline points="5 12 12 5 19 12" />
              </svg>
            </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, computed } from "vue";
import { useRouter } from "vue-router";
import { settings, persistSettings } from "../../stores/chat.js";
import {
  filterWorkflows,
  getToolSchemas,
  dispatchTool,
} from "../../stores/workflows.js";
import MentionMenu from "../MentionMenu.vue";
import hljs from "highlight.js";
import "highlight.js/styles/github-dark.css";

const props = defineProps({
  attachments: { type: Array, default: () => [] },
});
const emit = defineEmits(["detach", "tool-result"]);

const router = useRouter();
const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const MAX_TOOL_ITERATIONS = 4;

// ── State ─────────────────────────────────────────────────────────────────────

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

const mentionOpen = ref(false);
const mentionQuery = ref("");
const mentionIndex = ref(0);
const mentionStart = ref(-1);
const mentionItems = computed(() => filterWorkflows(mentionQuery.value));

const editingId = ref(null);
const editDraft = ref("");

const scrollEl = ref(null);
const bottomEl = ref(null);
const inputEl = ref(null);

let abortController = null;
let userScrolledUp = false;

// Cache library doc context so attachments don't re-fetch every turn.
const contextCache = new Map();

const lastAssistantIndex = computed(() => {
  for (let i = messages.value.length - 1; i >= 0; i--) {
    if (messages.value[i].role === "assistant") return i;
  }
  return -1;
});

// ── Think-tag stream parser ───────────────────────────────────────────────────

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
  if (state.inThink) state.thinking += state.pendingTag;
  else state.content += state.pendingTag;
  state.pendingTag = "";
}

function extractReasoningDelta(delta) {
  const parts = [];
  for (const key of ["thinking", "reasoning_content", "reasoning"]) {
    const value = delta?.[key];
    if (typeof value === "string" && value.length > 0) parts.push(value);
  }
  return parts.join("");
}

function shouldRetryWithoutThink(status, errText) {
  if (status < 400 || status >= 500) return false;
  return /think|unknown|unexpected|additional|invalid|unrecognized|schema/i.test(
    errText,
  );
}

// ── Models ────────────────────────────────────────────────────────────────────

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
    if (models.value.length > 0) {
      const exists = models.value.some((m) => m.id === activeModel.value);
      if (!exists) {
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
  editingId.value = null;
  nextTick(() => inputEl.value?.focus());
}

function stopStream() {
  abortController?.abort();
  abortController = null;
}

// ── Attachments → system message ──────────────────────────────────────────────

async function buildAttachmentsSystemMessage() {
  if (!props.attachments?.length) return null;
  const parts = ["The user has attached the following documents as context:"];
  for (const att of props.attachments) {
    if (att.kind === "library") {
      let ctx = contextCache.get(att.id);
      if (!ctx) {
        try {
          const res = await fetch(`${apiBase}/documents/${att.id}/context`);
          if (res.ok) {
            const data = await res.json();
            ctx = data.context_text || "";
            contextCache.set(att.id, ctx);
          }
        } catch {
          ctx = "";
        }
      }
      parts.push(`\n--- ${att.name} ---\n${ctx || "(no extractable text)"}`);
    } else {
      parts.push(`\n--- ${att.name} (local collection file, no text) ---`);
    }
  }
  return { role: "system", content: parts.join("\n") };
}

// ── API message conversion ────────────────────────────────────────────────────

function toApiMessage(m) {
  if (m.role === "tool") {
    return { role: "tool", tool_call_id: m.tool_call_id, content: m.content };
  }
  if (m.role === "assistant" && m.toolCalls?.length) {
    return {
      role: "assistant",
      content: m.content || "",
      tool_calls: m.toolCalls.map((tc) => ({
        id: tc.id,
        type: "function",
        function: { name: tc.name, arguments: tc.args || "{}" },
      })),
    };
  }
  return { role: m.role, content: m.content };
}

function accumulateToolCalls(acc, deltaCalls) {
  for (const dc of deltaCalls) {
    const i = dc.index ?? 0;
    if (!acc[i]) {
      acc[i] = { id: "", name: "", args: "", status: "pending", result: "" };
    }
    if (dc.id) acc[i].id = dc.id;
    if (dc.function?.name) acc[i].name += dc.function.name;
    if (dc.function?.arguments) acc[i].args += dc.function.arguments;
  }
}

// ── One streaming round ───────────────────────────────────────────────────────

async function runChatTurn() {
  const assistantMsg = reactive({
    id: crypto.randomUUID(),
    role: "assistant",
    content: "",
    thinking: "",
    streamingThinking: false,
    thinkingExpanded: false,
    streaming: true,
    toolCalls: [],
  });
  messages.value.push(assistantMsg);
  scrollToBottom();

  abortController = new AbortController();
  const thinkState = createThinkState();
  let hasExplicitThinking = false;

  const sysMsg = await buildAttachmentsSystemMessage();
  const history = messages.value
    .filter((m) => m.id !== assistantMsg.id)
    .map(toApiMessage);
  if (sysMsg) history.unshift(sysMsg);

  const baseBody = {
    model: activeModel.value,
    messages: history,
    stream: true,
    tools: getToolSchemas(),
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

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop();

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

        if (delta.tool_calls) {
          accumulateToolCalls(assistantMsg.toolCalls, delta.tool_calls);
        }

        if (delta.content != null) {
          if (hasExplicitThinking) {
            if (delta.content.length > 0) {
              assistantMsg.streamingThinking = false;
              assistantMsg.content += delta.content;
            }
          } else {
            processDelta(thinkState, delta.content);
            assistantMsg.thinking = thinkState.thinking;
            assistantMsg.content = thinkState.content;
            assistantMsg.streamingThinking = thinkState.inThink;
          }
        }

        if (!userScrolledUp) scrollToBottom();
      }
    }

    if (!hasExplicitThinking) {
      flushThinkState(thinkState);
      assistantMsg.thinking = thinkState.thinking;
      assistantMsg.content = thinkState.content;
    }
  } finally {
    assistantMsg.streaming = false;
    assistantMsg.streamingThinking = false;
    if (assistantMsg.thinking) assistantMsg.thinkingExpanded = false;
    abortController = null;
  }

  return assistantMsg;
}

// ── Tool loop driver ──────────────────────────────────────────────────────────

async function runToolLoop() {
  isStreaming.value = true;
  streamError.value = "";
  try {
    for (let iter = 0; iter < MAX_TOOL_ITERATIONS; iter++) {
      const assistantMsg = await runChatTurn();
      if (!assistantMsg.toolCalls?.length) break;

      for (const tc of assistantMsg.toolCalls) {
        let parsedArgs = {};
        try {
          parsedArgs = tc.args ? JSON.parse(tc.args) : {};
        } catch {
          parsedArgs = {};
        }
        tc.status = "running";
        const result = await dispatchTool(tc.name, parsedArgs, {
          router,
          attachments: props.attachments,
        });
        tc.status = "done";
        tc.result = result.summary;

        emit("tool-result", { name: tc.name, args: parsedArgs, ...result });

        messages.value.push({
          id: crypto.randomUUID(),
          role: "tool",
          tool_call_id: tc.id,
          name: tc.name,
          content: result.summary,
        });
      }
      scrollToBottom();
    }
  } catch (err) {
    if (err.name !== "AbortError") {
      streamError.value = err.message || "Stream failed";
    }
  } finally {
    isStreaming.value = false;
    scrollToBottom(true);
  }
}

async function send() {
  const text = input.value.trim();
  if (!text || isStreaming.value) return;
  messages.value.push({
    id: crypto.randomUUID(),
    role: "user",
    content: text,
  });
  input.value = "";
  mentionOpen.value = false;
  nextTick(autoResize);
  await runToolLoop();
}

// ── Regenerate / edit ─────────────────────────────────────────────────────────

async function regenerate() {
  if (isStreaming.value) return;
  // Strip everything after the last user message.
  let lastUserIdx = -1;
  for (let i = messages.value.length - 1; i >= 0; i--) {
    if (messages.value[i].role === "user") {
      lastUserIdx = i;
      break;
    }
  }
  if (lastUserIdx === -1) return;
  messages.value = messages.value.slice(0, lastUserIdx + 1);
  await runToolLoop();
}

function beginEdit(msg) {
  editingId.value = msg.id;
  editDraft.value = msg.content;
}

function cancelEdit() {
  editingId.value = null;
  editDraft.value = "";
}

async function commitEdit(idx) {
  const text = editDraft.value.trim();
  if (!text) return;
  messages.value[idx].content = text;
  // Truncate everything after this user message.
  messages.value = messages.value.slice(0, idx + 1);
  editingId.value = null;
  editDraft.value = "";
  await runToolLoop();
}

// ── Mention autocomplete ──────────────────────────────────────────────────────

function detectMention() {
  const el = inputEl.value;
  if (!el) return null;
  const caret = el.selectionStart;
  const text = input.value.slice(0, caret);
  const at = text.lastIndexOf("@");
  if (at === -1) return null;
  if (at > 0 && !/\s/.test(text[at - 1])) return null;
  const after = text.slice(at + 1);
  if (/\s/.test(after)) return null;
  return { start: at, query: after };
}

function updateMention() {
  const m = detectMention();
  if (!m) {
    mentionOpen.value = false;
    return;
  }
  mentionOpen.value = true;
  mentionQuery.value = m.query;
  mentionStart.value = m.start;
  if (mentionIndex.value >= mentionItems.value.length) {
    mentionIndex.value = 0;
  }
}

function selectMention(wf) {
  if (mentionStart.value < 0) return;
  const before = input.value.slice(0, mentionStart.value);
  const caret = inputEl.value?.selectionStart ?? input.value.length;
  const after = input.value.slice(caret);
  const insert = `@${wf.label} `;
  input.value = before + insert + after;
  mentionOpen.value = false;
  mentionQuery.value = "";
  mentionStart.value = -1;
  nextTick(() => {
    autoResize();
    const pos = before.length + insert.length;
    inputEl.value?.setSelectionRange(pos, pos);
    inputEl.value?.focus();
  });
}

function onInputEvent() {
  autoResize();
  updateMention();
}

function onInputKeydown(e) {
  if (mentionOpen.value && mentionItems.value.length > 0) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      mentionIndex.value =
        (mentionIndex.value + 1) % mentionItems.value.length;
      return;
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      mentionIndex.value =
        (mentionIndex.value - 1 + mentionItems.value.length) %
        mentionItems.value.length;
      return;
    }
    if (e.key === "Enter" || e.key === "Tab") {
      e.preventDefault();
      selectMention(mentionItems.value[mentionIndex.value]);
      return;
    }
    if (e.key === "Escape") {
      e.preventDefault();
      mentionOpen.value = false;
      return;
    }
  }
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
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

function handleMessageClick(e) {
  const btn = e.target.closest(".copy-code-btn");
  if (btn) {
    const codeNode = btn.parentElement.querySelector("code");
    if (codeNode) {
      navigator.clipboard
        .writeText(codeNode.textContent)
        .then(() => {
          const originalHtml = btn.innerHTML;
          btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#4ade80" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
          setTimeout(() => {
            if (btn.parentElement) btn.innerHTML = originalHtml;
          }, 2000);
        })
        .catch((err) => console.error("Failed to copy text: ", err));
    }
  }
}

function autoResize() {
  const el = inputEl.value;
  if (!el) return;
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 200) + "px";
}

// ── Markdown ──────────────────────────────────────────────────────────────────

function escHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderMarkdown(text) {
  if (!text) return "";
  const parts = text.split(/(```[\s\S]*?```)/g);
  const rendered = parts.map((part, i) => {
    if (i % 2 === 1) {
      const match = part.match(/```(\w*)\n?([\s\S]*?)```/);
      if (match) {
        const lang = match[1] || "";
        const code = match[2].trim();
        const langHtml = lang
          ? `<span class="code-lang">${escHtml(lang)}</span>`
          : "";
        const copyBtn = `<button class="copy-code-btn" title="Copy code" aria-label="Copy code"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg></button>`;
        let highlightedCode = escHtml(code);
        if (lang && hljs.getLanguage(lang)) {
          highlightedCode = hljs.highlight(code, {
            language: lang,
            ignoreIllegals: true,
          }).value;
        } else {
          highlightedCode = hljs.highlightAuto(code).value;
        }
        return `<pre class="chat-code-block hljs">${langHtml}${copyBtn}<code class="hljs ${lang ? "language-" + escHtml(lang) : ""}">${highlightedCode}</code></pre>`;
      }
      return escHtml(part);
    }
    let html = escHtml(part);
    html = html.replace(
      /`([^`\n]+)`/g,
      '<code class="chat-inline-code">$1</code>',
    );
    html = html.replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/(?<!\*)\*(?!\*)([^*\n]+)\*(?!\*)/g, "<em>$1</em>");
    html = html.replace(/^#### (.+)$/gm, "<h4>$1</h4>");
    html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
    html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
    html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");
    html = html.replace(/^---+$/gm, "<hr>");
    html = html.replace(/((?:^[ \t]*[-*•] .+(?:\n|$))+)/gm, (block) => {
      const items = block
        .trim()
        .split("\n")
        .map((l) => `<li>${l.replace(/^[ \t]*[-*•] /, "")}</li>`)
        .join("");
      return `<ul>${items}</ul>`;
    });
    html = html.replace(/((?:^[ \t]*\d+\. .+(?:\n|$))+)/gm, (block) => {
      const items = block
        .trim()
        .split("\n")
        .map((l) => `<li>${l.replace(/^[ \t]*\d+\. /, "")}</li>`)
        .join("");
      return `<ol>${items}</ol>`;
    });
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
.think-dot-pulsing {
  animation: think-pulse 1.2s ease-in-out infinite;
}
@keyframes think-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}
.typing-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--muted);
  animation: bounce 1.2s ease-in-out infinite;
}
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
  40% { transform: translateY(-5px); opacity: 1; }
}
.response-content :deep(p) { margin: 0 0 0.75em; }
.response-content :deep(p:last-child) { margin-bottom: 0; }
.response-content :deep(h1),
.response-content :deep(h2),
.response-content :deep(h3),
.response-content :deep(h4) {
  margin: 1.1em 0 0.4em;
  font-weight: 600;
  line-height: 1.3;
}
.response-content :deep(h1) { font-size: 1.25em; }
.response-content :deep(h2) { font-size: 1.1em; }
.response-content :deep(h3) { font-size: 1em; }
.response-content :deep(h4) { font-size: 0.95em; color: var(--muted); }
.response-content :deep(ul),
.response-content :deep(ol) {
  margin: 0.5em 0 0.75em;
  padding-left: 1.4em;
}
.response-content :deep(li) { margin-bottom: 0.25em; }
.response-content :deep(strong) { font-weight: 600; }
.response-content :deep(em) { font-style: italic; }
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
  position: relative;
}
.response-content :deep(.copy-code-btn) {
  position: absolute;
  top: 0.4rem;
  right: 0.4rem;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.6);
  border-radius: 6px;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s, background 0.2s, color 0.2s;
}
.response-content :deep(.chat-code-block:hover .copy-code-btn) { opacity: 1; }
.response-content :deep(.copy-code-btn:hover) {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
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
.think-expand-enter-active,
.think-expand-leave-active {
  transition: max-height 0.3s ease, opacity 0.2s ease;
  overflow: hidden;
  max-height: 320px;
}
.think-expand-enter-from,
.think-expand-leave-to { max-height: 0; opacity: 0; }
.slide-up-enter-active,
.slide-up-leave-active {
  transition: max-height 0.25s ease, opacity 0.2s ease, padding 0.25s ease, margin 0.25s ease;
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
.messages-area::-webkit-scrollbar,
.think-content::-webkit-scrollbar { width: 5px; }
.messages-area::-webkit-scrollbar-track,
.think-content::-webkit-scrollbar-track { background: transparent; }
.messages-area::-webkit-scrollbar-thumb,
.think-content::-webkit-scrollbar-thumb {
  background: rgba(12, 17, 24, 0.15);
  border-radius: 10px;
}
</style>
