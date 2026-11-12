import { useState, type FormEvent, type ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AuthError, useAuth } from "../auth";
import { useToast } from "../toast";

export interface Field {
  name: string;
  label: string;
  type: string;
  autoComplete: string;
}

interface Props {
  title: string;
  subtitle: string;
  fields: Field[];
  submitLabel: string;
  busyLabel: string;
  footer: ReactNode;
  /** Returns field errors found in the browser before anything is sent. */
  validate: (values: Record<string, string>) => Record<string, string>;
  onSubmit: (values: Record<string, string>) => Promise<unknown>;
}

/** The colourful panel beside the Log In / Create Account forms. */
function AuthArt() {
  return (
    <aside className="auth-art" aria-hidden="true">
      <span className="blob blob-coral float-slow" style={{ width: 170, height: 170, right: -80, top: -95 }} />
      <span className="blob blob-butter float-slower" style={{ width: 70, height: 70, left: "48%", bottom: 40 }} />
      <span className="blob blob-lavender" style={{ width: 260, height: 260, left: -110, bottom: -120, opacity: 0.55 }} />
      <div>
        <p className="eyebrow" style={{ color: "var(--butter)" }}>Campus Customs club</p>
        <h2>
          Your shop, <em>remembered.</em>
        </h2>
        <p>Log in and our shopping assistant picks up right where you left off, from gift ideas to sizes.</p>
      </div>
      <div className="art-photos">
        <span className="collage-card">
          <img src="/images/champion-reverse-weave-hoodie-1.jpg" alt="" />
        </span>
        <span className="collage-card">
          <img src="/images/berkeley-1-4-zip.jpg" alt="" />
        </span>
      </div>
    </aside>
  );
}

/** Shared layout for the Log In and Create Account pages. */
export default function AuthForm({ title, subtitle, fields, submitLabel, busyLabel, footer, validate, onSubmit }: Props) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();
  const [values, setValues] = useState<Record<string, string>>({});
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) {
    return (
      <div className="container page auth-page">
        <div className="auth-shell reveal">
        <AuthArt />
        <div className="auth-card">
          <h1>You're logged in</h1>
          <p className="muted">
            Signed in as <strong>{user.first_name} {user.last_name}</strong> ({user.email}).
          </p>
          <div className="auth-actions">
            <Link to="/products" className="btn btn-primary btn-lg">Keep shopping</Link>
            <button className="btn btn-ghost btn-lg" onClick={() => logout()}>Log Out</button>
          </div>
        </div>
        </div>
      </div>
    );
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    const problems = validate(values);
    setFieldErrors(problems);
    if (Object.keys(problems).length) {
      setError("Please fix the highlighted fields.");
      return;
    }
    setBusy(true);
    try {
      const u = (await onSubmit(values)) as { first_name?: string } | undefined;
      toast(`Welcome${u?.first_name ? `, ${u.first_name}` : ""}! You're logged in.`, "success");
      navigate("/", { state: { welcome: true } });
    } catch (err) {
      const authErr = err instanceof AuthError ? err : new AuthError("Something went wrong. Please try again.");
      setError(authErr.message);
      setFieldErrors(authErr.fields);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="container page auth-page">
      <div className="auth-shell reveal">
      <AuthArt />
      <div className="auth-card">
        <h1>{title}</h1>
        <p className="muted">{subtitle}</p>
        <form onSubmit={handleSubmit} noValidate>
          {fields.map((f) => {
            const msg = fieldErrors[f.name];
            return (
              <div className={`field ${msg ? "has-error" : ""}`} key={f.name}>
                <label htmlFor={f.name}>{f.label}</label>
                <input
                  id={f.name}
                  name={f.name}
                  type={f.type}
                  autoComplete={f.autoComplete}
                  required
                  aria-invalid={Boolean(msg)}
                  aria-describedby={msg ? `${f.name}-error` : undefined}
                  value={values[f.name] ?? ""}
                  onChange={(e) => {
                    setValues((v) => ({ ...v, [f.name]: e.target.value }));
                    if (msg) setFieldErrors(({ [f.name]: _, ...rest }) => rest);
                  }}
                />
                {msg && <p className="field-error" id={`${f.name}-error`}>{msg}</p>}
              </div>
            );
          })}
          {error && <p className="notice notice-error" role="alert">{error}</p>}
          <button className="btn btn-primary btn-lg btn-block" type="submit" disabled={busy}>
            {busy ? busyLabel : submitLabel}
          </button>
        </form>
        <p className="auth-footer">{footer}</p>
      </div>
      </div>
    </div>
  );
}

export const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
