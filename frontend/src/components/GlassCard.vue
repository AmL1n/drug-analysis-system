<template>
  <div
    ref="cardRef"
    class="glass-card"
    :class="{ 'is-hover': isHover, 'no-tilt': !tilt }"
    :style="cardStyle"
    @mousemove="onMouseMove"
    @mouseleave="onMouseLeave"
  >
    <div v-if="rim" class="glass-card__rim" aria-hidden="true" />
    <div v-if="halo" class="glass-card__halo" :style="haloStyle" aria-hidden="true" />
    <div v-if="glare" class="glass-card__glare" :style="glareStyle" aria-hidden="true" />
    <div v-if="$slots.header || title" class="glass-card__header">
      <slot name="header">
        <span class="glass-card__title">{{ title }}</span>
      </slot>
    </div>
    <div class="glass-card__content">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface Props {
  tilt?: boolean
  halo?: boolean
  glare?: boolean
  rim?: boolean
  haloColor?: string
  rimColor?: string
  title?: string
}

const props = withDefaults(defineProps<Props>(), {
  tilt: true,
  halo: true,
  glare: true,
  rim: true,
  haloColor: 'rgba(120, 180, 255, 0.18)',
  rimColor: 'rgba(255, 255, 255, 0.28)',
})

const cardRef = ref<HTMLElement | null>(null)
const isHover = ref(false)
const mouse = ref({ x: 0.5, y: 0.5 })

const cardStyle = computed(() => {
  const x = mouse.value.x - 0.5
  const y = mouse.value.y - 0.5
  const rotateY = props.tilt ? x * 6 : 0
  const rotateX = props.tilt ? -y * 6 : 0
  return {
    transform: `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(${isHover.value ? 1.004 : 1}, ${isHover.value ? 1.004 : 1}, 1)`,
  }
})

const haloStyle = computed(() => {
  const x = mouse.value.x * 100
  const y = mouse.value.y * 100
  return {
    background: `radial-gradient(circle 180px at ${x}% ${y}%, ${props.haloColor}, transparent 70%)`,
    opacity: isHover.value ? 1 : 0,
  }
})

const glareStyle = computed(() => {
  const x = mouse.value.x * 100
  const y = mouse.value.y * 100
  return {
    background: `radial-gradient(circle at ${x}% ${y}%, rgba(255,255,255,0.10), transparent 55%)`,
    opacity: isHover.value ? 1 : 0,
  }
})

function onMouseMove(e: MouseEvent) {
  if (!cardRef.value) return
  const rect = cardRef.value.getBoundingClientRect()
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
</script>

<style scoped lang="scss">
.glass-card {
  position: relative;
  overflow: hidden;
  border-radius: 20px;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.08) 0%,
    rgba(255, 255, 255, 0.03) 100%
  );
  backdrop-filter: blur(22px) saturate(140%);
  -webkit-backdrop-filter: blur(22px) saturate(140%);
  border: 1px solid rgba(255, 255, 255, 0.10);
  box-shadow:
    0 6px 22px rgba(0, 0, 0, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.10),
    inset 0 0 16px rgba(255, 255, 255, 0.02);
  transform-style: preserve-3d;
  transition: transform 0.25s cubic-bezier(0.23, 1, 0.32, 1),
              box-shadow 0.25s ease;
  will-change: transform;
}

.glass-card__content {
  position: relative;
  z-index: 2;
  height: 100%;
}

.glass-card__header {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 44px;
  padding: 14px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.glass-card__title {
  font-size: 16px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.92);
  letter-spacing: 0.02em;
}

.glass-card__rim {
  position: absolute;
  inset: -1px;
  border-radius: 20px;
  padding: 1px;
  background: conic-gradient(
    from 0deg,
    transparent 0%,
    v-bind(rimColor) 12%,
    transparent 24%,
    transparent 50%,
    v-bind(rimColor) 62%,
    transparent 74%,
    transparent 100%
  );
  -webkit-mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  opacity: 0.32;
  animation: rim-rotate 14s linear infinite;
  z-index: 0;
  pointer-events: none;
}

.glass-card__halo,
.glass-card__glare {
  position: absolute;
  inset: 0;
  border-radius: 20px;
  pointer-events: none;
  z-index: 1;
  transition: opacity 0.3s ease;
}

.glass-card__glare {
  mix-blend-mode: overlay;
}

.glass-card.is-hover {
  box-shadow:
    0 14px 42px rgba(0, 0, 0, 0.35),
    0 0 0 1px rgba(255, 255, 255, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.18),
    inset 0 0 22px rgba(255, 255, 255, 0.04);
}

.glass-card.no-tilt {
  transform: none !important;
}

@keyframes rim-rotate {
  to {
    transform: rotate(360deg);
  }
}
</style>
