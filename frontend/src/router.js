import { createRouter, createWebHistory } from "vue-router";
import InvestigationsPage from "./pages/InvestigationsPage.vue";
import InvestigationPage from "./pages/InvestigationPage.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/investigations" },
    { path: "/investigations", component: InvestigationsPage },
    { path: "/investigations/:id", component: InvestigationPage },
  ],
});

export default router;
