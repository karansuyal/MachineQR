import { useEffect, useState } from "react";
import { fetchMachinePhoto } from "../api/machines";

export function useMachinePhoto(code, enabled, version) {
  const [url, setUrl] = useState(null);

  useEffect(() => {
    if (!enabled) {
      setUrl(null);
      return undefined;
    }
    let objectUrl;
    let cancelled = false;
    fetchMachinePhoto(code)
      .then((blob) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setUrl(objectUrl);
      })
      .catch(() => !cancelled && setUrl(null));
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [code, enabled, version]);

  return url;
}
