"use strict";
const $ = (id) => document.getElementById(id);
// Una sola lista; conserva las preferencias anteriores de cada modo.
function themeOption(mode) {
  const palette = document.documentElement.dataset[mode + "Palette"];
  return mode === "system" || !palette || palette === "sage"
    ? mode
    : mode + ":" + palette;
}
$("theme").replaceChildren(
  new Option("Sistema", "system"),
  ...Object.entries(appearancePalettes).flatMap(([mode, values]) =>
    Object.entries(values).map(
      ([palette, label]) =>
        new Option(
          palette === "sage"
            ? mode === "light"
              ? "Claro · salvia"
              : "Oscuro · salvia"
            : label,
          palette === "sage" ? mode : mode + ":" + palette,
        ),
    ),
  ),
);
function applyTheme(value) {
  const theme = ["light", "dark"].includes(value) ? value : "system";
  document.documentElement.dataset.theme = theme;
  applyCustomThemes();
  $("theme").value = themeOption(theme);
  updateThemeIcon();
  if (typeof renderCustomTheme === "function") renderCustomTheme();
}
function updateThemeIcon() {
  const dark =
    document.documentElement.dataset.theme === "dark" ||
    (document.documentElement.dataset.theme === "system" &&
      matchMedia("(prefers-color-scheme:dark)").matches);
  $("theme-toggle").textContent = dark ? "☀" : "☾";
  $("theme-toggle").title = dark ? "Usar tema claro" : "Usar tema oscuro";
  $("theme-toggle").setAttribute("aria-label", $("theme-toggle").title);
}
$("theme-toggle").onclick = () => {
  const mode =
    document.documentElement.dataset.theme === "dark" ||
    (document.documentElement.dataset.theme === "system" &&
      matchMedia("(prefers-color-scheme:dark)").matches)
      ? "light"
      : "dark";
  $("theme").value = themeOption(mode);
  $("theme").onchange();
};
matchMedia("(prefers-color-scheme:dark)").addEventListener("change", () => {
  updateThemeIcon();
  if (typeof renderCustomTheme === "function") renderCustomTheme();
});
applyTheme(document.documentElement.dataset.theme);
$("theme").onchange = () => {
  const [mode, palette = "sage"] = $("theme").value.split(":");
  if (
    palette === "custom" &&
    !customTheme(mode) &&
    typeof customizeCurrentTheme === "function"
  ) {
    applyTheme(mode);
    customizeCurrentTheme();
    return;
  }
  const selected =
    Object.hasOwn(appearancePalettes, mode) &&
    Object.hasOwn(appearancePalettes[mode], palette)
      ? mode
      : "system";
  if (selected !== "system")
    document.documentElement.dataset[selected + "Palette"] = palette;
  applyTheme(selected);
  try {
    if (selected === "system") localStorage.removeItem("sw-theme");
    else {
      localStorage.setItem("sw-theme", selected);
      localStorage.setItem("sw-palette-" + selected, palette);
    }
  } catch {
    notice(
      "El tema se aplicó, pero el navegador no permitió recordar la elección.",
      true,
    );
  }
};
window.addEventListener("storage", (event) => {
  if (event.key === null || event.key === "sw-font")
    applyAppFont(storedAppearance("sw-font", "system"));
  if (
    event.key === null ||
    event.key === "sw-theme" ||
    event.key.startsWith("sw-palette-") ||
    event.key.startsWith("sw-custom-")
  ) {
    for (const mode of ["light", "dark"]) {
      const value = storedAppearance("sw-palette-" + mode, "sage");
      document.documentElement.dataset[mode + "Palette"] = Object.hasOwn(
        appearancePalettes[mode],
        value,
      )
        ? value
        : "sage";
    }
    applyTheme(storedAppearance("sw-theme", "system"));
  }
});
const escapeHTML = (text) =>
  String(text).replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const labels = {
  panel: "Panel ciego",
  translate: "Traducción",
  draft: "Borrador",
  interview: "Entrevista",
  manuscrito: "Manuscrito",
  canon: "Canon",
  estilo: "Voz y estilo",
  referencia: "Referencia",
  plan: "Planificación",
  traducción: "Traducción",
  accepted: "Aprobada",
  rejected: "Rechazada",
  pending: "Pendiente",
  chat: "Conversación",
  diagnosis: "Diagnóstico",
  impact: "Impacto",
  proposal: "Propuesta",
  summary: "Resumen",
  connecting: "Conectando…",
  running: "La IA está trabajando…",
  cancelling: "Deteniendo…",
  completed: "Completado",
  interrupted: "Interrumpido",
  failed: "No completado",
};
let token =
  new URLSearchParams(location.hash.slice(1)).get("token") ||
  sessionStorage.getItem("sw-token") ||
  "";
if (token) sessionStorage.setItem("sw-token", token);
history.replaceState(null, "", "/");
let state = null,
  current = null,
  dirty = false,
  view = "edit",
  panel = "conversation",
  polling = false,
  backgroundURL = null;
let stateEpoch = 0;
let lastRuns = "",
  lastProposals = "",
  lastDecisions = "";
const notices = [];
const busy = () =>
  state?.runs.findLast((r) =>
    ["connecting", "running", "cancelling"].includes(r.status),
  );
const currentRuns = () => state?.runs.slice(state.history_start || 0) || [];
const draftKey = () => `sw-draft-${state.id}-${current.id}`;

// El orden del HTML no coincide con el orden de apertura de diálogos anidados.
let dialogStack = [];
function topDialog() {
  dialogStack = dialogStack.filter((dialog) => dialog.open);
  return dialogStack.at(-1);
}
function placeNotice() {
  const dialog = topDialog();
  if (dialog) dialog.prepend($("notice"));
  else if (!state) $("welcome").prepend($("notice"));
  else {
    $("notice").hidden = true;
    document.body.append($("notice"));
  }
}
function showDialog(dialog) {
  dialog.showModal();
  dialogStack = dialogStack.filter((item) => item !== dialog);
  dialogStack.push(dialog);
  placeNotice();
}
function renderNotices(markRead = false) {
  if (markRead) for (const entry of notices) entry.unread = false;
  const unread = notices.filter((entry) => entry.unread).length;
  $("notices-count").textContent = unread;
  $("notices-count").hidden = !unread;
  document
    .querySelector('[data-panel="notices"]')
    .setAttribute(
      "aria-label",
      unread ? `Avisos · ${unread} sin leer` : "Avisos",
    );
  $("notices-clear").disabled = !notices.length;
  $("notices-list").innerHTML =
    notices
      .slice()
      .reverse()
      .map(
        (entry) =>
          `<article class="notice-entry ${entry.error ? "notice-error" : ""}"><div><strong>${entry.error ? "Error" : "Aviso"}</strong><time>${new Date(entry.date).toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit" })}</time>${entry.count > 1 ? `<span>×${entry.count}</span>` : ""}</div><p>${escapeHTML(entry.text)}</p>${entry.project ? `<small>${escapeHTML(entry.project)}</small>` : ""}</article>`,
      )
      .join("") ||
    '<p class="assistant-empty">No hay avisos en esta sesión.</p>';
}
function notice(text, error = false) {
  const previous = notices.at(-1),
    project = state?.title || "";
  if (
    previous &&
    previous.text === text &&
    previous.error === error &&
    previous.project === project
  ) {
    previous.count++;
    previous.date = Date.now();
    previous.unread = true;
  } else
    notices.push({
      text,
      error,
      project,
      date: Date.now(),
      count: 1,
      unread: true,
    });
  // ponytail: últimos 100 avisos en memoria de esta ventana; sin historial en disco.
  if (notices.length > 100) notices.shift();
  renderNotices(panel === "notices" && !$("workspace").hidden && !topDialog());
  $("notices-live").setAttribute("aria-live", error ? "assertive" : "polite");
  $("notices-live").textContent =
    state && !topDialog() ? (error ? "Error: " : "") + text : "";
  if (!error && !$("notice").hidden && $("notice").classList.contains("error"))
    return;
  placeNotice();
  $("notice-text").textContent = text;
  $("notice").setAttribute("role", error ? "alert" : "status");
  $("notice").setAttribute("aria-live", error ? "assertive" : "polite");
  $("notice").classList.toggle("error", error);
  $("notice").hidden = !!state && !topDialog();
  if (error && topDialog()) $("notice").scrollIntoView({ block: "nearest" });
}
async function api(path, data) {
  if (data) stateEpoch++;
  const response = await fetch(path, {
    method: data ? "POST" : "GET",
    headers: {
      Authorization: `Bearer ${token}`,
      ...(data ? { "Content-Type": "application/json" } : {}),
    },
    body: data ? JSON.stringify(data) : undefined,
  });
  if (data) stateEpoch++;
  if (!response.ok) {
    const body = await response.json();
    const error = new Error(body.error);
    error.status = response.status;
    throw error;
  }
  return response.headers.get("content-type").includes("application/json")
    ? response.json()
    : response.blob();
}
function action(fn) {
  return async (event) => {
    // Los paneles delegan clics a varios handlers; solo bloquear controles directos.
    let button =
      event?.submitter ||
      (event?.currentTarget?.matches?.("button") ? event.currentTarget : null);
    if (button?.id === "dictate") button = null; // El micrófono sigue siendo un toggle durante la conexión.
    if (button?.getAttribute("aria-busy") === "true") {
      event.preventDefault();
      return;
    }
    button?.setAttribute("aria-busy", "true");
    try {
      await fn(event);
    } catch (error) {
      notice(error.message, true);
    } finally {
      button?.removeAttribute("aria-busy");
    }
  };
}
function confirmLeave() {
  return (
    !dirty ||
    confirm(
      "Hay cambios sin guardar. Se conserva un borrador en esta pestaña. ¿Querés cambiar de documento?",
    )
  );
}
async function refreshProjects() {
  const data = await api("/api/projects");
  $("project").innerHTML = data.projects
    .map((p) => `<option value="${p.id}">${escapeHTML(p.title)}</option>`)
    .join("");
  if (state) $("project").value = state.id;
  $("archived-projects").innerHTML =
    data.archived
      .map(
        (p) =>
          `<div class="archived-project"><span>${escapeHTML(p.title)}</span><button class="secondary" data-restore-project="${p.id}" aria-label="Restaurar ${escapeHTML(p.title)} a la biblioteca">Restaurar</button></div>`,
      )
      .join("") || "<p>No hay proyectos archivados.</p>";
  return data.projects;
}
async function openProject(id, startInterview = true) {
  if (!confirmLeave()) {
    $("project").value = state.id;
    return;
  }
  await cancelVoice();
  const incoming = await api(`/api/projects/${id}`);
  if (incoming.archived)
    throw new Error(
      "Este proyecto está archivado. Restauralo desde Proyectos archivados.",
    );
  state = incoming;
  if ($("team-enabled")) $("team-enabled").checked = false;
  resetVoiceProject();
  $("prompt").value = sessionStorage.getItem("sw-message-" + id) || "";
  current = null;
  dirty = false;
  if (backgroundURL) {
    URL.revokeObjectURL(backgroundURL);
    backgroundURL = null;
    $("ambient-image").hidden = true;
    $("inspire").textContent = "◐ Ambiente";
  }
  sessionStorage.setItem("sw-project", id);
  $("welcome").hidden = true;
  $("workspace").hidden = false;
  $("export").disabled = false;
  $("book-open").disabled = false;
  $("plan-open").disabled = false;
  $("project").value = id;
  $("project-title").textContent = state.title;
  $("search").value = "";
  lastRuns = lastProposals = lastDecisions = "";
  document.body.classList.remove("material-open", "library-open");
  $("material-toggle").textContent = "Ver material";
  $("material-toggle").setAttribute("aria-expanded", "false");
  applyWorkflow();
  const savedMode = sessionStorage.getItem("sw-message-mode-" + id);
  if ([...$("mode").options].some((option) => option.value === savedMode)) {
    $("mode").value = savedMode;
    setTaskMode();
  }
  renderDocuments();
  renderAssistant();
  renderEngine();
  if (state.documents.length) {
    const last = sessionStorage.getItem(`sw-doc-${id}`);
    openDocument(
      state.documents.some((d) => d.id === last) ? last : state.documents[0].id,
      true,
    );
  } else clearDocument();
  showPanel("conversation");
  if (
    startInterview &&
    state.history_start === undefined &&
    state.workflow === "guided" &&
    !hasPurposeInterview()
  ) {
    try {
      await beginInterview();
    } catch (error) {
      notice(error.message, true);
    }
  }
}
$("archive-project").onclick = action(async () => {
  if (!state) return;
  if (dirty)
    throw new Error(
      "Guardá los cambios del documento antes de archivar el proyecto.",
    );
  const project = state.id;
  savePromptDraft();
  await api("/api/project/archive", { project, archived: true });
  if (state?.id !== project) {
    await refreshProjects();
    return;
  }
  await cancelVoice();
  if (state?.id !== project) {
    await refreshProjects();
    return;
  }
  state = null;
  dirty = false;
  stateEpoch++;
  clearDocument();
  resetVoiceProject();
  renderVoice();
  sessionStorage.removeItem("sw-project");
  $("prompt").value = "";
  if (backgroundURL) {
    URL.revokeObjectURL(backgroundURL);
    backgroundURL = null;
    $("ambient-image").hidden = true;
    $("inspire").textContent = "◐ Ambiente";
  }
  document.body.classList.remove(
    "focus",
    "guided",
    "material-open",
    "library-open",
  );
  $("workspace").hidden = true;
  $("welcome").hidden = false;
  for (const id of ["export", "book-open", "plan-open"]) $(id).disabled = true;
  const projects = await refreshProjects();
  if (!state && projects.length) {
    await openProject(projects[0].id, false);
    $("project").focus();
  } else if (!state) $("blank").focus();
  notice(
    "Proyecto archivado. Conserva sus archivos e historial; podés restaurarlo desde Proyectos archivados.",
  );
});
document.querySelectorAll("[data-archived-open]").forEach(
  (button) =>
    (button.onclick = action(async () => {
      await refreshProjects();
      showDialog($("archived-dialog"));
    })),
);
$("archived-close").onclick = () => $("archived-dialog").close();
$("archived-projects").onclick = action(async (event) => {
  const button = event.target.closest("[data-restore-project]");
  if (!button) return;
  const project = button.dataset.restoreProject;
  await api("/api/project/archive", { project, archived: false });
  await refreshProjects();
  if (!state) {
    $("archived-dialog").close();
    await openProject(project, false);
    $("project").focus();
  } else $("archived-close").focus();
  notice("Proyecto restaurado a Tu biblioteca.");
});
function clearDocument() {
  current = null;
  $("editor").value = "";
  $("doc-title").value = "";
  $("editor").disabled = true;
  for (const id of ["save", "rename", "role", "download", "undo", "redo"])
    $(id).disabled = true;
  $("history").textContent = "Todavía no hay documentos.";
  $("preview").textContent = "";
  $("conflict").hidden = true;
  updateStats();
  renderView();
}
function renderDocuments() {
  renderBookProgress();
  const term = $("search").value.toLocaleLowerCase();
  $("search-clear").hidden = !term;
  const docs = state.documents.filter((d) =>
    `${d.name} ${d.content}`.toLocaleLowerCase().includes(term),
  );
  $("documents").innerHTML =
    docs
      .map(
        (d) =>
          `<div class="document-item ${d.id === current?.id ? "active" : ""}"><button data-doc="${d.id}" title="${escapeHTML(d.name)}"><span class="document-icon" aria-hidden="true">${d.role === "canon" ? "◇" : d.role === "estilo" ? "✧" : "≡"}</span><span><strong>${escapeHTML(d.name.replace(/\.md$/i, ""))}</strong><small>${labels[d.role]} · ${wordCount(d.content)} palabras</small></span></button><input type="checkbox" data-context="${d.id}" ${d.selected ? "checked" : ""} aria-label="Compartir ${escapeHTML(d.name)} con Codex"></div>`,
      )
      .join("") ||
    `<p class="assistant-empty">${term ? "No hay coincidencias. Probá otra palabra o limpiá la búsqueda." : "Todavía no hay documentos. Podés continuar la entrevista sin fuentes o crear una ficha."}</p>`;
  $("doc-count").textContent = state.documents.length;
  const selected = state.documents.filter((d) => d.selected),
    chars = selected.reduce(
      (n, d) =>
        n + d.content.length + (d.synopsis || "").length + (d.pov || "").length,
      0,
    );
  $("context-count").textContent =
    `${selected.length} fuente${selected.length === 1 ? "" : "s"} seleccionada${selected.length === 1 ? "" : "s"}`;
  $("context-size").textContent =
    `${chars.toLocaleString("es")} caracteres seleccionados`;
}
function openDocument(id, force = false) {
  if (!force && !confirmLeave()) return;
  if (!force) showMaterial();
  current = { ...state.documents.find((d) => d.id === id) };
  if (!current.id) return clearDocument();
  sessionStorage.setItem(`sw-doc-${state.id}`, current.id);
  $("editor").disabled = false;
  for (const id of ["save", "rename", "role", "download", "undo", "redo"])
    $(id).disabled = false;
  $("doc-title").value = current.name.replace(/\.md$/i, "");
  $("role").value = current.role;
  $("doc-role-label").textContent = labels[current.role];
  $("editor").value = current.content;
  dirty = false;
  $("conflict").hidden = true;
  const draft = sessionStorage.getItem(draftKey());
  if (draft !== null && draft !== current.content) {
    $("editor").value = draft;
    dirty = true;
    notice(
      "Recuperamos tu borrador de esta pestaña. Revisalo antes de guardar.",
    );
  }
  renderDocuments();
  updateStats();
  renderView();
}
function wordCount(text) {
  return text.trim() ? text.trim().split(/\s+/u).length : 0;
}
function updateStats() {
  const n = wordCount($("editor").value);
  $("words").textContent = `${n.toLocaleString("es")} palabras`;
  $("reading").textContent =
    `${Math.max(1, Math.ceil(n / 220))} min de lectura`;
  const savedLabel = dirty ? "Borrador sin guardar" : "Guardado local";
  if ($("save-state").textContent !== savedLabel)
    $("save-state").textContent = savedLabel;
  $("save-state").dataset.state = dirty ? "dirty" : "saved";
  $("save-state").setAttribute("role", "status");
  $("save").disabled = !current || !dirty;
}
function renderView() {
  $("editor").hidden = view !== "edit";
  $("preview").hidden = view !== "preview";
  $("history").hidden = view !== "history";
  document.querySelectorAll("[data-view]").forEach((b) => {
    b.classList.toggle("active", b.dataset.view === view);
    b.setAttribute("aria-selected", b.dataset.view === view);
  });
  if (view === "preview") $("preview").innerHTML = markdown($("editor").value);
  if (view === "history" && current)
    $("history").innerHTML =
      current.history
        .slice()
        .reverse()
        .map(
          (v) =>
            `<div class="history-entry"><div>${escapeHTML(v.reason)}<small>${new Date(v.date * 1000).toLocaleString("es")}</small></div><button class="secondary" data-restore="${v.id}">Restaurar</button></div>`,
        )
        .join("") ||
      '<p class="assistant-empty">Cada guardado que cambia el texto conserva la versión anterior aquí.</p>';
}
async function save() {
  if (!current || !dirty) return;
  const documentId = current.id,
    content = $("editor").value;
  try {
    const saved = await api("/api/document/save", {
      project: state.id,
      document: documentId,
      content,
      hash: current.hash,
    });
    state.documents = state.documents.map((d) =>
      d.id === saved.id ? saved : d,
    );
    current = saved;
    dirty = $("editor").value !== content;
    if (!dirty) sessionStorage.removeItem(draftKey());
    $("conflict").hidden = true;
    updateStats();
    renderDocuments();
    notice("Guardado. La versión anterior está en el historial.");
  } catch (error) {
    if (error.status === 409) $("conflict").hidden = false;
    throw error;
  }
}
async function nameDialog(title, value = "") {
  $("name-dialog").returnValue = "";
  $("dialog-title").textContent = title;
  $("new-name").value = value;
  showDialog($("name-dialog"));
  $("new-name").focus();
  return new Promise((resolve) =>
    $("name-dialog").addEventListener(
      "close",
      () =>
        resolve(
          $("name-dialog").returnValue === "ok"
            ? $("new-name").value.trim()
            : null,
        ),
      { once: true },
    ),
  );
}
let wizardStep = 1,
  wizardProject = null,
  wizardCreating = false;
function setWizardStep(step) {
  wizardStep = step;
  $("wizard-translation").disabled =
    step !== 2 || $("wizard-purpose").value !== "translation";
  $("wizard-details").hidden = step !== 1;
  $("wizard-approach").hidden = step !== 2;
  $("wizard-back").hidden = step !== 2;
  $("wizard-next").hidden = step !== 1;
  $("wizard-create").hidden = step !== 2;
  $("wizard-step").textContent =
    step === 1
      ? "PASO 1 DE 2 · TU PROYECTO"
      : "PASO 2 DE 2 · TU PUNTO DE PARTIDA";
  $("wizard-title").textContent =
    step === 1
      ? "Dale un espacio a tu historia."
      : "Elegí cómo querés continuar.";
  (step === 1 ? $("project-name") : $("wizard-purpose")).focus();
}
function projectWizard(folder = false) {
  $("wizard-form").reset();
  clearWizardMaterial();
  updateWizardPurpose();
  wizardProject = null;
  $("project-wizard").returnValue = "";
  $("wizard-guided-note").hidden = false;
  $("wizard-create").textContent = "Crear e iniciar entrevista";
  showDialog($("project-wizard"));
  setWizardStep(1);
  $("wizard-folder-options").open = folder;
  return new Promise((resolve) =>
    $("project-wizard").addEventListener(
      "close",
      () => {
        wizardMaterialEpoch++;
        resolve(wizardProject);
      },
      { once: true },
    ),
  );
}
$("wizard-next").onclick = () => {
  if ($("project-name").reportValidity() && $("project-name").value.trim())
    setWizardStep(2);
};
$("wizard-back").onclick = () => setWizardStep(1);
$("wizard-cancel").onclick = () => {
  if (!wizardCreating) $("project-wizard").close("cancel");
};
$("project-wizard").oncancel = (e) => {
  if (wizardCreating) e.preventDefault();
};
$("wizard-form").onsubmit = action(async (e) => {
  e.preventDefault();
  if (wizardStep === 1) {
    $("wizard-next").click();
    return;
  }
  if (wizardCreating) return;
  const setup = wizardPayload();
  wizardCreating = true;
  $("wizard-back").disabled = $("wizard-cancel").disabled = true;
  try {
    wizardProject = await api("/api/projects", setup);
    $("project-wizard").close("create");
  } finally {
    wizardCreating = false;
    $("wizard-back").disabled = $("wizard-cancel").disabled = false;
  }
});
document.querySelectorAll('[name="start-workflow"]').forEach(
  (input) =>
    (input.onchange = () => {
      const guided =
        document.querySelector('[name="start-workflow"]:checked').value ===
        "guided";
      $("wizard-guided-note").hidden = !guided;
      $("wizard-create").textContent = guided
        ? "Crear e iniciar entrevista"
        : "Crear proyecto";
    }),
);
async function createProject(demo = false, folder = false) {
  if (!confirmLeave()) return;
  const project = demo
    ? await api("/api/projects", {
        title: "El faro · proyecto ficticio",
        workflow: "writing",
        demo: true,
      })
    : await projectWizard(folder);
  if (!project) return;
  dirty = false;
  await refreshProjects();
  await openProject(project.id);
}
function applyWorkflow() {
  const guided = state.workflow === "guided";
  document.body.classList.toggle("guided", guided);
  $("workflow").value = guided ? "guided" : "writing";
  $("material-toggle").hidden = !guided;
  updateLibraryToggle();
  const assistant = document.querySelector(".assistant"),
    manuscript = document.querySelector(".manuscript");
  $("workspace").insertBefore(
    guided ? assistant : manuscript,
    guided ? manuscript : assistant,
  );
  $("assistant-title").textContent = guided
    ? "Construyamos tu historia"
    : "Asistente editorial";
  $("assistant-eyebrow").textContent = guided
    ? "UNA PREGUNTA POR VEZ"
    : "UNA SEGUNDA MIRADA";
  $("editor").placeholder = guided
    ? "Tu material se reúne aquí. Podés crear notas o pasar a Escribir cuando quieras."
    : "Toda historia empieza en alguna parte…";
  $("mode").value = guided ? "interview" : "chat";
  setTaskMode();
  applyPurpose();
  lastRuns = "";
}
function setTaskMode() {
  if (typeof renderTeam === "function") renderTeam();
  updateTaskHelp();
  const interview = $("mode").value === "interview";
  if (interview) $("skill").checked = true;
  $("skill").disabled = interview;
  $("prompt").placeholder = interview
    ? "Respondé con tus ideas. Vamos una pregunta por vez…"
    : "¿Qué te gustaría trabajar en esta historia?";
}
async function beginInterview(retry = false) {
  const project = state.id;
  if (!(await engineReady())) return;
  await api("/api/interview/start", { project, retry });
  if (state.id !== project) return;
  const incoming = await api(`/api/projects/${project}`);
  if (state.id !== project) return;
  state = incoming;
  renderAssistant();
}
$("workflow").onchange = action(async (e) => {
  state = await api("/api/project/workflow", {
    project: state.id,
    workflow: e.target.value,
  });
  applyWorkflow();
  savePromptDraft();
  renderAssistant();
  showPanel("conversation");
  if (state.workflow === "guided" && !hasPurposeInterview())
    await beginInterview();
});
$("mode").onchange = () => {
  setTaskMode();
  savePromptDraft();
};
$("interview-start").onclick = action(() => beginInterview(true));
function imageAttachmentsHTML(run) {
  return (
    (run.attachments || [])
      .map((id) => {
        const record = state.images?.find((image) => image.id === id);
        return record
          ? `<button class="image-attachment" data-image="${escapeHTML(id)}" data-image-project="${escapeHTML(state.id)}" aria-label="Ampliar imagen generada"><img alt="Imagen generada provisional" width="240" height="180"><span>Imagen · ${record.width} × ${record.height}<small>Ampliar · original descargable</small></span></button>`
          : "";
      })
      .join("") +
    (run.attachment_error
      ? `<p class="run-error">${escapeHTML(run.attachment_error)}</p>`
      : "")
  );
}
function workingTime(start) {
  const seconds = Math.max(0, Math.floor(Date.now()/1000-start));
  return `Trabajando (${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,'0')} · presioná Escape para interrumpir)`;
}
setInterval(() => {
  for (const node of document.querySelectorAll('[data-working-since]'))
    node.textContent = workingTime(Number(node.dataset.workingSince));
}, 1000);
function runTimestamp(run) {
  if (['connecting','running'].includes(run.status) && Number.isFinite(run.date))
    return `<span class="run-time" data-working-since="${run.date}">${workingTime(run.date)}</span>`;
  const value = run.finished_at ?? run.date;
  if (!Number.isFinite(value)) return '';
  const date = new Date(value * 1000);
  const label = run.finished_at ? (run.status === 'completed' ? 'Última respuesta' : 'Finalizada') : 'Inicio';
  return `<time class="run-time" datetime="${date.toISOString()}" title="${label}">${label}: ${escapeHTML(date.toLocaleString('es', {dateStyle:'short', timeStyle:'medium'}))}</time>`;
}
function renderAssistant() {
  resizePrompt();
  renderContextWarning();
  renderTranslationNext();
  renderAISettings();
  renderProgress();
  updateRealtime();
  updateVoice();
  const active = busy();
  $("cancel").hidden = !active;
  $("send").disabled = !!active || !!recording || transcribing;
  renderEngine();
  if (active) $("connection").textContent += " · " + labels[active.status];
  renderConversations();
  const interview = currentRuns().findLast(
    (r) =>
      r.mode === "interview" &&
      (r.purpose || "novel") === (state.purpose || "novel"),
  );
  $("interview-actions").hidden =
    state.workflow !== "guided" ||
    !!active ||
    (interview && !["failed", "interrupted"].includes(interview.status));
  $("interview-start").textContent = interview
    ? "Retomar entrevista"
    : "Comenzar entrevista";
  $("interview-hint").textContent = interview
    ? "La entrevista quedó incompleta. Podés retomarla con el historial guardado."
    : "Podés empezar sin documentos. El agente te ayudará a encontrar el punto de partida.";
  const runsKey = JSON.stringify([
    currentRuns(),
    state.history_start,
    state.documents.map((d) => [d.hash, d.translation_status]),
    state.workflow,
  ]);
  if (runsKey !== lastRuns) {
    const restoreTranslationFocus = rememberTranslationFocus();
    const scrollPosition = $("runs").scrollTop;
    const messagesKey = JSON.stringify(
      currentRuns().map((r) => [r.id, r.prompt, r.text, r.attachments]),
    );
    const newMessage = $("runs").dataset.messages !== messagesKey;
    $("runs").dataset.messages = messagesKey;
    const nearBottom =
      $("runs").scrollHeight - $("runs").scrollTop - $("runs").clientHeight <
      100;
    lastRuns = runsKey;
    $("runs").innerHTML =
      currentRuns()
        .map(
          (r) =>
            `<div class="run"><div class="run-prompt">${escapeHTML(r.prompt)}</div><div class="run-label"><span>✧ ${labels[r.mode].toUpperCase()} · ${labels[r.status] || r.status}${r.model ? ` · ${escapeHTML(r.provider && r.provider !== "codex" ? r.provider + " · experimental" : "Codex")} · ${escapeHTML(r.reported_model || r.model)}${r.effort ? " · " + escapeHTML(effortLabels[r.effort] || r.effort) : ""}` : ""}</span>${runTimestamp(r)}</div><details class="run-output ${outputPreference(r.id).seen ? "" : "is-new"}" data-output="${r.id}" ${outputPreference(r.id).open !== false ? "open" : ""}><summary>${r.status === "completed" ? "Respuesta lista" : labels[r.status] || r.status}${r.status === "running" ? '<span class="work-spinner" aria-hidden="true"></span>' : ""}${outputPreference(r.id).seen ? "" : '<span class="new-tag">Nuevo</span>'}</summary><div class="run-text markdown${r.status === "running" && r.text && r.mode !== "translate" ? " is-streaming" : ""}">${markdown(r.mode === "translate" && r.status !== "completed" ? "Preparando la consulta o traducción revisable…" : r.text || (["running", "connecting"].includes(r.status) ? "Preparando una respuesta…" : ""))}</div>${imageAttachmentsHTML(r)}${translationHTML(r)}${typeof teamHTML === "function" ? teamHTML(r) : ""}${r.error ? `<div class="run-error">${escapeHTML(r.error)}</div>` : ""}<details class="run-sources" data-output="sources-${r.id}" ${outputPreference("sources-" + r.id).open ? "open" : ""}><summary>${r.sources.length} fuentes enviadas · ${r.guide === "integrated" ? "Guía integrada" : r.skill ? "build-novel" : "Asistente general"}</summary>${r.sources.map((s) => `${escapeHTML(s.name)} · ${s.hash.slice(0, 8)}${s.synopsis || s.pov ? " · incluye ficha del plan" : ""}${state.documents.find((d) => d.id === s.id)?.hash !== s.hash ? " · cambió desde este envío" : ""}`).join("<br>")}<br>Se enviaron como texto. No afirmamos lectura mediante herramientas.</details>${r.status === "completed" ? `<button class="quiet" data-read="${r.id}">Escuchar</button>` : ""}${r.mode === "draft" && r.status === "completed" ? `<button class="quiet" data-draft="${r.id}">${r.saved_document ? "Abrir borrador guardado" : r.purpose === "rpg" ? "Guardar material de rol provisional" : "Guardar como borrador provisional"}</button>` : ""}${r.mode === "summary" && r.status === "completed" ? `<button class="quiet" data-summary="${r.id}">Guardar resumen como fuente provisional</button>` : ""}${r.status === "completed" && !outputPreference(r.id).seen ? `<button class="quiet run-seen" data-seen="${r.id}">Marcar como visto</button>` : ""}</details></div>`,
        )
        .join("") ||
      '<div class="assistant-empty"><div class="empty-symbol">✧</div><h3>Tu historia, con otra mirada.</h3><p>Las fuentes dan contexto.<br>Vos marcás el rumbo.</p><div class="quick-actions"><button data-quick="diagnosis">◈ Encontrar contradicciones</button><button data-quick="impact">↗ ¿Qué cambia si cambio esto?</button><button data-quick="proposal">≋ Afinar un pasaje</button></div></div>';
    if (!currentRuns().length && state.workflow === "guided")
      $("runs").innerHTML =
        '<div class="assistant-empty"><div class="empty-symbol">✧</div><h3>Empecemos con lo que imaginás.</h3><p>No hace falta llegar con un argumento cerrado.<br>El asistente te acompaña, una pregunta por vez.</p></div>';
    if (!currentRuns().length && state.conversations?.length)
      $("runs").innerHTML =
        '<div class="assistant-empty"><h3>Nueva conversación</h3><p>El chat anterior ya no forma parte del contexto.<br>Las fuentes seleccionadas y las decisiones del proyecto siguen disponibles.</p></div>';
    if (newMessage || nearBottom) $("runs").scrollTop = $("runs").scrollHeight;
    else $("runs").scrollTop = scrollPosition;
    restoreTranslationFocus();
    document.dispatchEvent(new Event("workbench:images-render"));
    updateLatestAnswer();
  }
  const proposalsKey = JSON.stringify(state.proposals);
  $("proposal-count").textContent = state.proposals.filter(
    (p) => p.status === "pending",
  ).length;
  if (proposalsKey !== lastProposals) {
    lastProposals = proposalsKey;
    $("proposals").innerHTML =
      state.proposals
        .slice()
        .reverse()
        .map(
          (p) =>
            `<article class="proposal"><details data-output="proposal-${p.id}" ${outputPreference("proposal-" + p.id).open !== false ? "open" : ""}><summary>${escapeHTML(state.documents.find((d) => d.id === p.document)?.name || "Documento")} · ${labels[p.status]}</summary><p>${escapeHTML(p.reason)}</p><small>ANTES</small><pre class="before">${escapeHTML(p.before)}</pre><small>PROPUESTA</small><pre class="after">${escapeHTML(p.after)}</pre><div class="proposal-actions">${p.status === "pending" ? `<button class="quiet" data-reject="${p.id}">Rechazar</button><button class="primary" data-accept="${p.id}">Aceptar bloque</button>` : `<span class="tag">${labels[p.status]}</span>`}</div></details></article>`,
        )
        .join("") ||
      '<p class="assistant-empty">Cuando pidas «Proponer cambios», los bloques aparecerán aquí para revisarlos.</p>';
  }
  const decisionsKey = JSON.stringify(state.decisions);
  if (decisionsKey !== lastDecisions) {
    lastDecisions = decisionsKey;
    $("decisions").innerHTML =
      state.decisions
        .slice()
        .reverse()
        .map(
          (d) =>
            `<div class="decision"><span class="tag">${labels[d.status]}</span><p>${escapeHTML(d.text)}</p><small>${new Date(d.date * 1000).toLocaleString("es")}</small></div>`,
        )
        .join("") ||
      '<p class="assistant-empty">Todavía no registraste decisiones.</p>';
  }
}
function showPanel(name) {
  panel = name;
  for (const n of ["conversation", "proposals", "decisions", "notices"])
    $(`${n}-panel`).hidden = n !== name;
  if (name === "notices") renderNotices(true);
  document.querySelectorAll("[data-panel]").forEach((b) => {
    b.classList.toggle("active", b.dataset.panel === name);
    b.setAttribute("aria-selected", b.dataset.panel === name);
  });
}
async function poll() {
  if (!state || polling) return;
  polling = true;
  try {
    const project = state.id,
      epoch = stateEpoch,
      incoming = await api(`/api/projects/${project}`);
    if (project !== state?.id || epoch !== stateEpoch) return;
    const wasBusy = !!busy();
    const workflowChanged = state.workflow !== incoming.workflow;
    state = incoming;
    if (workflowChanged) applyWorkflow();
    if (current) {
      const latest = state.documents.find((d) => d.id === current.id);
      if (latest && latest.hash !== current.hash) $("conflict").hidden = false;
    }
    renderAssistant();
    renderBookProgress();
    if (wasBusy && !busy()) {
      renderDocuments();
      notice(
        state.runs.at(-1).status === "completed"
          ? "La respuesta está lista."
          : "La tarea terminó. Revisá su estado.",
      );
    }
  } catch (error) {
    if (busy()) notice(error.message, true);
  } finally {
    polling = false;
  }
}
async function download(blob, name) {
  if (window.storyDesktop) {
    const response = await fetch(
      "/api/desktop/save?name=" + encodeURIComponent(name),
      {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: new Uint8Array(await blob.arrayBuffer()),
      },
    );
    const result = await response.json();
    if (!response.ok) throw Error(result.error);
    if (result.saved) notice("Exportación guardada.");
    return result.saved;
  }
  const url = URL.createObjectURL(blob),
    link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
async function downloadDocument() {
  if (current)
    return download(
      new Blob([$("editor").value], { type: "text/markdown;charset=utf-8" }),
      current.name.replace(/\.md$/i, "") + ".md",
    );
}

$("demo").onclick = action(() => createProject(true));
$("blank").onclick = action(() => createProject());
$("new-project").onclick = action(() => createProject());
$("project").onchange = action((e) => openProject(e.target.value));
$("search").oninput = renderDocuments;
$("documents").onclick = action((e) => {
  const b = e.target.closest("[data-doc]");
  if (b) openDocument(b.dataset.doc);
});
$("documents").onchange = action(async (e) => {
  if (!e.target.dataset.context) return;
  state = await api("/api/document/meta", {
    project: state.id,
    document: e.target.dataset.context,
    selected: e.target.checked,
  });
  renderDocuments();
});
$("new-doc").onclick = action(async () => {
  const name = await nameDialog("Un documento nuevo");
  if (!name) return;
  const doc = await api("/api/document/add", {
    project: state.id,
    name: name + ".md",
    role: "manuscrito",
    content: "",
  });
  state = await api(`/api/projects/${state.id}`);
  openDocument(doc.id);
});
$("import").onclick = () => $("files").click();
async function importBookFile(file) {
  return (
    await import(new URL("./formats.js", document.baseURI).href)
  ).importBookFile(file, api);
}
$("files").onchange = action(async (e) => {
  const project = state.id,
    documents = [],
    warnings = [];
  for (const file of e.target.files) {
    const result = await importBookFile(file);
    // Preserve the reference role of loose text imports; book containers are manuscripts.
    const role = /\.(epub|docx)$/i.test(file.name)
      ? "manuscrito"
      : "referencia";
    documents.push(
      ...result.documents.map((document) => ({ ...document, role })),
    );
    warnings.push(...result.warnings);
  }
  if (state.id !== project)
    throw Error("Cambió el proyecto. Volvé a importar en el proyecto elegido.");
  if (!documents.length) return;
  state = await api("/api/document/import", { project, documents });
  renderDocuments();
  if (!current && state.documents.length)
    openDocument(state.documents[0].id, true);
  e.target.value = "";
  notice(
    "Copias importadas, sin seleccionar para IA. " +
      [...new Set(warnings)].join(" "),
  );
});
$("editor").oninput = () => {
  if (!current) return;
  dirty = $("editor").value !== current.content;
  try {
    sessionStorage.setItem(draftKey(), $("editor").value);
  } catch {
    notice(
      "No se pudo conservar el borrador de la pestaña. Guardá o descargá tu texto.",
      true,
    );
  }
  updateStats();
};
$("save").onclick = action(save);
$("download").onclick = action(downloadDocument);
$("rename").onclick = action(async () => {
  if (!current) return;
  state = await api("/api/document/meta", {
    project: state.id,
    document: current.id,
    name: $("doc-title").value.trim() + ".md",
  });
  current.name = state.documents.find((d) => d.id === current.id).name;
  renderDocuments();
  notice("Nombre actualizado.");
});
$("role").onchange = action(async (e) => {
  if (!current) return;
  state = await api("/api/document/meta", {
    project: state.id,
    document: current.id,
    role: e.target.value,
  });
  current.role = e.target.value;
  $("doc-role-label").textContent = labels[current.role];
  renderDocuments();
});
$("reload").onclick = action(async () => {
  if (dirty && !confirm("¿Descartar el borrador y cargar la versión guardada?"))
    return;
  sessionStorage.removeItem(draftKey());
  state = await api(`/api/projects/${state.id}`);
  openDocument(current.id, true);
});
document.querySelectorAll("[data-view]").forEach(
  (b) =>
    (b.onclick = () => {
      view = b.dataset.view;
      renderView();
    }),
);
document
  .querySelectorAll("[data-panel]")
  .forEach((b) => (b.onclick = () => showPanel(b.dataset.panel)));
$("notices-clear").onclick = () => {
  notices.length = 0;
  renderNotices();
};
document.querySelectorAll("[data-format]").forEach(
  (b) =>
    (b.onclick = () => {
      if (!current) return;
      view = "edit";
      renderView();
      const e = $("editor"),
        start = e.selectionStart,
        end = e.selectionEnd,
        selected = e.value.slice(start, end),
        mark =
          b.dataset.format === "bold"
            ? "**"
            : b.dataset.format === "italic"
              ? "*"
              : "## ";
      e.focus();
      e.setSelectionRange(start, end);
      // insertText conserva la pila nativa de deshacer en Chromium; setRangeText la saltea.
      const replacement =
        mark + selected + (b.dataset.format === "heading" ? "" : mark);
      if (document.execCommand("insertText", false, replacement))
        e.setSelectionRange(start, start + replacement.length);
      else notice("No se pudo aplicar el formato.", true);
    }),
);
$("history").onclick = action(async (e) => {
  const b = e.target.closest("[data-restore]");
  if (!b) return;
  if (dirty)
    throw new Error("Guardá o descargá tu borrador antes de restaurar.");
  if (
    !confirm(
      "¿Restaurar esta versión? También conservaremos la versión actual.",
    )
  )
    return;
  const doc = await api("/api/document/restore", {
    project: state.id,
    document: current.id,
    version: b.dataset.restore,
    hash: current.hash,
  });
  state.documents = state.documents.map((d) => (d.id === doc.id ? doc : d));
  sessionStorage.removeItem(draftKey());
  openDocument(doc.id, true);
  notice("Versión restaurada.");
});
$("runs").onclick = action(async (e) => {
  const draft = e.target.closest("[data-draft]");
  if (draft) {
    if (dirty)
      throw new Error(
        "Guardá tu documento actual antes de abrir otro borrador.",
      );
    const run = state.runs.find((r) => r.id === draft.dataset.draft),
      project = state.id;
    draft.disabled = true;
    try {
      const doc = await api("/api/run/save-draft", { project, run: run.id });
      if (state.id !== project) return;
      state = await api(`/api/projects/${project}`);
      showMaterial();
      openDocument(doc.id, true);
      view = "edit";
      renderView();
      renderAssistant();
      $("editor").focus();
      $("editor").select();
      notice(
        "Borrador guardado como documento nuevo. Podés revisarlo en el editor.",
      );
    } finally {
      draft.disabled = false;
    }
    return;
  }
  const b = e.target.closest("[data-quick]");
  if (b) {
    $("mode").value = b.dataset.quick;
    setTaskMode();
    $("prompt").value = {
      diagnosis:
        "Revisá las fuentes seleccionadas y señalá contradicciones con sus pasajes, sin reescribir.",
      impact:
        "Si cambiamos este hecho de canon: [describí el cambio], ¿qué más deberíamos revisar?",
      proposal:
        "Proponé cambios mínimos y justificados en el manuscrito seleccionado. Conservá voz, tono y canon; separá cada cambio en un bloque.",
    }[b.dataset.quick];
    savePromptDraft();
    $("prompt").focus();
  }
  const s = e.target.closest("[data-summary]");
  if (s) {
    const r = state.runs.find((r) => r.id === s.dataset.summary);
    await api("/api/document/add", {
      project: state.id,
      name: "Resumen provisional.md",
      role: "referencia",
      content:
        "# Resumen provisional — verificar fuentes\n\n" +
        r.text +
        "\n\nFuentes de origen:\n" +
        r.sources.map((s) => `- ${s.name} (${s.hash})`).join("\n"),
    });
    state = await api(`/api/projects/${state.id}`);
    renderDocuments();
    notice("Resumen guardado como referencia provisional, con sus fuentes.");
  }
});
function resizePrompt() {
  const prompt = $("prompt");
  if (!prompt.clientWidth) return;
  const style = getComputedStyle(prompt);
  const padding =
    parseFloat(style.paddingTop) + parseFloat(style.paddingBottom);
  const max = parseFloat(style.lineHeight) * 7 + padding;
  const scrollTop = prompt.scrollTop;
  prompt.style.height = "auto";
  const height = prompt.scrollHeight;
  prompt.style.height = Math.min(height, max) + "px";
  prompt.style.overflowY = height > max ? "auto" : "hidden";
  prompt.scrollTop = scrollTop;
}
let composerWidth = 0;
new ResizeObserver(([entry]) => {
  if (entry.contentRect.width !== composerWidth) {
    composerWidth = entry.contentRect.width;
    resizePrompt();
  }
}).observe($("prompt").parentElement);
function savePromptDraft() {
  resizePrompt();
  if (!state) return;
  try {
    sessionStorage.setItem("sw-message-" + state.id, $("prompt").value);
    sessionStorage.setItem("sw-message-mode-" + state.id, $("mode").value);
  } catch {
    notice(
      "No se pudo conservar el mensaje en esta ventana. Copialo antes de salir.",
      true,
    );
  }
}
$("prompt").addEventListener("input", savePromptDraft);
async function sendChatMessage(
  message = $("prompt").value,
  valid = () => true,
) {
  if (!valid()) return;
  if (busy()) throw Error("Ya hay una tarea en curso.");
  if (dirty)
    throw new Error(
      "Guardá el documento antes de enviarlo: El motor editorial recibe la versión guardada.",
    );
  const project = state.id,
    mode = $("mode").value,
    skill = $("skill").checked,
    team = $("team-enabled").checked;
  if (!message.trim()) return;
  if (!(await engineReady()) || state.id !== project || !valid()) return;
  if (mode === "panel" && !team)
    throw Error("Activá múltiples agentes para ejecutar el panel ciego.");
  const previousResponses = currentRuns().filter(r => r.status === "completed").map(r => r.id);
  const run = await api("/api/run", {
    project,
    mode,
    prompt: message.trim(),
    skill,
    team,
  });
  if (state.id !== project) return;
  for (const id of previousResponses) saveOutputPreference(id, { seen: true });
  lastRuns = "";
  $("team-enabled").checked = false;
  renderTeam();
  if ($("prompt").value === message) {
    $("prompt").value = "";
    savePromptDraft();
  }
  showPanel("conversation");
  await poll();
  return run;
}
$("send").onclick = action(() => sendChatMessage());
$("cancel").onclick = action(async () => {
  const run = busy();
  if (run) {
    await api("/api/run/cancel", { project: state.id, run: run.id });
    await poll();
  }
});
window.addEventListener('keydown', event => {
  if (event.key !== 'Escape' || event.repeat || event.isComposing || event.defaultPrevented ||
      document.querySelector('dialog[open]') || event.target?.matches('select') || !busy() ||
      busy().status === 'cancelling') return;
  event.preventDefault();
  $('cancel').click();
});
$("prompt").onkeydown = (e) => {
  if (
    e.key !== "Enter" ||
    e.shiftKey ||
    e.altKey ||
    e.isComposing ||
    e.keyCode === 229
  )
    return;
  e.preventDefault();
  if (!e.repeat) $("send").click();
};
$("proposals").onclick = action(async (e) => {
  const button = e.target.closest("[data-accept],[data-reject]");
  if (!button) return;
  const accept = !!button.dataset.accept;
  if (dirty && accept)
    throw new Error("Guardá o descargá tu borrador antes de aceptar cambios.");
  const proposal = state.proposals.find(
    (p) => p.id === (button.dataset.accept || button.dataset.reject),
  );
  const offset = state.documents
    .find((d) => d.id === proposal.document)
    ?.content.indexOf(proposal.before);
  state = await api("/api/proposal/decide", {
    project: state.id,
    proposal: proposal.id,
    accept,
  });
  if (accept) {
    if (current) sessionStorage.removeItem(draftKey());
    showMaterial();
    openDocument(proposal.document, true);
    view = "edit";
    renderView();
    $("editor").focus();
    $("editor").setSelectionRange(offset, offset + proposal.after.length);
  }
  renderAssistant();
  notice(
    accept
      ? "Bloque aceptado y resaltado en el editor. La versión anterior se conserva."
      : "Propuesta rechazada.",
  );
});
$("decision-form").onsubmit = action(async (e) => {
  e.preventDefault();
  state = await api("/api/decision", {
    project: state.id,
    text: $("decision-text").value,
    status: $("decision-status").value,
  });
  $("decision-text").value = "";
  renderAssistant();
  notice("Decisión registrada.");
});
$("new-thread").onclick = action(async () => {
  await cancelVoice();
  stopRealtime();
  state = await api("/api/thread/reset", {
    project: state.id,
    draft: $("prompt").value,
  });
  $("prompt").value = "";
  savePromptDraft();
  if ($("team-enabled")) $("team-enabled").checked = false;
  lastRuns = "";
  renderAssistant();
  showPanel("conversation");
  $("prompt").focus();
  notice("Chat vacío. Podés consultar los anteriores en la biblioteca.");
});
function renderConversations() {
  const chats = state.conversations || [],
    key = JSON.stringify(chats);
  $("previous-chats").hidden = !chats.length;
  $("new-thread").disabled = !!busy();
  if ($("chat-links").dataset.key === key) return;
  $("chat-links").dataset.key = key;
  $("chat-links").innerHTML = chats
    .slice()
    .reverse()
    .map(
      (c) =>
        `<button class="quiet" data-chat="${escapeHTML(c.id)}">${escapeHTML(c.title)}<small>${new Date(c.date * 1000).toLocaleString("es")}</small></button>`,
    )
    .join("");
}
$("chat-links").onclick = action((event) => {
  const button = event.target.closest("[data-chat]");
  if (!button) return;
  const chat = state.conversations.find((c) => c.id === button.dataset.chat);
  if (!chat) return;
  $("chat-history-title").textContent = chat.title;
  $("chat-history-content").innerHTML =
    state.runs
      .slice(chat.start, chat.end)
      .map(
        (r) =>
          `<article class="run"><div class="run-prompt">${escapeHTML(r.prompt)}</div><p>${escapeHTML(labels[r.mode] || r.mode)} · ${escapeHTML(labels[r.status] || r.status)}</p><div class="run-text markdown">${markdown(r.text || "Sin respuesta guardada.")}</div>${imageAttachmentsHTML(r)}${teamHTML(r)}${r.error ? `<p class="run-error">${escapeHTML(r.error)}</p>` : ""}</article>`,
      )
      .join("") +
    (chat.draft
      ? `<article><h3>Mensaje que quedó sin enviar</h3><div class="run-text">${escapeHTML(chat.draft)}</div></article>`
      : "");
  showDialog($("chat-history"));
  document.dispatchEvent(new Event("workbench:images-render"));
});
$("chat-history-close").onclick = () => $("chat-history").close();
$("export").onclick = action(async () => {
  if (!state) return;
  if (dirty)
    throw new Error(
      "Guardá antes de exportar el proyecto o descargá el borrador como Markdown.",
    );
  const blob = await api(`/api/projects/${state.id}/export`);
  await download(blob, "story-workbench.zip");
});
$("focus").onclick = () => {
  const focused = document.body.classList.toggle("focus");
  $("focus").textContent = focused ? "⛶ Salir de foco" : "⛶ Modo foco";
  $("focus").setAttribute("aria-pressed", focused);
  if (state?.workflow === "guided") $("prompt").focus();
  else if (current) $("editor").focus();
};
$("inspire").onclick = () => {
  if (backgroundURL) {
    URL.revokeObjectURL(backgroundURL);
    backgroundURL = null;
    $("ambient-image").hidden = true;
    $("inspire").textContent = "◐ Ambiente";
  } else $("background-file").click();
};
$("background-file").onchange = action((e) => {
  const file = e.target.files[0];
  if (!file) return;
  if (
    !["image/png", "image/jpeg", "image/webp"].includes(file.type) ||
    file.size > 10000000
  )
    throw new Error("Usá una imagen PNG, JPEG o WebP de hasta 10 MB.");
  backgroundURL = URL.createObjectURL(file);
  $("ambient-image").src = backgroundURL;
  $("ambient-image").hidden = false;
  $("inspire").textContent = "◑ Quitar ambiente";
  notice("Imagen local de esta pestaña. No se envía a Codex.");
  e.target.value = "";
});
window.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
    e.preventDefault();
    if (!document.querySelector("dialog[open]")) $("save").click();
  }
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === "f") {
    e.preventDefault();
    if (!document.querySelector("dialog[open]")) $("focus").click();
  }
});
window.addEventListener("beforeunload", (e) => {
  if (dirty) {
    e.preventDefault();
    e.returnValue = "";
  }
});
window.addEventListener("DOMContentLoaded", async () => {
  try {
    const projects = await refreshProjects();
    if (!setupSeen()) {
      $("welcome").hidden = false;
      await openSetup();
      return;
    }
    if (projects.length) {
      const saved = sessionStorage.getItem("sw-project");
      await openProject(
        projects.some((p) => p.id === saved) ? saved : projects[0].id,
      );
    } else {
      $("welcome").hidden = false;
      $("export").disabled = true;
    }
  } catch (error) {
    $("welcome").hidden = false;
    notice(error.message, true);
  }
});
setInterval(poll, 1500);

function outputPreference(id) {
  try {
    return JSON.parse(
      localStorage.getItem(`sw-output-${state.id}-${id}`) || "{}",
    );
  } catch {
    return {};
  }
}
function saveOutputPreference(id, values) {
  try {
    localStorage.setItem(
      `sw-output-${state.id}-${id}`,
      JSON.stringify({ ...outputPreference(id), ...values }),
    );
  } catch {
    /* Lectura y escritura siguen funcionando sin almacenamiento de UI. */
  }
}
document.addEventListener("click", (event) => {
  const summary = event.target.closest("summary");
  if (summary?.parentElement.dataset.output)
    saveOutputPreference(summary.parentElement.dataset.output, {
      open: !summary.parentElement.open,
    });
  const seen = event.target.closest("[data-seen]");
  if (seen) {
    saveOutputPreference(seen.dataset.seen, { seen: true });
    lastRuns = "";
    renderAssistant();
  }
});
function renderProgress() {
  const run = currentRuns().at(-1),
    box = $("task-progress");
  box.hidden = !run;
  if (!run) return;
  const steps = {
    connection: 0,
    context: 1,
    generation: 2,
    validation: 3,
    ready: 4,
  };
  const names = [
    "Conectando con el proveedor elegido",
    "Preparando el contexto",
    "Generando la respuesta",
    "Comprobando y guardando el resultado",
    "Listo para revisar",
  ];
  const stage =
    run.status === "completed"
      ? 4
      : Math.min(steps[run.stage] ?? (run.status === "connecting" ? 0 : 2), 3);
  const stopped = ["interrupted", "failed", "cancelling"].includes(run.status);
  box.classList.toggle(
    "just-completed",
    box.dataset.run === run.id &&
      box.dataset.status !== run.status &&
      run.status === "completed",
  );
  box.dataset.run = run.id;
  box.dataset.status = run.status;
  if (!box.querySelector("progress"))
    box.innerHTML =
      '<strong></strong><progress max="4" aria-label="Etapas completadas de la tarea"></progress><small></small>';
  const title = `${labels[run.mode]} · ${stopped ? labels[run.status] : run.team && stage < 4 ? run.team_stage || names[stage] : names[stage]}`;
  const detail = `${stage} de 4 etapas completadas. ${stage === 4 ? "El resultado requiere tu revisión." : "No es un porcentaje del libro ni una estimación de tiempo."}`;
  if (box.firstElementChild.textContent !== title)
    box.firstElementChild.textContent = title;
  box.querySelector("progress").value = stage;
  if (box.lastElementChild.textContent !== detail)
    box.lastElementChild.textContent = detail;
}
let accountState = { status: "unknown" },
  accountPolling = false;
function renderAccount() {
  const status = accountState.status;
  renderAISettings();
  $("account-open").innerHTML =
    '<i aria-hidden="true"></i><span>ChatGPT</span>';
  $("account-open").dataset.status = status;
  $("account-open").title =
    status === "connected"
      ? "Cuenta ChatGPT conectada"
      : ["checking", "waiting"].includes(status)
        ? "Conexión ChatGPT en curso"
        : "Cuenta ChatGPT desconectada. Abrir cuenta";
  $("account-open").setAttribute("aria-label", $("account-open").title);
  $("account-status").textContent =
    {
      unknown: "Conectá tu cuenta para comenzar.",
      checking: "Comprobando la conexión…",
      connected: "Tu cuenta ChatGPT está conectada. Ya podés crear y revisar.",
      signed_out: "Iniciá sesión en el navegador con tu propia cuenta ChatGPT.",
      waiting:
        "Continuá en tu navegador. Volvé a esta ventana cuando termines.",
      error: accountState.error,
    }[status] || "";
  $("account-login").hidden = ["connected", "waiting", "checking"].includes(
    status,
  );
  $("account-logout").hidden = status !== "connected";
  $("account-cancel").hidden = status !== "waiting";
  $("account-link").hidden = status !== "waiting";
  $("account-link").removeAttribute("href");
  if (status === "waiting") {
    try {
      const url = new URL(accountState.url);
      if (
        url.origin === "https://auth.openai.com" &&
        !url.username &&
        !url.password
      )
        $("account-link").href = url.href;
    } catch {
      $("account-link").hidden = true;
    }
  }
}
async function refreshAccount() {
  accountState = await api("/api/account");
  if (accountState.status === "unknown")
    accountState = await api("/api/account/refresh", {});
  renderAccount();
  return accountState;
}
async function ensureAccount() {
  await refreshAccount();
  if (accountState.status === "connected") return true;
  showDialog($("account-dialog"));
  return false;
}
$("account-open").onclick = action(async () => {
  showDialog($("account-dialog"));
  await refreshAccount();
});
$("account-close").onclick = () => $("account-dialog").close();
$("account-login").onclick = action(async () => {
  accountState = await api("/api/account/login", {});
  renderAccount();
});
$("account-cancel").onclick = action(async () => {
  accountState = await api("/api/account/cancel", {});
  renderAccount();
});
$("account-logout").onclick = action(async () => {
  if (
    !confirm(
      "¿Cerrar la sesión de ChatGPT que usa esta app? Tus proyectos permanecen guardados.",
    )
  )
    return;
  accountState = await api("/api/account/logout", {});
  renderAccount();
});
setInterval(async () => {
  if (accountPolling || !["checking", "waiting"].includes(accountState.status))
    return;
  accountPolling = true;
  try {
    const previous = accountState.status;
    await refreshAccount();
    if (previous !== "connected" && accountState.status === "connected") {
      $("account-dialog").close();
      if (
        state?.workflow === "guided" &&
        selectedEngine() === "codex" &&
        !$("setup-dialog").open &&
        !hasPurposeInterview()
      )
        await beginInterview();
    }
  } catch (error) {
    notice(error.message, true);
  } finally {
    accountPolling = false;
  }
}, 1000);

const effortLabels = {
  none: "Sin razonamiento",
  minimal: "Mínimo",
  low: "Bajo",
  medium: "Medio",
  high: "Alto",
  xhigh: "Muy alto",
  max: "Máximo",
  ultra: "Ultra",
};
function renderAISettings() {
  const models = accountState.models || [],
    preferences = state?.ai_preferences || {};
  const selected = preferences.model
    ? models.find((m) => m.model === preferences.model)
    : models.find((m) => m.isDefault) || models[0];
  const model = $("ai-model"),
    effort = $("ai-effort");
  model.innerHTML =
    models
      .map(
        (m) =>
          `<option value="${escapeHTML(m.model)}">${escapeHTML(m.displayName)}</option>`,
      )
      .join("") || '<option value="">Conectá ChatGPT</option>';
  if (preferences.model && !selected)
    model.insertAdjacentHTML(
      "beforeend",
      `<option value="${escapeHTML(preferences.model)}">${escapeHTML(preferences.model)} · no disponible</option>`,
    );
  model.value = preferences.model || selected?.model || "";
  const choices = selected?.supportedReasoningEfforts || [];
  effort.innerHTML =
    choices
      .map(
        (e) =>
          `<option value="${escapeHTML(e.reasoningEffort)}">${escapeHTML(effortLabels[e.reasoningEffort] || e.reasoningEffort)}</option>`,
      )
      .join("") || '<option value="">—</option>';
  if (
    preferences.effort &&
    !choices.some((e) => e.reasoningEffort === preferences.effort)
  )
    effort.insertAdjacentHTML(
      "beforeend",
      `<option value="${escapeHTML(preferences.effort)}">${escapeHTML(preferences.effort)} · no disponible</option>`,
    );
  effort.value =
    preferences.effort ||
    (choices.some((e) => e.reasoningEffort === "medium")
      ? "medium"
      : selected?.defaultReasoningEffort) ||
    "";
  $("ai-summary").textContent =
    "Modelo y esfuerzo · " +
    (model.selectedOptions[0]?.textContent || "Conectá ChatGPT") +
    (effort.value ? " · " + (effortLabels[effort.value] || effort.value) : "");
  model.title = $("ai-summary").textContent;
  effort.title =
    "Razonamiento para el próximo mensaje; se guarda por proyecto.";
  model.disabled = !state || !models.length || !!busy();
  effort.disabled = model.disabled || !selected;
  $("ai-refresh").disabled =
    !!busy() || ["checking", "waiting"].includes(accountState.status);
  if (typeof renderTeam === "function") renderTeam();
  $("ai-hint").textContent =
    accountState.models_error ||
    (!models.length
      ? "Conectá ChatGPT para ver sus modelos."
      : preferences.model && !selected
        ? "El modelo guardado ya no está disponible. Elegí otro."
        : "Se guarda por proyecto y se aplica al próximo mensaje. Un esfuerzo mayor puede tardar más.");
}
async function saveAISettings(changeModel) {
  const models = accountState.models || [],
    selected = models.find((m) => m.model === $("ai-model").value);
  if (!selected) throw new Error("Elegí un modelo disponible.");
  let effort = $("ai-effort").value;
  if (
    changeModel &&
    !selected.supportedReasoningEfforts.some(
      (e) => e.reasoningEffort === effort,
    )
  )
    effort = selected.defaultReasoningEffort;
  const project = state.id;
  $("ai-model").disabled = $("ai-effort").disabled = true;
  try {
    const updated = await api("/api/project/ai", {
      project,
      preferences: { model: selected.model, effort },
    });
    if (state.id === project) state.ai_preferences = updated.ai_preferences;
  } finally {
    renderAISettings();
    renderContextWarning();
  }
}
$("ai-model").onchange = action(() => saveAISettings(true));
$("ai-effort").onchange = action(() => saveAISettings(false));
$("ai-refresh").onclick = action(async () => {
  accountState = await api("/api/account/refresh", {});
  renderAccount();
});
refreshAccount().catch(() => {});

document.addEventListener("close", placeNotice, true);

for (const command of ["undo", "redo"]) {
  $(command).onmousedown = (event) => event.preventDefault();
  $(command).onclick = () => {
    if (!current) return;
    view = "edit";
    renderView();
    $("editor").focus();
    if (!document.execCommand(command))
      notice(
        "No hay más cambios para " +
          (command === "undo" ? "deshacer" : "rehacer") +
          " en este documento. Las versiones guardadas están en Historial.",
      );
  };
}

function showMaterial() {
  document.body.classList.add("material-open");
  $("material-toggle").textContent = "Ocultar material";
  $("material-toggle").setAttribute("aria-expanded", "true");
}
$("material-toggle").onclick = () => {
  const visible = document.body.classList.toggle("material-open");
  $("material-toggle").textContent = visible
    ? "Ocultar material"
    : "Ver material";
  $("material-toggle").setAttribute("aria-expanded", String(visible));
};

window.storyRequestClose = async () => {
  if (
    dirty &&
    !confirm("Hay texto sin guardar. ¿Cerrar y descartar esos cambios?")
  )
    return;
  if (busy() && !confirm("Hay una tarea en curso. ¿Detenerla y cerrar?"))
    return;
  try {
    await api("/api/desktop/close", {});
  } catch (error) {
    notice(error.message, true);
  }
};
