<script setup lang="ts">
withDefaults(
  defineProps<{
    /** `mark`: the plumb bob of the navigation. `pendulum`: the long line of the login hero. */
    variant?: 'mark' | 'pendulum'
    size?: 'sm' | 'md'
    animated?: boolean
  }>(),
  { variant: 'mark', size: 'md', animated: true },
)
</script>

<template>
  <svg
    v-if="variant === 'mark'"
    class="p-logo"
    :class="[`p-logo--${size}`, { 'p-logo--animated': animated }]"
    viewBox="0 0 24 38"
    aria-hidden="true"
  >
    <path class="p-logo__line" d="M5 2h14M12 2v20" />
    <circle class="p-logo__bob" cx="12" cy="29" r="7.5" />
    <circle class="p-logo__eye" cx="12" cy="29" r="2.4" />
  </svg>
  <svg
    v-else
    class="p-pendulum"
    :class="{ 'p-logo--animated': animated }"
    viewBox="0 0 80 460"
    aria-hidden="true"
  >
    <path class="p-pendulum__line" d="M40 0v360" />
    <circle class="p-pendulum__bob" cx="40" cy="392" r="32" />
    <circle class="p-pendulum__eye" cx="40" cy="392" r="10" />
  </svg>
</template>

<style scoped>
.p-logo {
  display: block;
  width: 24px;
  height: 38px;
  color: var(--color-text);
  transform-origin: 50% 2px;
}

.p-logo--sm {
  width: 20px;
  height: 32px;
}

.p-logo__line {
  fill: none;
  stroke: currentColor;
  stroke-width: 2.2;
  stroke-linecap: round;
}

.p-logo--sm .p-logo__line {
  stroke-width: 2.4;
}

.p-logo__bob {
  fill: currentColor;
}

.p-logo__eye {
  fill: var(--logo-eye, var(--color-bg));
}

.p-logo--animated {
  animation: p-swing var(--duration-swing) var(--easing-swing) both;
}

.p-pendulum {
  display: block;
  width: 80px;
  height: 460px;
  transform-origin: 40px 0;
}

.p-pendulum.p-logo--animated {
  animation-duration: calc(var(--duration-swing) * 1.25);
}

.p-pendulum__line {
  fill: none;
  stroke: var(--color-border-strong);
  stroke-width: 2;
}

.p-pendulum__bob {
  fill: var(--color-text);
}

.p-pendulum__eye {
  fill: var(--color-surface);
}
</style>
