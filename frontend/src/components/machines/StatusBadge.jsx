import { statusLabel } from "../../utils/machines";

const STYLES = {
  running: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  stopped: "bg-red-50 text-red-700 ring-red-600/20",
  under_maintenance: "bg-amber-50 text-amber-800 ring-amber-600/20",
};

const DOTS = { running: "bg-emerald-500", stopped: "bg-red-500", under_maintenance: "bg-amber-500" };

export default function StatusBadge({ status }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${STYLES[status] ?? "bg-slate-50 text-slate-700 ring-slate-500/20"}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${DOTS[status] ?? "bg-slate-400"}`} />
      {statusLabel(status)}
    </span>
  );
}
