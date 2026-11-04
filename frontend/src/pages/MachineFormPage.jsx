import { ArrowLeft, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useFieldArray, useForm } from "react-hook-form";
import { Link, useNavigate, useParams } from "react-router-dom";
import { createMachine, getMachine, getMachineOptions, updateMachine } from "../api/machines";
import Alert from "../components/Alert";
import Button from "../components/Button";
import Field, { inputClass } from "../components/Field";
import Spinner from "../components/Spinner";
import { errorMessage } from "../utils/errors";
import { SPEC_CATEGORIES, STATUS_OPTIONS } from "../utils/machines";

const EMPTY = {
  name: "", category: "", department: "", production_line: "", location: "",
  manufacturer: "", model_number: "", serial_number: "",
  installation_date: "", commissioning_date: "",
  plc_manufacturer: "", plc_model: "", hmi_manufacturer: "", hmi_model: "",
  operating_instructions: "", technical_notes: "", status: "stopped",
  specifications: [],
};

const TEXT_FIELDS = [
  "name", "category", "department", "production_line", "location", "manufacturer",
  "model_number", "serial_number", "plc_manufacturer", "plc_model", "hmi_manufacturer",
  "hmi_model", "operating_instructions", "technical_notes",
];

function toFormValues(machine) {
  const values = { ...EMPTY, status: machine.status };
  TEXT_FIELDS.forEach((f) => (values[f] = machine[f] ?? ""));
  values.installation_date = machine.installation_date ?? "";
  values.commissioning_date = machine.commissioning_date ?? "";
  values.specifications = (machine.specifications ?? []).flatMap((group) =>
    group.items.map((item) => ({
      category: group.category,
      spec_key: item.spec_key,
      spec_value: item.spec_value,
      unit: item.unit ?? "",
    }))
  );
  return values;
}

function toPayload(values) {
  const payload = { status: values.status };
  TEXT_FIELDS.forEach((f) => (payload[f] = values[f].trim() || null));
  payload.installation_date = values.installation_date || null;
  payload.commissioning_date = values.commissioning_date || null;
  payload.specifications = values.specifications.map((s) => ({
    category: s.category,
    spec_key: s.spec_key.trim(),
    spec_value: s.spec_value.trim(),
    unit: s.unit.trim() || null,
  }));
  return payload;
}

function Section({ title, children }) {
  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm">
      <h2 className="mb-4 text-base font-semibold text-slate-900">{title}</h2>
      <div className="grid gap-4 sm:grid-cols-2">{children}</div>
    </section>
  );
}

export default function MachineFormPage() {
  const { code } = useParams();
  const isEdit = Boolean(code);
  const navigate = useNavigate();
  const [loading, setLoading] = useState(isEdit);
  const [loadError, setLoadError] = useState("");
  const [serverError, setServerError] = useState("");
  const [options, setOptions] = useState({ departments: [], categories: [] });

  const {
    register,
    handleSubmit,
    control,
    reset,
    getValues,
    formState: { errors, isSubmitting },
  } = useForm({ defaultValues: EMPTY });
  const { fields, append, remove } = useFieldArray({ control, name: "specifications" });

  useEffect(() => {
    getMachineOptions().then(setOptions).catch(() => {});
  }, []);

  useEffect(() => {
    if (!isEdit) return;
    getMachine(code)
      .then((machine) => reset(toFormValues(machine)))
      .catch((err) => setLoadError(errorMessage(err)))
      .finally(() => setLoading(false));
  }, [code, isEdit, reset]);

  const onSubmit = async (values) => {
    setServerError("");
    try {
      const payload = toPayload(values);
      const saved = isEdit ? await updateMachine(code, payload) : await createMachine(payload);
      navigate(`/machine/${saved.machine_code}`);
    } catch (err) {
      setServerError(errorMessage(err));
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  const validateDates = () => {
    const { installation_date: install, commissioning_date: commission } = getValues();
    return !install || !commission || commission >= install || "Cannot be before installation date";
  };

  if (loading) return <Spinner />;
  if (loadError) return <Alert>{loadError}</Alert>;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
      <Link to={isEdit ? `/machine/${code}` : "/machines"} className="inline-flex min-h-11 items-center gap-1.5 text-sm font-medium text-slate-600 hover:text-slate-900">
        <ArrowLeft className="h-4 w-4" /> Back
      </Link>
      <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
        {isEdit ? `Edit ${code}` : "Add machine"}
      </h1>
      {!isEdit && <p className="text-sm text-slate-500">The Machine ID (for example M-001) is generated automatically and cannot be changed later.</p>}
      <Alert>{serverError}</Alert>

      <datalist id="department-options">{options.departments.map((d) => <option key={d} value={d} />)}</datalist>
      <datalist id="category-options">{options.categories.map((c) => <option key={c} value={c} />)}</datalist>

      <Section title="Basic details">
        <div className="sm:col-span-2">
          <Field label="Machine name" htmlFor="name" error={errors.name?.message}>
            <input id="name" className={inputClass} {...register("name", { required: "Machine name is required", validate: (v) => v.trim() !== "" || "Machine name is required" })} />
          </Field>
        </div>
        <Field label="Category" htmlFor="category">
          <input id="category" list="category-options" className={inputClass} {...register("category")} />
        </Field>
        <Field label="Department" htmlFor="department">
          <input id="department" list="department-options" className={inputClass} {...register("department")} />
        </Field>
        <Field label="Production line" htmlFor="production_line">
          <input id="production_line" className={inputClass} {...register("production_line")} />
        </Field>
        <Field label="Location" htmlFor="location">
          <input id="location" className={inputClass} {...register("location")} />
        </Field>
        <Field label="Manufacturer" htmlFor="manufacturer">
          <input id="manufacturer" className={inputClass} {...register("manufacturer")} />
        </Field>
        <Field label="Model number" htmlFor="model_number">
          <input id="model_number" className={inputClass} {...register("model_number")} />
        </Field>
        <Field label="Serial number" htmlFor="serial_number">
          <input id="serial_number" className={inputClass} {...register("serial_number")} />
        </Field>
        <Field label="Current status" htmlFor="status">
          <select id="status" className={inputClass} {...register("status")}>
            {STATUS_OPTIONS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>
        </Field>
        <Field label="Installation date" htmlFor="installation_date">
          <input id="installation_date" type="date" className={inputClass} {...register("installation_date")} />
        </Field>
        <Field label="Commissioning date" htmlFor="commissioning_date" error={errors.commissioning_date?.message}>
          <input id="commissioning_date" type="date" className={inputClass} {...register("commissioning_date", { validate: validateDates })} />
        </Field>
      </Section>

      <Section title="PLC and HMI">
        <Field label="PLC manufacturer" htmlFor="plc_manufacturer"><input id="plc_manufacturer" className={inputClass} {...register("plc_manufacturer")} /></Field>
        <Field label="PLC model" htmlFor="plc_model"><input id="plc_model" className={inputClass} {...register("plc_model")} /></Field>
        <Field label="HMI manufacturer" htmlFor="hmi_manufacturer"><input id="hmi_manufacturer" className={inputClass} {...register("hmi_manufacturer")} /></Field>
        <Field label="HMI model" htmlFor="hmi_model"><input id="hmi_model" className={inputClass} {...register("hmi_model")} /></Field>
      </Section>

      <Section title="Instructions and notes">
        <div className="sm:col-span-2">
          <Field label="Operating instructions" htmlFor="operating_instructions" hint="Shown to operators. Use only approved instructions.">
            <textarea id="operating_instructions" rows={4} className={inputClass} {...register("operating_instructions")} />
          </Field>
        </div>
        <div className="sm:col-span-2">
          <Field label="Technical notes" htmlFor="technical_notes" hint="Visible to admins and technicians only.">
            <textarea id="technical_notes" rows={4} className={inputClass} {...register("technical_notes")} />
          </Field>
        </div>
      </Section>

      <section className="rounded-2xl bg-white p-5 shadow-sm">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Technical specifications</h2>
            <p className="text-xs text-slate-500">Use "Custom field" for anything not covered by the standard categories.</p>
          </div>
          <Button type="button" variant="secondary" onClick={() => append({ category: "motor", spec_key: "", spec_value: "", unit: "" })}>
            <Plus className="h-4 w-4" /> Add
          </Button>
        </div>
        {fields.length === 0 && <p className="text-sm text-slate-500">No specifications added.</p>}
        <div className="space-y-3">
          {fields.map((row, index) => (
            <div key={row.id} className="rounded-xl border border-slate-200 p-3">
              <div className="grid gap-3 sm:grid-cols-[10rem_1fr_1fr_6rem_auto]">
                <select aria-label="Category" className={inputClass} {...register(`specifications.${index}.category`)}>
                  {SPEC_CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
                </select>
                <div>
                  <input aria-label="Name" placeholder="Name" className={inputClass} {...register(`specifications.${index}.spec_key`, { required: "Name required" })} />
                  {errors.specifications?.[index]?.spec_key && <p className="mt-1 text-xs text-red-600">Name required</p>}
                </div>
                <div>
                  <input aria-label="Value" placeholder="Value" className={inputClass} {...register(`specifications.${index}.spec_value`, { required: "Value required" })} />
                  {errors.specifications?.[index]?.spec_value && <p className="mt-1 text-xs text-red-600">Value required</p>}
                </div>
                <input aria-label="Unit" placeholder="Unit" className={inputClass} {...register(`specifications.${index}.unit`)} />
                <button type="button" onClick={() => remove(index)} className="flex min-h-11 min-w-11 items-center justify-center rounded-lg text-slate-500 hover:bg-red-50 hover:text-red-600" aria-label="Remove specification">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      <div className="flex flex-col-reverse gap-2 pb-4 sm:flex-row sm:justify-end">
        <Button type="button" variant="secondary" onClick={() => navigate(-1)}>Cancel</Button>
        <Button type="submit" loading={isSubmitting}>{isEdit ? "Save changes" : "Create machine"}</Button>
      </div>
    </form>
  );
}
