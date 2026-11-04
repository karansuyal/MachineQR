import { KeyRound, Pencil, Plus, Search } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { listUsers } from "../api/users";
import Alert from "../components/Alert";
import Button from "../components/Button";
import { inputClass } from "../components/Field";
import RoleBadge from "../components/RoleBadge";
import Spinner from "../components/Spinner";
import ResetPasswordModal from "../components/users/ResetPasswordModal";
import UserFormModal from "../components/users/UserFormModal";
import { useAuth } from "../context/AuthContext";
import { ROLE_OPTIONS } from "../utils/roles";

function StatusPill({ active }) {
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${active ? "text-emerald-700" : "text-slate-500"}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${active ? "bg-emerald-500" : "bg-slate-400"}`} />
      {active ? "Active" : "Inactive"}
    </span>
  );
}

function RowActions({ user, onEdit, onReset }) {
  return (
    <div className="flex gap-1">
      <button onClick={() => onEdit(user)} className="flex min-h-11 min-w-11 items-center justify-center rounded-lg text-slate-600 hover:bg-slate-100" aria-label={`Edit ${user.username}`}>
        <Pencil className="h-4 w-4" />
      </button>
      <button onClick={() => onReset(user)} className="flex min-h-11 min-w-11 items-center justify-center rounded-lg text-slate-600 hover:bg-slate-100" aria-label={`Reset password for ${user.username}`}>
        <KeyRound className="h-4 w-4" />
      </button>
    </div>
  );
}

export default function UsersPage() {
  const { user: currentUser } = useAuth();
  const [filters, setFilters] = useState({ search: "", role: "", page: 1 });
  const [searchInput, setSearchInput] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [formUser, setFormUser] = useState(undefined);
  const [resetUser, setResetUser] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setData(await listUsers(filters));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    const timer = setTimeout(() => setFilters((f) => (f.search === searchInput ? f : { ...f, search: searchInput, page: 1 })), 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const handleSaved = () => {
    setNotice(formUser ? "User updated." : "User created.");
    setFormUser(undefined);
    load();
  };

  const items = data?.items ?? [];

  return (
    <div>
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Users</h1>
        <Button onClick={() => setFormUser(null)}><Plus className="h-4 w-4" /> Add user</Button>
      </div>

      <div className="mt-4 flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
          <input
            className={`${inputClass} pl-9`}
            placeholder="Search name, username or email"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            aria-label="Search users"
          />
        </div>
        <select
          className={`${inputClass} sm:w-48`}
          value={filters.role}
          onChange={(e) => setFilters((f) => ({ ...f, role: e.target.value, page: 1 }))}
          aria-label="Filter by role"
        >
          <option value="">All roles</option>
          {ROLE_OPTIONS.map((r) => (
            <option key={r.value} value={r.value}>{r.label}</option>
          ))}
        </select>
      </div>

      <div className="mt-4 space-y-3">
        <Alert type="success">{notice}</Alert>
        <Alert>{error}</Alert>
      </div>

      {loading && !data ? (
        <Spinner />
      ) : items.length === 0 && !error ? (
        <div className="mt-4 rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
          No users match your filters.
        </div>
      ) : (
        <>
          <ul className="mt-4 space-y-3 md:hidden">
            {items.map((u) => (
              <li key={u.id} className="rounded-2xl bg-white p-4 shadow-sm">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate font-medium text-slate-900">{u.full_name}</p>
                    <p className="truncate text-sm text-slate-500">@{u.username}</p>
                    <p className="truncate text-sm text-slate-500">{u.email}</p>
                  </div>
                  <RowActions user={u} onEdit={setFormUser} onReset={setResetUser} />
                </div>
                <div className="mt-3 flex items-center justify-between">
                  <RoleBadge role={u.role} />
                  <StatusPill active={u.is_active} />
                </div>
              </li>
            ))}
          </ul>

          <div className="mt-4 hidden overflow-hidden rounded-2xl bg-white shadow-sm md:block">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3 font-medium">Name</th>
                  <th className="px-5 py-3 font-medium">Email</th>
                  <th className="px-5 py-3 font-medium">Role</th>
                  <th className="px-5 py-3 font-medium">Status</th>
                  <th className="px-5 py-3 font-medium"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((u) => (
                  <tr key={u.id}>
                    <td className="px-5 py-3">
                      <p className="font-medium text-slate-900">{u.full_name}</p>
                      <p className="text-slate-500">@{u.username}</p>
                    </td>
                    <td className="px-5 py-3 text-slate-600">{u.email}</td>
                    <td className="px-5 py-3"><RoleBadge role={u.role} /></td>
                    <td className="px-5 py-3"><StatusPill active={u.is_active} /></td>
                    <td className="px-5 py-3"><RowActions user={u} onEdit={setFormUser} onReset={setResetUser} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {data && data.pages > 1 && (
            <div className="mt-4 flex items-center justify-between text-sm text-slate-600">
              <span>Page {data.page} of {data.pages} ({data.total} users)</span>
              <div className="flex gap-2">
                <Button variant="secondary" disabled={data.page <= 1} onClick={() => setFilters((f) => ({ ...f, page: f.page - 1 }))}>Previous</Button>
                <Button variant="secondary" disabled={data.page >= data.pages} onClick={() => setFilters((f) => ({ ...f, page: f.page + 1 }))}>Next</Button>
              </div>
            </div>
          )}
        </>
      )}

      {formUser !== undefined && (
        <UserFormModal
          user={formUser}
          isSelf={formUser?.id === currentUser.id}
          onClose={() => setFormUser(undefined)}
          onSaved={handleSaved}
        />
      )}
      {resetUser && (
        <ResetPasswordModal
          user={resetUser}
          onClose={() => setResetUser(null)}
          onDone={() => {
            setNotice(`Password reset for ${resetUser.username}.`);
            setResetUser(null);
          }}
        />
      )}
    </div>
  );
}
