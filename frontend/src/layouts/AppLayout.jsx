import { Cog, LayoutDashboard, LogOut, QrCode, ScanLine, UserCircle, Users } from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import RoleBadge from "../components/RoleBadge";
import { useAuth } from "../context/AuthContext";
import { ROLES } from "../utils/roles";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/machines", label: "Machines", icon: Cog },
  { to: "/scan", label: "Scan", icon: ScanLine },
  { to: "/users", label: "Users", icon: Users, roles: [ROLES.ADMIN] },
  { to: "/profile", label: "Profile", icon: UserCircle },
];

function useNavItems() {
  const { user } = useAuth();
  return NAV_ITEMS.filter((item) => !item.roles || item.roles.includes(user.role));
}

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const items = useNavItems();

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="min-h-screen lg:flex">
      <aside className="hidden w-64 shrink-0 flex-col bg-navy-900 text-white lg:flex">
        <div className="flex items-center gap-2.5 px-6 py-6">
          <QrCode className="h-6 w-6 text-navy-200" aria-hidden="true" />
          <span className="text-lg font-semibold tracking-tight">MachineQR</span>
        </div>
        <nav className="flex-1 space-y-1 px-3">
          {items.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive ? "bg-white/10 text-white" : "text-navy-200 hover:bg-white/5 hover:text-white"
                }`
              }
            >
              <Icon className="h-5 w-5" aria-hidden="true" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-white/10 p-4">
          <p className="truncate text-sm font-medium">{user.full_name}</p>
          <div className="mt-1 mb-3"><RoleBadge role={user.role} /></div>
          <button onClick={handleLogout} className="flex min-h-11 items-center gap-2 text-sm text-navy-200 hover:text-white">
            <LogOut className="h-4 w-4" aria-hidden="true" /> Sign out
          </button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 lg:hidden">
          <div className="flex items-center gap-2">
            <QrCode className="h-5 w-5 text-navy-800" aria-hidden="true" />
            <span className="font-semibold text-navy-900">MachineQR</span>
          </div>
          <button onClick={handleLogout} className="flex min-h-11 min-w-11 items-center justify-center rounded-lg text-slate-600 hover:bg-slate-100" aria-label="Sign out">
            <LogOut className="h-5 w-5" />
          </button>
        </header>

        <main className="mx-auto w-full max-w-6xl flex-1 px-4 pb-24 pt-5 sm:px-6 lg:px-8 lg:pb-10 lg:pt-8">
          <Outlet />
        </main>

        <nav className="fixed inset-x-0 bottom-0 z-30 flex border-t border-slate-200 bg-white pb-[env(safe-area-inset-bottom)] lg:hidden">
          {items.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex min-h-14 flex-1 flex-col items-center justify-center gap-0.5 text-xs font-medium ${
                  isActive ? "text-navy-800" : "text-slate-500"
                }`
              }
            >
              <Icon className="h-5 w-5" aria-hidden="true" />
              {label}
            </NavLink>
          ))}
        </nav>
      </div>
    </div>
  );
}
