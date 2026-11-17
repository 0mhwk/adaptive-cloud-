// frontend/src/store/themeStore.ts
import { create } from 'zustand';

interface ThemeState {
  isDark: boolean;
  toggleTheme: () => void;
  setTheme: (isDark: boolean) => void;
}

export const useThemeStore = create<ThemeState>((set) => {
  // Always default to true OLED black theme for SecOps
  const saved = localStorage.getItem('adaptivecloud_theme');
  const initialDark = saved !== null ? saved === 'dark' : true;

  // Enforce dark class on DOM
  if (initialDark) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }

  return {
    isDark: initialDark,
    toggleTheme: () =>
      set((state) => {
        const next = !state.isDark;
        if (next) {
          document.documentElement.classList.add('dark');
          localStorage.setItem('adaptivecloud_theme', 'dark');
        } else {
          document.documentElement.classList.remove('dark');
          localStorage.setItem('adaptivecloud_theme', 'light');
        }
        return { isDark: next };
      }),
    setTheme: (isDark: boolean) => {
      if (isDark) {
        document.documentElement.classList.add('dark');
        localStorage.setItem('adaptivecloud_theme', 'dark');
      } else {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('adaptivecloud_theme', 'light');
      }
      set({ isDark });
    },
  };
});
