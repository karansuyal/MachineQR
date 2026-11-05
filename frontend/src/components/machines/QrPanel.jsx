import { AlertTriangle, Download, Printer, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import {
  fetchMachineLabelPdf,
  fetchMachineQrPng,
  regenerateMachineQr,
} from "../../api/machines";
import { openBlobInNewTab, saveBlob } from "../../utils/download";
import { errorMessage } from "../../utils/errors";
import { formatDateTime } from "../../utils/machines";
import Alert from "../Alert";
import Button from "../Button";

function pointsToLocalhost(url) {
  try {
    const host = new URL(url).hostname;
    return host === "localhost" || host === "127.0.0.1";
  } catch {
    return false;
  }
}

export default function QrPanel({ machine, onChanged }) {
  const code = machine.machine_code;
  const [previewUrl, setPreviewUrl] = useState(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let objectUrl;
    let cancelled = false;
    setPreviewUrl(null);
    fetchMachineQrPng(code, { preview: true })
      .then((blob) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setPreviewUrl(objectUrl);
      })
      .catch((err) => !cancelled && setError(errorMessage(err)));
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [code, machine.qr_version]);

  const run = async (key, action) => {
    setBusy(key);
    setError("");
    try {
      await action();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy("");
    }
  };

  const regenerate = () => {
    const message =
      "Regenerate the QR code? Labels already stuck on the machine will stop opening it, and you must print and replace the label.";
    if (window.confirm(message)) run("regenerate", async () => onChanged(await regenerateMachineQr(code)));
  };

  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm">
      <h2 className="mb-4 text-base font-semibold text-slate-900">QR code</h2>
      <div className="flex flex-col gap-5 sm:flex-row">
        <div className="mx-auto flex h-44 w-44 shrink-0 items-center justify-center rounded-xl border border-slate-200 bg-white p-2 sm:mx-0">
          {previewUrl ? <img src={previewUrl} alt={`QR code for ${code}`} className="h-full w-full" /> : <span className="text-xs text-slate-400">Loading…</span>}
        </div>
        <div className="min-w-0 flex-1 space-y-3">
          <dl className="space-y-1 text-sm">
            <div className="flex justify-between gap-4"><dt className="text-slate-500">Version</dt><dd className="font-medium">{machine.qr_version}</dd></div>
            <div className="flex justify-between gap-4"><dt className="text-slate-500">Generated</dt><dd className="font-medium">{formatDateTime(machine.qr_generated_at)}</dd></div>
          </dl>
          <p className="break-all rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">{machine.qr_url}</p>
          {pointsToLocalhost(machine.qr_url) && (
            <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <span>This QR points to localhost, which phones cannot open. Set PUBLIC_BASE_URL in the backend .env to your server address before printing labels.</span>
            </div>
          )}
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" loading={busy === "png"} onClick={() => run("png", async () => saveBlob(await fetchMachineQrPng(code), `${code}-qr.png`))}>
              <Download className="h-4 w-4" /> PNG
            </Button>
            <Button variant="secondary" loading={busy === "pdf"} onClick={() => run("pdf", async () => saveBlob(await fetchMachineLabelPdf(code), `${code}-label.pdf`))}>
              <Download className="h-4 w-4" /> Label PDF
            </Button>
            <Button variant="secondary" loading={busy === "print"} onClick={() => run("print", () => openBlobInNewTab(() => fetchMachineLabelPdf(code), `${code}-label.pdf`))}>
              <Printer className="h-4 w-4" /> Print label
            </Button>
            <Button variant="secondary" loading={busy === "regenerate"} onClick={regenerate}>
              <RefreshCw className="h-4 w-4" /> Regenerate
            </Button>
          </div>
        </div>
      </div>
      <div className="mt-3"><Alert>{error}</Alert></div>
    </section>
  );
}
