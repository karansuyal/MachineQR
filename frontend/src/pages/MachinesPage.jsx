import { ChevronRight, Cog, Plus, Search } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getMachineOptions, listMachines } from "../api/machines";
import Alert from "../components/Alert";
import { inputClass } from "../components/Field";
import Spinner from "../components/Spinner";
import StatusBadge from "../components/machines/StatusBadge";
import { useAuth } from "../context/AuthContext";
import { errorMessage } from "../utils/errors";
import { STATUS_OPTIONS } from "../utils/machines";
import { ROLES } from "../utils/roles";

const CHIPS = [{ value: "", label: "All" }, ...STATUS_OPTIONS];

export default function MachinesPage() {
  const { hasRole } = useAuth();
  const isAdmin = hasRole(ROLES.ADMIN);
  const [filters, setFilters] = useState({ search: "", status: "", department: "", includeInactive: false, page: 1 });
  const [searchInput, setSearchInput] = useState("");
  const [options, setOptions] = useState({ departments: [] });
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setData(await listMachines(filters));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    getMachineOptions().then(setOptions).catch(() => {});
  }, []);

  useEffect(() => {
    const timer = setTimeout(
      () => setFilters((f) => (f.search === searchInput ? f : { ...f, search: searchInput, page: 1 })),
      300
    );
    return () => clearTimeout(timer);
  }, [searchInput]);

  const update = (patch) => setFilters((f) => ({ ...f, ...patch, page: 1 }));
  const items = data?.items ?? [];

  return (
    <div>
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Machines</h1>
        {isAdmin && (
          <Link to="/machines/new" className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-navy-800 px-4 text-sm font-medium text-white hover:bg-navy-700">
            <Plus className="h-4 w-4" /> Add machine
          </Link>
        )}
      </div>

      <div className="mt-4 flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
          <input
            className={`${inputClass} pl-9`}
            placeholder="Search ID, name, manufacturer or model"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            aria-label="Search machines"
          />
        </div>
        <select className={`${inputClass} sm:w-52`} value={filters.department} onChange={(e) => update({ department: e.target.value })} aria-label="Filter by department">
          <option value="">All departments</option>
          {options.departments.map((d) => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
      </div>

      <div className="-mx-4 mt-3 flex gap-2 overflow-x-auto px-4 pb-1 sm:mx-0 sm:px-0">
        {CHIPS.map((chip) => (
          <button
            key={chip.value}
            onClick={() => update({ status: chip.value })}
            className={`min-h-11 shrink-0 rounded-full px-4 text-sm font-medium transition-colors ${
              filters.status === chip.value ? "bg-navy-800 text-white" : "bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50"
            }`}
          >
            {chip.label}
          </button>
        ))}
      </div>

      {isAdmin && (
        <label className="mt-3 flex min-h-11 items-center gap-3 text-sm text-slate-600">
          <input type="checkbox" className="h-5 w-5 rounded border-slate-300" checked={filters.includeInactive} onChange={(e) => update({ includeInactive: e.target.checked })} />
          Include deactivated machines
        </label>
      )}

      <div className="mt-3"><Alert>{error}</Alert></div>

      {loading && !data ? (
        <Spinner />
      ) : items.length === 0 && !error ? (
        <div className="mt-4 rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
          {isAdmin ? "No machines found. Add the first machine to get started." : "No machines are assigned to you yet. Contact an administrator."}
        </div>
      ) : (
        <>
          <ul className="mt-4 space-y-3 md:hidden">
            {items.map((m) => (
              <li key={m.id}>
                <Link to={`/machine/${m.machine_code}`} className="flex items-center gap-3 rounded-2xl bg-white p-4 shadow-sm active:bg-slate-50">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-navy-50 text-navy-700"><Cog className="h-5 w-5" /></div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium text-slate-900">{m.name}</p>
                    <p className="truncate text-xs text-slate-500">{m.machine_code}{m.department ? ` · ${m.department}` : ""}{m.location ? ` · ${m.location}` : ""}</p>
                    <div className="mt-2 flex items-center gap-2">
                      <StatusBadge status={m.status} />
                      {!m.is_active && <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">Deactivated</span>}
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 shrink-0 text-slate-400" aria-hidden="true" />
                </Link>
              </li>
            ))}
          </ul>

          <div className="mt-4 hidden overflow-hidden rounded-2xl bg-white shadow-sm md:block">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3 font-medium">ID</th>
                  <th className="px-5 py-3 font-medium">Machine</th>
                  <th className="px-5 py-3 font-medium">Department</th>
                  <th className="px-5 py-3 font-medium">Location</th>
                  <th className="px-5 py-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((m) => (
                  <tr key={m.id} className="hover:bg-slate-50">
                    <td className="px-5 py-3 font-medium text-navy-800"><Link to={`/machine/${m.machine_code}`}>{m.machine_code}</Link></td>
                    <td className="px-5 py-3">
                      <Link to={`/machine/${m.machine_code}`} className="font-medium text-slate-900 hover:underline">{m.name}</Link>
                      <p className="text-slate-500">{[m.manufacturer, m.model_number].filter(Boolean).join(" ")}</p>
                    </td>
                    <td className="px-5 py-3 text-slate-600">{m.department ?? "—"}</td>
                    <td className="px-5 py-3 text-slate-600">{m.location ?? "—"}</td>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2">
                        <StatusBadge status={m.status} />
                        {!m.is_active && <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">Deactivated</span>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {data && data.pages > 1 && (
            <div className="mt-4 flex items-center justify-between text-sm text-slate-600">
              <span>Page {data.page} of {data.pages} ({data.total} machines)</span>
              <div className="flex gap-2">
                <button className="min-h-11 rounded-lg border border-slate-300 bg-white px-4 font-medium disabled:opacity-50" disabled={data.page <= 1} onClick={() => setFilters((f) => ({ ...f, page: f.page - 1 }))}>Previous</button>
                <button className="min-h-11 rounded-lg border border-slate-300 bg-white px-4 font-medium disabled:opacity-50" disabled={data.page >= data.pages} onClick={() => setFilters((f) => ({ ...f, page: f.page + 1 }))}>Next</button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
