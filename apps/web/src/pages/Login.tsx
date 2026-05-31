import { useState } from "react";

import { login } from "../api/client";
import type { AuthResponse } from "../types/api";

export function Login({ onLogin }: { onLogin: (auth: AuthResponse) => void }) {
  const [email, setEmail] = useState("owner@gyutron.local");
  const [password, setPassword] = useState("ChangeMe123!");
  const [error, setError] = useState<string>();

  async function submit() {
    try {
      const auth = await login({ email, password });
      window.localStorage.setItem("gyutron_session_token", auth.token);
      onLogin(auth);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Login failed.");
    }
  }

  return (
    <main className="onboarding-shell">
      <section className="onboarding-card compact-card">
        <p className="eyebrow">Local admin</p>
        <h1>Sign in to GyuTron</h1>
        <label>Email<input value={email} onChange={(event) => setEmail(event.target.value)} /></label>
        <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
        {error ? <div className="inline-error">{error}</div> : null}
        <button className="button primary" onClick={submit} type="button">Login</button>
      </section>
    </main>
  );
}
