import { inject, provide, type InjectionKey } from 'vue'

type Run = (id: string) => void
const RUN_QUICK_ACTION: InjectionKey<Run> = Symbol('run-quick-action')

/** Provided by the AppShell: opens the dialog of a quick action from anywhere (Início chips). */
export function provideQuickActions(run: Run): void {
  provide(RUN_QUICK_ACTION, run)
}

export function useRunQuickAction(): Run {
  return inject(RUN_QUICK_ACTION, () => undefined)
}
