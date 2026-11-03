import type { RouteRecordRaw } from 'vue-router'

const UUID = '[0-9a-f-]{36}'

export const routes: RouteRecordRaw[] = [
  {
    path: '/livros',
    component: () => import('./pages/ReadingPage.vue'),
    children: [
      { path: '', name: 'reading.home', component: () => import('./pages/ShelfTab.vue') },
      {
        path: 'anotacoes',
        name: 'reading.notes',
        component: () => import('./pages/NotesTab.vue'),
      },
    ],
  },
  {
    path: `/livros/:bookId(${UUID})`,
    name: 'reading.book',
    component: () => import('./pages/BookDetailPage.vue'),
    props: true,
  },
]
