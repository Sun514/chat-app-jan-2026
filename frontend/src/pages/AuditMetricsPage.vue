<template>
  <PageShell footer-text="Red Pajama Labs · Audit metrics">

    <Message v-if="error" severity="error"
      class="relative z-10 m-0 rounded-xl border border-red-700/20 text-[#9f2d1f] bg-red-700/10 text-sm px-4 py-3 reveal">
      {{ error }}</Message>

    <section class="relative z-10 grid gap-5 grid-cols-[repeat(auto-fit,minmax(220px,1fr))] reveal">
      <Card
        class="relative z-10 rounded-[26px] p-7 grid gap-1.5 bg-white border border-black/5 shadow-[0_24px_60px_rgba(11,17,25,0.18)]">
        <template #content>
          <p class="m-0 text-md font-bold uppercase tracking-[0.18em] text-[#4b5664]">
            Users total
          </p>
          <h3>{{ formatInteger(users.total_users) }}</h3>
          <p class="m-0 text-[#4b5664]">Registered accounts in the app.</p>
        </template>
      </Card>
      <Card
        class="relative z-10 rounded-[26px] p-7 grid gap-1.5 bg-white border border-black/5 shadow-[0_24px_60px_rgba(11,17,25,0.18)]">
        <template #content>
          <p class="m-0 text-md font-bold uppercase tracking-[0.18em] text-[#4b5664]">
            Active users (30d)
          </p>
          <h3>{{ formatInteger(users.active_users_30d) }}</h3>
          <p class="m-0 text-[#4b5664]">Users active within the past month.</p>
        </template>
      </Card>
      <Card
        class="relative z-10 rounded-[26px] p-7 grid gap-1.5 bg-white border border-black/5 shadow-[0_24px_60px_rgba(11,17,25,0.18)]">
        <template #content>
          <p class="m-0 text-md font-bold uppercase tracking-[0.18em] text-[#4b5664]">
            New users (7d)
          </p>
          <h3>{{ formatInteger(users.new_users_7d) }}</h3>
          <p class="m-0 text-[#4b5664]">Recent signups for the last 7 days.</p>
        </template>
      </Card>
    </section>

    <main class="relative z-10 grid gap-8 reveal">
      <section class="grid gap-6 grid-cols-[repeat(auto-fit,minmax(min(420px,100%),1fr))]">
        <article
          class="relative z-10 flex flex-col gap-6 rounded-[28px] p-8 min-w-0 bg-white/92 border border-black/5 shadow-[0_24px_60px_rgba(11,17,25,0.18)]">
          <div class="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <p class="uppercase tracking-[0.26em] text-md font-semibold text-[#4b5664] m-0">
                Model usage
              </p>
            </div>
            <span
              class="px-4 py-1.5 rounded-full text-xs font-semibold uppercase tracking-[0.12em] text-right bg-orange-500/15 text-[#c84b00]">{{
                topModel
                  ? `${topModel.model} · ${formatPercent(topModel.computed_share)}`
                  : "--"
              }}</span>
          </div>
          <div
            class="flex items-center justify-between gap-4 flex-wrap rounded-2xl border border-black/5 bg-black/2 px-4 py-3">
            <span class="text-[#4b5664] text-sm">Requests</span>
            <strong>{{ formatInteger(modelRequests.total_requests) }}</strong>
          </div>
          <div v-if="normalizedModelItems.length > 0" class="flex justify-center gap-5 items-start">
            <div class="grid justify-items-center content-start gap-3">
              <div class="w-130 h-130 max-w-full [&_canvas]:w-full! [&_canvas]:h-full!">
                <Chart type="doughnut" :data="modelChartData" :options="doughnutOptions" :canvasProps="{
                  role: 'img',
                  'aria-label': 'Model requests by model chart',
                }" />
              </div>
              <p class="m-0 text-[#4b5664] text-xs uppercase tracking-[0.12em]">
                Top model: <strong>{{ topModel?.model || "--" }}</strong>
              </p>
            </div>
          </div>
          <p v-else class="text-[#4b5664] text-sm">
            No model request data available.
          </p>
        </article>

        <article
          class="relative z-10 flex flex-col gap-6 rounded-[28px] p-8 min-w-0 bg-white/92 border border-black/5 shadow-[0_24px_60px_rgba(11,17,25,0.18)]">
          <div class="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <p class="uppercase tracking-[0.26em] text-md font-semibold text-[#4b5664] m-0">
                Module usage
              </p>
            </div>
            <span
              class="px-4 py-1.5 rounded-full text-xs font-semibold uppercase tracking-[0.12em] text-right bg-orange-500/15 text-[#c84b00]">{{
                topModule
                  ? `${topModule.module} · ${formatPercent(topModule.computed_share)}`
                  : "--"
              }}</span>
          </div>
          <div
            class="flex items-center justify-between gap-4 flex-wrap rounded-2xl border border-black/5 bg-black/2 px-4 py-3">
            <span class="text-[#4b5664] text-sm">Total visits</span>
            <strong>{{ formatInteger(moduleTraffic.total_visits) }}</strong>
          </div>
          <div v-if="normalizedModuleItems.length > 0" class="flex justify-center gap-5 items-start">
            <div class="grid justify-items-center content-start gap-3">
              <div class="w-130 h-130 max-w-full [&_canvas]:w-full! [&_canvas]:h-full!">
                <Chart type="doughnut" :data="moduleChartData" :options="doughnutOptions" :canvasProps="{
                  role: 'img',
                  'aria-label': 'Visits by module chart',
                }" />
              </div>
              <p class="m-0 text-[#4b5664] text-xs uppercase tracking-[0.12em]">
                Top module: <strong>{{ topModule?.module || "--" }}</strong>
              </p>
            </div>
          </div>
          <p v-else class="text-[#4b5664] text-sm">
            No module traffic data available.
          </p>
        </article>

        <article
          class="relative z-10 flex flex-col gap-6 rounded-[28px] p-8 min-w-0 bg-white/92 border border-black/5 shadow-[0_24px_60px_rgba(11,17,25,0.18)]">
          <div class="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <p class="uppercase tracking-[0.26em] text-md font-semibold text-[#4b5664] m-0">
                Case workflows
              </p>
            </div>
          </div>
          <div
            class="flex items-center justify-between gap-4 flex-wrap rounded-2xl border border-black/5 bg-black/2 px-4 py-3">
            <span class="text-[#4b5664] text-sm">Started</span>
            <strong>{{ formatInteger(caseWorkflows.started) }}</strong>
          </div>
          <div
            class="flex items-center justify-between gap-4 flex-wrap rounded-2xl border border-black/5 bg-black/2 px-4 py-3">
            <span class="text-[#4b5664] text-sm">Completed</span>
            <strong>{{ formatInteger(caseWorkflows.completed) }}</strong>
          </div>
          <div
            class="flex items-center justify-between gap-4 flex-wrap rounded-2xl border border-black/5 bg-black/2 px-4 py-3">
            <span class="text-[#4b5664] text-sm">Completion rate</span>
            <strong>{{
              formatPercent(caseWorkflows.completion_rate_percent)
            }}</strong>
          </div>
        </article>

        <article
          class="relative z-10 flex flex-col gap-6 rounded-[28px] p-8 min-w-0 bg-white/92 border border-black/5 shadow-[0_24px_60px_rgba(11,17,25,0.18)]">
          <div class="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <p class="uppercase tracking-[0.26em] text-md font-semibold text-[#4b5664] m-0">
                Audio transcriptions
              </p>
            </div>
          </div>
          <div
            class="flex items-center justify-between gap-4 flex-wrap rounded-2xl border border-black/5 bg-black/2 px-4 py-3">
            <span class="text-[#4b5664] text-sm">Files transcribed</span>
            <strong>{{
              formatInteger(audioTranscription.audio_files_transcribed)
            }}</strong>
          </div>
          <div
            class="flex items-center justify-between gap-4 flex-wrap rounded-2xl border border-black/5 bg-black/2 px-4 py-3">
            <span class="text-[#4b5664] text-sm">Total duration</span>
            <strong>{{
              formatDuration(audioTranscription.total_duration_seconds)
            }}</strong>
          </div>
        </article>

        <article
          class="relative z-10 flex flex-col gap-6 rounded-[28px] p-8 min-w-0 bg-white/92 border border-black/5 shadow-[0_24px_60px_rgba(11,17,25,0.18)]">
          <div class="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <p class="uppercase tracking-[0.26em] text-md font-semibold text-[#4b5664] m-0">
                API metrics
              </p>
            </div>
          </div>
          <div
            class="flex items-center justify-between gap-4 flex-wrap rounded-2xl border border-black/5 bg-black/2 px-4 py-3">
            <span class="text-[#4b5664] text-sm">API requests (24h)</span>
            <strong>{{ formatInteger(usage.total_api_requests_24h) }}</strong>
          </div>
          <div
            class="flex items-center justify-between gap-4 flex-wrap rounded-2xl border border-black/5 bg-black/2 px-4 py-3">
            <span class="text-[#4b5664] text-sm">Success rate</span>
            <strong>{{ formatPercent(usage.success_rate_percent) }}</strong>
          </div>
          <div
            class="flex items-center justify-between gap-4 flex-wrap rounded-2xl border border-black/5 bg-black/2 px-4 py-3">
            <span class="text-[#4b5664] text-sm">Avg requests per user</span>
            <strong>{{ formatDecimal(usage.avg_requests_per_user) }}</strong>
          </div>
        </article>
      </section>
    </main>

  </PageShell>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import Button from "primevue/button";
import Card from "primevue/card";
import Chart from "primevue/chart";
import Message from "primevue/message";
import PageShell from "../components/PageShell.vue";

const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const loading = ref(false);
const error = ref("");
const summary = ref(null);

const users = computed(() => summary.value?.users || {});
const modelRequests = computed(() => summary.value?.model_requests || {});
const moduleTraffic = computed(() => summary.value?.module_traffic || {});
const audioTranscription = computed(
  () => summary.value?.audio_transcription || {},
);
const caseWorkflows = computed(() => summary.value?.case_workflows || {});
const moduleUsage = computed(() => summary.value?.most_used_module || {});
const usage = computed(() => summary.value?.usage || {});
const modelPalette = [
  "#ff6a00",
  "#1bb2a0",
  "#3f8efc",
  "#f4b400",
  "#e66f00",
  "#64748b",
];
const modulePalette = [
  "#1bb2a0",
  "#3f8efc",
  "#ff6a00",
  "#f4b400",
  "#9b6ef3",
  "#64748b",
];
const legendLabelWithPercent = (value, total) => {
  const share = total > 0 ? (value / total) * 100 : 0;
  return `${share.toFixed(1)}%`;
};

const buildLegendLabels = (chart) => {
  const labels = Array.isArray(chart.data?.labels) ? chart.data.labels : [];
  const dataset = chart.data?.datasets?.[0] || {};
  const values = Array.isArray(dataset.data)
    ? dataset.data.map((item) => Number(item) || 0)
    : [];
  const total = values.reduce((sum, item) => sum + item, 0);
  const backgroundColors = Array.isArray(dataset.backgroundColor)
    ? dataset.backgroundColor
    : [];
  const borderColors = Array.isArray(dataset.borderColor)
    ? dataset.borderColor
    : [dataset.borderColor || "#ffffff"];
  const borderWidth = Number(dataset.borderWidth) || 1;

  return labels.map((label, index) => {
    const numericValue = values[index] || 0;
    return {
      text: `${label} (${legendLabelWithPercent(numericValue, total)})`,
      fillStyle: backgroundColors[index] || backgroundColors[0] || "#cbd5e1",
      strokeStyle: borderColors[index] || borderColors[0] || "#ffffff",
      lineWidth: borderWidth,
      hidden: !chart.getDataVisibility(index),
      index,
      pointStyle: "circle",
    };
  });
};

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: "62%",
  plugins: {
    legend: {
      display: true,
      position: "bottom",
      labels: {
        color: "#4b5664",
        usePointStyle: true,
        pointStyle: "circle",
        boxWidth: 10,
        boxHeight: 10,
        padding: 14,
        generateLabels: buildLegendLabels,
        font: {
          size: 12,
          family: "Space Grotesk",
        },
      },
    },
    tooltip: {
      callbacks: {
        label(context) {
          const value = Number(context.parsed) || 0;
          const dataset = Array.isArray(context.dataset.data)
            ? context.dataset.data
            : [];
          const total = dataset.reduce(
            (sum, item) => sum + (Number(item) || 0),
            0,
          );
          const share = total > 0 ? ((value / total) * 100).toFixed(1) : "0.0";
          return `${context.label}: ${new Intl.NumberFormat().format(value)} (${share}%)`;
        },
      },
    },
  },
};

const normalizedModelItems = computed(() => {
  const items = Array.isArray(modelRequests.value?.items)
    ? [...modelRequests.value.items]
    : [];
  if (items.length === 0) return [];

  const totalFromApi = Number(modelRequests.value?.total_requests) || 0;
  const totalFromItems = items.reduce(
    (sum, item) => sum + (Number(item.request_count) || 0),
    0,
  );
  const total = totalFromApi > 0 ? totalFromApi : totalFromItems;

  return items
    .sort(
      (a, b) => (Number(b.request_count) || 0) - (Number(a.request_count) || 0),
    )
    .map((item, index) => {
      const requestCount = Number(item.request_count) || 0;
      const fallbackShare = Number(item.share_percent) || 0;
      const computedShare =
        total > 0 ? (requestCount / total) * 100 : fallbackShare;
      return {
        ...item,
        request_count: requestCount,
        computed_share: computedShare,
        color: modelPalette[index % modelPalette.length],
      };
    });
});

const topModel = computed(() => normalizedModelItems.value[0] || null);

const normalizedModuleItems = computed(() => {
  const items = Array.isArray(moduleTraffic.value?.items)
    ? [...moduleTraffic.value.items]
    : [];

  if (items.length === 0 && moduleUsage.value?.module) {
    return [
      {
        module: moduleUsage.value.module,
        visit_count: Number(moduleUsage.value.visit_count) || 0,
        computed_share: Number(moduleUsage.value.usage_percent) || 100,
        color: modulePalette[0],
      },
    ];
  }

  if (items.length === 0) return [];

  const totalFromApi = Number(moduleTraffic.value?.total_visits) || 0;
  const totalFromItems = items.reduce(
    (sum, item) => sum + (Number(item.visit_count) || 0),
    0,
  );
  const total = totalFromApi > 0 ? totalFromApi : totalFromItems;

  return items
    .sort((a, b) => (Number(b.visit_count) || 0) - (Number(a.visit_count) || 0))
    .map((item, index) => {
      const visitCount = Number(item.visit_count) || 0;
      const fallbackShare = Number(item.share_percent) || 0;
      const computedShare =
        total > 0 ? (visitCount / total) * 100 : fallbackShare;
      return {
        ...item,
        visit_count: visitCount,
        computed_share: computedShare,
        color: modulePalette[index % modulePalette.length],
      };
    });
});

const topModule = computed(() => normalizedModuleItems.value[0] || null);

const modelChartData = computed(() => ({
  labels: normalizedModelItems.value.map((item) => item.model),
  datasets: [
    {
      data: normalizedModelItems.value.map((item) => item.request_count),
      backgroundColor: normalizedModelItems.value.map((item) => item.color),
      borderColor: "rgba(255, 255, 255, 0.92)",
      borderWidth: 2,
      hoverOffset: 6,
    },
  ],
}));

const moduleChartData = computed(() => ({
  labels: normalizedModuleItems.value.map((item) => item.module),
  datasets: [
    {
      data: normalizedModuleItems.value.map((item) => item.visit_count),
      backgroundColor: normalizedModuleItems.value.map((item) => item.color),
      borderColor: "rgba(255, 255, 255, 0.92)",
      borderWidth: 2,
      hoverOffset: 6,
    },
  ],
}));

const formatInteger = (value) => {
  if (typeof value !== "number") return "--";
  return new Intl.NumberFormat().format(value);
};

const formatDecimal = (value) => {
  if (typeof value !== "number") return "--";
  return value.toFixed(1);
};

const formatPercent = (value) => {
  if (typeof value !== "number") return "--";
  return `${value.toFixed(1)}%`;
};

const formatDuration = (value) => {
  if (typeof value !== "number") return "--";
  const totalSeconds = Math.max(0, Math.floor(value));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
};

const fetchSummary = async () => {
  loading.value = true;
  error.value = "";
  try {
    const res = await fetch(`${apiBase}/audit/summary`);
    if (!res.ok) {
      throw new Error(`Audit API error (${res.status})`);
    }
    summary.value = await res.json();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Unable to load metrics";
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchSummary();
});
</script>
