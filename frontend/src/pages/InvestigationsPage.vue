<template>
  <div class="case-hub">
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
          <p class="brand-title">Red Pajama Labs</p>
          <p class="brand-subtitle">Manage active investigations</p>
        </div>
      </div>
      <div class="top-actions"></div>
    </header>

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

      <form class="create-card reveal" @submit.prevent="create">
        <p class="eyebrow">New investigation</p>
        <div class="field">
          <label>Case name</label>
          <input type="text" v-model="form.name" placeholder="Northpoint Contract Review" required />
        </div>
        <div class="field">
          <label>Owner</label>
          <input type="text" v-model="form.owner" placeholder="Threat Intel" />
        </div>
        <div class="field">
          <label>Summary</label>
          <textarea v-model="form.description" rows="3" placeholder="What is this investigation about?"></textarea>
        </div>
        <button class="btn primary full" type="submit">Create investigation</button>
      </form>
    </section>

    <section class="case-grid reveal">
      <div v-if="state.items.length === 0" class="empty-card">
        No investigations yet. Create one to begin.
      </div>
      <div v-for="item in state.items" :key="item.id" class="case-card">
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
            <RouterLink class="btn dark" :to="`/investigations/${item.id}`">Open</RouterLink>
            <button class="btn ghost" @click="remove(item.id)">Archive</button>
          </div>
        </div>
      </div>
    </section>

    <footer class="footer">Red Pajama Labs · Case hub</footer>
  </div>
</template>

<script setup>
import { reactive } from "vue";
import { RouterLink } from "vue-router";
import { state, createInvestigation, removeInvestigation } from "../stores/investigations";

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

</script>
