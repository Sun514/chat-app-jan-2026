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
          Case management
        </p>
        <h1
          class="font-[Playfair_Display] text-3xl md:text-4xl lg:text-[clamp(2.2rem,3.4vw,3.6rem)] font-semibold"
        >
          Create and control investigations before evidence lands.
        </h1>
        <p class="text-[#4b5664] text-[1.05rem] m-0">
          Build a workspace for each inquiry, then open a case to upload
          documents and run investigative queries.
        </p>
        <div class="grid gap-3 rounded-[18px] p-4 px-5 bg-black/6">
          <div class="flex flex-col gap-0.5">
            <span class="text-xs uppercase tracking-[0.18em] text-[#4b5664]"
              >Active cases</span
            >
            <span class="font-semibold">{{ state.items.length }}</span>
          </div>
          <div class="flex flex-col gap-0.5">
            <span class="text-xs uppercase tracking-[0.18em] text-[#4b5664]"
              >Data retention</span
            >
            <span class="font-semibold">Local storage only</span>
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
              New investigation
            </p>
            <div class="flex flex-col gap-2">
              <label
                class="text-xs font-semibold text-[#4b5664] uppercase tracking-[0.16em]"
                >Case name</label
              >
              <InputText
                v-model="form.name"
                placeholder="Northpoint Contract Review"
                required
                fluid
              />
            </div>
            <div class="flex flex-col gap-2">
              <label
                class="text-xs font-semibold text-[#4b5664] uppercase tracking-[0.16em]"
                >Owner</label
              >
              <InputText
                v-model="form.owner"
                placeholder="Threat Intel"
                fluid
              />
            </div>
            <div class="flex flex-col gap-2">
              <label
                class="text-xs font-semibold text-[#4b5664] uppercase tracking-[0.16em]"
                >Summary</label
              >
              <Textarea
                v-model="form.description"
                rows="3"
                autoResize
                placeholder="What is this investigation about?"
                fluid
              />
            </div>
            <Button class="w-full" type="submit" label="Create investigation" />
          </form>
        </template>
      </Card>
    </section>

    <section class="relative z-10 grid gap-5 reveal">
      <Card
        v-if="state.items.length === 0"
        class="flex justify-between gap-4 rounded-[18px] border border-black/10 px-4 py-3.5 bg-white"
      >
        <template #content>
          No investigations yet. Create one to begin.
        </template>
      </Card>
      <Card
        v-for="item in state.items"
        :key="item.id"
        class="relative z-10 flex justify-between gap-6 rounded-[22px] p-7 bg-white border border-black/10 shadow-[0_24px_60px_rgba(11,17,25,0.18)]"
      >
        <template #content>
          <div class="flex">
            <div class="grow">
              <h3>{{ item.name }}</h3>
              <p class="mt-1 text-[#4b5664] text-sm">Owner: {{ item.owner }}</p>
              <p class="mt-1.5 text-[#4b5664] max-w-[46ch]">
                {{ item.description || "No summary yet." }}
              </p>
            </div>
            <div class="grid gap-3 min-w-55 justify-items-end">
              <div class="grid gap-1 text-[#4b5664] text-sm">
                <span>{{ item.documents.length }} files</span>
                <span>Last query: {{ item.lastQuery }}</span>
              </div>
              <div class="flex gap-1.5 flex-wrap justify-end">
                <Button label="Open" @click="open(item.id)" />
                <Button
                  severity="secondary"
                  variant="outlined"
                  label="Archive"
                  @click="remove(item.id)"
                />
              </div>
            </div>
          </div>
        </template>
      </Card>
    </section>

    <footer
      class="relative z-10 text-center text-sm uppercase tracking-[0.2em] text-[#4b5664]"
    >
      Red Pajama Labs · Case hub
    </footer>
  </div>
</template>

<script setup>
import { reactive } from "vue";
import { useRouter } from "vue-router";
import Button from "primevue/button";
import Card from "primevue/card";
import InputText from "primevue/inputtext";
import Textarea from "primevue/textarea";
import {
  state,
  createInvestigation,
  removeInvestigation,
} from "../stores/investigations";

const router = useRouter();

const form = reactive({
  name: "",
  description: "",
  owner: "",
});

const create = () => {
  if (!form.name.trim()) return;
  createInvestigation({
    name: form.name.trim(),
    description: form.description.trim(),
    owner: form.owner.trim(),
  });
  form.name = "";
  form.description = "";
  form.owner = "";
};

const remove = (id) => {
  removeInvestigation(id);
};

const open = (id) => {
  router.push(`/investigations/${id}`);
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
