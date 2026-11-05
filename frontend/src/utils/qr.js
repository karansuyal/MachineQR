const MACHINE_CODE = /^M-\d{1,6}$/i;

export function parseMachineQr(text) {
  try {
    const url = new URL(String(text).trim());
    if (url.protocol !== "http:" && url.protocol !== "https:") return null;
    const match = url.pathname.match(/^\/machine\/([^/]+)\/?$/);
    if (!match || !MACHINE_CODE.test(match[1])) return null;
    const version = url.searchParams.get("v");
    return { code: match[1].toUpperCase(), version: /^\d+$/.test(version ?? "") ? version : null };
  } catch {
    return null;
  }
}

export const isMachineCode = (value) => MACHINE_CODE.test(value.trim());
