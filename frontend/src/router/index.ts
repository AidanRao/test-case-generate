import { createRouter, createWebHistory } from 'vue-router'
import Projects from '../views/Projects.vue'
import TestCases from '../views/TestCases.vue'
import ModuleRequirements from '../views/ModuleRequirements.vue'
import Settings from '../views/Settings.vue'

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
    },
    {
      path: '/projects/:projectId/modules/:moduleName/requirements',
      name: 'module-requirements',
      component: ModuleRequirements
    },
    {
      path: '/settings',
      name: 'settings',
      component: Settings
    }
  ]
})

export default router
