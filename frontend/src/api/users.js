import { api } from "./client";

export function listUsers({ search = "", role = "", isActive = null, page = 1, perPage = 20 } = {}) {
  const params = new URLSearchParams({ page, per_page: perPage });
  if (search) params.set("search", search);
  if (role) params.set("role", role);
  if (isActive !== null) params.set("is_active", String(isActive));
  return api.get(`/users?${params}`);
}

export const createUser = (payload) => api.post("/users", payload).then((d) => d.user);
export const updateUser = (id, payload) => api.patch(`/users/${id}`, payload).then((d) => d.user);
export const resetUserPassword = (id, newPassword) =>
  api.post(`/users/${id}/reset-password`, { new_password: newPassword });
