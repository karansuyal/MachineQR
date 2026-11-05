export function saveBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 10000);
}

export async function openBlobInNewTab(getBlob, fallbackFilename) {
  const tab = window.open("", "_blank");
  try {
    const blob = await getBlob();
    if (!tab) {
      saveBlob(blob, fallbackFilename);
      return;
    }
    tab.location.href = URL.createObjectURL(blob);
  } catch (err) {
    tab?.close();
    throw err;
  }
}
