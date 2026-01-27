<template>
  <div class="investigation">
    <div class="backdrop">
      <span class="halo"></span>
      <span class="halo secondary"></span>
      <span class="beam"></span>
      <span class="noise"></span>
    </div>

    <header class="topbar">
      <div class="brand">
        <div class="brand-mark">RPL</div>
        <div>
          <p class="brand-title">{{ investigation?.name || "Investigation" }}</p>
          <p class="brand-subtitle">{{ investigation?.description || "Evidence intelligence workspace" }}</p>
        </div>
      </div>
      <div class="top-actions">
        <RouterLink class="btn ghost" to="/collections">Document collections</RouterLink>
        <RouterLink class="btn ghost" to="/investigations">Back to cases</RouterLink>
      </div>
    </header>

    <section v-if="!investigation" class="missing-case">
      <h1>Investigation not found</h1>
      <p>Return to the case hub to create or select a case.</p>
      <RouterLink class="btn dark" to="/investigations">Go to case hub</RouterLink>
    </section>

    <template v-else>
      <section class="stats-row reveal">
        <div class="stat-card">
          <p class="stat-label">Evidence logged</p>
          <h3>{{ investigation.documents.length }}</h3>
          <p class="stat-note">Files indexed for this case.</p>
        </div>
        <div class="stat-card">
          <p class="stat-label">Last ingest</p>
          <h3>{{ investigation.lastUploadAt }}</h3>
          <p class="stat-note">Latest upload activity.</p>
        </div>
        <div class="stat-card">
          <p class="stat-label">Query focus</p>
          <h3>{{ investigation.lastQuery }}</h3>
          <p class="stat-note">Most recent inquiry issued.</p>
        </div>
      </section>

      <main class="workspace">
        <section class="panel collection-panel reveal">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Document collections</p>
              <h2>Attach shared folders</h2>
            </div>
            <span class="chip muted">Shared</span>
          </div>

          <div class="collection-panel-grid">
            <div class="collection-picker">
              <p class="collection-label">Available folders</p>
              <div v-if="collectionsState.items.length === 0" class="empty">
                No collections yet. Create one to share files across investigations.
              </div>
              <div v-else class="collection-list">
                <label v-for="collection in collectionsState.items" :key="collection.id" class="collection-option">
                  <input
                    type="checkbox"
                    :checked="isCollectionSelected(collection.id)"
                    @change="toggleCollection(collection.id)"
                  />
                  <div>
                    <h4>{{ collection.name }}</h4>
                    <p>{{ collection.files.length }} files · {{ collection.description || "No description" }}</p>
                  </div>
                </label>
              </div>
              <RouterLink class="btn ghost" to="/collections">Manage collections</RouterLink>
            </div>

            <div class="collection-preview">
              <p class="collection-label">Included files</p>
              <div v-if="selectedCollectionFiles.length === 0" class="empty">
                Select a folder to surface shared evidence here.
              </div>
              <div v-else class="collection-files">
                <div v-for="file in selectedCollectionFiles" :key="file.id" class="collection-file">
                  <div>
                    <h4>{{ file.name }}</h4>
                    <p>{{ file.collectionName }} · {{ file.sizeLabel }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section class="evidence-row">
          <section class="panel intake reveal">
            <div class="panel-head">
              <div>
                <p class="eyebrow">Evidence intake</p>
                <h2>Upload files</h2>
              </div>
              <span class="chip">Secure</span>
            </div>

            <label class="dropzone">
              <input
                type="file"
                multiple
                @change="onFileChange"
                accept=".pdf,.docx,.doc,.pptx,.ppt,.xlsx,.xls,.csv,.txt,.md,.html,.json,.xml,.rtf,.eml"
              />
              <div>
                <p>{{ uploadSummary }}</p>
                <span>{{ uploadForm.files.length ? uploadSizes : "PDF, DOCX, TXT, CSV, EML" }}</span>
              </div>
              <span class="btn ghost">Browse</span>
            </label>

            <div class="field-grid">
              <div class="field">
                <label>Chunk size</label>
                <input type="number" v-model.number="uploadForm.chunkSize" min="100" max="10000" />
              </div>
              <div class="field">
                <label>Chunk overlap</label>
                <input type="number" v-model.number="uploadForm.chunkOverlap" min="0" max="1000" />
              </div>
            </div>

            <button class="btn primary full" @click="uploadDocument" :disabled="loading.upload || uploadForm.files.length === 0">
              {{ loading.upload ? "Uploading..." : "Upload evidence" }}
            </button>

            <div class="hint">
              <strong>Ingest tips:</strong> Keep chunks near 1000 tokens, and upload source documents before asking
              comparative questions.
            </div>

            <div class="upload-status" v-if="uploadResult">
              <h4>Upload response</h4>
              <pre>{{ uploadResult }}</pre>
            </div>
          </section>

          <section class="ledger reveal">
            <div class="panel-head">
              <div>
                <p class="eyebrow">Ledger</p>
                <h2>Evidence timeline</h2>
              </div>
              <span class="chip muted">Case activity</span>
            </div>

            <div class="ledger-grid">
              <div v-if="investigation.documents.length === 0" class="empty-card">
                Upload a file to start the investigation ledger.
              </div>
              <div v-for="file in investigation.documents" :key="file.id" class="ledger-card">
                <div>
                  <h4>{{ file.name }}</h4>
                  <p>{{ file.timestamp }}</p>
                </div>
                <div class="ledger-meta">
                  <span>{{ file.size }}</span>
                  <span :class="['status', file.status.toLowerCase()]">{{ file.status }}</span>
                </div>
              </div>
            </div>
          </section>
        </section>

        <section class="panel inquiry full-width reveal">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Query</p>
              <h2>Interrogate the evidence</h2>
            </div>
            <span class="chip muted">Live</span>
          </div>

          <div class="field">
            <label>Investigation query</label>
            <textarea
              v-model="searchForm.query"
              rows="4"
              placeholder="Which emails mention the contract renewal?"
              @keydown="onQueryKeydown"
            ></textarea>
          </div>

          <div class="field-grid">
            <div class="field">
              <label>Limit</label>
              <input type="number" v-model.number="searchForm.limit" min="1" max="100" @keydown="onQueryKeydown" />
            </div>
            <div class="field">
              <label>Similarity threshold</label>
              <input type="number" v-model.number="searchForm.threshold" min="0" max="1" step="0.05" @keydown="onQueryKeydown" />
            </div>
          </div>

          <div class="inline-actions">
            <button class="btn dark" @click="runSearch" :disabled="loading.search || !searchForm.query">
              {{ loading.search ? "Searching..." : "Run query" }}
            </button>
            <button class="btn ghost" @click="clearSearch" :disabled="!searchForm.query && searchResults.length === 0">
              Clear
            </button>
          </div>

          <div class="results">
            <div v-if="searchResults.length === 0" class="empty">No matches yet. Run a query to surface evidence.</div>
            <div v-for="item in searchResults" :key="item.chunk_id" class="result-card">
              <div class="result-head">
                <h4>{{ item.filename }}</h4>
                <span>{{ item.similarity.toFixed(3) }}</span>
              </div>
              <p>{{ item.content }}</p>
            </div>
          </div>
        </section>
      </main>

      <footer class="footer">Red Pajama Labs · File intelligence console</footer>
    </template>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { RouterLink } from "vue-router";
import {
  addDocument,
  getInvestigation,
  setLastQuery,
  updateInvestigation,
  toggleInvestigationCollection,
} from "../stores/investigations";
import { state as collectionsState } from "../stores/documentCollections";

const route = useRoute();

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
  const entries = collectionsState.items.filter((item) => selectedIds.includes(item.id));
  return entries.flatMap((collection) =>
    collection.files.map((file) => ({
      ...file,
      collectionName: collection.name,
    }))
  );
});

const healthSummary = computed(() => {
  if (!health.value) return "Not checked";
  if (health.value.database?.startsWith("unhealthy")) return "Degraded";
  return health.value.status || "Unknown";
});

const formatBytes = (value) => {
  if (!value && value !== 0) return "";
  if (value < 1024) return `${value} B`;
  const kb = value / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
};

const onFileChange = (event) => {
  uploadForm.files = Array.from(event.target.files || []);
};

const pingHealth = async () => {
  loading.health = true;
  try {
    const res = await fetch(`${apiBase}/health`);
    health.value = await res.json();
  } catch (error) {
    health.value = { status: "error", database: error.message };
  } finally {
    loading.health = false;
  }
};

const fetchSupportedTypes = async () => {
  loading.types = true;
  try {
    const res = await fetch(`${apiBase}/documents/supported-types`);
    const data = await res.json();
    supportedTypes.value = data.extensions || [];
  } catch (error) {
    supportedTypes.value = [`Error: ${error.message}`];
  } finally {
    loading.types = false;
  }
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
  { immediate: true }
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
