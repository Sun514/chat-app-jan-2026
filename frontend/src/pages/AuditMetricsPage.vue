<template>
  <div class="audit-metrics">
    <div class="backdrop">
      <span class="halo"></span>
      <span class="halo secondary"></span>
      <span class="beam"></span>
      <span class="noise"></span>
    </div>

    <section class="audit-actions reveal">
      <Button class="btn primary" type="button" @click="fetchSummary" :disabled="loading" :label="loading ? 'Refreshing...' : 'Refresh metrics'" />
    </section>
    <Message v-if="error" severity="error" class="audit-error reveal">{{ error }}</Message>

    <section class="stats-row reveal">
      <Card class="stat-card">
        <template #content>
        <p class="stat-label">Users total</p>
        <h3>{{ formatInteger(users.total_users) }}</h3>
        <p class="stat-note">Registered accounts in the app.</p>
        </template>
      </Card>
      <Card class="stat-card">
        <template #content>
        <p class="stat-label">Active users (30d)</p>
        <h3>{{ formatInteger(users.active_users_30d) }}</h3>
        <p class="stat-note">Users active within the past month.</p>
        </template>
      </Card>
      <Card class="stat-card">
        <template #content>
        <p class="stat-label">New users (7d)</p>
        <h3>{{ formatInteger(users.new_users_7d) }}</h3>
        <p class="stat-note">Recent signups for the last 7 days.</p>
        </template>
      </Card>
    </section>

    <main class="workspace reveal">
      <section class="audit-grid">
        <article class="panel model-usage-panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Model usage</p>
              <h2>Requests by model</h2>
            </div>
            <span class="chip">{{
              topModel
                ? `${topModel.model} · ${formatPercent(topModel.computed_share)}`
                : "--"
            }}</span>
          </div>
          <div class="metric-kv">
            <span>Requests</span>
            <strong>{{ formatInteger(modelRequests.total_requests) }}</strong>
          </div>
          <div v-if="normalizedModelItems.length > 0" class="model-usage-layout">
            <div class="model-chart-wrap">
              <div class="model-chart-canvas">
                <Chart
                  type="doughnut"
                  :data="modelChartData"
                  :options="doughnutOptions"
                  :canvasProps="{ role: 'img', 'aria-label': 'Model requests by model chart' }"
                />
              </div>
              <p class="model-chart-caption">
                Top model: <strong>{{ topModel?.model || "--" }}</strong>
              </p>
            </div>
          </div>
          <p v-else class="empty">No model request data available.</p>
        </article>

        <article class="panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Navigation usage</p>
              <h2>Visits by module</h2>
            </div>
            <span class="chip">{{
              topModule
                ? `${topModule.module} · ${formatPercent(topModule.computed_share)}`
                : "--"
            }}</span>
          </div>
          <div class="metric-kv">
            <span>Total visits</span>
            <strong>{{ formatInteger(moduleTraffic.total_visits) }}</strong>
          </div>
          <div v-if="normalizedModuleItems.length > 0" class="model-usage-layout">
            <div class="model-chart-wrap">
              <div class="model-chart-canvas">
                <Chart
                  type="doughnut"
                  :data="moduleChartData"
                  :options="doughnutOptions"
                  :canvasProps="{ role: 'img', 'aria-label': 'Visits by module chart' }"
                />
              </div>
              <p class="model-chart-caption">
                Top module: <strong>{{ topModule?.module || "--" }}</strong>
              </p>
            </div>
          </div>
          <p v-else class="empty">No module traffic data available.</p>
        </article>

        <article class="panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Workflow execution</p>
              <h2>Case workflows</h2>
            </div>
            <span class="chip">{{
              formatPercent(caseWorkflows.completion_rate_percent)
            }}</span>
          </div>
          <div class="metric-kv">
            <span>Started</span>
            <strong>{{ formatInteger(caseWorkflows.started) }}</strong>
          </div>
          <div class="metric-kv">
            <span>Completed</span>
            <strong>{{ formatInteger(caseWorkflows.completed) }}</strong>
          </div>
          <div class="metric-kv">
            <span>Completion rate</span>
            <strong>{{
              formatPercent(caseWorkflows.completion_rate_percent)
            }}</strong>
          </div>
        </article>

        <article class="panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Speech processing</p>
              <h2>Audio transcriptions</h2>
            </div>
            <span class="chip">{{
              formatInteger(audioTranscription.audio_files_transcribed)
            }}</span>
          </div>
          <div class="metric-kv">
            <span>Files transcribed</span>
            <strong>{{
              formatInteger(audioTranscription.audio_files_transcribed)
            }}</strong>
          </div>
          <div class="metric-kv">
            <span>Total duration</span>
            <strong>{{
              formatDuration(audioTranscription.total_duration_seconds)
            }}</strong>
          </div>
        </article>

        <article class="panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Platform reliability</p>
              <h2>API metrics</h2>
            </div>
            <span class="chip">{{ formatPercent(usage.success_rate_percent) }}</span>
          </div>
          <div class="metric-kv">
            <span>API requests (24h)</span>
            <strong>{{ formatInteger(usage.total_api_requests_24h) }}</strong>
          </div>
          <div class="metric-kv">
            <span>Success rate</span>
            <strong>{{ formatPercent(usage.success_rate_percent) }}</strong>
          </div>
          <div class="metric-kv">
            <span>Avg requests per user</span>
            <strong>{{ formatDecimal(usage.avg_requests_per_user) }}</strong>
          </div>
        </article>
      </section>

    </main>

    <footer class="footer">Red Pajama Labs · Audit metrics</footer>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import Button from "primevue/button";
import Card from "primevue/card";
import Chart from "primevue/chart";
import Message from "primevue/message";

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
const modulePalette = ["#1bb2a0", "#3f8efc", "#ff6a00", "#f4b400", "#9b6ef3", "#64748b"];
const legendLabelWithPercent = (value, total) => {
  const share = total > 0 ? (value / total) * 100 : 0;
  return `${share.toFixed(1)}%`;
};

const buildLegendLabels = (chart) => {
  const labels = Array.isArray(chart.data?.labels) ? chart.data.labels : [];
  const dataset = chart.data?.datasets?.[0] || {};
  const values = Array.isArray(dataset.data) ? dataset.data.map((item) => Number(item) || 0) : [];
  const total = values.reduce((sum, item) => sum + item, 0);
  const backgroundColors = Array.isArray(dataset.backgroundColor) ? dataset.backgroundColor : [];
  const borderColors = Array.isArray(dataset.borderColor) ? dataset.borderColor : [dataset.borderColor || "#ffffff"];
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
          const dataset = Array.isArray(context.dataset.data) ? context.dataset.data : [];
          const total = dataset.reduce((sum, item) => sum + (Number(item) || 0), 0);
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
    .sort((a, b) => (Number(b.request_count) || 0) - (Number(a.request_count) || 0))
    .map((item, index) => {
      const requestCount = Number(item.request_count) || 0;
      const fallbackShare = Number(item.share_percent) || 0;
      const computedShare = total > 0 ? (requestCount / total) * 100 : fallbackShare;
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
      const computedShare = total > 0 ? (visitCount / total) * 100 : fallbackShare;
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
