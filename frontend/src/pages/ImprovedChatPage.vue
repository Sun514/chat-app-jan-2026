<template>
  <div class="relative h-screen flex flex-col pt-[56px] overflow-hidden bg-white">
    <div class="flex-1 flex w-full border-t border-[rgba(12,17,24,0.08)] overflow-hidden">
      <!-- Left: Data sources -->
      <div class="w-[280px] shrink-0 border-r border-[rgba(12,17,24,0.08)] bg-[#f9f9fa]">
      <DataSourcesPanel
        :attachments="attachments"
        @attach="onAttach"
        @detach="onDetach"
        @preview="onPreview"
      />
      </div>

      <!-- Center: Chat -->
      <div class="flex-1 min-w-0 bg-white">
        <ChatPanel
          :attachments="attachments"
          @detach="onDetach"
          @tool-result="onToolResult"
        />
      </div>

      <!-- Right: Output -->
      <div class="w-[360px] shrink-0 border-l border-[rgba(12,17,24,0.08)] bg-[#f9f9fa]">
        <OutputPanel :items="outputItems" @clear="outputItems = []" />
      </div>
    </div>

    <!-- Preview overlay -->
    <Transition name="preview-fade">
      <div
        v-if="preview"
        class="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(12,17,24,0.4)] backdrop-blur-sm px-6"
        @click.self="preview = null"
      >
        <div
          class="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] flex flex-col overflow-hidden"
        >
          <div
            class="flex items-center justify-between px-4 py-3 border-b border-[rgba(12,17,24,0.08)]"
          >
            <div class="min-w-0 flex-1">
              <div class="text-[0.7rem] uppercase tracking-[0.08em] text-(--muted)">
                {{ preview.kind === "library" ? "Library document" : "Collection file" }}
              </div>
              <div class="text-[0.95rem] font-semibold text-(--ink) truncate">
                {{ preview.name }}
              </div>
            </div>
            <button
              class="text-(--muted) hover:text-(--ink) cursor-pointer bg-transparent border-none text-xl leading-none"
              @click="preview = null"
            >
              ×
            </button>
          </div>
          <div class="flex-1 overflow-y-auto p-4">
            <p
              v-if="previewLoading"
              class="text-[0.82rem] text-(--muted)"
            >
              Loading preview…
            </p>
            <p
              v-else-if="previewError"
              class="text-[0.82rem] text-red-600"
            >
              {{ previewError }}
            </p>
            <pre
              v-else
              class="m-0 text-[0.78rem] font-mono text-(--ink) whitespace-pre-wrap wrap-break-word leading-relaxed"
              >{{ previewText }}</pre
            >
          </div>
          <div
            class="flex items-center justify-end gap-2 px-4 py-3 border-t border-[rgba(12,17,24,0.08)]"
          >
            <button
              class="px-3 py-1.5 text-[0.8rem] rounded-lg border border-[rgba(12,17,24,0.15)] bg-transparent text-(--ink) cursor-pointer hover:bg-[rgba(12,17,24,0.04)]"
              @click="preview = null"
            >
              Close
            </button>
            <button
              v-if="!isAttached(preview)"
              class="px-3 py-1.5 text-[0.8rem] rounded-lg border-none bg-(--accent) text-white cursor-pointer hover:opacity-90"
              @click="onAttach(preview); preview = null"
            >
              Attach to chat
            </button>
            <button
              v-else
              class="px-3 py-1.5 text-[0.8rem] rounded-lg border border-[rgba(12,17,24,0.15)] bg-transparent text-(--ink) cursor-pointer hover:bg-[rgba(12,17,24,0.04)]"
              @click="onDetach(preview); preview = null"
            >
              Detach from chat
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, watch } from "vue";
import DataSourcesPanel from "../components/chat/DataSourcesPanel.vue";
import ChatPanel from "../components/chat/ChatPanel.vue";
import OutputPanel from "../components/chat/OutputPanel.vue";

const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const attachments = ref([]);
const outputItems = ref([]);

const preview = ref(null);
const previewLoading = ref(false);
const previewError = ref("");
const previewText = ref("");

function isAttached(att) {
  if (!att) return false;
  return attachments.value.some(
    (a) => a.kind === att.kind && a.id === att.id,
  );
}

function onAttach(att) {
  if (isAttached(att)) return;
  attachments.value.push({ kind: att.kind, id: att.id, name: att.name });
}

function onDetach(att) {
  attachments.value = attachments.value.filter(
    (a) => !(a.kind === att.kind && a.id === att.id),
  );
}

function onToolResult(payload) {
  outputItems.value.push(payload);
}

async function onPreview(item) {
  preview.value = item;
  previewText.value = "";
  previewError.value = "";

  if (item.kind === "library") {
    previewLoading.value = true;
    try {
      const res = await fetch(`${apiBase}/documents/${item.id}/context`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      previewText.value = (data.context_text || "").slice(0, 4000) || "(empty)";
    } catch (err) {
      previewError.value = `Failed to load preview: ${err.message}`;
    } finally {
      previewLoading.value = false;
    }
  } else {
    const f = item.file || {};
    previewText.value =
      `Local file (no extracted text).\n\n` +
      `Name: ${f.name || item.name}\n` +
      `Type: ${f.type || "Unknown"}\n` +
      `Size: ${f.sizeLabel || ""}\n` +
      `Uploaded: ${f.uploadedAt || ""}`;
  }
}

watch(preview, (v) => {
  if (!v) {
    previewText.value = "";
    previewError.value = "";
  }
});
</script>

<style scoped>
.preview-fade-enter-active,
.preview-fade-leave-active {
  transition: opacity 0.18s ease;
}
.preview-fade-enter-from,
.preview-fade-leave-to {
  opacity: 0;
}
</style>
