import { createRouter, createWebHistory } from "vue-router";
import InvestigationsPage from "./pages/InvestigationsPage.vue";
import InvestigationPage from "./pages/InvestigationPageDetails.vue";
import DocumentCollectionsPage from "./pages/DocumentCollectionsPage.vue";
import AuditMetricsPage from "./pages/AuditMetricsPage.vue";
import ChatPage from "./pages/ChatPage.vue";
import ImprovedChatPage from "./pages/ImprovedChatPage.vue";
import MediaSplitterPage from "./pages/MediaSplitterPage.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/investigations" },
    {
      path: "/chat",
      component: ChatPage,
      meta: {
        headerTitle: "Chat",
        headerSubtitle: "Ollama-powered AI assistant",
      },
    },
    {
      path: "/improved-chat",
      component: ImprovedChatPage,
      meta: {
        headerTitle: "Improved chat",
        headerSubtitle: "Sources, conversation, and outputs side by side",
      },
    },
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
    {
      path: "/media",
      component: MediaSplitterPage,
      meta: {
        headerTitle: "Media Tools",
        headerSubtitle: "Split media or extract audio.",
      },
    },
  ],
});

export default router;
