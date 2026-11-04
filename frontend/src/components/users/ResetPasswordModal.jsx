import { useState } from "react";
import { useForm } from "react-hook-form";
import { resetUserPassword } from "../../api/users";
import Alert from "../Alert";
import Button from "../Button";
import Field, { inputClass } from "../Field";
import Modal from "../Modal";

export default function ResetPasswordModal({ user, onClose, onDone }) {
  const [serverError, setServerError] = useState("");
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({ defaultValues: { password: "" } });

  const onSubmit = async ({ password }) => {
    setServerError("");
    try {
      await resetUserPassword(user.id, password);
      onDone();
    } catch (err) {
      setServerError(err.message);
    }
  };

  return (
    <Modal title={`Reset password: ${user.username}`} onClose={onClose}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <Alert>{serverError}</Alert>
        <Field label="New password" htmlFor="reset_password" error={errors.password?.message} hint="Minimum 10 characters, letters and numbers">
          <input
            id="reset_password"
            type="password"
            autoComplete="new-password"
            className={inputClass}
            {...register("password", {
              required: "Password is required",
              minLength: { value: 10, message: "At least 10 characters" },
              validate: (v) => (/[A-Za-z]/.test(v) && /\d/.test(v)) || "Use letters and numbers",
            })}
          />
        </Field>
        <div className="flex flex-col-reverse gap-2 pt-2 sm:flex-row sm:justify-end">
          <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
          <Button type="submit" loading={isSubmitting}>Reset password</Button>
        </div>
      </form>
    </Modal>
  );
}
