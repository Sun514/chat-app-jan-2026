<template>
  <div class="collections">
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
          <p class="brand-title">Document collections</p>
          <p class="brand-subtitle">Organize evidence into shared folders.</p>
        </div>
      </div>
      <div class="top-actions">
        <RouterLink class="btn ghost" to="/investigations">Back to cases</RouterLink>
      </div>
    </header>

    <section class="hub-hero">
      <div class="hero-text reveal">
        <p class="eyebrow">Collection hub</p>
        <h1>Build folders that investigations can reuse.</h1>
        <p class="lead">
          Upload evidence into shared folders, then attach them to investigations when you need quick
          cross-case access.
        </p>
        <div class="meta-strip">
          <div class="meta-item">
            <span class="meta-label">Folders</span>
            <span class="meta-value">{{ state.items.length }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Files stored</span>
            <span class="meta-value">{{ totalFiles }}</span>
          </div>
        </div>
      </div>

      <form class="create-card reveal" @submit.prevent="create">
        <p class="eyebrow">New folder</p>
        <div class="field">
          <label>Folder name</label>
          <input type="text" v-model="form.name" placeholder="Vendor contracts" required />
        </div>
        <div class="field">
          <label>Description</label>
          <textarea v-model="form.description" rows="3" placeholder="What belongs in this collection?"></textarea>
        </div>
        <button class="btn primary full" type="submit">Create folder</button>
      </form>
    </section>

    <section class="collection-grid reveal">
      <div v-if="state.items.length === 0" class="empty-card">
        No collections yet. Create a folder to start organizing uploads.
      </div>

      <article v-for="collection in state.items" :key="collection.id" class="collection-card">
        <div class="collection-header">
          <div>
            <h3>{{ collection.name }}</h3>
            <p class="case-desc">{{ collection.description || "No description yet." }}</p>
            <p class="collection-meta">Created {{ collection.createdAt }} · {{ collection.files.length }} files</p>
          </div>
          <button class="btn ghost" @click="removeCollection(collection.id)">Remove folder</button>
        </div>

        <div class="collection-upload">
          <label class="dropzone compact">
            <input
              :key="inputKeys[collection.id] || 0"
              type="file"
              multiple
              @change="(event) => onCollectionFileChange(collection.id, event)"
              accept=".pdf,.docx,.doc,.pptx,.ppt,.xlsx,.xls,.csv,.txt,.md,.html,.json,.xml,.rtf,.eml"
            />
            <div>
              <p>{{ uploadSummary(collection.id) }}</p>
              <span>{{ uploadSizes(collection.id) || "PDF, DOCX, TXT, CSV, EML" }}</span>
            </div>
            <span class="btn ghost">Browse</span>
          </label>
          <button
            class="btn dark"
            type="button"
            @click="addFiles(collection.id)"
            :disabled="!uploads[collection.id] || uploads[collection.id].length === 0"
          >
            Add to folder
          </button>
        </div>

        <div class="collection-files">
          <div v-if="collection.files.length === 0" class="empty">
            Upload files to populate this folder.
          </div>
          <div v-for="file in collection.files" :key="file.id" class="collection-file">
            <div>
              <h4>{{ file.name }}</h4>
              <p>{{ file.sizeLabel }} · {{ file.type }} · {{ file.uploadedAt }}</p>
            </div>
            <button class="btn ghost" @click="removeFile(collection.id, file.id)">Remove</button>
          </div>
        </div>
      </article>
    </section>

    <footer class="footer">Red Pajama Labs · Document collections</footer>
  </div>
</template>

<script setup>
import { computed, reactive } from "vue";
import { RouterLink } from "vue-router";
import {
  state,
  createCollection,
  removeCollection as removeCollectionRecord,
  addFilesToCollection,
  removeFileFromCollection,
} from "../stores/documentCollections";

const form = reactive({
  name: "",
  description: "",
});

const uploads = reactive({});
const inputKeys = reactive({});

const totalFiles = computed(() =>
  state.items.reduce((sum, collection) => sum + collection.files.length, 0)
);

const formatBytes = (value) => {
  if (!value && value !== 0) return "";
  if (value < 1024) return `${value} B`;
  const kb = value / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
};

const create = () => {
  if (!form.name.trim()) return;
  createCollection({
    name: form.name.trim(),
    description: form.description.trim(),
  });
  form.name = "";
  form.description = "";
};

const onCollectionFileChange = (collectionId, event) => {
  uploads[collectionId] = Array.from(event.target.files || []);
};

const uploadSummary = (collectionId) => {
  const files = uploads[collectionId] || [];
  if (files.length === 0) return "Drop or select files";
  if (files.length === 1) return files[0].name;
  return `${files.length} files selected`;
};

const uploadSizes = (collectionId) => {
  const files = uploads[collectionId] || [];
  if (files.length === 0) return "";
  const total = files.reduce((sum, file) => sum + file.size, 0);
  return `${formatBytes(total)} total`;
};

const addFiles = (collectionId) => {
  const files = uploads[collectionId];
  if (!files || files.length === 0) return;
  addFilesToCollection(collectionId, files);
  uploads[collectionId] = [];
  inputKeys[collectionId] = (inputKeys[collectionId] || 0) + 1;
};

const removeFile = (collectionId, fileId) => {
  removeFileFromCollection(collectionId, fileId);
};

const removeCollection = (collectionId) => {
  removeCollectionRecord(collectionId);
};
</script>
