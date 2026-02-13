<template>
  <div class="collections">
    <div class="backdrop">
      <span class="halo"></span>
      <span class="halo secondary"></span>
      <span class="beam"></span>
      <span class="noise"></span>
    </div>

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

      <Card class="create-card reveal">
        <template #content>
          <form @submit.prevent="create">
            <p class="eyebrow">New folder</p>
            <div class="field">
              <label>Folder name</label>
              <InputText v-model="form.name" placeholder="Vendor contracts" required fluid />
            </div>
            <div class="field">
              <label>Description</label>
              <Textarea v-model="form.description" rows="3" autoResize placeholder="What belongs in this collection?" fluid />
            </div>
            <Button class="btn primary full" type="submit" label="Create folder" />
          </form>
        </template>
      </Card>
    </section>

    <section class="collection-grid reveal">
      <Card v-if="state.items.length === 0" class="empty-card">
        <template #content>
          No collections yet. Create a folder to start organizing uploads.
        </template>
      </Card>

      <Card v-for="collection in state.items" :key="collection.id" class="collection-card">
        <template #content>
        <div class="collection-header">
          <div>
            <h3>{{ collection.name }}</h3>
            <p class="case-desc">{{ collection.description || "No description yet." }}</p>
            <p class="collection-meta">Created {{ collection.createdAt }} · {{ collection.files.length }} files</p>
          </div>
          <Button class="btn ghost" severity="secondary" variant="outlined" label="Remove folder" @click="removeCollection(collection.id)" />
        </div>

        <div class="collection-upload">
          <div class="upload-picker compact">
            <FileUpload
              :key="inputKeys[collection.id] || 0"
              mode="basic"
              name="files[]"
              :multiple="true"
              :customUpload="true"
              :auto="false"
              chooseLabel="Browse files"
              :accept="acceptedFileTypes"
              @select="(event) => onCollectionFileChange(collection.id, event)"
            />
            <div>
              <p>{{ uploadSummary(collection.id) }}</p>
              <span>{{ uploadSizes(collection.id) || "PDF, DOCX, TXT, CSV, EML" }}</span>
            </div>
          </div>
          <Button
            class="btn primary"
            type="button"
            label="Add to folder"
            @click="addFiles(collection.id)"
            :disabled="!uploads[collection.id] || uploads[collection.id].length === 0"
          />
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
            <Button class="btn ghost" severity="secondary" variant="outlined" label="Remove" @click="removeFile(collection.id, file.id)" />
          </div>
        </div>
        </template>
      </Card>
    </section>

    <footer class="footer">Red Pajama Labs · Document collections</footer>
  </div>
</template>

<script setup>
import { computed, reactive } from "vue";
import Button from "primevue/button";
import Card from "primevue/card";
import FileUpload from "primevue/fileupload";
import InputText from "primevue/inputtext";
import Textarea from "primevue/textarea";
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

const acceptedFileTypes = ".pdf,.docx,.doc,.pptx,.ppt,.xlsx,.xls,.csv,.txt,.md,.html,.json,.xml,.rtf,.eml";

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
  uploads[collectionId] = Array.from(event.files || []);
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
