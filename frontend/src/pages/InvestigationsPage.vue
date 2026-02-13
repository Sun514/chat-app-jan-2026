<template>
  <div class="case-hub">
    <div class="backdrop">
      <span class="halo"></span>
      <span class="halo secondary"></span>
      <span class="beam"></span>
      <span class="noise"></span>
    </div>

    <section class="hub-hero">
      <div class="hero-text reveal">
        <p class="eyebrow">Case management</p>
        <h1>Create and control investigations before evidence lands.</h1>
        <p class="lead">
          Build a workspace for each inquiry, then open a case to upload documents and run investigative queries.
        </p>
        <div class="meta-strip">
          <div class="meta-item">
            <span class="meta-label">Active cases</span>
            <span class="meta-value">{{ state.items.length }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Data retention</span>
            <span class="meta-value">Local storage only</span>
          </div>
        </div>
      </div>

      <Card class="create-card reveal">
        <template #content>
          <form @submit.prevent="create">
            <p class="eyebrow">New investigation</p>
            <div class="field">
              <label>Case name</label>
              <InputText v-model="form.name" placeholder="Northpoint Contract Review" required fluid />
            </div>
            <div class="field">
              <label>Owner</label>
              <InputText v-model="form.owner" placeholder="Threat Intel" fluid />
            </div>
            <div class="field">
              <label>Summary</label>
              <Textarea v-model="form.description" rows="3" autoResize placeholder="What is this investigation about?" fluid />
            </div>
            <Button class="btn primary full" type="submit" label="Create investigation" />
          </form>
        </template>
      </Card>
    </section>

    <section class="case-grid reveal">
      <Card v-if="state.items.length === 0" class="empty-card">
        <template #content>
        No investigations yet. Create one to begin.
        </template>
      </Card>
      <Card v-for="item in state.items" :key="item.id" class="case-card">
        <template #content>
          <div>
            <h3>{{ item.name }}</h3>
            <p class="case-meta">Owner: {{ item.owner }}</p>
            <p class="case-desc">{{ item.description || "No summary yet." }}</p>
          </div>
          <div class="case-actions">
            <div class="case-stats">
              <span>{{ item.documents.length }} files</span>
              <span>Last query: {{ item.lastQuery }}</span>
            </div>
            <div class="case-buttons">
              <Button class="btn primary" label="Open" @click="open(item.id)" />
              <Button class="btn ghost" severity="secondary" variant="outlined" label="Archive" @click="remove(item.id)" />
            </div>
          </div>
        </template>
      </Card>
    </section>

    <footer class="footer">Red Pajama Labs · Case hub</footer>
  </div>
</template>

<script setup>
import { reactive } from "vue";
import { useRouter } from "vue-router";
import Button from "primevue/button";
import Card from "primevue/card";
import InputText from "primevue/inputtext";
import Textarea from "primevue/textarea";
import { state, createInvestigation, removeInvestigation } from "../stores/investigations";

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
