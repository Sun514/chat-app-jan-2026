import { createApp } from "vue";
import "./style.css";
import App from "./App.vue";
import router from "./router";
import PrimeVue from "primevue/config";
import Aura from "@primeuix/themes/aura";
import { definePreset } from "@primeuix/themes";

const AppTheme = definePreset(Aura, {
  semantic: {
    primary: {
      50: "#fff4eb",
      100: "#ffe5d1",
      200: "#ffccab",
      300: "#ffaf80",
      400: "#ff8f52",
      500: "#ff6a00",
      600: "#db5700",
      700: "#b54400",
      800: "#8f3500",
      900: "#6e2900",
      950: "#3f1400",
    },
  },
  components: {
    button: {
      root: {
        secondary: {
          background: "#1bb2a0",
          hoverBackground: "#169688",
          activeBackground: "#127a6f",
          borderColor: "#1bb2a0",
          hoverBorderColor: "#169688",
          activeBorderColor: "#127a6f",
          color: "#ffffff",
          hoverColor: "#ffffff",
          activeColor: "#ffffff",
        },
      },
      outlined: {
        secondary: {
          color: "#127a6f",
          borderColor: "#1bb2a0",
          hoverBackground: "rgba(27, 178, 160, 0.14)",
          activeBackground: "rgba(27, 178, 160, 0.24)",
        },
      },
      text: {
        secondary: {
          color: "#127a6f",
          hoverBackground: "rgba(27, 178, 160, 0.14)",
          activeBackground: "rgba(27, 178, 160, 0.24)",
        },
      },
    },
  },
});

const app = createApp(App);

app.use(router);
app.use(PrimeVue, {
  theme: {
    preset: AppTheme,
    options: {
      darkModeSelector: false,
    },
  },
});

app.mount("#app");
