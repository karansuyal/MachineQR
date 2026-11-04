import { api, tokenStore } from "./client";

export async function login(username, password) {
  const data = await api.post("/auth/login", { username, password }, { auth: false });
  tokenStore.set(data.access_token, data.refresh_token);
  return data.user;
}

export async function logout() {
  try {
    await api.post("/auth/logout", { refresh_token: tokenStore.getRefresh() });
  } catch {
    // session is cleared locally regardless
  } finally {
    tokenStore.clear();
  }
}

export const fetchCurrentUser = () => api.get("/auth/me").then((data) => data.user);

export const changePassword = (currentPassword, newPassword) =>
  api.post("/auth/change-password", {
    current_password: currentPassword,
    new_password: newPassword,
  });
