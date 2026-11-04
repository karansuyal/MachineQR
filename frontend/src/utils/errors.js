function flatten(value, path, out) {
  if (typeof value === "string") {
    out.push(path ? `${path}: ${value}` : value);
  } else if (Array.isArray(value)) {
    value.forEach((item) => flatten(item, path, out));
  } else if (value && typeof value === "object") {
    Object.entries(value).forEach(([key, item]) => flatten(item, path ? `${path}.${key}` : key, out));
  }
}

export function errorMessage(err) {
  const messages = [];
  if (err?.details) flatten(err.details, "", messages);
  return messages.length ? messages.join(" · ") : err?.message || "Something went wrong";
}
