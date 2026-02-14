<template>
  <div
    class="relative min-h-screen flex flex-col gap-10 overflow-hidden py-28 px-[clamp(1.5rem,3vw,4rem)] pb-16"
  >
    <!-- Backdrop -->
    <div class="absolute inset-0 pointer-events-none overflow-hidden">
      <span
        class="absolute rounded-full w-130 h-130 bg-[radial-gradient(circle,rgba(255,106,0,0.35)_0%,transparent_60%)] -top-45 -left-30"
      ></span>
      <span
        class="absolute rounded-full w-115 h-115 bg-[radial-gradient(circle,rgba(27,178,160,0.3)_0%,transparent_65%)] top-10 -right-35"
      ></span>
      <span
        class="absolute w-300 h-100 bg-[linear-gradient(120deg,rgba(12,17,24,0.05),transparent)] -rotate-[8deg] top-[48%] -left-[20%]"
      ></span>
      <span
        class="absolute inset-0 opacity-50 bg-[linear-gradient(rgba(12,17,24,0.04)_1px,transparent_1px),linear-gradient(90deg,rgba(12,17,24,0.04)_1px,transparent_1px)] bg-size-[56px_56px]"
      ></span>
    </div>

    <section
      class="relative z-10 grid gap-8 grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]"
    >
      <div
        class="relative z-10 flex flex-col gap-6 rounded-4xl p-10 bg-white/92 border border-white/50 shadow-[0_24px_60px_rgba(11,17,25,0.18)] reveal"
      >
        <p
          class="uppercase tracking-[0.26em] text-xs font-semibold text-[#4b5664] m-0"
        >
          Collection hub
        </p>
        <h1
          class="font-[Playfair_Display] text-3xl md:text-4xl lg:text-[clamp(2.2rem,3.4vw,3.6rem)] font-semibold"
        >
          Build folders that investigations can reuse.
        </h1>
        <p class="text-[#4b5664] text-[1.05rem] m-0">
          Upload evidence into shared folders, then attach them to
          investigations when you need quick cross-case access.
        </p>
        <div class="grid gap-3 rounded-[18px] p-4 px-5 bg-black/6">
          <div class="flex flex-col gap-0.5">
            <span class="text-xs uppercase tracking-[0.18em] text-[#4b5664]"
              >Folders</span
            >
            <span class="font-semibold">{{ state.items.length }}</span>
          </div>
          <div class="flex flex-col gap-0.5">
            <span class="text-xs uppercase tracking-[0.18em] text-[#4b5664]"
              >Files stored</span
            >
            <span class="font-semibold">{{ totalFiles }}</span>
          </div>
        </div>
      </div>

      <Card
        class="relative z-10 grid gap-5 rounded-[28px] p-8 bg-white border border-black/8 shadow-[0_24px_60px_rgba(11,17,25,0.18)] reveal"
      >
        <template #content>
          <form @submit.prevent="create" class="grid gap-5">
            <p
              class="uppercase tracking-[0.26em] text-xs font-semibold text-[#4b5664] m-0"
            >
              New folder
            </p>
            <div class="flex flex-col gap-2">
              <label
                class="text-xs font-semibold text-[#4b5664] uppercase tracking-[0.16em]"
                >Folder name</label
              >
              <InputText
                v-model="form.name"
                placeholder="Vendor contracts"
                required
                fluid
              />
            </div>
            <div class="flex flex-col gap-2">
              <label
                class="text-xs font-semibold text-[#4b5664] uppercase tracking-[0.16em]"
                >Description</label
              >
              <Textarea
                v-model="form.description"
                rows="3"
                autoResize
                placeholder="What belongs in this collection?"
                fluid
              />
            </div>
            <Button class="w-full" type="submit" label="Create folder" />
          </form>
        </template>
      </Card>
    </section>

    <section class="relative z-10 grid gap-6 reveal">
      <Card
        v-if="state.items.length === 0"
        class="flex justify-between gap-4 rounded-[18px] border border-black/10 px-4 py-3.5 bg-white"
      >
        <template #content>
          No collections yet. Create a folder to start organizing uploads.
        </template>
      </Card>

      <Card
        v-for="collection in state.items"
        :key="collection.id"
        class="relative z-10 grid gap-6 rounded-3xl p-7 bg-white border border-black/8 shadow-[0_24px_60px_rgba(11,17,25,0.18)]"
      >
        <template #content>
          <div class="flex justify-between gap-4 items-start">
            <div>
              <h3>{{ collection.name }}</h3>
              <p class="mt-1.5 text-[#4b5664] max-w-[46ch]">
                {{ collection.description || "No description yet." }}
              </p>
              <p class="mt-1 text-[#4b5664] text-sm">
                Created {{ collection.createdAt }} ·
                {{ collection.files.length }} files
              </p>
            </div>
            <Button
              severity="secondary"
              variant="outlined"
              label="Remove folder"
              @click="removeCollection(collection.id)"
            />
          </div>

          <div class="flex flex-wrap my-4 gap-4 items-center justify-between">
            <div
              class="grid gap-3 rounded-[22px] px-5 py-4 border border-dashed border-black/20 bg-black/3"
            >
              <FileUpload
                :key="inputKeys[collection.id] || 0"
                mode="basic"
                name="files[]"
                :multiple="true"
                :customUpload="true"
                :auto="false"
                chooseLabel="Browse files"
                :accept="acceptedFileTypes"
                @select="
                  (event) => onCollectionFileChange(collection.id, event)
                "
              />
              <div>
                <p class="m-0 font-semibold">
                  {{ uploadSummary(collection.id) }}
                </p>
                <span class="text-[#4b5664] text-sm">{{
                  uploadSizes(collection.id) || "PDF, DOCX, TXT, CSV, EML"
                }}</span>
              </div>
            </div>
            <Button
              type="button"
              label="Add to folder"
              @click="addFiles(collection.id)"
              :disabled="
                !uploads[collection.id] || uploads[collection.id].length === 0
              "
            />
          </div>

          <div class="grid gap-3">
            <div
              v-if="collection.files.length === 0"
              class="text-[#4b5664] text-sm"
            >
              Upload files to populate this folder.
            </div>
            <div
              v-for="file in collection.files"
              :key="file.id"
              class="flex justify-between gap-4 rounded-2xl border border-black/8 px-4 py-3.5 bg-white"
            >
              <div>
                <h4 class="m-0 text-[0.95rem]">{{ file.name }}</h4>
                <p class="mt-1 text-[#4b5664] text-[0.78rem]">
                  {{ file.sizeLabel }} · {{ file.type }} · {{ file.uploadedAt }}
                </p>
              </div>
              <Button
                severity="secondary"
                variant="outlined"
                label="Remove"
                @click="removeFile(collection.id, file.id)"
              />
            </div>
          </div>
        </template>
      </Card>
    </section>

    <footer
      class="relative z-10 text-center text-sm uppercase tracking-[0.2em] text-[#4b5664]"
    >
      Red Pajama Labs · Document collections
    </footer>
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

const acceptedFileTypes =
  ".pdf,.docx,.doc,.pptx,.ppt,.xlsx,.xls,.csv,.txt,.md,.html,.json,.xml,.rtf,.eml";

const uploads = reactive({});
const inputKeys = reactive({});

const totalFiles = computed(() =>
  state.items.reduce((sum, collection) => sum + collection.files.length, 0),
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

<style scoped>
.reveal {
  opacity: 0;
  animation: glide 0.7s ease forwards;
}

.reveal:nth-of-type(1) {
  animation-delay: 0.05s;
}

.reveal:nth-of-type(2) {
  animation-delay: 0.12s;
}

.reveal:nth-of-type(3) {
  animation-delay: 0.2s;
}

.reveal:nth-of-type(4) {
  animation-delay: 0.28s;
}

@keyframes glide {
  from {
    opacity: 0;
    transform: translateY(18px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .reveal {
    opacity: 1;
    animation: none;
  }
}
</style>
