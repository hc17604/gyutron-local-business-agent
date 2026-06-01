import { useState } from "react";
import { useTranslation } from "react-i18next";

import { login } from "../api/client";
import type { AuthResponse } from "../types/api";

export function Login({ onLogin }: { onLogin: (auth: AuthResponse) => void }) {
  const { t } = useTranslation();
  const [email, setEmail] = useState("owner@gyutron.local");
  const [password, setPassword] = useState("ChangeMe123!");
  const [error, setError] = useState<string>();

  async function submit() {
    try {
      const auth = await login({ email, password });
      window.localStorage.setItem("gyutron_session_token", auth.token);
      onLogin(auth);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : t("login.failed", { defaultValue: "Login failed." }));
    }
  }

  return (
    <main className="onboarding-shell">
      <section className="onboarding-card compact-card">
        <p className="eyebrow">{t("login.eyebrow")}</p>
        <h1>{t("login.title")}</h1>
        <label>{t("login.email")}<input value={email} onChange={(event) => setEmail(event.target.value)} /></label>
        <label>{t("login.password")}<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
        {error ? <div className="inline-error">{error}</div> : null}
        <button className="button primary" onClick={submit} type="button">{t("login.submit")}</button>
      </section>
    </main>
  );
}
