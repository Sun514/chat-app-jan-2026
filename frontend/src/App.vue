<template>
  <AppHeader v-if="headerTitle" :title="headerTitle" :subtitle="headerSubtitle" />
  <RouterView />
</template>

<script setup>
import { computed } from "vue";
import { RouterView, useRoute } from "vue-router";
import AppHeader from "./components/AppHeader.vue";
import { getInvestigation } from "./stores/investigations";

const route = useRoute();

const headerTitle = computed(() => {
  if (route.path.startsWith("/investigations/") && route.params.id) {
    const investigation = getInvestigation(route.params.id);
    return investigation?.name || "Investigation";
  }
  return route.meta?.headerTitle || "";
});

const headerSubtitle = computed(() => {
  if (route.path.startsWith("/investigations/") && route.params.id) {
    const investigation = getInvestigation(route.params.id);
    return investigation?.description || "Evidence intelligence workspace";
  }
  return route.meta?.headerSubtitle || "";
});
</script>
