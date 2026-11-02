import { computed, inject, provide, type ComputedRef, type InjectionKey } from 'vue'

export interface FieldContext {
  id: ComputedRef<string>
  describedBy: ComputedRef<string | undefined>
  invalid: ComputedRef<boolean>
}

const FIELD: InjectionKey<FieldContext> = Symbol('p-field')

export function provideField(context: FieldContext): void {
  provide(FIELD, context)
}

/** Inside a <PField>, controls take their id, description and invalid state from it. */
export function useField(props: { id?: string; invalid?: boolean }) {
  const field = inject(FIELD, null)
  return {
    id: computed(() => props.id ?? field?.id.value),
    describedBy: computed(() => field?.describedBy.value),
    invalid: computed(() => Boolean(props.invalid || field?.invalid.value)),
  }
}
