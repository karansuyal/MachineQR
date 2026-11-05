import { Html5Qrcode, Html5QrcodeScannerState } from "html5-qrcode";
import { useEffect, useRef } from "react";

const READER_ID = "machineqr-reader";

function describeCameraError(err) {
  const text = String(err?.message ?? err);
  if (/permission|notallowed/i.test(text)) {
    return "Camera permission was denied. Allow camera access in your browser settings, or enter the Machine ID below.";
  }
  if (/notfound|no camera|requested device/i.test(text)) {
    return "No camera was found on this device. Enter the Machine ID below.";
  }
  return "Could not start the camera. Enter the Machine ID below.";
}

export default function QrScanner({ onDecode, onError }) {
  const onDecodeRef = useRef(onDecode);
  const onErrorRef = useRef(onError);
  onDecodeRef.current = onDecode;
  onErrorRef.current = onError;

  useEffect(() => {
    const scanner = new Html5Qrcode(READER_ID);
    let stopped = false;

    const started = scanner
      .start(
        { facingMode: "environment" },
        {
          fps: 10,
          aspectRatio: 1,
          qrbox: (width, height) => {
            const size = Math.floor(Math.min(width, height) * 0.7);
            return { width: size, height: size };
          },
        },
        (text) => onDecodeRef.current(text),
        () => {}
      )
      .catch((err) => {
        if (!stopped) onErrorRef.current(describeCameraError(err));
      });

    return () => {
      stopped = true;
      started
        .then(() => {
          if (scanner.getState() === Html5QrcodeScannerState.SCANNING) return scanner.stop();
          return undefined;
        })
        .then(() => scanner.clear())
        .catch(() => {});
    };
  }, []);

  return <div id={READER_ID} className="w-full overflow-hidden rounded-2xl bg-slate-900" />;
}
