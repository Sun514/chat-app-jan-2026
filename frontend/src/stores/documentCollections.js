import { reactive } from "vue";

const STORAGE_KEY = "documentCollections.v1";

const formatBytes = (value) => {
  if (!value && value !== 0) return "";
  if (value < 1024) return `${value} B`;
  const kb = value / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
};

const normalizeCollection = (collection) => ({
  id:
    collection.id ||
    `col-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
  name: collection.name || "Untitled folder",
  description: collection.description || "",
  createdAt: collection.createdAt || new Date().toLocaleDateString(),
  files: Array.isArray(collection.files)
    ? collection.files.map((file) => ({
        id:
          file.id ||
          `file-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
        name: file.name || "Untitled",
        bytes: typeof file.bytes === "number" ? file.bytes : 0,
        sizeLabel: file.sizeLabel || formatBytes(file.bytes || 0),
        uploadedAt: file.uploadedAt || new Date().toLocaleString(),
        type: file.type || "Unknown",
      }))
    : [],
});

const readStorage = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    if (!Array.isArray(parsed)) return [];
    return parsed.map(normalizeCollection);
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
  return `col-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
};

const createCollection = ({ name, description }) => {
  const collection = normalizeCollection({
    id: ensureId(),
    name: name || "Untitled folder",
    description: description || "",
    createdAt: new Date().toLocaleDateString(),
    files: [],
  });
  state.items.unshift(collection);
  persist(state.items);
  return collection;
};

const removeCollection = (id) => {
  const next = state.items.filter((item) => item.id !== id);
  state.items.splice(0, state.items.length, ...next);
  persist(state.items);
};

const addFilesToCollection = (id, files) => {
  const target = state.items.find((item) => item.id === id);
  if (!target || !Array.isArray(files)) return;
  const records = files.map((file) => ({
    id: ensureId(),
    name: file.name,
    bytes: file.size || 0,
    sizeLabel: formatBytes(file.size || 0),
    uploadedAt: new Date().toLocaleString(),
    type: file.type || "Unknown",
  }));
  target.files.unshift(...records);
  persist(state.items);
};

const removeFileFromCollection = (collectionId, fileId) => {
  const target = state.items.find((item) => item.id === collectionId);
  if (!target) return;
  target.files = target.files.filter((file) => file.id !== fileId);
  persist(state.items);
};

const getCollection = (id) =>
  state.items.find((item) => item.id === id) || null;

export {
  state,
  createCollection,
  removeCollection,
  addFilesToCollection,
  removeFileFromCollection,
  getCollection,
};
