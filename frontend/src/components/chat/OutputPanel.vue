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
          <span class="text-[0.65rem] uppercase tracking-[0.08em] text-(--muted)">
            {{ item.view || "json" }}
          </span>
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
import { formatBytes, formatDuration } from "../../utils/format.js";

defineProps({
  items: { type: Array, default: () => [] },
});
defineEmits(["clear"]);

const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

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
</script>

<style scoped>
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
