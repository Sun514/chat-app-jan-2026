<template>
  <div class="relative h-screen flex flex-col pt-[56px] overflow-hidden bg-white">
    <div
      ref="layoutEl"
      class="flex-1 flex w-full border-t border-[rgba(12,17,24,0.08)] overflow-hidden"
    >
      <div
        v-if="!isPreviewMode"
        class="w-[280px] shrink-0 border-r border-[rgba(12,17,24,0.08)] bg-[#f9f9fa]"
      >
        <DataSourcesPanel
          :attachments="attachments"
          :refresh-token="libraryRefreshToken"
          @attach="onAttach"
          @detach="onDetach"
          @preview="onPreview"
        />
      </div>

      <div
        v-else
        class="w-[86px] shrink-0 border-r border-[rgba(12,17,24,0.08)] bg-[linear-gradient(180deg,#f7f8fa_0%,#f1f3f6_100%)] flex flex-col items-center px-2 py-3"
      >
        <button
          class="w-full rounded-[22px] border border-[rgba(12,17,24,0.1)] bg-white text-(--ink) cursor-pointer transition-[transform,box-shadow,border-color] duration-150 hover:-translate-y-px hover:border-[rgba(12,17,24,0.16)] hover:shadow-[0_10px_22px_rgba(12,17,24,0.08)] px-2 py-3 flex flex-col items-center gap-2"
          :title="previewBackTitle"
          @click="closePreview"
        >
          <span
            class="grid place-items-center w-11 h-11 rounded-[16px] bg-[#111722] text-white shadow-[0_6px_16px_rgba(17,23,34,0.18)]"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.25"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M15 18l-6-6 6-6" />
            </svg>
          </span>
          <span class="text-center leading-tight">
            <span
              class="block text-[0.58rem] font-semibold uppercase tracking-[0.18em] text-[#475467]"
            >
              View
            </span>
            <span class="mt-1 block text-[0.7rem] font-medium text-(--ink)">
              {{ previewRailLabel }}
            </span>
          </span>
        </button>
      </div>

      <div
        class="min-w-0 bg-white"
        :class="isPreviewMode ? 'flex-1 basis-0' : 'flex-1'"
      >
        <ChatPanel
          :attachments="attachments"
          @detach="onDetach"
          @tool-result="onToolResult"
        />
      </div>

      <div
        v-if="!isPreviewMode"
        class="w-[400px] shrink-0 border-l border-[rgba(12,17,24,0.08)] bg-[#f9f9fa]"
      >
        <OutputPanel
          :items="outputItems"
          @clear="outputItems = []"
          @library-uploaded="onLibraryUploaded"
          @open-preview="onPreview"
        />
      </div>

      <template v-else>
        <div
          class="flex-1 basis-0 min-w-0 border-l border-[rgba(12,17,24,0.08)] bg-[#fbfbfc] flex flex-col"
        >
          <div
            class="shrink-0 flex items-start justify-between gap-3 px-4 py-3 border-b border-[rgba(12,17,24,0.08)] bg-white"
          >
            <div class="min-w-0 flex-1">
              <div
                class="text-[0.68rem] uppercase tracking-[0.1em] text-(--muted)"
              >
                {{ previewKindLabel }}
              </div>
              <div class="mt-1 text-[0.98rem] font-semibold text-(--ink) truncate">
                {{ preview?.name }}
              </div>
              <p class="mt-1 mb-0 text-[0.74rem] text-(--muted)">
                {{ previewDescription }}
              </p>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <button
                v-if="canAttachPreview && preview && isAttached(preview)"
                class="px-3 py-1.5 text-[0.8rem] rounded-lg border border-[rgba(12,17,24,0.15)] bg-transparent text-(--ink) cursor-pointer hover:bg-[rgba(12,17,24,0.04)]"
                @click="onDetach(preview)"
              >
                Detach from chat
              </button>
              <button
                class="w-9 h-9 rounded-lg border border-[rgba(12,17,24,0.12)] bg-transparent text-(--muted) cursor-pointer hover:bg-[rgba(12,17,24,0.04)] hover:text-(--ink)"
                title="Close preview"
                @click="closePreview"
              >
                ×
              </button>
            </div>
          </div>

          <div class="flex-1 overflow-y-auto min-h-0 px-4 py-4">
            <p
              v-if="previewLoading"
              class="m-0 text-[0.82rem] text-(--muted)"
            >
              Loading preview…
            </p>
            <p
              v-else-if="previewError"
              class="m-0 text-[0.82rem] text-red-600"
            >
              {{ previewError }}
            </p>
            <pre
              v-else
              class="m-0 text-[0.78rem] font-mono text-(--ink) whitespace-pre-wrap wrap-break-word leading-relaxed"
              >{{ previewText }}</pre
            >
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import {
  computed,
  onBeforeUnmount,
  ref,
  watch,
} from "vue";
import DataSourcesPanel from "../components/chat/DataSourcesPanel.vue";
import ChatPanel from "../components/chat/ChatPanel.vue";
import OutputPanel from "../components/chat/OutputPanel.vue";

const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const attachments = ref([]);
const outputItems = ref([]);
const libraryRefreshToken = ref(0);

const preview = ref(null);
const previewLoading = ref(false);
const previewError = ref("");
const previewText = ref("");
const previewRequestId = ref(0);

const isPreviewMode = computed(() => !!preview.value);
const canAttachPreview = computed(
  () => preview.value?.kind === "library" || preview.value?.kind === "collection",
);
const previewRailLabel = computed(() =>
  preview.value?.kind === "output" ? "Output" : "Sources",
);
const previewBackTitle = computed(() =>
  preview.value?.kind === "output"
    ? "Return to outputs"
    : "Return to data sources",
);
const previewKindLabel = computed(() =>
  preview.value?.kind === "library"
    ? "Source Collection document"
    : preview.value?.kind === "collection"
      ? "Knowledge profile file"
      : "Output item",
);
const previewDescription = computed(() =>
  preview.value?.kind === "output"
    ? "Focus mode hides the output list and expands the selected output preview."
    : "Focus mode hides outputs and expands the selected source preview.",
);

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

function onLibraryUploaded() {
  libraryRefreshToken.value += 1;
}

function closePreview() {
  previewRequestId.value += 1;
  preview.value = null;
}

async function onPreview(item) {
  const requestId = previewRequestId.value + 1;
  previewRequestId.value = requestId;
  preview.value = item;
  previewText.value = "";
  previewError.value = "";

  if (item.kind === "library") {
    previewLoading.value = true;
    try {
      const res = await fetch(`${apiBase}/documents/${item.id}/context`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (previewRequestId.value !== requestId) return;
      previewText.value = (data.context_text || "").slice(0, 12000) || "(empty)";
    } catch (err) {
      if (previewRequestId.value !== requestId) return;
      previewError.value = `Failed to load preview: ${err.message}`;
    } finally {
      if (previewRequestId.value === requestId) {
        previewLoading.value = false;
      }
    }
  } else if (item.kind === "output") {
    previewLoading.value = false;
    previewText.value = item.content || "(empty)";
  } else {
    previewLoading.value = false;
    const f = item.file || {};
    previewText.value =
      `Knowledge profile file preview is metadata-only.\n\n` +
      `Name: ${f.name || item.name}\n` +
      `Type: ${f.type || "Unknown"}\n` +
      `Size: ${f.sizeLabel || ""}\n` +
      `Uploaded: ${f.uploadedAt || ""}`;
  }
}

watch(preview, (value) => {
  if (!value) {
    previewText.value = "";
    previewError.value = "";
    previewLoading.value = false;
  }
});

onBeforeUnmount(() => {
});
</script>

<style scoped>
</style>
