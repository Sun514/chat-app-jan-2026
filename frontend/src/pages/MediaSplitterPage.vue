<template>
  <main class="min-h-screen pt-32 pb-24 px-4 sm:px-[clamp(1.5rem,3vw,4rem)]">
    <div class="max-w-4xl mx-auto space-y-8">
      <Card class="bg-white/50 backdrop-blur-md rounded-[24px] border border-black/5 shadow-sm p-2 sm:p-4">
        <template #title>
          <div class="mb-4">
            <h1 class="text-2xl font-bold text-gray-900 tracking-tight">Split Media File</h1>
            <p class="text-gray-500 text-sm mt-1">
              Upload a media file and split it by duration or by file size
            </p>
          </div>
        </template>
        <template #content>
          <div class="space-y-6">
            <!-- File Mode Selection -->
            <div class="flex gap-4 p-1 bg-gray-100/50 rounded-xl w-fit">
              <button
                @click="splitMethod = 'duration'"
                :class="[ 'px-4 py-2 rounded-lg text-sm font-medium transition-colors', splitMethod === 'duration' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500 hover:text-gray-700' ]"
              >
                Split by Duration
              </button>
              <button
                @click="splitMethod = 'size'"
                :class="[ 'px-4 py-2 rounded-lg text-sm font-medium transition-colors', splitMethod === 'size' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500 hover:text-gray-700' ]"
              >
                Split by Size
              </button>
            </div>

            <!-- Value Input -->
            <div class="space-y-2">
              <label class="block text-sm font-medium text-gray-700">
                {{ splitMethod === 'duration' ? 'Segment duration (minutes)' : 'Segment size (MB)' }}
              </label>
              <InputText
                type="number"
                v-model.number="splitValue"
                min="0.1"
                step="0.1"
                class="w-full md:w-64 rounded-xl"
                :placeholder="splitMethod === 'duration' ? 'e.g. 1.5' : 'e.g. 20'"
              />
            </div>

            <!-- File Upload -->
            <div class="space-y-4 pt-4 border-t border-gray-100">
              <input type="file" ref="fileInput" @change="onFileChange" class="hidden" accept="video/*,audio/*" />
              <div 
                @click="$refs.fileInput.click()"
                @dragover.prevent="dragOver = true"
                @dragleave.prevent="dragOver = false"
                @drop.prevent="onDrop"
                class="cursor-pointer group flex flex-col items-center justify-center p-10 border-2 border-dashed rounded-[24px] transition-colors bg-gray-50/50"
                :class="dragOver ? 'border-primary-500 bg-primary-50/50' : 'border-gray-200 hover:border-gray-300'"
              >
                <i class="pi pi-cloud-upload text-4xl text-gray-400 mb-3 group-hover:text-primary-500 transition-colors"></i>
                <p class="font-medium text-gray-700">{{ file ? file.name : 'Click or drag media file to upload' }}</p>
                <p v-if="file" class="text-sm text-gray-500 mt-1">{{ formatBytes(file.size) }}</p>
              </div>

              <div class="flex justify-end pt-4">
                <Button 
                  label="Split Media" 
                  icon="pi pi-cog" 
                  :loading="isLoading"
                  :disabled="!file || !splitValue || splitValue <= 0"
                  @click="submitSplit"
                  class="rounded-xl px-6 py-2.5 font-medium" 
                />
              </div>
            </div>

            <!-- Error Message -->
            <Message v-if="error" severity="error" :closable="false" class="mt-4">{{ error }}</Message>

            <!-- Results -->
            <div v-if="result" class="pt-8 mt-8 border-t border-gray-100 animate-fade-in">
              <div class="flex items-center justify-between mb-6">
                <h2 class="text-xl font-semibold text-gray-900">Split Results</h2>
                <a :href="`http://localhost:8000${result.zip_url}`" download>
                  <Button label="Download ZIP Archive" severity="success" icon="pi pi-download" class="rounded-xl px-4 py-2" />
                </a>
              </div>
              
              <div class="flex flex-col gap-3">
                <div v-for="(url, index) in result.file_urls" :key="index"
                     class="flex items-center justify-between p-4 rounded-xl bg-gray-50 border border-gray-100 hover:border-gray-200 transition-colors"
                >
                  <div class="flex items-center gap-3 overflow-hidden">
                    <i class="pi pi-file-media text-gray-400"></i>
                    <span class="text-sm font-medium text-gray-700 truncate" :title="result.files[index]">
                      {{ result.files[index] }}
                    </span>
                  </div>
                  <a :href="`http://localhost:8000${url}`" download>
                    <Button icon="pi pi-download" text rounded severity="secondary" aria-label="Download" />
                  </a>
                </div>
              </div>
            </div>
          </div>
        </template>
      </Card>
    </div>
  </main>
</template>

<script setup>
import { ref } from 'vue';
import Card from 'primevue/card';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import Message from 'primevue/message';

const splitMethod = ref('duration');
const splitValue = ref(5);
const file = ref(null);
const fileInput = ref(null);
const dragOver = ref(false);

const isLoading = ref(false);
const error = ref(null);
const result = ref(null);

const onFileChange = (e) => {
  const selected = e.target.files[0];
  if (selected) {
    file.value = selected;
  }
};

const onDrop = (e) => {
  dragOver.value = false;
  const dropped = e.dataTransfer.files[0];
  if (dropped && (dropped.type.startsWith('audio/') || dropped.type.startsWith('video/'))) {
    file.value = dropped;
  }
};

const formatBytes = (bytes, decimals = 2) => {
    if (!+bytes) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
};

const submitSplit = async () => {
  if (!file.value || !splitValue.value) return;
  
  isLoading.value = true;
  error.value = null;
  result.value = null;
  
  const formData = new FormData();
  formData.append('file', file.value);
  
  try {
    const response = await fetch(`http://localhost:8000/media/split?method=${splitMethod.value}&value=${splitValue.value}`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || 'Failed to split media');
    }
    
    result.value = await response.json();
  } catch (err) {
    error.value = err.message;
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.4s ease-out forwards;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
