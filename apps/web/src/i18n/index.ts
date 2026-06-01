import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";

import en from "./locales/en.json";
import zhCN from "./locales/zh-CN.json";

export const LANGUAGE_STORAGE_KEY = "gyutron_lang";
export const supportedLanguages = ["en", "zh-CN"] as const;
export type SupportedLanguage = (typeof supportedLanguages)[number];

function normalizeLanguage(language?: string | null): SupportedLanguage {
  if (!language) {
    return "en";
  }
  return language.toLowerCase().startsWith("zh") ? "zh-CN" : "en";
}

export function getInitialLanguage(): SupportedLanguage {
  const stored = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
  if (stored) {
    return normalizeLanguage(stored);
  }
  return normalizeLanguage(window.navigator.language);
}

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      "zh-CN": { translation: zhCN },
    },
    lng: getInitialLanguage(),
    fallbackLng: "en",
    interpolation: {
      escapeValue: false,
    },
    returnEmptyString: false,
    detection: {
      order: ["localStorage", "navigator"],
      lookupLocalStorage: LANGUAGE_STORAGE_KEY,
      caches: ["localStorage"],
      convertDetectedLanguage: normalizeLanguage,
    },
  });

i18n.on("languageChanged", (language) => {
  window.localStorage.setItem(LANGUAGE_STORAGE_KEY, normalizeLanguage(language));
  document.documentElement.lang = normalizeLanguage(language);
});

document.documentElement.lang = getInitialLanguage();

export function changeLanguage(language: SupportedLanguage) {
  return i18n.changeLanguage(language);
}

export function getCurrentLanguage(): SupportedLanguage {
  return normalizeLanguage(i18n.language);
}

export default i18n;
