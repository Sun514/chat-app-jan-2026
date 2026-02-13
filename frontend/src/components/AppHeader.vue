<template>
  <Menubar class="topbar top-menubar" :model="navItems">
    <template #start>
      <div class="brand">
        <RouterLink class="brand-mark" to="/" aria-label="Go to home">RPL</RouterLink>
        <div class="brand-copy">
          <p class="brand-title">{{ title }}</p>
          <p class="brand-subtitle">{{ subtitle }}</p>
        </div>
      </div>
    </template>
  </Menubar>
</template>

<script setup>
import { computed } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import Menubar from "primevue/menubar";

defineProps({
  title: {
    type: String,
    required: true,
  },
  subtitle: {
    type: String,
    default: "",
  },
});

const route = useRoute();
const router = useRouter();

const navItems = computed(() => {
  const isActive = (pathPrefix) => route.path.startsWith(pathPrefix);

  return [
    {
      label: "Case hub",
      command: () => router.push("/investigations"),
      class: isActive("/investigations") ? "menu-item-active" : "",
    },
    {
      label: "Collections",
      command: () => router.push("/collections"),
      class: isActive("/collections") ? "menu-item-active" : "",
    },
    {
      label: "Audit metrics",
      command: () => router.push("/audit"),
      class: isActive("/audit") ? "menu-item-active" : "",
    },
  ];
});
</script>
