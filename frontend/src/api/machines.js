import { api } from "./client";

const path = (code) => `/machines/${encodeURIComponent(code)}`;

export function listMachines({ search = "", status = "", department = "", includeInactive = false, page = 1, perPage = 20 } = {}) {
  const params = new URLSearchParams({ page, per_page: perPage });
  if (search) params.set("search", search);
  if (status) params.set("status", status);
  if (department) params.set("department", department);
  if (!includeInactive) params.set("is_active", "true");
  return api.get(`/machines?${params}`);
}

export const getMachineOptions = () => api.get("/machines/options");
export const getMachine = (code) => api.get(path(code)).then((d) => d.machine);
export const createMachine = (payload) => api.post("/machines", payload).then((d) => d.machine);
export const updateMachine = (code, payload) => api.patch(path(code), payload).then((d) => d.machine);
export const setMachineStatus = (code, status) => api.patch(`${path(code)}/status`, { status }).then((d) => d.machine);
export const deactivateMachine = (code) => api.post(`${path(code)}/deactivate`).then((d) => d.machine);
export const reactivateMachine = (code) => api.post(`${path(code)}/reactivate`).then((d) => d.machine);
export const setMachineAssignments = (code, userIds) =>
  api.put(`${path(code)}/assignments`, { user_ids: userIds }).then((d) => d.assigned_users);

export function uploadMachinePhoto(code, file) {
  const form = new FormData();
  form.append("photo", file);
  return api.post(`${path(code)}/photo`, form).then((d) => d.machine);
}

export const removeMachinePhoto = (code) => api.delete(`${path(code)}/photo`).then((d) => d.machine);
export const fetchMachinePhoto = (code) => api.get(`${path(code)}/photo`, { responseType: "blob" });
