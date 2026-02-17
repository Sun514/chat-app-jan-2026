<template>
  <Menubar
    class="fixed z-40 flex items-center gap-6 justify-between top-4 left-[clamp(1.5rem,3vw,4rem)] right-[clamp(1.5rem,3vw,4rem)] px-4 py-3.5 rounded-[22px] border border-black/12 bg-white/85 backdrop-blur-[10px] shadow-[0_14px_34px_rgba(12,17,24,0.14)]"
    :model="navItems"
  >
    <template #start>
      <div class="flex items-center gap-4">
        <RouterLink
          class="grid place-items-center w-14 h-14 rounded-[18px] bg-[#111722] text-white font-bold tracking-[0.2em] text-xs no-underline"
          to="/"
          aria-label="Go to home"
        >
          RPL
        </RouterLink>
        <div class="min-w-0">
          <p class="m-0 font-semibold truncate">{{ title }}</p>
          <p class="mt-1 text-[#4b5664] text-sm truncate">{{ subtitle }}</p>
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
    {
      label: "Chat",
      command: () => router.push("/chat"),
      class: isActive("/chat") ? "menu-item-active" : "",
    },
  ];
});
</script>

<style scoped>
/* PrimeVue Menubar overrides */
:deep(.p-menubar-start) {
  margin-right: 1rem;
  min-width: 0;
}

:deep(.p-menubar-root-list) {
  margin-left: auto;
  gap: 0.25rem;
  flex-wrap: wrap;
  row-gap: 0.35rem;
}

:deep(.p-menubar-item-link) {
  border-radius: 999px !important;
  padding: 0.55rem 0.9rem !important;
  font-size: 0.875rem;
}

:deep(.menu-item-active > .p-menubar-item-link) {
  background: rgba(12, 17, 24, 0.1) !important;
  border-radius: 999px !important;
}

@media (max-width: 1024px) {
  :deep(.p-menubar-start) {
    width: 100%;
  }

  :deep(.p-menubar-root-list) {
    width: 100%;
    margin-left: 0;
  }
}

@media (max-width: 640px) {
  :deep(.p-menubar-item-link) {
    padding: 0.42rem 0.7rem !important;
    font-size: 0.82rem !important;
  }
}
</style>
