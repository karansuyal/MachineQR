import { AlertCircle, CheckCircle2 } from "lucide-react";

const STYLES = {
  error: "border-red-200 bg-red-50 text-red-800",
  success: "border-emerald-200 bg-emerald-50 text-emerald-800",
};

export default function Alert({ type = "error", children }) {
  if (!children) return null;
  const Icon = type === "success" ? CheckCircle2 : AlertCircle;
  return (
    <div className={`flex items-start gap-2 rounded-lg border px-3 py-2.5 text-sm ${STYLES[type]}`} role="alert">
      <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
      <div>{children}</div>
    </div>
  );
}
