import { Link } from "react-router-dom";
import { useAuth } from "../auth";
import AuthForm from "./AuthForm";

export default function Login() {
  const { login } = useAuth();
  return (
    <AuthForm
      title="Welcome back"
      subtitle="Log in to your Campus Customs account."
      submitLabel="Log In"
      busyLabel="Logging in…"
      fields={[
        { name: "email", label: "Email", type: "email", autoComplete: "email" },
        { name: "password", label: "Password", type: "password", autoComplete: "current-password" },
      ]}
      validate={(v) => {
        const e: Record<string, string> = {};
        if (!v.email?.trim()) e.email = "Please enter your email.";
        if (!v.password) e.password = "Please enter your password.";
        return e;
      }}
      onSubmit={(v) => login(v.email.trim(), v.password)}
      footer={<>New here? <Link to="/signup">Create an account</Link></>}
    />
  );
}
