<template>
  <button
    ref="btnRef"
    class="glass-button"
    :class="{ 'is-primary': primary, 'is-danger': danger, 'is-large': large, 'is-loading': loading, 'is-disabled': disabled }"
    :disabled="disabled || loading"
    :type="type"
    @mousemove="onMouseMove"
    @mouseleave="onMouseLeave"
    @click="onClick"
  >
    <span class="glass-button__glow" :style="glowStyle" aria-hidden="true" />
    <span class="glass-button__rim" aria-hidden="true" />
    <span class="glass-button__content">
      <slot />
    </span>
  </button>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface Props {
  primary?: boolean
  danger?: boolean
  large?: boolean
  loading?: boolean
  disabled?: boolean
  type?: 'button' | 'submit' | 'reset'
}

const props = withDefaults(defineProps<Props>(), {
  primary: false,
  danger: false,
  large: false,
  loading: false,
  disabled: false,
  type: 'button',
})

const emit = defineEmits<{
  (e: 'click', event: MouseEvent): void
}>()

const btnRef = ref<HTMLElement | null>(null)
const isHover = ref(false)
const mouse = ref({ x: 0.5, y: 0.5 })

const glowStyle = computed(() => {
  const x = mouse.value.x * 100
  const y = mouse.value.y * 100
  let color = 'rgba(255, 255, 255, 0.20)'
  if (props.danger) {
    color = 'rgba(245, 108, 108, 0.32)'
  } else if (props.primary) {
    color = 'rgba(64, 158, 255, 0.32)'
  }
  return {
    background: `radial-gradient(circle 72px at ${x}% ${y}%, ${color}, transparent 70%)`,
    opacity: isHover.value ? 1 : 0,
  }
})

function onMouseMove(e: MouseEvent) {
  if (!btnRef.value) return
  const rect = btnRef.value.getBoundingClientRect()
  mouse.value = {
    x: (e.clientX - rect.left) / rect.width,
    y: (e.clientY - rect.top) / rect.height,
  }
  isHover.value = true
}

function onMouseLeave() {
  isHover.value = false
  // 保留鼠标最后位置，避免移出边界时光效先跳回中间再消失
}

function onClick(e: MouseEvent) {
  if (!props.loading && !props.disabled) {
    emit('click', e)
  }
}
</script>

<style scoped lang="scss">
.glass-button {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 9px 20px;
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.92);
  letter-spacing: 0.02em;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  overflow: hidden;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.08) 0%,
    rgba(255, 255, 255, 0.03) 100%
  );
  backdrop-filter: blur(14px) saturate(130%);
  -webkit-backdrop-filter: blur(14px) saturate(130%);
  box-shadow:
    0 3px 12px rgba(0, 0, 0, 0.22),
    inset 0 1px 0 rgba(255, 255, 255, 0.12),
    inset 0 0 10px rgba(255, 255, 255, 0.02);
  transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
  user-select: none;
}

.glass-button__content {
  position: relative;
  z-index: 3;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.glass-button__rim {
  position: absolute;
  inset: 0;
  border-radius: 12px;
  padding: 1px;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.28) 0%,
    rgba(255, 255, 255, 0.08) 50%,
    rgba(255, 255, 255, 0.28) 100%
  );
  -webkit-mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  opacity: 0.45;
  z-index: 1;
  pointer-events: none;
}

.glass-button__glow {
  position: absolute;
  inset: 0;
  border-radius: 12px;
  pointer-events: none;
  z-index: 2;
  transition: opacity 0.25s ease;
}

.glass-button.is-primary {
  background: linear-gradient(
    135deg,
    rgba(64, 158, 255, 0.14) 0%,
    rgba(64, 158, 255, 0.05) 100%
  );
  box-shadow:
    0 3px 14px rgba(64, 158, 255, 0.16),
    inset 0 1px 0 rgba(255, 255, 255, 0.16),
    inset 0 0 10px rgba(64, 158, 255, 0.08);
}

.glass-button.is-danger {
  background: linear-gradient(
    135deg,
    rgba(245, 108, 108, 0.14) 0%,
    rgba(245, 108, 108, 0.05) 100%
  );
  box-shadow:
    0 3px 14px rgba(245, 108, 108, 0.16),
    inset 0 1px 0 rgba(255, 255, 255, 0.16),
    inset 0 0 10px rgba(245, 108, 108, 0.08);
}

.glass-button.is-large {
  padding: 13px 28px;
  font-size: 15px;
  border-radius: 14px;
}

.glass-button.is-large .glass-button__rim,
.glass-button.is-large .glass-button__glow {
  border-radius: 14px;
}

.glass-button:hover:not(:disabled) {
  transform: translateY(-1.5px);
  box-shadow:
    0 7px 22px rgba(0, 0, 0, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.20),
    inset 0 0 14px rgba(255, 255, 255, 0.05);
}

.glass-button:active:not(:disabled) {
  transform: translateY(0) scale(0.98);
}

.glass-button:disabled,
.glass-button.is-disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.glass-button.is-loading .glass-button__content {
  opacity: 0.7;
}
</style>
