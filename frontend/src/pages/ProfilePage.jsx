import { useState } from "react";
import { useForm } from "react-hook-form";
import { changePassword } from "../api/auth";
import Alert from "../components/Alert";
import Button from "../components/Button";
import Field, { inputClass } from "../components/Field";
import RoleBadge from "../components/RoleBadge";
import { useAuth } from "../context/AuthContext";

export default function ProfilePage() {
  const { user } = useAuth();
  const [serverError, setServerError] = useState("");
  const [success, setSuccess] = useState("");
  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm({ defaultValues: { current: "", next: "", confirm: "" } });

  const onSubmit = async ({ current, next }) => {
    setServerError("");
    setSuccess("");
    try {
      await changePassword(current, next);
      setSuccess("Password updated.");
      reset();
    } catch (err) {
      setServerError(err.message);
    }
  };

  return (
    <div className="max-w-xl">
      <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Profile</h1>

      <section className="mt-5 rounded-2xl bg-white p-5 shadow-sm">
        <dl className="space-y-3 text-sm">
          <div className="flex justify-between gap-4"><dt className="text-slate-500">Name</dt><dd className="font-medium">{user.full_name}</dd></div>
          <div className="flex justify-between gap-4"><dt className="text-slate-500">Username</dt><dd className="font-medium">{user.username}</dd></div>
          <div className="flex justify-between gap-4"><dt className="text-slate-500">Email</dt><dd className="break-all font-medium">{user.email}</dd></div>
          <div className="flex justify-between gap-4"><dt className="text-slate-500">Role</dt><dd><RoleBadge role={user.role} /></dd></div>
        </dl>
      </section>

      <section className="mt-5 rounded-2xl bg-white p-5 shadow-sm">
        <h2 className="mb-4 text-base font-semibold text-slate-900">Change password</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          <Alert>{serverError}</Alert>
          <Alert type="success">{success}</Alert>
          <Field label="Current password" htmlFor="current" error={errors.current?.message}>
            <input id="current" type="password" autoComplete="current-password" className={inputClass} {...register("current", { required: "Required" })} />
          </Field>
          <Field label="New password" htmlFor="next" error={errors.next?.message} hint="Minimum 10 characters, letters and numbers">
            <input
              id="next"
              type="password"
              autoComplete="new-password"
              className={inputClass}
              {...register("next", {
                required: "Required",
                minLength: { value: 10, message: "At least 10 characters" },
                validate: (v) => (/[A-Za-z]/.test(v) && /\d/.test(v)) || "Use letters and numbers",
              })}
            />
          </Field>
          <Field label="Confirm new password" htmlFor="confirm" error={errors.confirm?.message}>
            <input
              id="confirm"
              type="password"
              autoComplete="new-password"
              className={inputClass}
              {...register("confirm", { validate: (v) => v === watch("next") || "Passwords do not match" })}
            />
          </Field>
          <Button type="submit" loading={isSubmitting}>Update password</Button>
        </form>
      </section>
    </div>
  );
}
