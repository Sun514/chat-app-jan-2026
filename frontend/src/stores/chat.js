import { reactive } from "vue";

const SETTINGS_KEY = "chat.settings.v1";

const defaultSettings = {
  endpoint: import.meta.env.VITE_OLLAMA_ENDPOINT || "http://localhost:11434",
  model: "qwen3-next-thinking",
};

const readSettings = () => {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    return raw
      ? { ...defaultSettings, ...JSON.parse(raw) }
      : { ...defaultSettings };
  } catch {
    return { ...defaultSettings };
  }
};

const settings = reactive(readSettings());

const persistSettings = () => {
  try {
    localStorage.setItem(
      SETTINGS_KEY,
      JSON.stringify({ endpoint: settings.endpoint, model: settings.model }),
    );
  } catch {
    // ignore
  }
};

export { settings, persistSettings };
