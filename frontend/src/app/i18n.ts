import { createI18n } from 'vue-i18n'

import ptBR from './locales/pt-BR.json'

export const DEFAULT_LOCALE = 'pt-BR'

export const i18n = createI18n({
  legacy: false,
  locale: DEFAULT_LOCALE,
  fallbackLocale: DEFAULT_LOCALE,
  messages: { [DEFAULT_LOCALE]: ptBR },
  missingWarn: import.meta.env.DEV,
  fallbackWarn: false,
})

type Messages = Record<string, unknown>

/** Module texts live under the module id: `garage.nav`, `finance.actions.addExpense`… */
export async function loadModuleMessages(
  modules: {
    id: string
    messages: Partial<Record<string, () => Promise<{ default: Messages }>>>
  }[],
  locale: string = DEFAULT_LOCALE,
): Promise<void> {
  await Promise.all(
    modules.map(async (module) => {
      const load = module.messages[locale] ?? module.messages[DEFAULT_LOCALE]
      if (!load) return
      const { default: messages } = await load()
      i18n.global.mergeLocaleMessage(locale, { [module.id]: messages })
    }),
  )
}
