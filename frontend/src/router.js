import { createRouter, createWebHistory } from "vue-router";
import InvestigationsPage from "./pages/InvestigationsPage.vue";
import InvestigationPage from "./pages/InvestigationPage.vue";
import DocumentCollectionsPage from "./pages/DocumentCollectionsPage.vue";
import AuditMetricsPage from "./pages/AuditMetricsPage.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/investigations" },
    {
      path: "/investigations",
      component: InvestigationsPage,
      meta: {
        headerTitle: "Red Pajama Labs",
        headerSubtitle: "Manage active investigations",
      },
    },
    {
      path: "/investigations/:id",
      component: InvestigationPage,
      meta: {
        headerTitle: "Investigation",
        headerSubtitle: "Evidence intelligence workspace",
      },
    },
    {
      path: "/collections",
      component: DocumentCollectionsPage,
      meta: {
        headerTitle: "Document collections",
        headerSubtitle: "Organize evidence into shared folders.",
      },
    },
    {
      path: "/audit",
      component: AuditMetricsPage,
      meta: {
        headerTitle: "Audit metrics",
        headerSubtitle: "Operational analytics and usage trends.",
      },
    },
  ],
});

export default router;
