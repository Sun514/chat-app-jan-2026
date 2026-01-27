import { reactive } from "vue";

const STORAGE_KEY = "investigations.v1";

const readStorage = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (error) {
    return [];
  }
};

const persist = (items) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  } catch (error) {
    // ignore write errors (private mode, storage full)
  }
};

const state = reactive({
  items: readStorage(),
});

const ensureId = () => {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `inv-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
};

const createInvestigation = ({ name, description, owner }) => {
  const investigation = {
    id: ensureId(),
    name: name || "Untitled investigation",
    description: description || "",
    owner: owner || "Internal",
    createdAt: new Date().toLocaleDateString(),
    lastUploadAt: "Awaiting",
    lastQuery: "None",
    documents: [],
  };
  state.items.unshift(investigation);
  persist(state.items);
  return investigation;
};

const updateInvestigation = (id, updates) => {
  const target = state.items.find((item) => item.id === id);
  if (!target) return null;
  Object.assign(target, updates);
  persist(state.items);
  return target;
};

const removeInvestigation = (id) => {
  const next = state.items.filter((item) => item.id !== id);
  state.items.splice(0, state.items.length, ...next);
  persist(state.items);
};

const addDocument = (id, document) => {
  const target = state.items.find((item) => item.id === id);
  if (!target) return;
  target.documents.unshift(document);
  target.lastUploadAt = document.timestamp || "Uploaded";
  persist(state.items);
};

const setLastQuery = (id, query) => {
  const target = state.items.find((item) => item.id === id);
  if (!target) return;
  target.lastQuery = query || "None";
  persist(state.items);
};

const getInvestigation = (id) => state.items.find((item) => item.id === id) || null;

export {
  state,
  createInvestigation,
  updateInvestigation,
  removeInvestigation,
  addDocument,
  setLastQuery,
  getInvestigation,
};
