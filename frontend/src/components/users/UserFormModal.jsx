import { useState } from "react";
import { useForm } from "react-hook-form";
import { createUser, updateUser } from "../../api/users";
import { ROLE_OPTIONS } from "../../utils/roles";
import Alert from "../Alert";
import Button from "../Button";
import Field, { inputClass } from "../Field";
import Modal from "../Modal";

const PASSWORD_RULES = {
  required: "Password is required",
  minLength: { value: 10, message: "At least 10 characters" },
  validate: (v) => (/[A-Za-z]/.test(v) && /\d/.test(v)) || "Use letters and numbers",
};

export default function UserFormModal({ user, isSelf, onClose, onSaved }) {
  const isEdit = Boolean(user);
  const [serverError, setServerError] = useState("");
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    defaultValues: {
      username: user?.username ?? "",
      full_name: user?.full_name ?? "",
      email: user?.email ?? "",
      role: user?.role ?? "operator",
      is_active: user?.is_active ?? true,
      password: "",
    },
  });

  const onSubmit = async (values) => {
    setServerError("");
    try {
      if (isEdit) {
        const payload = { full_name: values.full_name, email: values.email };
        if (!isSelf) {
          payload.role = values.role;
          payload.is_active = values.is_active;
        }
        await updateUser(user.id, payload);
      } else {
        await createUser({
          username: values.username,
          full_name: values.full_name,
          email: values.email,
          role: values.role,
          password: values.password,
        });
      }
      onSaved();
    } catch (err) {
      setServerError(err.message);
    }
  };

  return (
    <Modal title={isEdit ? "Edit user" : "Add user"} onClose={onClose}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <Alert>{serverError}</Alert>
        <Field label="Full name" htmlFor="full_name" error={errors.full_name?.message}>
          <input id="full_name" className={inputClass} {...register("full_name", { required: "Full name is required" })} />
        </Field>
        <Field label="Username" htmlFor="username" error={errors.username?.message}>
          <input
            id="username"
            className={inputClass}
            autoCapitalize="none"
            disabled={isEdit}
            {...register("username", {
              required: "Username is required",
              minLength: { value: 3, message: "At least 3 characters" },
              pattern: { value: /^[A-Za-z0-9_.-]+$/, message: "Letters, numbers, . - _ only" },
            })}
          />
        </Field>
        <Field label="Email" htmlFor="email" error={errors.email?.message}>
          <input
            id="email"
            type="email"
            className={inputClass}
            {...register("email", { required: "Email is required", pattern: { value: /^\S+@\S+\.\S+$/, message: "Enter a valid email" } })}
          />
        </Field>
        <Field label="Role" htmlFor="role" hint={isSelf ? "You cannot change your own role" : undefined}>
          <select id="role" className={inputClass} disabled={isSelf} {...register("role")}>
            {ROLE_OPTIONS.map((r) => (
              <option key={r.value} value={r.value}>{r.label}</option>
            ))}
          </select>
        </Field>
        {!isEdit && (
          <Field label="Temporary password" htmlFor="password" error={errors.password?.message} hint="Minimum 10 characters, letters and numbers">
            <input id="password" type="password" autoComplete="new-password" className={inputClass} {...register("password", PASSWORD_RULES)} />
          </Field>
        )}
        {isEdit && (
          <label className="flex min-h-11 items-center gap-3 text-sm text-slate-700">
            <input type="checkbox" className="h-5 w-5 rounded border-slate-300" disabled={isSelf} {...register("is_active")} />
            Account active
          </label>
        )}
        <div className="flex flex-col-reverse gap-2 pt-2 sm:flex-row sm:justify-end">
          <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
          <Button type="submit" loading={isSubmitting}>{isEdit ? "Save changes" : "Create user"}</Button>
        </div>
      </form>
    </Modal>
  );
}
