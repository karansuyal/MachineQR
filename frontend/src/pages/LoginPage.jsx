import { Eye, EyeOff, QrCode } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import Alert from "../components/Alert";
import Button from "../components/Button";
import Field, { inputClass } from "../components/Field";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [showPassword, setShowPassword] = useState(false);
  const [serverError, setServerError] = useState("");
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({ defaultValues: { username: "", password: "" } });

  const redirectTo = location.state?.from
    ? `${location.state.from.pathname}${location.state.from.search ?? ""}`
    : "/";

  if (user) return <Navigate to={redirectTo} replace />;

  const onSubmit = async ({ username, password }) => {
    setServerError("");
    try {
      await login(username, password);
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setServerError(err.message);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-navy-50 px-4 py-8">
      <div className="w-full max-w-sm">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-navy-900 text-white">
            <QrCode className="h-6 w-6" aria-hidden="true" />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-navy-900">MachineQR</h1>
          <p className="mt-1 text-sm text-slate-500">Sign in to continue</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 rounded-2xl bg-white p-6 shadow-sm" noValidate>
          <Alert>{serverError}</Alert>
          <Field label="Username" htmlFor="username" error={errors.username?.message}>
            <input
              id="username"
              className={inputClass}
              autoComplete="username"
              autoCapitalize="none"
              autoCorrect="off"
              {...register("username", { required: "Enter your username" })}
            />
          </Field>
          <Field label="Password" htmlFor="password" error={errors.password?.message}>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                className={`${inputClass} pr-12`}
                autoComplete="current-password"
                {...register("password", { required: "Enter your password" })}
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute inset-y-0 right-0 flex w-12 items-center justify-center text-slate-500"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
              </button>
            </div>
          </Field>
          <Button type="submit" className="w-full" loading={isSubmitting}>Sign in</Button>
        </form>
      </div>
    </div>
  );
}
