<template>
  <PageShell footer-text="Red Pajama Labs · Media Splitter">
    <Message v-if="error" severity="error" class="relative z-10 m-0 rounded-xl border border-red-700/20 text-[#9f2d1f] bg-red-700/10 text-sm px-4 py-3 reveal">
      {{ error }}
    </Message>

    <section class="relative z-10 grid gap-8 grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
      <div class="relative z-10 flex flex-col gap-6 rounded-4xl p-10 bg-white/92 border border-white/50 shadow-[0_24px_60px_rgba(11,17,25,0.18)] reveal">
        <p class="uppercase tracking-[0.26em] text-xs font-semibold text-[#4b5664] m-0">
          Audio / Video Splitter
        </p>
        <h1 class="font-[Playfair_Display] text-3xl md:text-4xl lg:text-[clamp(2.2rem,3.4vw,3.6rem)] font-semibold">
          Split large media files into smaller chunks.
        </h1>
        <p class="text-[#4b5664] text-[1.05rem] m-0">
          Upload an audio or video file and split it into smaller pieces.
          Original format is preserved. Download each chunk individually.
        </p>
        <div class="grid gap-3 rounded-[18px] p-4 px-5 bg-black/6">
          <div class="flex flex-col gap-0.5">
            <span class="text-xs uppercase tracking-[0.18em] text-[#4b5664]">Supported formats</span>
            <span class="font-semibold">{{ supportedFormats.join(', ') }}</span>
          </div>
          <div class="flex flex-col gap-0.5">
            <span class="text-xs uppercase tracking-[0.18em] text-[#4b5664]">Chunks created</span>
            <span class="font-semibold">{{ chunks.length }}</span>
          </div>
        </div>
      </div>

      <Card class="relative z-10 grid gap-5 rounded-[28px] p-8 bg-white border border-black/8 shadow-[0_24px_60px_rgba(11,17,25,0.18)] reveal">
        <template #content>
          <form @submit.prevent="splitFile" class="grid gap-5">
            <p class="uppercase tracking-[0.26em] text-xs font-semibold text-[#4b5664] m-0">
              Upload media file
            </p>
            
            <div 
              class="flex flex-col gap-4 rounded-[22px] px-5 py-6 border-2 border-dashed transition-colors"
              :class="file ? 'border-green-500 bg-green-500/5' : 'border-black/20 bg-black/3'"
              @dragover.prevent="dragOver = true"
              @dragleave.prevent="dragOver = false"
              @drop.prevent="onDrop"
            >
              <div v-if="!file" class="text-center">
                <i class="pi pi-cloud-upload text-4xl text-[#4b5664] mb-3"></i>
                <p class="m-0 font-semibold">Drop file here or click to browse</p>
                <span class="text-[#4b5664] text-sm">MP4, AVI, MKV, MOV, MP3, WAV, AAC, M4A, OGG, FLAC</span>
              </div>
              <div v-else class="text-center">
                <i class="pi pi-file text-4xl text-green-600 mb-3"></i>
                <p class="m-0 font-semibold">{{ file.name }}</p>
                <span class="text-[#4b5664] text-sm">{{ formatBytes(file.size) }}</span>
              </div>
              <FileUpload
                v-if="!file"
                mode="basic"
                name="file"
                :customUpload="true"
                :auto="false"
                chooseLabel=""
                :accept="acceptedFileTypes"
                @select="onFileSelect"
                class="!absolute inset-0 !opacity-0 cursor-pointer"
                style="position: absolute; inset: 0; opacity: 0; cursor: pointer;"
              />
              <Button v-if="file" type="button" severity="secondary" variant="outlined" label="Remove" @click="clearFile" class="mt-2" />
            </div>

            <div class="flex gap-4">
              <div class="flex-1 flex flex-col gap-2">
                <div class="flex items-center gap-2">
                  <input 
                    type="radio" 
                    id="splitByDuration" 
                    :value="'duration'" 
                    v-model="splitMode"
                    class="w-4 h-4"
                  />
                  <label for="splitByDuration" class="text-xs font-semibold text-[#4b5664] uppercase tracking-[0.16em]">
                    Split by duration
                  </label>
                </div>
                <InputNumber 
                  v-model="chunkDuration" 
                  :min="1" 
                  :max="60" 
                  :disabled="splitMode !== 'duration'"
                  showButtons 
                  fluid 
                />
                <span class="text-[#4b5664] text-xs">Minutes (default: 5)</span>
              </div>

              <div class="flex-1 flex flex-col gap-2">
                <div class="flex items-center gap-2">
                  <input 
                    type="radio" 
                    id="splitBySize" 
                    :value="'size'" 
                    v-model="splitMode"
                    class="w-4 h-4"
                  />
                  <label for="splitBySize" class="text-xs font-semibold text-[#4b5664] uppercase tracking-[0.16em]">
                    Split by size
                  </label>
                </div>
                <InputNumber 
                  v-model="chunkSizeMb" 
                  :min="1" 
                  :max="2000" 
                  :disabled="splitMode !== 'size'"
                  showButtons 
                  fluid 
                />
                <span class="text-[#4b5664] text-xs">MB (default: 100)</span>
              </div>
            </div>

            <Button 
              type="submit" 
              label="Split File" 
              :loading="splitting" 
              :disabled="!file || splitting"
              class="w-full" 
            />
          </form>
        </template>
      </Card>
    </section>

    <section v-if="chunks.length > 0" class="relative z-10 grid gap-6 reveal">
      <Card class="relative z-10 grid gap-6 rounded-3xl p-7 bg-white border border-black/8 shadow-[0_24px_60px_rgba(11,17,25,0.18)]">
        <template #content>
          <div class="flex justify-between items-center">
            <div>
              <h3>Split Results</h3>
              <p class="mt-1 text-[#4b5664]">
                {{ chunks.length }} chunks created from {{ originalFilename }}
              </p>
            </div>
            <Button severity="secondary" variant="outlined" label="Clear All" @click="clearChunks" />
          </div>

          <div class="grid gap-3 mt-4">
            <div v-for="(chunk, index) in chunks" :key="index"
              class="flex justify-between gap-4 rounded-2xl border border-black/8 px-4 py-3.5 bg-white">
              <div class="flex items-center gap-3">
                <i class="pi pi-file text-[#4b5664]"></i>
                <div>
                  <h4 class="m-0 text-[0.95rem]">{{ chunk.filename }}</h4>
                  <p class="mt-1 text-[#4b5664] text-[0.78rem]">
                    Part {{ index + 1 }} of {{ chunks.length }}
                  </p>
                </div>
              </div>
              <Button 
                type="button" 
                label="Download" 
                icon="pi pi-download" 
                @click="downloadChunk(chunk.filename)" 
              />
            </div>
          </div>
        </template>
      </Card>
    </section>

    <section v-if="mediaInfo" class="relative z-10 grid gap-4 reveal">
      <Card class="relative z-10 rounded-[20px] p-5 bg-white border border-black/5 shadow-[0_24px_60px_rgba(11,17,25,0.18)]">
        <template #content>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <span class="text-xs uppercase tracking-[0.18em] text-[#4b5664]">Format</span>
              <p class="font-semibold mt-1">{{ mediaInfo.format.toUpperCase() }}</p>
            </div>
            <div>
              <span class="text-xs uppercase tracking-[0.18em] text-[#4b5664]">Duration</span>
              <p class="font-semibold mt-1">{{ formatDuration(mediaInfo.duration_seconds) }}</p>
            </div>
            <div>
              <span class="text-xs uppercase tracking-[0.18em] text-[#4b5664]">Type</span>
              <p class="font-semibold mt-1">{{ mediaInfo.is_video ? 'Video' : 'Audio' }}</p>
            </div>
            <div>
              <span class="text-xs uppercase tracking-[0.18em] text-[#4b5664]">Estimated chunks</span>
              <p class="font-semibold mt-1">
                {{ splitMode === 'duration' 
                  ? Math.ceil(mediaInfo.duration_seconds / (chunkDuration * 60)) 
                  : Math.ceil(mediaInfo.file_size_mb / chunkSizeMb) }}
              </p>
            </div>
          </div>
        </template>
      </Card>
    </section>
  </PageShell>
</template>

<script setup>
import { ref, reactive } from "vue";
import Button from "primevue/button";
import Card from "primevue/card";
import FileUpload from "primevue/fileupload";
import InputNumber from "primevue/inputnumber";
import Message from "primevue/message";
import PageShell from "../components/PageShell.vue";

const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const supportedFormats = ['mp4', 'avi', 'mkv', 'mov', 'mp3', 'wav', 'aac', 'm4a', 'ogg', 'flac'];
const acceptedFileTypes = ".mp4,.avi,.mkv,.mov,.wmv,.flv,.webm,.m4v,.mpeg,.mpg,.mp3,.wav,.aac,.m4a,.ogg,.flac,.wma,.aiff";

const file = ref(null);
const chunks = ref([]);
const originalFilename = ref("");
const splitting = ref(false);
const error = ref("");
const mediaInfo = ref(null);
const chunkDuration = ref(5);
const chunkSizeMb = ref(100);
const splitMode = ref("duration");
const dragOver = ref(false);

const formatBytes = (value) => {
  if (!value && value !== 0) return "";
  if (value < 1024) return `${value} B`;
  const kb = value / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
};

const formatDuration = (seconds) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}m ${secs}s`;
};

const onFileSelect = (event) => {
  const selectedFile = event.files?.[0];
  if (selectedFile) {
    file.value = selectedFile;
    getMediaInfo(selectedFile);
  }
};

const onDrop = (event) => {
  dragOver.value = false;
  const droppedFile = event.dataTransfer?.files?.[0];
  if (droppedFile) {
    file.value = droppedFile;
    getMediaInfo(droppedFile);
  }
};

const clearFile = () => {
  file.value = null;
  mediaInfo.value = null;
  error.value = "";
};

const clearChunks = () => {
  chunks.value = [];
  originalFilename.value = "";
};

const getMediaInfo = async (file) => {
  try {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(`${apiBase}/media/info`, {
      method: "GET",
      body: formData,
    });

    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || "Failed to get media info");
    }

    mediaInfo.value = await res.json();
  } catch (err) {
    console.error("Error getting media info:", err);
    mediaInfo.value = null;
  }
};

const splitFile = async () => {
  if (!file.value) return;

  splitting.value = true;
  error.value = "";
  chunks.value = [];

  try {
    const formData = new FormData();
    formData.append("file", file.value);

    if (splitMode.value === "duration") {
      formData.append("chunk_duration", chunkDuration.value * 60);
    } else {
      formData.append("chunk_size_mb", chunkSizeMb.value);
    }

    const res = await fetch(`${apiBase}/media/split`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || "Failed to split file");
    }

    const data = await res.json();
    chunks.value = data.chunks;
    originalFilename.value = data.filename;
  } catch (err) {
    error.value = err.message;
  } finally {
    splitting.value = false;
  }
};

const downloadChunk = async (filename) => {
  try {
    const res = await fetch(`${apiBase}/media/download/${encodeURIComponent(filename)}`);
    
    if (!res.ok) {
      throw new Error("Failed to download file");
    }

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  } catch (err) {
    error.value = "Failed to download chunk: " + err.message;
  }
};
</script>
