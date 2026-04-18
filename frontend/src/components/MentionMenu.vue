<template>
  <Transition name="mention-fade">
    <div
      v-if="open && items.length > 0"
      class="absolute z-50 w-72 max-h-72 overflow-y-auto rounded-xl border border-[rgba(12,17,24,0.12)] bg-white shadow-[0_8px_24px_rgba(12,17,24,0.12)] py-1"
      :style="{ bottom: `${bottomOffset}px`, left: `${leftOffset}px` }"
      @mousedown.prevent
    >
      <div
        class="px-3 py-1.5 text-[0.65rem] font-semibold tracking-[0.1em] uppercase text-(--muted)"
      >
        Workflows
      </div>
      <button
        v-for="(wf, i) in items"
        :key="wf.id"
        type="button"
        class="w-full flex flex-col items-start gap-0.5 text-left px-3 py-2 transition-colors duration-100 cursor-pointer border-none bg-transparent"
        :class="
          i === activeIndex
            ? 'bg-[rgba(255,106,0,0.08)]'
            : 'hover:bg-[rgba(12,17,24,0.04)]'
        "
        @click="$emit('select', wf)"
        @mouseenter="$emit('hover', i)"
      >
        <span class="text-[0.85rem] font-medium text-(--ink)">
          @{{ wf.label }}
        </span>
        <span class="text-[0.72rem] text-(--muted) leading-snug">
          {{ wf.description }}
        </span>
      </button>
    </div>
  </Transition>
</template>

<script setup>
defineProps({
  open: { type: Boolean, default: false },
  items: { type: Array, default: () => [] },
  activeIndex: { type: Number, default: 0 },
  bottomOffset: { type: Number, default: 80 },
  leftOffset: { type: Number, default: 0 },
});

defineEmits(["select", "hover"]);
</script>

<style scoped>
.mention-fade-enter-active,
.mention-fade-leave-active {
  transition:
    opacity 0.12s ease,
    transform 0.12s ease;
}

.mention-fade-enter-from,
.mention-fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

div::-webkit-scrollbar {
  width: 5px;
}

div::-webkit-scrollbar-thumb {
  background: rgba(12, 17, 24, 0.15);
  border-radius: 10px;
}
</style>
