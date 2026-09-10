import { initImages } from "./images.js";
// Explicit boundary while the existing chat/voice controllers migrate to modules.
// DOM is static; modules initialize once, after the legacy controllers are ready.
function initialize() {
  initImages({
    getProject: () => state,
    api,
    action,
    showDialog,
    openSettings,
    download,
    binary: async (path) => {
      const response = await fetch(path, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw Error((await response.json()).error);
      return response.blob();
    },
    applyCover: async (blob) => {
      $("book-open").click();
      await setBookImage(blob, "front");
    },
  });
}
if (document.readyState === "loading")
  document.addEventListener("DOMContentLoaded", initialize, { once: true });
else initialize();
