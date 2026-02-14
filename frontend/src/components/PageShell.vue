<template>
  <div
    class="relative min-h-screen flex flex-col gap-10 overflow-hidden py-28 px-[clamp(1.5rem,3vw,4rem)] pb-16"
  >
    <PageBackdrop />
    <slot />
    <footer
      v-if="footerText"
      class="relative z-10 text-center text-sm uppercase tracking-[0.2em] text-[#4b5664]"
    >
      {{ footerText }}
    </footer>
  </div>
</template>

<script setup>
import PageBackdrop from "./PageBackdrop.vue";

defineProps({
  footerText: {
    type: String,
    default: "",
  },
});
</script>
