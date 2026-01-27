import { reactive } from "vue";

const STORAGE_KEY = "investigations.v1";

const normalizeInvestigation = (item) => ({
  id: item.id || `inv-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
  name: item.name || "Untitled investigation",
  description: item.description || "",
  owner: item.owner || "Internal",
  createdAt: item.createdAt || new Date().toLocaleDateString(),
  lastUploadAt: item.lastUploadAt || "Awaiting",
  lastQuery: item.lastQuery || "None",
  documents: Array.isArray(item.documents) ? item.documents : [],
  collectionIds: Array.isArray(item.collectionIds) ? item.collectionIds : [],
});

const readStorage = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    if (!Array.isArray(parsed)) return [];
    return parsed.map(normalizeInvestigation);
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
  const investigation = normalizeInvestigation({
    id: ensureId(),
    name,
    description,
    owner,
    createdAt: new Date().toLocaleDateString(),
    lastUploadAt: "Awaiting",
    lastQuery: "None",
    documents: [],
    collectionIds: [],
  });
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

const toggleInvestigationCollection = (id, collectionId) => {
  const target = state.items.find((item) => item.id === id);
  if (!target) return null;
  if (!Array.isArray(target.collectionIds)) {
    target.collectionIds = [];
  }
  if (target.collectionIds.includes(collectionId)) {
    target.collectionIds = target.collectionIds.filter((entry) => entry !== collectionId);
  } else {
    target.collectionIds = [...target.collectionIds, collectionId];
  }
  persist(state.items);
  return target;
};

const setInvestigationCollections = (id, collectionIds) => {
  const target = state.items.find((item) => item.id === id);
  if (!target) return null;
  target.collectionIds = Array.isArray(collectionIds) ? collectionIds : [];
  persist(state.items);
  return target;
};

export {
  state,
  createInvestigation,
  updateInvestigation,
  removeInvestigation,
  addDocument,
  setLastQuery,
  getInvestigation,
  toggleInvestigationCollection,
  setInvestigationCollections,
};
