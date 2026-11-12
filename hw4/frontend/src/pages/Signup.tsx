import { Link } from "react-router-dom";
import { useAuth } from "../auth";
import AuthForm, { EMAIL_RE } from "./AuthForm";

export default function Signup() {
  const { signup } = useAuth();
  return (
    <AuthForm
      title="Create your account"
      subtitle="Join Campus Customs to save your chats with our shopping assistant."
      submitLabel="Create Account"
      busyLabel="Creating your account…"
      fields={[
        { name: "first_name", label: "First name", type: "text", autoComplete: "given-name" },
        { name: "last_name", label: "Last name", type: "text", autoComplete: "family-name" },
        { name: "email", label: "Email address", type: "email", autoComplete: "email" },
        { name: "password", label: "Password (at least 8 characters)", type: "password", autoComplete: "new-password" },
        { name: "confirm_password", label: "Confirm password", type: "password", autoComplete: "new-password" },
      ]}
      validate={(v) => {
        const e: Record<string, string> = {};
        if (!v.first_name?.trim()) e.first_name = "Please enter your first name.";
        if (!v.last_name?.trim()) e.last_name = "Please enter your last name.";
        if (!v.email?.trim()) e.email = "Please enter your email address.";
        else if (!EMAIL_RE.test(v.email.trim())) e.email = "Please enter a valid email address.";
        if (!v.password) e.password = "Please choose a password.";
        else if (v.password.length < 8) e.password = "Password must be at least 8 characters.";
        if (!v.confirm_password) e.confirm_password = "Please confirm your password.";
        else if (v.password !== v.confirm_password) e.confirm_password = "Passwords don't match.";
        return e;
      }}
      onSubmit={(v) =>
        signup({
          first_name: v.first_name.trim(),
          last_name: v.last_name.trim(),
          email: v.email.trim(),
          password: v.password,
          confirm_password: v.confirm_password,
        })
      }
      footer={<>Already have an account? <Link to="/login">Log in</Link></>}
    />
  );
}
