<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import { installedModules } from '@/modules'
import { PLogo, PTile } from '@/ui'

const { t } = useI18n()
</script>

<template>
  <div class="auth">
    <section class="auth__hero" :aria-label="t('auth.login.about')">
      <div class="auth__brand">
        <PLogo size="sm" class="auth__logo" />
        <span class="auth__name">{{ t('app.name') }}</span>
      </div>
      <div class="auth__pendulum" aria-hidden="true"><PLogo variant="pendulum" /></div>
      <div class="auth__pitch">
        <h1 class="auth__tagline">{{ t('app.tagline') }}</h1>
        <p class="auth__description">{{ t('app.description') }}</p>
        <div v-if="installedModules.length" class="auth__modules">
          <PTile
            v-for="module in installedModules"
            :key="module.id"
            :icon="module.icon"
            :tone="module.id"
            :label="t(module.nav.labelKey)"
          />
        </div>
      </div>
      <p class="auth__footer">{{ t('app.openSource') }}</p>
    </section>
    <main class="auth__main">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.auth {
  display: grid;
  min-height: 100dvh;
  grid-template-columns: repeat(auto-fit, minmax(min(460px, 100%), 1fr));
}

.auth__hero {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: var(--space-10);
  padding: var(--space-12) var(--space-14);
  overflow: hidden;
  background: var(--color-surface);
}

.auth__brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.auth__logo {
  --logo-eye: var(--color-surface);
}

.auth__name {
  font-size: var(--text-2xl);
  font-weight: var(--weight-heavy);
  letter-spacing: var(--tracking-tight);
}

.auth__pendulum {
  position: absolute;
  top: 0;
  right: 96px;
  display: flex;
  width: 80px;
  height: 460px;
  justify-content: center;
}

.auth__pitch {
  position: relative;
  display: flex;
  max-width: 440px;
  flex-direction: column;
  gap: var(--space-4-5);
}

.auth__tagline {
  font-size: var(--text-5xl);
  font-weight: var(--weight-bold);
  line-height: 1.08;
  letter-spacing: var(--tracking-tighter);
}

.auth__description {
  color: var(--color-text-secondary);
  font-size: var(--text-xl);
  text-wrap: pretty;
}

.auth__modules {
  display: flex;
  gap: var(--space-2-5);
  margin-top: var(--space-2);
}

.auth__footer {
  position: relative;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.auth__main {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-12) var(--space-6);
}

@media (width < 940px) {
  .auth__hero {
    gap: var(--space-6);
    padding: var(--space-8) var(--space-6);
  }

  .auth__pendulum,
  .auth__footer {
    display: none;
  }

  .auth__tagline {
    font-size: var(--text-4xl);
  }
}
</style>
