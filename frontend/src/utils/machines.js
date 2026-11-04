export const STATUS_OPTIONS = [
  { value: "running", label: "Running" },
  { value: "stopped", label: "Stopped" },
  { value: "under_maintenance", label: "Under maintenance" },
];

export const SPEC_CATEGORIES = [
  { value: "motor", label: "Motor" },
  { value: "sensor", label: "Sensor" },
  { value: "electrical", label: "Electrical" },
  { value: "pneumatic", label: "Pneumatic" },
  { value: "hydraulic", label: "Hydraulic" },
  { value: "communication", label: "Communication" },
  { value: "custom", label: "Custom field" },
];

export const statusLabel = (status) => STATUS_OPTIONS.find((s) => s.value === status)?.label ?? status;
export const specCategoryLabel = (value) => SPEC_CATEGORIES.find((c) => c.value === value)?.label ?? value;

export function formatDate(value) {
  if (!value) return "—";
  return new Date(`${value}T00:00:00`).toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" });
}
