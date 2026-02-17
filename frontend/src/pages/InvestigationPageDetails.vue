<template>
  <PageShell :footer-text="investigation ? 'Red Pajama Labs · File intelligence console' : ''
    ">

    <section v-if="!investigation"
      class="relative z-10 grid gap-4 rounded-[28px] p-10 text-left bg-white/92 border border-white/50 shadow-[0_24px_60px_rgba(11,17,25,0.18)]">
      <h1>Investigation not found</h1>
      <p>Return to the case hub to create or select a case.</p>
      <Button label="Go to case hub" @click="router.push('/investigations')" />
    </section>

    <template v-else>
      <section class="relative z-10 grid gap-5 grid-cols-[repeat(auto-fit,minmax(220px,1fr))] reveal">
        <Card
          class="relative z-10 rounded-[26px] p-7 grid gap-1.5 bg-white border border-black/5 shadow-[0_24px_60px_rgba(11,17,25,0.18)]">
          <template #content>
            <p class="m-0 text-sm uppercase tracking-[0.18em] text-[#4b5664]">
              Evidence logged
            </p>
            <h3>{{ investigation.documents.length }}</h3>
            <p class="m-0 text-[#4b5664]">Files indexed for this case.</p>
          </template>
        </Card>
        <Card
          class="relative z-10 rounded-[26px] p-7 grid gap-1.5 bg-white border border-black/5 shadow-[0_24px_60px_rgba(11,17,25,0.18)]">
          <template #content>
            <p class="m-0 text-sm uppercase tracking-[0.18em] text-[#4b5664]">
              Last ingest
            </p>
            <h3>{{ investigation.lastUploadAt }}</h3>
            <p class="m-0 text-[#4b5664]">Latest upload activity.</p>
          </template>
        </Card>
        <Card
          class="relative z-10 rounded-[26px] p-7 grid gap-1.5 bg-white border border-black/5 shadow-[0_24px_60px_rgba(11,17,25,0.18)]">
          <template #content>
            <p class="m-0 text-sm uppercase tracking-[0.18em] text-[#4b5664]">
              Query focus
            </p>
            <h3>{{ investigation.lastQuery }}</h3>
            <p class="m-0 text-[#4b5664]">Most recent inquiry issued.</p>
          </template>
        </Card>
      </section>

      <main class="relative z-10 grid gap-8">
        <section
          class="relative z-10 flex flex-col gap-6 rounded-[28px] p-8 min-w-0 bg-white border border-black/5 shadow-[0_24px_60px_rgba(11,17,25,0.18)] reveal">
          <div class="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <p class="uppercase tracking-[0.26em] text-xs font-semibold text-[#4b5664] m-0">
                Document collections
              </p>
              <h2>Attach shared folders</h2>
            </div>
            <span
              class="px-4 py-1.5 rounded-full text-xs font-semibold uppercase tracking-[0.12em] text-right bg-black/12 text-[#4b5664]">Shared</span>
          </div>

          <div class="grid gap-7 grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
            <div class="grid gap-4">
              <p class="m-0 text-xs uppercase tracking-[0.16em] text-[#4b5664] font-semibold">
                Available folders
              </p>
              <div v-if="collectionsState.items.length === 0" class="text-[#4b5664] text-sm">
                No collections yet. Create one to share files across
                investigations.
              </div>
              <div v-else class="flex-col gap-3">
                <label v-for="collection in collectionsState.items" :key="collection.id"
                  class="flex gap-3 items-start rounded-2xl border border-black/8 px-4 py-3 bg-white cursor-pointer">
                  <Checkbox binary :modelValue="isCollectionSelected(collection.id)"
                    @update:modelValue="toggleCollection(collection.id)" />
                  <div>
                    <h4 class="m-0 text-[0.95rem]">{{ collection.name }}</h4>
                    <p class="mt-1 text-[#4b5664] text-[0.8rem]">
                      {{ collection.files.length }} files ·
                      {{ collection.description || "No description" }}
                    </p>
                  </div>
                </label>
              </div>
              <RouterLink
                class="inline-flex items-center justify-center rounded-full border border-[rgba(12,17,24,0.2)] bg-transparent px-6 py-3.5 text-[0.95rem] font-semibold text-[#0c1118] no-underline transition-transform duration-200 hover:-translate-y-px"
                to="/collections">
                Manage collections
              </RouterLink>
            </div>

            <div class="grid gap-4">
              <p class="m-0 text-xs uppercase tracking-[0.16em] text-[#4b5664] font-semibold">
                Included files
              </p>
              <div v-if="selectedCollectionFiles.length === 0" class="text-[#4b5664] text-sm">
                Select a folder to surface shared evidence here.
              </div>
              <div v-else class="grid gap-3">
                <div v-for="file in selectedCollectionFiles" :key="file.id"
                  class="flex justify-between gap-4 rounded-2xl border border-black/8 px-4 py-3.5 bg-white">
                  <div>
                    <h4 class="m-0 text-[0.95rem]">{{ file.name }}</h4>
                    <p class="mt-1 text-[#4b5664] text-[0.78rem]">
                      {{ file.collectionName }} · {{ file.sizeLabel }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section class="grid gap-8 grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
          <section
            class="relative z-10 flex flex-col gap-6 rounded-[28px] p-8 min-w-0 bg-white border border-black/5 shadow-[0_24px_60px_rgba(11,17,25,0.18)] reveal">
            <div class="flex items-center justify-between gap-4 flex-wrap">
              <div>
                <p class="uppercase tracking-[0.26em] text-xs font-semibold text-[#4b5664] m-0">
                  Evidence intake
                </p>
                <h2>Upload files</h2>
              </div>
              <span
                class="px-4 py-1.5 rounded-full text-xs font-semibold uppercase tracking-[0.12em] text-right bg-orange-500/15 text-[#c84b00]">Secure</span>
            </div>

            <div class="grid gap-3 rounded-[22px] p-5 border border-dashed border-black/20 bg-black/3">
              <FileUpload :key="uploadInputKey" name="files[]" :multiple="true" :customUpload="true"
                :showUploadButton="false" :showCancelButton="false" :auto="false" chooseLabel="Select evidence files"
                :accept="acceptedFileTypes" @select="onFileChange">
                <template #empty>
                  <p class="m-0 font-semibold">Drop or select files</p>
                </template>
              </FileUpload>
              <div>
                <p class="m-0 font-semibold">{{ uploadSummary }}</p>
                <span class="text-[#4b5664] text-sm">{{
                  uploadForm.files.length
                    ? uploadSizes
                    : "PDF, DOCX, TXT, CSV, EML"
                }}</span>
              </div>
            </div>

            <div class="grid gap-4 grid-cols-[repeat(auto-fit,minmax(180px,1fr))]">
              <div class="flex flex-col gap-2">
                <label class="text-xs font-semibold text-[#4b5664] uppercase tracking-[0.16em]">Chunk size</label>
                <InputNumber v-model="uploadForm.chunkSize" :min="100" :max="10000" fluid />
              </div>
              <div class="flex flex-col gap-2">
                <label class="text-xs font-semibold text-[#4b5664] uppercase tracking-[0.16em]">Chunk overlap</label>
                <InputNumber v-model="uploadForm.chunkOverlap" :min="0" :max="1000" fluid />
              </div>
            </div>

            <Button class="w-full" @click="uploadDocument" :disabled="loading.upload || uploadForm.files.length === 0"
              :label="loading.upload ? 'Uploading...' : 'Upload evidence'" />

            <div class="rounded-[18px] p-4 px-5 text-[#4b5664] text-sm bg-black/5">
              <strong class="text-[#0c1118]">Ingest tips:</strong> Keep chunks
              near 1000 tokens, and upload source documents before asking
              comparative questions.
            </div>

            <div class="rounded-[18px] p-5 text-[0.85rem] bg-[#0f1722] text-[#f7f9fb]" v-if="uploadResult">
              <h4>Upload response</h4>
              <pre class="mt-1.5 whitespace-pre-wrap">{{ uploadResult }}</pre>
            </div>
          </section>

          <section
            class="relative z-10 grid gap-6 rounded-[28px] p-8 bg-white/92 border border-white/45 shadow-[0_24px_60px_rgba(11,17,25,0.18)] reveal">
            <div class="flex items-center justify-between gap-4 flex-wrap">
              <div>
                <p class="uppercase tracking-[0.26em] text-xs font-semibold text-[#4b5664] m-0">
                  Ledger
                </p>
                <h2>Evidence timeline</h2>
              </div>
              <span
                class="px-4 py-1.5 rounded-full text-xs font-semibold uppercase tracking-[0.12em] text-right bg-black/12 text-[#4b5664]">Case
                activity</span>
            </div>

            <div class="grid gap-4 grid-cols-1">
              <div v-if="investigation.documents.length === 0"
                class="flex justify-between gap-4 rounded-[18px] border border-black/10 px-4 py-3.5 bg-white">
                Upload a file to start the investigation ledger.
              </div>
              <div v-for="file in investigation.documents" :key="file.id"
                class="flex justify-between gap-4 rounded-[18px] border border-black/10 px-4 py-3.5 bg-white">
                <div>
                  <h4 class="m-0 text-[0.95rem]">{{ file.name }}</h4>
                  <p class="mt-1 text-[#4b5664] text-[0.78rem]">
                    {{ file.timestamp }}
                  </p>
                </div>
                <div class="flex flex-col gap-1 items-end text-xs text-[#4b5664]">
                  <span>{{ file.size }}</span>
                  <span :class="[
                    'font-semibold uppercase tracking-[0.12em] text-[0.7rem]',
                    file.status.toLowerCase() === 'indexed'
                      ? 'text-[#0f7b67]'
                      : file.status.toLowerCase() === 'uploading'
                        ? 'text-[#b96b00]'
                        : file.status.toLowerCase() === 'failed'
                          ? 'text-[#c0392b]'
                          : '',
                  ]">{{ file.status }}</span>
                </div>
              </div>
            </div>
          </section>
        </section>

        <section
          class="relative z-10 flex flex-col gap-6 rounded-[28px] p-8 min-w-0 bg-white border border-black/5 shadow-[0_24px_60px_rgba(11,17,25,0.18)] w-full reveal">
          <div class="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <p class="uppercase tracking-[0.26em] text-xs font-semibold text-[#4b5664] m-0">
                Query
              </p>
              <h2>Interrogate the evidence</h2>
            </div>
            <span
              class="px-4 py-1.5 rounded-full text-xs font-semibold uppercase tracking-[0.12em] text-right bg-black/12 text-[#4b5664]">Live</span>
          </div>

          <div class="flex flex-col gap-2">
            <label class="text-xs font-semibold text-[#4b5664] uppercase tracking-[0.16em]">Investigation query</label>
            <Textarea v-model="searchForm.query" rows="4" autoResize
              placeholder="Which emails mention the contract renewal?" @keydown="onQueryKeydown" fluid />
          </div>

          <div class="grid gap-4 grid-cols-[repeat(auto-fit,minmax(180px,1fr))]">
            <div class="flex flex-col gap-2">
              <label class="text-xs font-semibold text-[#4b5664] uppercase tracking-[0.16em]">Limit</label>
              <InputNumber v-model="searchForm.limit" :min="1" :max="100" @keydown="onQueryKeydown" fluid />
            </div>
            <div class="flex flex-col gap-2">
              <label class="text-xs font-semibold text-[#4b5664] uppercase tracking-[0.16em]">Similarity
                threshold</label>
              <InputNumber v-model="searchForm.threshold" :min="0" :max="1" :step="0.05" :minFractionDigits="2"
                :maxFractionDigits="2" @keydown="onQueryKeydown" fluid />
            </div>
          </div>

          <div class="flex flex-wrap gap-3">
            <Button @click="runSearch" :disabled="loading.search || !searchForm.query"
              :label="loading.search ? 'Searching...' : 'Run query'" />
            <Button severity="secondary" variant="outlined" @click="clearSearch"
              :disabled="!searchForm.query && searchResults.length === 0" label="Clear" />
          </div>

          <div class="grid gap-4">
            <div v-if="searchResults.length === 0" class="text-[#4b5664] text-sm">
              No matches yet. Run a query to surface evidence.
            </div>
            <div v-for="item in searchResults" :key="item.chunk_id"
              class="rounded-[18px] border border-black/8 p-4 px-5 bg-white shadow-[0_10px_20px_rgba(12,17,24,0.06)]">
              <div class="flex justify-between items-center gap-4">
                <h4 class="m-0 text-base">{{ item.filename }}</h4>
                <span class="font-semibold text-sm text-[#c84b00]">{{
                  item.similarity.toFixed(3)
                }}</span>
              </div>
              <p class="mt-1.5 text-[#4b5664] leading-relaxed">
                {{ item.content }}
              </p>
            </div>
          </div>
        </section>
      </main>

    </template>
  </PageShell>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import Button from "primevue/button";
import Card from "primevue/card";
import Checkbox from "primevue/checkbox";
import FileUpload from "primevue/fileupload";
import InputNumber from "primevue/inputnumber";
import Textarea from "primevue/textarea";
import PageShell from "../components/PageShell.vue";
import {
  addDocument,
  getInvestigation,
  setLastQuery,
  updateInvestigation,
  toggleInvestigationCollection,
} from "../stores/investigations";
import { state as collectionsState } from "../stores/documentCollections";

const route = useRoute();
const router = useRouter();
const acceptedFileTypes =
  ".pdf,.docx,.doc,.pptx,.ppt,.xlsx,.xls,.csv,.txt,.md,.html,.json,.xml,.rtf,.eml";
const uploadInputKey = ref(0);

const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const loading = reactive({
  health: false,
  types: false,
  upload: false,
  search: false,
});

const health = ref(null);
const supportedTypes = ref([]);
const uploadResult = ref("");
const searchResults = ref([]);

const uploadForm = reactive({
  files: [],
  chunkSize: 1000,
  chunkOverlap: 200,
});

const searchForm = reactive({
  query: "",
  limit: 10,
  threshold: 0.3,
});

const investigation = ref(getInvestigation(route.params.id));

const isCollectionSelected = (collectionId) => {
  if (!investigation.value) return false;
  return (investigation.value.collectionIds || []).includes(collectionId);
};

const toggleCollection = (collectionId) => {
  if (!investigation.value) return;
  toggleInvestigationCollection(investigation.value.id, collectionId);
};

const selectedCollectionFiles = computed(() => {
  if (!investigation.value) return [];
  const selectedIds = investigation.value.collectionIds || [];
  const entries = collectionsState.items.filter((item) =>
    selectedIds.includes(item.id),
  );
  return entries.flatMap((collection) =>
    collection.files.map((file) => ({
      ...file,
      collectionName: collection.name,
    })),
  );
});

const formatBytes = (value) => {
  if (!value && value !== 0) return "";
  if (value < 1024) return `${value} B`;
  const kb = value / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
};

const onFileChange = (event) => {
  uploadForm.files = Array.from(event.files || []);
};

const uploadDocument = async () => {
  if (uploadForm.files.length === 0 || !investigation.value) return;
  loading.upload = true;
  uploadResult.value = "";

  const records = uploadForm.files.map((file) => ({
    id: Date.now() + Math.random(),
    name: file.name,
    size: formatBytes(file.size),
    status: "Uploading",
    timestamp: new Date().toLocaleString(),
  }));
  records.forEach((record) => addDocument(investigation.value.id, record));

  try {
    const formData = new FormData();
    uploadForm.files.forEach((file) => formData.append("files", file));
    formData.append("chunk_size", uploadForm.chunkSize);
    formData.append("chunk_overlap", uploadForm.chunkOverlap);

    const res = await fetch(`${apiBase}/documents/upload`, {
      method: "POST",
      body: formData,
    });
    const data = await res.json();
    uploadResult.value = JSON.stringify(data, null, 2);
    if (Array.isArray(data.results)) {
      data.results.forEach((result, index) => {
        if (records[index]) {
          records[index].status = result.success ? "Indexed" : "Failed";
        }
      });
    } else {
      records.forEach((record) => {
        record.status = "Indexed";
      });
    }
    updateInvestigation(investigation.value.id, {
      lastUploadAt: new Date().toLocaleTimeString(),
    });
    uploadForm.files = [];
    uploadInputKey.value += 1;
  } catch (error) {
    uploadResult.value = `Upload failed: ${error.message}`;
    records.forEach((record) => {
      record.status = "Failed";
    });
    updateInvestigation(investigation.value.id, {
      lastUploadAt: "Error",
    });
  } finally {
    loading.upload = false;
  }
};

const uploadSummary = computed(() => {
  if (uploadForm.files.length === 0) return "Drop or select files";
  if (uploadForm.files.length === 1) return uploadForm.files[0].name;
  return `${uploadForm.files.length} files selected`;
});

const uploadSizes = computed(() => {
  if (uploadForm.files.length === 0) return "";
  const total = uploadForm.files.reduce((sum, file) => sum + file.size, 0);
  return `${formatBytes(total)} total`;
});

const onQueryKeydown = (event) => {
  if (event.key !== "Enter" || event.shiftKey) return;
  event.preventDefault();
  if (!loading.search && searchForm.query) {
    runSearch();
  }
};

watch(
  () => route.params.id,
  (id) => {
    investigation.value = getInvestigation(id);
  },
  { immediate: true },
);

const runSearch = async () => {
  if (!investigation.value) return;
  loading.search = true;
  searchResults.value = [];
  try {
    const url = new URL(`${apiBase}/documents/search`);
    url.searchParams.set("q", searchForm.query);
    url.searchParams.set("limit", String(searchForm.limit));
    url.searchParams.set("threshold", String(searchForm.threshold));

    const res = await fetch(url.toString());
    const data = await res.json();
    searchResults.value = data.results || [];
    setLastQuery(investigation.value.id, searchForm.query || "None");
  } catch (error) {
    searchResults.value = [
      {
        chunk_id: "error",
        filename: "Request failed",
        content: error.message,
        similarity: 0,
      },
    ];
    setLastQuery(investigation.value.id, "Error");
  } finally {
    loading.search = false;
  }
};

const clearSearch = () => {
  searchForm.query = "";
  searchResults.value = [];
  if (investigation.value) {
    setLastQuery(investigation.value.id, "None");
  }
};
</script>
