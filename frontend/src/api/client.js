const ACCESS_KEY = "machineqr.access";
const REFRESH_KEY = "machineqr.refresh";

export class ApiError extends Error {
  constructor(message, status, details) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

export const tokenStore = {
  getAccess: () => localStorage.getItem(ACCESS_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  set(access, refresh) {
    localStorage.setItem(ACCESS_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

let sessionExpiredHandler = () => {};
let refreshPromise = null;

export function setSessionExpiredHandler(handler) {
  sessionExpiredHandler = handler;
}

async function refreshAccessToken() {
  const refresh = tokenStore.getRefresh();
  if (!refresh) throw new ApiError("Session expired", 401);
  const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
    method: "POST",
    headers: { Authorization: `Bearer ${refresh}` },
  });
  if (!response.ok) throw new ApiError("Session expired", 401);
  const data = await response.json();
  tokenStore.set(data.access_token);
}

function endSession() {
  tokenStore.clear();
  sessionExpiredHandler();
  return new ApiError("Session expired. Please sign in again.", 401);
}

async function send(path, { method = "GET", body, auth = true, retry = true, responseType = "json" } = {}) {
  const headers = {};
  const isForm = body instanceof FormData;
  if (body !== undefined && !isForm) headers["Content-Type"] = "application/json";
  const token = tokenStore.getAccess();
  if (auth && token) headers.Authorization = `Bearer ${token}`;

  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
    });
  } catch {
    throw new ApiError("Cannot reach the server. Check your connection.", 0);
  }

  if (response.status === 401 && auth) {
    if (retry && tokenStore.getRefresh()) {
      try {
        refreshPromise = refreshPromise || refreshAccessToken().finally(() => (refreshPromise = null));
        await refreshPromise;
      } catch {
        throw endSession();
      }
      return send(path, { method, body, auth, retry: false, responseType });
    }
    throw endSession();
  }

  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new ApiError(data?.error || "Something went wrong", response.status, data?.details);
  }
  return responseType === "blob" ? response.blob() : response.json().catch(() => null);
}

export const api = {
  get: (path, options) => send(path, options),
  post: (path, body = {}, options = {}) => send(path, { method: "POST", body, ...options }),
  put: (path, body = {}) => send(path, { method: "PUT", body }),
  patch: (path, body = {}) => send(path, { method: "PATCH", body }),
  delete: (path) => send(path, { method: "DELETE" }),
};
