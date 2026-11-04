import { roleLabel } from "../utils/roles";

const STYLES = {
  admin: "bg-navy-100 text-navy-800",
  technician: "bg-amber-100 text-amber-800",
  operator: "bg-slate-100 text-slate-700",
};

export default function RoleBadge({ role }) {
  return (
    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${STYLES[role] ?? STYLES.operator}`}>
      {roleLabel(role)}
    </span>
  );
}
