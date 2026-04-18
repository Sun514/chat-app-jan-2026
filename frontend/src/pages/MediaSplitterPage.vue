<template>
  <PageShell footer-text="Red Pajama Labs · Media tools">
    <div class="reveal mx-auto w-full max-w-3xl flex flex-col gap-8">
      <!-- Upload & Split Card -->
      <div
        class="rounded-3xl border border-black/10 bg-white/90 backdrop-blur-md shadow-[0_24px_60px_rgba(11,17,25,0.12)] p-8">
        <h2 class="text-xl font-semibold mb-1">Split media or extract audio</h2>
        <p class="text-sm text-[#4b5664] mb-6">
          Upload an audio or video file to split it into smaller parts by duration
          or file size, or extract audio to your preferred format.
        </p>

        <!-- File upload -->
        <div class="mb-5">
          <label class="block text-sm font-medium mb-2">File</label>
          <FileUpload :key="uploadKey" mode="basic" name="file" :auto="false" :customUpload="true"
            chooseLabel="Choose file" :accept="acceptedTypes" @select="onFileSelect" />
          <p v-if="selectedFile" class="mt-2 text-sm text-[#4b5664]">
            {{ selectedFile.name }}
            <span class="text-xs">({{ formatBytes(selectedFile.size) }})</span>
          </p>
        </div>

        <!-- Mode: Split or Extract Audio -->
        <div class="mb-5">
          <label class="block text-sm font-medium mb-2">Action</label>
          <SelectButton v-model="actionMode" :options="actionOptions" optionLabel="label" optionValue="value"
            :allowEmpty="false" />
        </div>

        <!-- Split options (only when splitting) -->
        <template v-if="actionMode === 'split'">
          <!-- Split mode -->
          <div class="mb-5">
            <label class="block text-sm font-medium mb-2">Split by</label>
            <SelectButton v-model="splitBy" :options="splitOptions" optionLabel="label" optionValue="value"
              :allowEmpty="false" />
          </div>

          <!-- Value input -->
          <div class="mb-6">
            <label class="block text-sm font-medium mb-2">
              {{ splitBy === "duration" ? "Segment length (minutes)" : "Target size per part (MB)" }}
            </label>
            <InputNumber v-model="splitValue" :min="0.1" :step="splitBy === 'duration' ? 1 : 5" :minFractionDigits="1"
              :maxFractionDigits="1" class="w-full" />
          </div>
        </template>

        <!-- Extract audio options -->
        <template v-if="actionMode === 'extract-audio'">
          <div class="mb-6">
            <label class="block text-sm font-medium mb-2">Output format</label>
            <SelectButton v-model="audioFormat" :options="audioFormatOptions" optionLabel="label" optionValue="value"
              :allowEmpty="false" />
          </div>
        </template>

        <!-- Submit -->
        <Button
          :label="splitting ? (actionMode === 'split' ? 'Splitting...' : 'Extracting...') : (actionMode === 'split' ? 'Split file' : 'Extract audio')"
          :loading="splitting" :disabled="!selectedFile || splitting"
          @click="actionMode === 'split' ? splitFile() : extractAudio()" class="w-full" />

        <!-- Error -->
        <Message v-if="error" severity="error" class="mt-4" :closable="false">
          {{ error }}
        </Message>
      </div>

      <!-- Split Results Card -->
      <div v-if="result && result.parts"
        class="reveal rounded-3xl border border-black/10 bg-white/90 backdrop-blur-md shadow-[0_24px_60px_rgba(11,17,25,0.12)] p-8">
        <h2 class="text-xl font-semibold mb-1">Split complete</h2>
        <p class="text-sm text-[#4b5664] mb-5">
          {{ result.original_filename }} split into
          {{ result.total_parts }} parts
          <span class="text-xs">
            ({{ result.split_by === "duration" ? result.value + " min segments" : result.value + " MB target" }})
          </span>
        </p>

        <div class="flex flex-col gap-2">
          <div v-for="part in result.parts" :key="part.filename"
            class="flex items-center justify-between gap-4 rounded-xl border border-black/8 bg-white/70 px-5 py-3">
            <div class="min-w-0">
              <p class="text-sm font-medium truncate">{{ part.filename }}</p>
              <p class="text-xs text-[#4b5664]">
                {{ formatBytes(part.size_bytes) }}
                <span v-if="part.duration_seconds">
                  &middot; {{ formatDuration(part.duration_seconds) }}
                </span>
              </p>
            </div>
            <a :href="downloadUrl(part.download_url)" download class="shrink-0">
              <Button label="Download" size="small" outlined />
            </a>
          </div>
        </div>

        <!-- Download all -->
        <div class="mt-4 flex gap-3">
          <Button label="Download all (.zip)" size="small" severity="secondary" @click="downloadAllZip" />
          <Button label="Split another file" size="small" outlined @click="reset" />
        </div>
      </div>

      <!-- Extract Audio Result Card -->
      <div v-if="result && result.download_url && !result.parts"
        class="reveal rounded-3xl border border-black/10 bg-white/90 backdrop-blur-md shadow-[0_24px_60px_rgba(11,17,25,0.12)] p-8">
        <h2 class="text-xl font-semibold mb-1">Audio extracted</h2>
        <p class="text-sm text-[#4b5664] mb-5">
          Extracted audio from {{ result.original_filename }}
        </p>

        <div class="flex items-center justify-between gap-4 rounded-xl border border-black/8 bg-white/70 px-5 py-3">
          <div class="min-w-0">
            <p class="text-sm font-medium truncate">{{ result.filename }}</p>
            <p class="text-xs text-[#4b5664]">
              {{ formatBytes(result.size_bytes) }}
              <span v-if="result.duration_seconds">
                &middot; {{ formatDuration(result.duration_seconds) }}
              </span>
            </p>
          </div>
          <a :href="downloadUrl(result.download_url)" download class="shrink-0">
            <Button label="Download" size="small" outlined />
          </a>
        </div>

        <div class="mt-4">
          <Button label="Extract another file" size="small" outlined @click="reset" />
        </div>
      </div>
    </div>
  </PageShell>
</template>

<script setup>
import { ref, watch } from "vue";
import PageShell from "../components/PageShell.vue";
import { formatBytes, formatDuration } from "../utils/format.js";
import FileUpload from "primevue/fileupload";
import SelectButton from "primevue/selectbutton";
import InputNumber from "primevue/inputnumber";
import Button from "primevue/button";
import Message from "primevue/message";

const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const acceptedTypes =
  ".mp3,.wav,.ogg,.flac,.m4a,.aac,.wma,.mp4,.mkv,.avi,.mov,.webm";

const actionOptions = [
  { label: "Split", value: "split" },
  { label: "Extract audio", value: "extract-audio" },
];

const splitOptions = [
  { label: "Duration", value: "duration" },
  { label: "File size", value: "size" },
];

const audioFormatOptions = [
  { label: "MP3", value: "mp3" },
  { label: "WAV", value: "wav" },
  { label: "FLAC", value: "flac" },
];

const actionMode = ref("split");
const selectedFile = ref(null);
const splitBy = ref("duration");
const splitValue = ref(240);
const audioFormat = ref("mp3");
const splitting = ref(false);
const error = ref("");
const result = ref(null);
const uploadKey = ref(0);

watch(splitBy, (mode) => {
  splitValue.value = mode === "duration" ? 240 : 2000;
});

function onFileSelect(event) {
  const files = event.files || [];
  selectedFile.value = files.length > 0 ? files[0] : null;
}

async function splitFile() {
  if (!selectedFile.value) return;

  splitting.value = true;
  error.value = "";
  result.value = null;

  const formData = new FormData();
  formData.append("file", selectedFile.value);
  formData.append("split_by", splitBy.value);
  formData.append("value", splitValue.value);

  try {
    const res = await fetch(`${apiBase}/media/split`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const body = await res.json().catch(() => null);
      throw new Error(body?.detail || `Server error (${res.status})`);
    }

    result.value = await res.json();
  } catch (err) {
    error.value = err.message;
  } finally {
    splitting.value = false;
  }
}

async function extractAudio() {
  if (!selectedFile.value) return;

  splitting.value = true;
  error.value = "";
  result.value = null;

  const formData = new FormData();
  formData.append("file", selectedFile.value);
  formData.append("format", audioFormat.value);

  try {
    const res = await fetch(`${apiBase}/media/extract-audio`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const body = await res.json().catch(() => null);
      throw new Error(body?.detail || `Server error (${res.status})`);
    }

    result.value = await res.json();
  } catch (err) {
    error.value = err.message;
  } finally {
    splitting.value = false;
  }
}

function downloadUrl(path) {
  return `${apiBase}${path}`;
}

function downloadAllZip() {
  if (!result.value) return;
  const link = document.createElement("a");
  link.href = `${apiBase}/media/download-zip/${result.value.job_id}`;
  link.download = `${result.value.original_filename}_parts.zip`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function reset() {
  selectedFile.value = null;
  result.value = null;
  error.value = "";
  splitValue.value = splitBy.value === "duration" ? 240 : 2000;
  uploadKey.value++;
}

</script>
