"use strict";
// La estructura permanente vive en index.html; aquí solo se conectan sus controles.
const appearanceControls = $("appearance-controls"),
  fontSelect = $("app-font");
fontSelect.replaceChildren(
  ...Object.entries(appFonts).map(
    ([key, value]) => new Option(value.label, key),
  ),
);
fontSelect.value = document.documentElement.dataset.font;
fontSelect.onchange = action(() => {
  applyAppFont(fontSelect.value);
  localStorage.setItem("sw-font", fontSelect.value);
});
$("chat-engine").onclick = action(() => openEngineSettings());
function openSettings() {
  document.dispatchEvent(new Event("workbench:settings-open"));
  $("purpose").disabled = $("workflow").disabled = !state;
  renderAISettings();
  renderEngine();
  showDialog($("settings-dialog"));
  refreshWorkspace().catch((error) => notice(error.message, true));
}
$("settings-open").onclick = openSettings;
$("settings-close").onclick = () => $("settings-dialog").close();
$("settings-dialog").addEventListener("close", () => {
  if (!document.querySelector("dialog[open]")) $("prompt").focus();
});

new ResizeObserver(() =>
  document.documentElement.style.setProperty(
    "--topbar-height",
    document.querySelector(".topbar").offsetHeight + "px",
  ),
).observe(document.querySelector(".topbar"));

let workspaceInfo = null;
async function refreshWorkspace() {
  const previous = $("workspace-path").value;
  workspaceInfo = await api("/api/workspace");
  $("workspace-status").textContent =
    `En uso: ${workspaceInfo.active}${workspaceInfo.restart ? ` · Al reiniciar: ${workspaceInfo.pending}` : ""}${workspaceInfo.warning ? " · " + workspaceInfo.warning : ""}`;
  if ($("workspace-path").value === previous)
    $("workspace-path").value = workspaceInfo.pending;
}
$("workspace-pick").hidden = !window.storyDesktop;
$("workspace-pick").onclick = action(async () => {
  const result = await api("/api/desktop/folder", {});
  if (result.path) $("workspace-path").value = result.path;
});
$("workspace-save").onclick = action(async () => {
  await api("/api/workspace", {
    path: $("workspace-path").value.trim(),
    name: $("workspace-name").value.trim(),
  });
  $("workspace-name").value = "";
  await refreshWorkspace();
  notice(
    "Ubicación guardada. Cerrá y volvé a abrir la app para usarla. Los proyectos anteriores permanecen en su carpeta.",
  );
});
$("workspace-default").onclick = action(async () => {
  await api("/api/workspace", { path: workspaceInfo.default });
  await refreshWorkspace();
  notice("Volverás a la ubicación predeterminada al reiniciar.");
});
$("workspace-import").onclick = action(async () => {
  $("settings-dialog").close();
  await createProject(false, true);
});
$("welcome-import").onclick = action(() => createProject(false, true));
refreshWorkspace()
  .then(() => {
    if (workspaceInfo.warning) notice(workspaceInfo.warning, true);
  })
  .catch((error) => notice(error.message, true));

const customControls = document.createElement("details");
customControls.id = "custom-theme-controls";
customControls.innerHTML =
  '<summary>Personalizar o compartir un tema</summary><p>Creá tu paleta o importá un tema JSON. Se guarda en este equipo. Los colores se aplican al instante; revisá que el texto siga siendo legible.</p><button id="theme-customize" class="secondary">Personalizar tema actual</button><div id="custom-theme-editor" hidden><label for="custom-theme-name">Nombre del tema</label><input id="custom-theme-name" maxlength="80"><div class="theme-color-grid">' +
  Object.entries(themeColors)
    .map(
      ([key, label]) =>
        "<label>" +
        label +
        '<input type="color" data-theme-color="' +
        key +
        '"></label>',
    )
    .join("") +
  '</div><button id="theme-export" class="secondary">Exportar tema JSON</button></div><button id="theme-import" class="secondary">Importar tema JSON…</button><input id="theme-file" type="file" accept=".json,application/json" hidden><button id="theme-reset" class="quiet">Volver al tema original</button>';
appearanceControls.append(customControls);
const opacityControls = document.createElement("div");
opacityControls.innerHTML =
  '<label for="background-opacity">Opacidad de la imagen de ambiente · <output id="background-opacity-value" for="background-opacity"></output></label><input id="background-opacity" type="range" min="0" max="100" value="10"><p>0% la oculta; 100% la muestra sin transparencia. La opacidad se recuerda; la imagen se elige con Ambiente para esta sesión.</p>';
$("settings-general").append(opacityControls);
function effectiveThemeMode() {
  return document.documentElement.dataset.theme === "system"
    ? matchMedia("(prefers-color-scheme:dark)").matches
      ? "dark"
      : "light"
    : document.documentElement.dataset.theme;
}
function renderCustomTheme() {
  if (!$("custom-theme-editor")) return;
  const mode = effectiveThemeMode(),
    value =
      document.documentElement.dataset[mode + "Palette"] === "custom"
        ? customTheme(mode)
        : null;
  $("custom-theme-editor").hidden = !value;
  if (value) {
    $("custom-theme-name").value = value.name;
    for (const input of document.querySelectorAll("[data-theme-color]"))
      input.value = value.colors[input.dataset.themeColor];
  }
}
function saveCustomTheme(value) {
  value = validateCustomTheme(value);
  localStorage.setItem("sw-custom-" + value.mode, JSON.stringify(value));
  $("theme").value = value.mode + ":custom";
  $("theme").onchange();
}
function customizeCurrentTheme() {
  const mode = effectiveThemeMode(),
    colors = {};
  // getComputedStyle resuelve light-dark al aplicarlo a una propiedad de color.
  const sample = document.createElement("span");
  document.body.append(sample);
  for (const key of Object.keys(themeColors)) {
    sample.style.color = "var(--" + key + ")";
    const rgb = getComputedStyle(sample).color.match(/[\d.]+/g);
    colors[key] =
      "#" +
      rgb
        .slice(0, 3)
        .map((v) => Math.round(Number(v)).toString(16).padStart(2, "0"))
        .join("");
  }
  sample.remove();
  saveCustomTheme({
    version: 1,
    name: "Mi tema",
    mode,
    colors,
    backgroundOpacity: Number($("background-opacity").value),
  });
  $("custom-theme-name").focus();
}
$("theme-customize").onclick = action(customizeCurrentTheme);
$("custom-theme-editor").oninput = action(() => {
  const value = customTheme(effectiveThemeMode());
  if (!value) return;
  value.name = $("custom-theme-name").value.trim() || "Mi tema";
  for (const input of document.querySelectorAll("[data-theme-color]"))
    value.colors[input.dataset.themeColor] = input.value;
  localStorage.setItem("sw-custom-" + value.mode, JSON.stringify(value));
  applyCustomThemes();
});
$("theme-export").onclick = action(() => {
  const value = customTheme(effectiveThemeMode());
  if (!value) return;
  value.backgroundOpacity = Number($("background-opacity").value);
  return download(
    new Blob([JSON.stringify(value, null, 2) + "\n"], {
      type: "application/json",
    }),
    "story-workbench-theme.json",
  );
});
$("theme-import").onclick = () => $("theme-file").click();
$("theme-file").onchange = action(async (event) => {
  const file = event.target.files[0];
  event.target.value = "";
  if (!file) return;
  if (file.size > 20000)
    throw Error("El tema JSON debe ocupar menos de 20 KB.");
  const value = validateCustomTheme(JSON.parse(await file.text()));
  saveCustomTheme(value);
  $("background-opacity").value = value.backgroundOpacity;
  $("background-opacity").oninput();
  customControls.open = true;
  notice("Tema importado: " + value.name);
});
$("theme-reset").onclick = () => {
  $("theme").value = effectiveThemeMode();
  $("theme").onchange();
};
function renderBackgroundOpacity() {
  const value = applyBackgroundOpacity(
    storedAppearance("sw-background-opacity", "10"),
  );
  $("background-opacity").value = value;
  $("background-opacity-value").textContent = value + "%";
}
$("background-opacity").oninput = () => {
  const value = applyBackgroundOpacity($("background-opacity").value);
  $("background-opacity-value").textContent = value + "%";
  try {
    localStorage.setItem("sw-background-opacity", value);
  } catch {
    notice("No se pudo recordar la opacidad.", true);
  }
};
window.addEventListener("storage", (event) => {
  if (event.key === null || event.key === "sw-background-opacity")
    renderBackgroundOpacity();
});
renderCustomTheme();
renderBackgroundOpacity();
