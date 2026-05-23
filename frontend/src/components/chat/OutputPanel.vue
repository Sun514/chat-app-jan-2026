<template>
  <div
    class="flex flex-col h-full bg-transparent overflow-hidden min-h-0"
  >
    <!-- Header -->
    <div
      class="shrink-0 flex items-center justify-between px-4 py-3 border-b border-[rgba(12,17,24,0.08)]"
    >
      <div class="text-[0.7rem] font-semibold tracking-[0.1em] uppercase text-(--muted)">
        Output
        <span v-if="items.length > 0" class="opacity-60">({{ items.length }})</span>
      </div>
      <button
        v-if="items.length > 0"
        class="text-[0.72rem] text-(--muted) hover:text-(--ink) cursor-pointer bg-transparent border-none"
        @click="$emit('clear')"
      >
        Clear
      </button>
    </div>

    <!-- Body -->
    <div class="flex-1 overflow-y-auto min-h-0 px-3 py-3 flex flex-col gap-3">
      <p
        v-if="items.length === 0"
        class="text-[0.78rem] text-(--muted) text-center py-8 px-4"
      >
        Tool results and generated files appear here.
      </p>

      <div
        v-for="(item, i) in items"
        :key="i"
        class="border border-[rgba(12,17,24,0.1)] rounded-xl bg-white overflow-hidden"
      >
        <div
          class="flex items-center justify-between px-3 py-2 bg-[rgba(12,17,24,0.03)] border-b border-[rgba(12,17,24,0.06)]"
        >
          <span class="text-[0.75rem] font-semibold text-(--ink)">
            {{ item.name }}
          </span>
          <div class="flex items-center gap-1.5">
            <button
              class="inline-flex items-center justify-center w-7 h-7 rounded-md border border-[rgba(12,17,24,0.08)] bg-white text-(--muted) cursor-pointer transition-colors hover:text-(--ink) hover:bg-[rgba(12,17,24,0.04)]"
              title="Open in right panel"
              aria-label="Open in right panel"
              @click="openItemPreview(item)"
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
                <rect x="3" y="4" width="18" height="16" rx="2" />
                <path d="M15 4v16" />
              </svg>
            </button>
            <button
              class="inline-flex items-center justify-center w-7 h-7 rounded-md border border-[rgba(12,17,24,0.08)] bg-white text-(--muted) cursor-pointer transition-colors hover:text-(--ink) hover:bg-[rgba(12,17,24,0.04)] disabled:opacity-50 disabled:cursor-default"
              :class="uploadButtonClass(i)"
              :title="uploadButtonTitle(item, i)"
              aria-label="Upload to data sources"
              :disabled="isUploading(i) || !canUploadItem(item)"
              @click="uploadItemToLibrary(item, i)"
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
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </button>
            <button
              class="inline-flex items-center justify-center w-7 h-7 rounded-md border border-[rgba(12,17,24,0.08)] bg-white text-(--muted) cursor-pointer transition-colors hover:text-(--ink) hover:bg-[rgba(12,17,24,0.04)]"
              :class="{ 'text-(--accent)! border-[rgba(255,106,0,0.22)] bg-[rgba(255,106,0,0.06)]': copiedIndex === i }"
              :title="copiedIndex === i ? 'Copied' : 'Copy output'"
              aria-label="Copy output"
              @click="copyItem(item, i)"
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
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
              </svg>
            </button>
            <button
              class="inline-flex items-center justify-center w-7 h-7 rounded-md border border-[rgba(12,17,24,0.08)] bg-white text-(--muted) cursor-pointer transition-colors hover:text-(--ink) hover:bg-[rgba(12,17,24,0.04)]"
              title="Download output"
              aria-label="Download output"
              @click="downloadItem(item)"
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
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
            </button>
            <span class="text-[0.65rem] uppercase tracking-[0.08em] text-(--muted)">
              {{ item.view || "json" }}
            </span>
          </div>
        </div>

        <!-- Files -->
        <div
          v-if="item.files && item.files.length > 0"
          class="px-3 py-2 flex flex-col gap-2"
        >
          <a
            v-for="file in item.files"
            :key="file.filename"
            :href="`${apiBase}${file.download_url}`"
            :download="file.filename"
            class="flex items-center gap-2 px-3 py-2 rounded-lg border border-[rgba(12,17,24,0.08)] bg-[rgba(12,17,24,0.02)] hover:bg-[rgba(255,106,0,0.06)] transition-colors no-underline text-(--ink)"
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
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            <div class="flex-1 min-w-0">
              <div class="text-[0.82rem] truncate">{{ file.filename }}</div>
              <div class="text-[0.7rem] text-(--muted)">
                {{ formatBytes(file.size_bytes) }}
                <span v-if="file.duration_seconds">
                  · {{ formatDuration(file.duration_seconds) }}
                </span>
              </div>
            </div>
          </a>
        </div>

        <!-- Search results -->
        <div
          v-else-if="item.view === 'search' && item.data?.results"
          class="px-3 py-2 flex flex-col gap-2"
        >
          <div
            v-for="(r, ri) in item.data.results"
            :key="r.chunk_id || ri"
            class="border border-[rgba(12,17,24,0.06)] rounded-lg p-2 bg-[rgba(12,17,24,0.02)]"
          >
            <div class="flex items-baseline justify-between gap-2 mb-1">
              <span class="text-[0.75rem] font-semibold text-(--ink) truncate">
                {{ r.filename }}
              </span>
              <span class="text-[0.65rem] text-(--muted) shrink-0">
                {{ (r.similarity * 100).toFixed(0) }}%
              </span>
            </div>
            <p class="m-0 text-[0.72rem] text-(--muted) leading-snug line-clamp-3">
              {{ r.content }}
            </p>
          </div>
        </div>

        <!-- Metrics -->
        <div
          v-else-if="item.view === 'metrics' && item.data"
          class="px-3 py-2 grid grid-cols-2 gap-2"
        >
          <div
            v-for="m in metricRows(item.data)"
            :key="m.label"
            class="bg-[rgba(12,17,24,0.03)] rounded-lg px-2 py-1.5"
          >
            <div class="text-[0.65rem] uppercase tracking-[0.05em] text-(--muted)">
              {{ m.label }}
            </div>
            <div class="text-[0.85rem] font-semibold text-(--ink)">
              {{ m.value }}
            </div>
          </div>
        </div>

        <!-- Text -->
        <div
          v-else-if="item.view === 'text'"
          class="px-3 py-2"
        >
          <pre
            class="m-0 text-[0.72rem] font-mono text-(--ink) bg-[rgba(12,17,24,0.03)] rounded-lg p-3 whitespace-pre-wrap wrap-break-word leading-[1.6] max-h-80 overflow-y-auto"
            >{{ getTextContent(item) }}</pre
          >
        </div>

        <!-- JSON fallback -->
        <details v-else class="px-3 py-2">
          <summary class="text-[0.72rem] text-(--muted) cursor-pointer">
            Raw response
          </summary>
          <pre
            class="mt-2 m-0 text-[0.7rem] font-mono text-(--ink) bg-[rgba(12,17,24,0.04)] rounded-md p-2 overflow-x-auto max-h-60"
            >{{ formatJson(item.data ?? item.summary) }}</pre
          >
        </details>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { formatBytes, formatDuration } from "../../utils/format.js";

const props = defineProps({
  items: { type: Array, default: () => [] },
});
const emit = defineEmits(["clear", "library-uploaded", "open-preview"]);

const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const copiedIndex = ref(null);
const supportedExtensions = ref([]);
const supportedTypesLoaded = ref(false);
const uploadStates = reactive({});

function metricRows(data) {
  const rows = [];
  if (data.users) {
    rows.push({ label: "Total users", value: data.users.total_users });
    rows.push({ label: "Active (30d)", value: data.users.active_users_30d });
  }
  if (data.most_used_llm) {
    rows.push({
      label: "Top model",
      value: `${data.most_used_llm.model} (${data.most_used_llm.usage_percent}%)`,
    });
  }
  if (data.most_used_module) {
    rows.push({
      label: "Top module",
      value: `${data.most_used_module.module} (${data.most_used_module.usage_percent}%)`,
    });
  }
  if (data.tokens_per_request) {
    rows.push({
      label: "Avg tokens in",
      value: data.tokens_per_request.avg_tokens_in,
    });
    rows.push({
      label: "Avg tokens out",
      value: data.tokens_per_request.avg_tokens_out,
    });
  }
  return rows;
}

function formatJson(value) {
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function getTextContent(item) {
  if (typeof item.data?.content === "string" && item.data.content) {
    return item.data.content;
  }
  if (typeof item.summary === "string") {
    return item.summary;
  }
  return formatJson(item.data ?? item.summary);
}

function slugify(value) {
  return String(value || "output")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "output";
}

function serializeItemText(item) {
  const sections = [];

  if (item.name) sections.push(item.name);
  if (item.summary) sections.push(String(item.summary));

  if (!item.summary && item.view === "metrics" && item.data) {
    sections.push(
      metricRows(item.data)
        .map((row) => `${row.label}: ${row.value}`)
        .join("\n"),
    );
  }

  if (!item.summary && item.view === "search" && item.data?.results) {
    sections.push(
      item.data.results.length
        ? item.data.results
            .map(
              (result, index) =>
                `[${index + 1}] ${result.filename || "Untitled"} (${((result.similarity || 0) * 100).toFixed(0)}%)\n${result.content || ""}`,
            )
            .join("\n\n")
        : "No matching chunks.",
    );
  }

  if (item.files?.length) {
    sections.push(
      item.files
        .map((file) => {
          const meta = [formatBytes(file.size_bytes)];
          if (file.duration_seconds) {
            meta.push(formatDuration(file.duration_seconds));
          }
          return [
            file.filename,
            meta.filter(Boolean).join(" · "),
            file.download_url ? `${apiBase}${file.download_url}` : "",
          ]
            .filter(Boolean)
            .join("\n");
        })
        .join("\n\n"),
    );
  }

  if (!item.summary && !item.files?.length && item.data != null) {
    sections.push(formatJson(item.data));
  }

  return sections.filter(Boolean).join("\n\n");
}

function getDownloadPayload(item) {
  const baseName = slugify(item.name || "output");

  if (item.view === "json" && item.data && typeof item.data === "object") {
    return {
      content: formatJson(item.data),
      filename: `${baseName}.json`,
      mimeType: "application/json;charset=utf-8",
    };
  }

  return {
    content: serializeItemText(item),
    filename: `${baseName}.txt`,
    mimeType: "text/plain;charset=utf-8",
  };
}

function fallbackCopyText(text) {
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "absolute";
  textarea.style.left = "-9999px";
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  document.body.removeChild(textarea);
}

async function copyItem(item, index) {
  const text = serializeItemText(item);
  if (!text) return;

  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
  } else {
    fallbackCopyText(text);
  }

  copiedIndex.value = index;
  window.setTimeout(() => {
    if (copiedIndex.value === index) copiedIndex.value = null;
  }, 1800);
}

function downloadItem(item) {
  const { content, filename, mimeType } = getDownloadPayload(item);
  if (!content) return;

  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function openItemPreview(item) {
  emit("open-preview", {
    kind: "output",
    name: item.name || "Output",
    view: item.view || "json",
    content: serializeItemText(item) || formatJson(item.data ?? item.summary),
  });
}

async function ensureSupportedTypes() {
  if (supportedTypesLoaded.value) return;
  supportedTypesLoaded.value = true;
  try {
    const res = await fetch(`${apiBase}/documents/supported-types`);
    if (!res.ok) return;
    const data = await res.json();
    supportedExtensions.value = data.extensions || [];
  } catch {
    // Fall back to letting the server validate uploads.
  }
}

function getFileExtension(name) {
  const idx = String(name || "").lastIndexOf(".");
  return idx >= 0 ? String(name).slice(idx).toLowerCase() : "";
}

function isSupportedOutputFile(file) {
  if (supportedExtensions.value.length === 0) return true;
  const ext = getFileExtension(file.filename || file.name);
  return supportedExtensions.value.some((supported) => supported === ext);
}

function getUploadableFiles(item) {
  if (!item.files?.length) return [];
  return item.files.filter(isSupportedOutputFile);
}

function canUploadItem(item) {
  if (!item.files?.length) return true;
  if (supportedTypesLoaded.value && supportedExtensions.value.length > 0) {
    return getUploadableFiles(item).length > 0;
  }
  return true;
}

function isUploading(index) {
  return uploadStates[index]?.status === "uploading";
}

function uploadButtonClass(index) {
  const status = uploadStates[index]?.status;
  if (status === "success") {
    return "text-(--teal)! border-[rgba(0,150,136,0.22)] bg-[rgba(0,150,136,0.06)]";
  }
  if (status === "error") {
    return "text-red-600! border-[rgba(220,38,38,0.18)] bg-[rgba(220,38,38,0.05)]";
  }
  if (status === "uploading") {
    return "text-(--accent)! border-[rgba(255,106,0,0.22)] bg-[rgba(255,106,0,0.06)]";
  }
  return "";
}

function uploadButtonTitle(item, index) {
  const state = uploadStates[index];
  if (state?.message) return state.message;
  if (state?.status === "uploading") return "Uploading to data sources…";
  if (!canUploadItem(item)) return "This output can't be uploaded to data sources";
  return "Upload to data sources";
}

async function fetchOutputFileAsFile(file) {
  const res = await fetch(`${apiBase}${file.download_url}`);
  if (!res.ok) throw new Error(`Failed to fetch ${file.filename}`);
  const blob = await res.blob();
  return new File([blob], file.filename, {
    type: blob.type || "application/octet-stream",
    lastModified: Date.now(),
  });
}

async function buildUploadFiles(item) {
  if (item.files?.length) {
    const files = getUploadableFiles(item);
    if (files.length === 0) {
      throw new Error("This output doesn't contain any supported document types");
    }
    return Promise.all(files.map(fetchOutputFileAsFile));
  }

  const { content, filename, mimeType } = getDownloadPayload(item);
  return [
    new File([content || ""], filename, {
      type: mimeType,
      lastModified: Date.now(),
    }),
  ];
}

async function uploadItemToLibrary(item, index) {
  uploadStates[index] = { status: "uploading", message: "Uploading to data sources…" };

  try {
    await ensureSupportedTypes();
    const files = await buildUploadFiles(item);
    const fd = new FormData();
    for (const file of files) fd.append("files", file);

    const res = await fetch(`${apiBase}/documents/upload`, {
      method: "POST",
      body: fd,
    });

    let body = null;
    try {
      body = await res.json();
    } catch {
      // Keep null and use generic fallback below.
    }

    if (!res.ok) {
      throw new Error(body?.detail || `HTTP ${res.status}`);
    }

    if (!body?.succeeded) {
      throw new Error(body?.results?.[0]?.message || "Upload rejected");
    }

    const suffix =
      body.failed > 0
        ? `${body.succeeded} uploaded, ${body.failed} failed`
        : body.succeeded === 1
          ? "Added to data sources"
          : `${body.succeeded} files added`;

    uploadStates[index] = { status: "success", message: suffix };
    emit("library-uploaded", {
      item,
      result: body,
    });
  } catch (err) {
    uploadStates[index] = {
      status: "error",
      message: err.message || "Upload failed",
    };
  }
}
</script>

<style scoped>
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
