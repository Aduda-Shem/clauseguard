import { useState } from "react";

import { apiErrorMessage } from "../api/client";
import { useLogin, useRegister } from "../api/hooks";

export default function AuthScreen({ onAuthenticated }) {
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const login = useLogin();
  const register = useRegister();
  const pending = login.isPending || register.isPending;
  const error = login.error || register.error;

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (mode === "login") {
      await login.mutateAsync({ username, password });
    } else {
      await register.mutateAsync({ username, email, password });
    }
    onAuthenticated();
  };

  return (
    <div className="auth-shell">
      <div className="auth-panel">
        <div className="brandmark">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
            <path
              d="M6 3h9l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"
              stroke="#C4A25C"
              strokeWidth="1.6"
              strokeLinejoin="round"
            />
            <path d="M9 12.5h6M9 15.5h6M9 9.5h3" stroke="#C4A25C" strokeWidth="1.6" strokeLinecap="round" />
          </svg>
        </div>
        <h1 className="auth-heading">
          Read the fine print
          <br />
          <span className="hl-heading">
            <span>without the headache.</span>
          </span>
        </h1>
        <p className="auth-sub">
          Upload any contract. Get a clause-by-clause risk review and the questions worth asking -
          before you sign.
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            Username
            <input value={username} onChange={(e) => setUsername(e.target.value)} required autoFocus />
          </label>
          {mode === "signup" && (
            <label>
              Email <span className="optional">(optional)</span>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
            </label>
          )}
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={mode === "signup" ? 8 : undefined}
            />
          </label>

          <button className="btn btn-primary" type="submit" disabled={pending}>
            {pending ? "Please wait..." : mode === "login" ? "Log in" : "Create account"}
          </button>
          {error && <p className="auth-error">{apiErrorMessage(error)}</p>}
        </form>

        <button
          type="button"
          className="auth-toggle"
          onClick={() => setMode(mode === "login" ? "signup" : "login")}
        >
          {mode === "login" ? "Don't have an account? Sign up" : "Already have an account? Log in"}
        </button>

        <p className="legal-note">
          ClauseGuard provides educational information, not legal advice. A human always makes the
          final Approve, Negotiate, or Escalate decision.
        </p>
      </div>
    </div>
  );
}
