import { Camera, CameraOff, Keyboard } from "lucide-react";
import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import Alert from "../components/Alert";
import Button from "../components/Button";
import Field, { inputClass } from "../components/Field";
import QrScanner from "../components/QrScanner";
import { isMachineCode, parseMachineQr } from "../utils/qr";

export default function ScanPage() {
  const navigate = useNavigate();
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState("");
  const [manual, setManual] = useState("");
  const [manualError, setManualError] = useState("");
  const handled = useRef(false);

  const openMachine = (code, version) => {
    navigate(`/machine/${code}${version ? `?v=${version}` : ""}`);
  };

  const handleDecode = (text) => {
    if (handled.current) return;
    const parsed = parseMachineQr(text);
    if (!parsed) {
      setError("This is not a MachineQR code.");
      return;
    }
    handled.current = true;
    setScanning(false);
    openMachine(parsed.code, parsed.version);
  };

  const handleCameraError = (message) => {
    setScanning(false);
    setError(message);
  };

  const start = () => {
    handled.current = false;
    setError("");
    setScanning(true);
  };

  const submitManual = (event) => {
    event.preventDefault();
    if (!isMachineCode(manual)) {
      setManualError("Enter a Machine ID like M-001.");
      return;
    }
    setManualError("");
    openMachine(manual.trim().toUpperCase());
  };

  return (
    <div className="mx-auto max-w-md">
      <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Scan machine QR</h1>
      <p className="mt-1 text-sm text-slate-500">Point the camera at the QR label on the machine.</p>

      <div className="mt-5 space-y-4">
        {scanning ? (
          <>
            <QrScanner onDecode={handleDecode} onError={handleCameraError} />
            <Button variant="secondary" className="w-full" onClick={() => setScanning(false)}>
              <CameraOff className="h-4 w-4" /> Stop camera
            </Button>
          </>
        ) : (
          <Button className="w-full" onClick={start}>
            <Camera className="h-4 w-4" /> Start camera
          </Button>
        )}
        <Alert>{error}</Alert>
        {!window.isSecureContext && (
          <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-900">
            Browsers only allow in-app camera scanning on HTTPS (or localhost). You can still scan with your phone's own camera app, or enter the Machine ID below.
          </p>
        )}
      </div>

      <form onSubmit={submitManual} className="mt-8 rounded-2xl bg-white p-5 shadow-sm" noValidate>
        <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-slate-900">
          <Keyboard className="h-4 w-4" aria-hidden="true" /> Enter Machine ID
        </h2>
        <Field label="Machine ID" htmlFor="manual-code" error={manualError}>
          <input
            id="manual-code"
            className={inputClass}
            placeholder="M-001"
            autoCapitalize="characters"
            autoComplete="off"
            value={manual}
            onChange={(e) => setManual(e.target.value)}
          />
        </Field>
        <Button type="submit" className="mt-4 w-full">Open machine</Button>
      </form>
    </div>
  );
}
