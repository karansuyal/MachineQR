import { ArrowLeft, Camera, Cog, Pencil, Trash2, Users } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import {
  deactivateMachine,
  getMachine,
  reactivateMachine,
  removeMachinePhoto,
  setMachineStatus,
  uploadMachinePhoto,
} from "../api/machines";
import Alert from "../components/Alert";
import Button from "../components/Button";
import { inputClass } from "../components/Field";
import Spinner from "../components/Spinner";
import AssignUsersModal from "../components/machines/AssignUsersModal";
import QrPanel from "../components/machines/QrPanel";
import StatusBadge from "../components/machines/StatusBadge";
import { useAuth } from "../context/AuthContext";
import { useMachinePhoto } from "../hooks/useAuthImage";
import { errorMessage } from "../utils/errors";
import { STATUS_OPTIONS, formatDate, specCategoryLabel } from "../utils/machines";
import { ROLES } from "../utils/roles";

function Card({ title, children }) {
  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm">
      <h2 className="mb-3 text-base font-semibold text-slate-900">{title}</h2>
      {children}
    </section>
  );
}

function InfoGrid({ rows }) {
  return (
    <dl className="grid gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
      {rows.map(([label, value]) => (
        <div key={label}>
          <dt className="text-slate-500">{label}</dt>
          <dd className="mt-0.5 break-words font-medium text-slate-900">{value || "—"}</dd>
        </div>
      ))}
    </dl>
  );
}

export default function MachineDetailPage() {
  const { code } = useParams();
  const [searchParams] = useSearchParams();
  const qrVersion = searchParams.get("v");
  const { hasRole } = useAuth();
  const isAdmin = hasRole(ROLES.ADMIN);
  const canChangeStatus = hasRole(ROLES.ADMIN, ROLES.TECHNICIAN);
  const fileInput = useRef(null);

  const [machine, setMachine] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [actionError, setActionError] = useState("");
  const [busy, setBusy] = useState(false);
  const [showAssign, setShowAssign] = useState(false);
  const photoUrl = useMachinePhoto(code, machine?.has_photo, machine?.updated_at);

  useEffect(() => {
    setMachine(null);
    setLoadError(null);
    getMachine(code, qrVersion).then(setMachine).catch(setLoadError);
  }, [code, qrVersion]);

  const run = async (action) => {
    setBusy(true);
    setActionError("");
    try {
      setMachine(await action());
    } catch (err) {
      setActionError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const onPhotoChosen = (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (file) run(() => uploadMachinePhoto(code, file));
  };

  const toggleActive = () => {
    const message = machine.is_active
      ? "Deactivate this machine? Technicians and operators will no longer be able to open it."
      : "Reactivate this machine?";
    if (window.confirm(message)) run(() => (machine.is_active ? deactivateMachine(code) : reactivateMachine(code)));
  };

  if (loadError) {
    return (
      <div className="mx-auto max-w-md pt-10 text-center">
        <h1 className="text-xl font-semibold text-slate-900">
          {{ 403: "Not assigned to you", 410: "Outdated QR label" }[loadError.status] ?? "Machine unavailable"}
        </h1>
        <p className="mt-2 text-sm text-slate-500">{errorMessage(loadError)}</p>
        <Link to="/machines" className="mt-6 inline-flex min-h-11 items-center rounded-lg bg-navy-800 px-4 text-sm font-medium text-white">Back to machines</Link>
      </div>
    );
  }
  if (!machine) return <Spinner />;

  const full = machine.access_level === "full";

  return (
    <div className="space-y-5">
      <Link to="/machines" className="inline-flex min-h-11 items-center gap-1.5 text-sm font-medium text-slate-600 hover:text-slate-900">
        <ArrowLeft className="h-4 w-4" /> Machines
      </Link>

      <section className="overflow-hidden rounded-2xl bg-white shadow-sm">
        <div className="flex aspect-[16/7] items-center justify-center bg-navy-50 sm:aspect-[16/5]">
          {photoUrl ? (
            <img src={photoUrl} alt={machine.name} className="h-full w-full object-cover" />
          ) : (
            <Cog className="h-14 w-14 text-navy-200" aria-hidden="true" />
          )}
        </div>
        <div className="p-5">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-semibold text-navy-700">{machine.machine_code}</span>
            <StatusBadge status={machine.status} />
            {!machine.is_active && <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">Deactivated</span>}
          </div>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-900">{machine.name}</h1>
          <p className="mt-1 text-sm text-slate-500">
            {[machine.department, machine.production_line, machine.location].filter(Boolean).join(" · ") || "No location details"}
          </p>

          {canChangeStatus && machine.is_active && (
            <div className="mt-4 max-w-xs">
              <label htmlFor="status" className="mb-1.5 block text-sm font-medium text-slate-700">Machine status</label>
              <select id="status" className={inputClass} value={machine.status} disabled={busy} onChange={(e) => run(() => setMachineStatus(code, e.target.value))}>
                {STATUS_OPTIONS.map((s) => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </div>
          )}

          {isAdmin && (
            <div className="mt-4 flex flex-wrap gap-2">
              <Link to={`/machine/${machine.machine_code}/edit`} className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 text-sm font-medium text-slate-700 hover:bg-slate-50">
                <Pencil className="h-4 w-4" /> Edit
              </Link>
              <Button variant="secondary" onClick={() => setShowAssign(true)}><Users className="h-4 w-4" /> Assign users</Button>
              <Button variant="secondary" onClick={() => fileInput.current?.click()} disabled={busy}><Camera className="h-4 w-4" /> {machine.has_photo ? "Change photo" : "Add photo"}</Button>
              {machine.has_photo && (
                <Button variant="secondary" onClick={() => window.confirm("Remove the photo?") && run(() => removeMachinePhoto(code))} disabled={busy}>
                  <Trash2 className="h-4 w-4" /> Remove photo
                </Button>
              )}
              <Button variant={machine.is_active ? "danger" : "primary"} onClick={toggleActive} disabled={busy}>
                {machine.is_active ? "Deactivate" : "Reactivate"}
              </Button>
              <input ref={fileInput} type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={onPhotoChosen} />
            </div>
          )}
          <div className="mt-3"><Alert>{actionError}</Alert></div>
        </div>
      </section>

      <Card title="Overview">
        <InfoGrid
          rows={[
            ["Category", machine.category],
            ["Manufacturer", machine.manufacturer],
            ["Model number", machine.model_number],
            ["Serial number", machine.serial_number],
            ["Installation date", formatDate(machine.installation_date)],
            ["Commissioning date", machine.commissioning_date ? formatDate(machine.commissioning_date) : "—"],
          ]}
        />
      </Card>

      {machine.operating_instructions && (
        <Card title="Operating instructions">
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">{machine.operating_instructions}</p>
        </Card>
      )}

      {full && (
        <>
          <Card title="PLC and HMI">
            <InfoGrid
              rows={[
                ["PLC manufacturer", machine.plc_manufacturer],
                ["PLC model", machine.plc_model],
                ["HMI manufacturer", machine.hmi_manufacturer],
                ["HMI model", machine.hmi_model],
              ]}
            />
          </Card>

          <Card title="Technical specifications">
            {machine.specifications.length === 0 ? (
              <p className="text-sm text-slate-500">No specifications recorded.</p>
            ) : (
              <div className="space-y-5">
                {machine.specifications.map((group) => (
                  <div key={group.category}>
                    <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{specCategoryLabel(group.category)}</h3>
                    <dl className="divide-y divide-slate-100 rounded-lg border border-slate-200 text-sm">
                      {group.items.map((item) => (
                        <div key={item.id} className="flex justify-between gap-4 px-3 py-2.5">
                          <dt className="text-slate-600">{item.spec_key}</dt>
                          <dd className="text-right font-medium text-slate-900">{item.spec_value}{item.unit ? ` ${item.unit}` : ""}</dd>
                        </div>
                      ))}
                    </dl>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {machine.technical_notes && (
            <Card title="Technical notes">
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">{machine.technical_notes}</p>
            </Card>
          )}
        </>
      )}

      {isAdmin && <QrPanel machine={machine} onChanged={setMachine} />}

      {isAdmin && (
        <Card title="Assigned users">
          {machine.assigned_users.length === 0 ? (
            <p className="text-sm text-slate-500">No technicians or operators are assigned to this machine.</p>
          ) : (
            <ul className="divide-y divide-slate-100 text-sm">
              {machine.assigned_users.map((u) => (
                <li key={u.id} className="flex items-center justify-between py-2.5">
                  <span className="font-medium text-slate-900">{u.full_name}</span>
                  <span className="text-slate-500 capitalize">{u.role}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      {showAssign && (
        <AssignUsersModal
          machine={machine}
          onClose={() => setShowAssign(false)}
          onSaved={(assigned) => {
            setMachine((m) => ({ ...m, assigned_users: assigned }));
            setShowAssign(false);
          }}
        />
      )}
    </div>
  );
}
