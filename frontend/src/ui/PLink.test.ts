import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import PLink from './PLink.vue'

const router = createRouter({
  history: createMemoryHistory(),
  routes: [{ path: '/livros/:id', name: 'book', component: { template: '<div />' } }],
})

describe('PLink', () => {
  it('keeps the href of router links', async () => {
    await router.push('/livros/a')
    const wrapper = mount(PLink, {
      props: { to: { name: 'book', params: { id: 'b1' } } },
      slots: { default: 'Ver detalhes' },
      global: { plugins: [router] },
    })
    expect(wrapper.get('a').attributes('href')).toBe('/livros/b1')
  })

  it('renders plain links with href', () => {
    const wrapper = mount(PLink, { props: { href: '#perfil' }, slots: { default: 'Perfil' } })
    expect(wrapper.get('a').attributes('href')).toBe('#perfil')
  })
})
