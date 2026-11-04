import { useAuth } from "../context/AuthContext";
import RoleBadge from "../components/RoleBadge";

export default function DashboardPage() {
  const { user } = useAuth();
  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Welcome, {user.full_name}</h1>
      <div className="mt-2 flex items-center gap-2 text-sm text-slate-500">
        Signed in as <RoleBadge role={user.role} />
      </div>
      <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-500">
        Machine, fault and maintenance overview will appear here as those modules are built.
      </div>
    </div>
  );
}
