import { createRouter, createWebHistory } from 'vue-router'
import Projects from '../views/Projects.vue'
import TestCases from '../views/TestCases.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/projects'
    },
    {
      path: '/projects',
      name: 'projects',
      component: Projects
    },
    {
      path: '/projects/:projectId/test-cases',
      name: 'test-cases',
      component: TestCases
    }
  ]
})

export default router
