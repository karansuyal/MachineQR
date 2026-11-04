import { useEffect, useState } from "react";
import { setMachineAssignments } from "../../api/machines";
import { listUsers } from "../../api/users";
import { errorMessage } from "../../utils/errors";
import Alert from "../Alert";
import Button from "../Button";
import Modal from "../Modal";
import RoleBadge from "../RoleBadge";
import Spinner from "../Spinner";

export default function AssignUsersModal({ machine, onClose, onSaved }) {
  const [candidates, setCandidates] = useState(null);
  const [selected, setSelected] = useState(() => new Set(machine.assigned_users.map((u) => u.id)));
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    listUsers({ isActive: true, perPage: 100 })
      .then((data) => setCandidates(data.items.filter((u) => u.role !== "admin")))
      .catch((err) => setError(errorMessage(err)));
  }, []);

  const toggle = (id) =>
    setSelected((current) => {
      const next = new Set(current);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

  const save = async () => {
    setSaving(true);
    setError("");
    try {
      onSaved(await setMachineAssignments(machine.machine_code, [...selected]));
    } catch (err) {
      setError(errorMessage(err));
      setSaving(false);
    }
  };

  return (
    <Modal title="Assign users" onClose={onClose}>
      <p className="mb-3 text-sm text-slate-500">
        Technicians and operators can only open machines assigned to them. Admins can open every machine.
      </p>
      <Alert>{error}</Alert>
      {!candidates && !error ? (
        <Spinner />
      ) : (
        <ul className="mt-3 max-h-72 divide-y divide-slate-100 overflow-y-auto rounded-lg border border-slate-200">
          {(candidates ?? []).map((u) => (
            <li key={u.id}>
              <label className="flex min-h-14 cursor-pointer items-center gap-3 px-3 py-2 hover:bg-slate-50">
                <input type="checkbox" className="h-5 w-5 rounded border-slate-300" checked={selected.has(u.id)} onChange={() => toggle(u.id)} />
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-medium text-slate-900">{u.full_name}</span>
                  <span className="block truncate text-xs text-slate-500">@{u.username}</span>
                </span>
                <RoleBadge role={u.role} />
              </label>
            </li>
          ))}
          {candidates?.length === 0 && <li className="p-4 text-center text-sm text-slate-500">No technicians or operators yet.</li>}
        </ul>
      )}
      <div className="mt-4 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button variant="secondary" onClick={onClose}>Cancel</Button>
        <Button onClick={save} loading={saving} disabled={!candidates}>Save assignments</Button>
      </div>
    </Modal>
  );
}
