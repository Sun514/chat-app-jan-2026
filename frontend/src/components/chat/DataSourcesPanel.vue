<template>
  <div
    class="relative flex flex-col h-full bg-transparent overflow-hidden min-h-0"
    @dragenter.prevent="onDragEnter"
    @dragover.prevent
    @dragleave.prevent="onDragLeave"
    @drop.prevent="onDrop"
  >
    <!-- Drag overlay -->
    <Transition name="drag-fade">
      <div
        v-if="dragActive"
        class="absolute inset-0 z-30 flex flex-col items-center justify-center gap-2 bg-[rgba(255,106,0,0.08)] border-2 border-dashed border-(--accent) rounded-2xl pointer-events-none"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="32"
          height="32"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
          class="text-(--accent)"
        >
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
        <p class="m-0 text-[0.85rem] font-semibold text-(--accent)">
          Drop to upload to Library
        </p>
      </div>
    </Transition>

    <!-- Header + tabs -->
    <div
      class="shrink-0 px-4 pt-3 pb-0 border-b border-[rgba(12,17,24,0.08)]"
    >
      <div class="flex items-center justify-between mb-2">
        <div
          class="text-[0.7rem] font-semibold tracking-[0.1em] uppercase text-(--muted)"
        >
          Data sources
        </div>
        <div class="flex items-center gap-1">
          <button
            v-if="activeTab === 'library'"
            class="flex items-center gap-1 px-2 py-0.5 text-[0.72rem] font-medium text-(--ink) hover:bg-[rgba(12,17,24,0.06)] cursor-pointer bg-transparent border border-[rgba(12,17,24,0.12)] rounded-md transition-colors"
            @click="openFilePicker"
            title="Upload files to Library"
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
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Upload
          </button>
          <button
            class="text-[0.78rem] text-(--muted) hover:text-(--ink) cursor-pointer bg-transparent border-none px-1"
            @click="refresh"
            title="Refresh"
            :disabled="libraryLoading"
          >
            ↻
          </button>
        </div>
      </div>
      <div class="flex gap-1">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="px-3 py-1.5 text-[0.78rem] font-medium border-none cursor-pointer rounded-t-md transition-colors duration-150"
          :class="
            activeTab === tab.id
              ? 'bg-[rgba(12,17,24,0.06)] text-(--ink)'
              : 'bg-transparent text-(--muted) hover:text-(--ink)'
          "
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
          <span class="text-[0.7rem] opacity-60">({{ tab.count }})</span>
        </button>
      </div>
    </div>

    <!-- Hidden file input -->
    <input
      ref="fileInputEl"
      type="file"
      multiple
      class="hidden"
      :accept="acceptAttr"
      @change="onFileInputChange"
    />

    <!-- Body -->
    <div class="flex-1 overflow-y-auto min-h-0 px-2 py-2">
      <!-- Library -->
      <div v-if="activeTab === 'library'">
        <!-- Upload tray -->
        <div
          v-if="uploads.length > 0"
          class="mb-2 border border-[rgba(12,17,24,0.08)] rounded-lg bg-[rgba(12,17,24,0.02)] p-2"
        >
          <div class="flex items-center justify-between mb-1.5">
            <span
              class="text-[0.65rem] font-semibold uppercase tracking-[0.08em] text-(--muted)"
            >
              Uploads ({{ activeUploadCount }} active)
            </span>
            <button
              class="text-[0.7rem] text-(--muted) hover:text-(--ink) cursor-pointer bg-transparent border-none"
              @click="clearFinishedUploads"
              :disabled="activeUploadCount === uploads.length"
            >
              Clear done
            </button>
          </div>
          <div
            v-for="up in uploads"
            :key="up.id"
            class="flex flex-col gap-1 px-1.5 py-1 rounded-md hover:bg-white/40"
          >
            <div class="flex items-start gap-1.5">
              <span
                class="shrink-0 w-3 h-3 mt-0.5 rounded-full"
                :class="{
                  'bg-[rgba(12,17,24,0.2)] think-dot-pulsing':
                    up.status === 'uploading' || up.status === 'processing',
                  'bg-(--teal)': up.status === 'success',
                  'bg-red-500': up.status === 'error',
                }"
              ></span>
              <div class="flex-1 min-w-0">
                <div
                  class="text-[0.75rem] text-(--ink) truncate"
                  :title="up.name"
                >
                  {{ up.name }}
                </div>
                <div
                  class="text-[0.65rem] leading-tight"
                  :class="
                    up.status === 'error' ? 'text-red-600' : 'text-(--muted)'
                  "
                >
                  <template v-if="up.status === 'uploading'">
                    Uploading {{ up.progress }}%
                  </template>
                  <template v-else-if="up.status === 'processing'">
                    Processing on server…
                  </template>
                  <template v-else-if="up.status === 'success'">
                    Indexed · {{ up.message }}
                  </template>
                  <template v-else-if="up.status === 'error'">
                    {{ up.message || "Failed" }}
                  </template>
                </div>
              </div>
            </div>
            <!-- Progress bar -->
            <div
              v-if="up.status === 'uploading' || up.status === 'processing'"
              class="h-1 rounded-full bg-[rgba(12,17,24,0.06)] overflow-hidden ml-4"
            >
              <div
                class="h-full bg-(--accent) transition-[width] duration-150"
                :class="{
                  'progress-indeterminate': up.status === 'processing',
                }"
                :style="
                  up.status === 'uploading'
                    ? { width: `${up.progress}%` }
                    : { width: '100%' }
                "
              ></div>
            </div>
          </div>
        </div>

        <p
          v-if="libraryLoading && libraryDocs.length === 0"
          class="text-[0.78rem] text-(--muted) px-2 py-3"
        >
          Loading…
        </p>
        <p
          v-else-if="libraryError"
          class="text-[0.78rem] text-red-600 px-2 py-3"
        >
          {{ libraryError }}
        </p>
        <p
          v-else-if="libraryDocs.length === 0 && uploads.length === 0"
          class="text-[0.78rem] text-(--muted) px-2 py-3"
        >
          No documents uploaded yet. Click <strong>Upload</strong> or drag files
          here.
        </p>
        <div
          v-for="doc in libraryDocs"
          :key="doc.id"
          class="w-full flex items-start gap-2 px-2 py-2 rounded-lg transition-colors duration-100 hover:bg-[rgba(12,17,24,0.04)]"
        >
          <input
            type="checkbox"
            class="mt-1 cursor-pointer accent-(--accent)"
            :checked="isAttached('library', doc.id)"
            @click.stop="toggle('library', doc.id, doc.filename)"
          />
          <button
            type="button"
            class="flex-1 min-w-0 text-left cursor-pointer bg-transparent border-none p-0"
            @click="
              $emit('preview', {
                kind: 'library',
                id: doc.id,
                name: doc.filename,
              })
            "
          >
            <div class="text-[0.82rem] text-(--ink) truncate">
              {{ doc.filename }}
            </div>
            <div class="text-[0.7rem] text-(--muted)">
              {{ doc.file_type }} · {{ formatBytes(doc.file_size) }}
            </div>
          </button>
          <button
            type="button"
            class="shrink-0 inline-flex items-center justify-center w-7 h-7 mt-0.5 rounded-md border border-[rgba(12,17,24,0.08)] bg-white text-(--muted) cursor-pointer transition-colors hover:text-red-600 hover:bg-[rgba(220,38,38,0.05)] disabled:opacity-50 disabled:cursor-default"
            :title="deletingDocs[doc.id] ? 'Deleting…' : 'Delete document'"
            :disabled="deletingDocs[doc.id]"
            @click.stop="deleteLibraryDoc(doc)"
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
              <polyline points="3 6 5 6 21 6" />
              <path d="M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2" />
              <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
              <line x1="10" y1="11" x2="10" y2="17" />
              <line x1="14" y1="11" x2="14" y2="17" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Collections -->
      <div v-else>
        <p
          v-if="collections.length === 0"
          class="text-[0.78rem] text-(--muted) px-2 py-3"
        >
          No local collections.
        </p>
        <div v-for="col in collections" :key="col.id" class="mb-2">
          <div
            class="px-2 py-1 text-[0.72rem] font-semibold tracking-[0.05em] uppercase text-(--muted)"
          >
            {{ col.name }}
          </div>
          <button
            v-for="file in col.files"
            :key="file.id"
            type="button"
            class="w-full flex items-start gap-2 px-2 py-2 rounded-lg cursor-pointer text-left bg-transparent border-none transition-colors duration-100 hover:bg-[rgba(12,17,24,0.04)]"
            @click="
              $emit('preview', {
                kind: 'collection',
                id: `${col.id}/${file.id}`,
                name: file.name,
                file,
              })
            "
          >
            <input
              type="checkbox"
              class="mt-1 cursor-pointer accent-(--accent)"
              :checked="isAttached('collection', `${col.id}/${file.id}`)"
              @click.stop="
                toggle('collection', `${col.id}/${file.id}`, file.name)
              "
            />
            <div class="flex-1 min-w-0">
              <div class="text-[0.82rem] text-(--ink) truncate">
                {{ file.name }}
              </div>
              <div class="text-[0.7rem] text-(--muted)">
                {{ file.type }} · {{ file.sizeLabel }}
              </div>
            </div>
          </button>
          <p
            v-if="col.files.length === 0"
            class="text-[0.7rem] text-(--muted) px-2 pb-1 italic"
          >
            (empty)
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { state as collectionsState } from "../../stores/documentCollections.js";
import { formatBytes } from "../../utils/format.js";

const props = defineProps({
  attachments: { type: Array, default: () => [] },
  autoAttachUploads: { type: Boolean, default: true },
  refreshToken: { type: Number, default: 0 },
});
const emit = defineEmits(["attach", "detach", "preview"]);

const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const activeTab = ref("library");
const libraryDocs = ref([]);
const libraryLoading = ref(false);
const libraryError = ref("");

const supportedExtensions = ref([]);
const fileInputEl = ref(null);
const uploads = ref([]);
const dragDepth = ref(0);
const dragActive = ref(false);
const deletingDocs = ref({});

const collections = computed(() => collectionsState.items);

const tabs = computed(() => [
  { id: "library", label: "Source Collection", count: libraryDocs.value.length },
  {
    id: "collections",
    label: "Knowledge Profiles",
    count: collections.value.reduce((n, c) => n + c.files.length, 0),
  },
]);

const acceptAttr = computed(() =>
  supportedExtensions.value.length > 0
    ? supportedExtensions.value.join(",")
    : "*",
);

const activeUploadCount = computed(
  () =>
    uploads.value.filter(
      (u) => u.status === "uploading" || u.status === "processing",
    ).length,
);

// ── Library load ──────────────────────────────────────────────────────────────

async function loadLibrary() {
  libraryLoading.value = true;
  libraryError.value = "";
  try {
    const res = await fetch(`${apiBase}/documents/?limit=100`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    libraryDocs.value = await res.json();
  } catch (err) {
    libraryError.value = `Failed to load library: ${err.message}`;
  } finally {
    libraryLoading.value = false;
  }
}

async function loadSupportedTypes() {
  try {
    const res = await fetch(`${apiBase}/documents/supported-types`);
    if (!res.ok) return;
    const data = await res.json();
    supportedExtensions.value = data.extensions || [];
  } catch {
    // Silent — fall back to accept-all and let server reject.
  }
}

function refresh() {
  if (activeTab.value === "library") loadLibrary();
}

// ── Selection / attach ────────────────────────────────────────────────────────

function isAttached(kind, id) {
  return props.attachments.some((a) => a.kind === kind && a.id === id);
}

function toggle(kind, id, name) {
  if (isAttached(kind, id)) {
    emit("detach", { kind, id, name });
  } else {
    emit("attach", { kind, id, name });
  }
}

// ── Upload ────────────────────────────────────────────────────────────────────

function openFilePicker() {
  fileInputEl.value?.click();
}

function onFileInputChange(e) {
  const files = Array.from(e.target.files || []);
  if (files.length > 0) handleFiles(files);
  e.target.value = ""; // allow re-uploading same file
}

function isSupported(file) {
  if (supportedExtensions.value.length === 0) return true;
  const lower = file.name.toLowerCase();
  return supportedExtensions.value.some((ext) =>
    lower.endsWith(ext.toLowerCase()),
  );
}

function makeUploadId() {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `up-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
}

function handleFiles(files) {
  // Switch to library tab so user sees what's happening.
  activeTab.value = "library";

  for (const file of files) {
    const entry = {
      id: makeUploadId(),
      file,
      name: file.name,
      size: file.size,
      status: "uploading",
      progress: 0,
      message: "",
    };

    if (!isSupported(file)) {
      entry.status = "error";
      entry.message = `Unsupported type. Allowed: ${supportedExtensions.value.join(", ")}`;
      uploads.value.unshift(entry);
      continue;
    }

    uploads.value.unshift(entry);
    uploadOne(entry);
  }
}

function uploadOne(entry) {
  const fd = new FormData();
  fd.append("files", entry.file);

  const xhr = new XMLHttpRequest();
  xhr.open("POST", `${apiBase}/documents/upload`);

  xhr.upload.addEventListener("progress", (e) => {
    if (e.lengthComputable) {
      entry.progress = Math.min(99, Math.round((e.loaded / e.total) * 100));
    }
  });

  xhr.upload.addEventListener("load", () => {
    // All bytes sent — server is now parsing/embedding.
    if (entry.status === "uploading") {
      entry.status = "processing";
    }
  });

  xhr.addEventListener("load", async () => {
    if (xhr.status >= 200 && xhr.status < 300) {
      let body = null;
      try {
        body = JSON.parse(xhr.responseText);
      } catch {
        // ignore
      }
      const result = body?.results?.[0];
      if (result?.success) {
        entry.status = "success";
        entry.progress = 100;
        entry.message =
          result.chunk_count > 0
            ? `${result.chunk_count} chunks`
            : result.message || "uploaded";
        entry.documentId = result.document_id;
        await loadLibrary();
        if (props.autoAttachUploads && result.document_id) {
          emit("attach", {
            kind: "library",
            id: result.document_id,
            name: entry.name,
          });
        }
        // Auto-clear after a short delay.
        setTimeout(() => {
          uploads.value = uploads.value.filter((u) => u.id !== entry.id);
        }, 4000);
      } else {
        entry.status = "error";
        entry.message = result?.message || "Upload rejected";
      }
    } else {
      entry.status = "error";
      let msg = `HTTP ${xhr.status}`;
      try {
        const body = JSON.parse(xhr.responseText);
        if (body?.detail) msg = body.detail;
      } catch {
        // keep default
      }
      entry.message = msg;
    }
  });

  xhr.addEventListener("error", () => {
    entry.status = "error";
    entry.message = "Network error";
  });

  xhr.addEventListener("abort", () => {
    entry.status = "error";
    entry.message = "Cancelled";
  });

  xhr.send(fd);
}

function clearFinishedUploads() {
  uploads.value = uploads.value.filter(
    (u) => u.status === "uploading" || u.status === "processing",
  );
}

async function deleteLibraryDoc(doc) {
  if (!doc?.id) return;
  const confirmed = window.confirm(`Delete "${doc.filename}" from Library?`);
  if (!confirmed) return;

  deletingDocs.value = { ...deletingDocs.value, [doc.id]: true };
  libraryError.value = "";

  try {
    const res = await fetch(`${apiBase}/documents/${doc.id}`, {
      method: "DELETE",
    });
    if (!res.ok) {
      let message = `HTTP ${res.status}`;
      try {
        const body = await res.json();
        if (body?.detail) message = body.detail;
      } catch {
        // keep fallback
      }
      throw new Error(message);
    }

    if (isAttached("library", doc.id)) {
      emit("detach", {
        kind: "library",
        id: doc.id,
        name: doc.filename,
      });
    }

    libraryDocs.value = libraryDocs.value.filter((item) => item.id !== doc.id);
  } catch (err) {
    libraryError.value = `Failed to delete document: ${err.message}`;
  } finally {
    const next = { ...deletingDocs.value };
    delete next[doc.id];
    deletingDocs.value = next;
  }
}

// ── Drag and drop ─────────────────────────────────────────────────────────────
// dragenter/leave fire for child elements too, so we use a depth counter.

function onDragEnter(e) {
  if (!e.dataTransfer?.types?.includes("Files")) return;
  dragDepth.value++;
  dragActive.value = true;
}

function onDragLeave() {
  dragDepth.value = Math.max(0, dragDepth.value - 1);
  if (dragDepth.value === 0) dragActive.value = false;
}

function onDrop(e) {
  dragDepth.value = 0;
  dragActive.value = false;
  const files = Array.from(e.dataTransfer?.files || []);
  if (files.length > 0) handleFiles(files);
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────

onMounted(() => {
  loadLibrary();
  loadSupportedTypes();
});

watch(
  () => props.refreshToken,
  () => {
    loadLibrary();
  },
);
</script>

<style scoped>
.hidden {
  display: none;
}

.drag-fade-enter-active,
.drag-fade-leave-active {
  transition: opacity 0.15s ease;
}
.drag-fade-enter-from,
.drag-fade-leave-to {
  opacity: 0;
}

.think-dot-pulsing {
  animation: think-pulse 1.2s ease-in-out infinite;
}
@keyframes think-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}

.progress-indeterminate {
  position: relative;
  background: linear-gradient(
    90deg,
    rgba(255, 106, 0, 0.2) 0%,
    var(--accent) 50%,
    rgba(255, 106, 0, 0.2) 100%
  );
  background-size: 200% 100%;
  animation: progress-slide 1.5s linear infinite;
}
@keyframes progress-slide {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
