// ES module: owns image state; the host supplies project/API/editor operations.
export function initImages({
  getProject,
  api,
  action,
  showDialog,
  download,
  binary,
  applyCover,
  openSettings,
}) {
  const $ = (id) => document.getElementById(id);
  const defaults = {
    openai: "gpt-image-2.5-flare",
    gemini: "gemini-3.1-flash-image",
  };
  let project = null,
    job = null,
    storage = null,
    providers = {},
    timer = null;
  const sameProject = () => project && getProject()?.id === project;
  const status = (message) => {
    $("image-status").textContent = message;
  };
  function controls() {
    const running = ["generating", "cancelling"].includes(job?.status);
    $("image-generate").disabled = running;
    $("image-cancel").hidden = !running;
    $("image-progress").hidden = !running;
    $("image-save").hidden = job?.status !== "ready";
    $("image-download").hidden = job?.status !== "ready";
    $("image-preview").hidden = job?.status !== "ready";
    if (job?.status === "ready")
      $("image-preview").src = `data:${job.mime};base64,${job.data}`;
    else $("image-preview").removeAttribute("src");
  }
  function providerFields() {
    const provider = $("image-settings-provider").value;
    $("image-key").value = "";
    $("image-remember").disabled = !storage?.available;
    $("image-remember").checked = !!storage?.stored[provider];
    $("image-key-status").textContent = providers[provider]
      ? "Clave disponible del motor editorial o de voz."
      : "Ingresá una clave API para este proveedor.";
  }
  async function gallery() {
    const data = await api(`/api/projects/${project}`);
    if (!sameProject()) return;
    const list = $("image-gallery");
    list.replaceChildren();
    for (const record of data.images || []) {
      const row = document.createElement("article");
      const title = document.createElement("p");
      title.textContent = record.prompt;
      const button = (label, handler) => {
        const element = document.createElement("button");
        element.className = "secondary";
        element.textContent = label;
        element.onclick = action(handler);
        row.append(element);
      };
      row.append(title);
      const load = () => binary(`/api/projects/${project}/images/${record.id}`);
      button("Descargar imagen", async () =>
        download(await load(), record.file),
      );
      button("Usar como portada 3D", async () => {
        const id = project,
          blob = await load();
        if (!sameProject() || project !== id)
          throw Error("El proyecto cambió.");
        $("images-dialog").close();
        await applyCover(blob);
      });
      list.append(row);
    }
    $("image-gallery-empty").hidden = !!data.images?.length;
  }
  async function open() {
    if (!getProject()) throw Error("Abrí un proyecto para crear imágenes.");
    if (project !== getProject().id) {
      project = getProject().id;
      job = null;
    }
    [providers, storage] = await Promise.all([
      api("/api/images/providers"),
      api("/api/engine-storage"),
    ]);
    $("image-provider").value = preference();
    $("image-model").value = defaults[preference()];
    controls();
    showDialog($("images-dialog"));
    await gallery();
    status(
      job?.status === "ready"
        ? "Imagen provisional lista. Guardala si querés conservarla."
        : "Solo se envía la descripción que escribas aquí.",
    );
    if (["generating", "cancelling"].includes(job?.status)) poll();
  }
  async function poll() {
    clearTimeout(timer);
    if (!job || !sameProject()) return;
    const target = job;
    try {
      const result = await api("/api/images/poll", { project, id: target.id });
      if (job !== target || !sameProject()) return;
      job = result;
      controls();
      status(
        {
          generating: "Generando imagen…",
          cancelling: "Descartando resultado al terminar…",
          ready:
            "Imagen provisional lista. Guardala en el proyecto o descargala.",
          cancelled: "Generación descartada.",
          failed: job.error,
        }[job.status],
      );
      if (["generating", "cancelling"].includes(job.status))
        timer = setTimeout(poll, 1500);
    } catch (error) {
      status(error.message);
    }
  }
  $("images-open").onclick = action(open);
  $("images-close").onclick = () => $("images-dialog").close();
  $("images-dialog").addEventListener("close", () => {
    $("image-key").value = "";
    clearTimeout(timer);
  });
  function preference() {
    try {
      return Object.hasOwn(defaults, localStorage.getItem("sw-image-provider"))
        ? localStorage.getItem("sw-image-provider")
        : "openai";
    } catch {
      return "openai";
    }
  }
  async function refreshSettings() {
    const fields = [
      "image-settings-provider",
      "image-key",
      "image-key-save",
      "image-key-forget",
    ];
    for (const id of fields) $(id).disabled = true;
    try {
      [providers, storage] = await Promise.all([
        api("/api/images/providers"),
        api("/api/engine-storage"),
      ]);
      $("image-settings-provider").value = preference();
      providerFields();
    } finally {
      for (const id of fields) $(id).disabled = false;
    }
  }
  document.addEventListener("workbench:settings-open", action(refreshSettings));
  $("settings-dialog").addEventListener("close", () => {
    $("image-key").value = "";
  });
  $("image-settings-provider").onchange = action(() => {
    localStorage.setItem(
      "sw-image-provider",
      $("image-settings-provider").value,
    );
    providerFields();
  });
  $("image-settings-open").onclick = () => {
    $("images-dialog").close();
    openSettings();
    $("settings-images").scrollIntoView({ block: "start" });
    $("image-settings-provider").focus();
  };
  $("image-provider").onchange = () => {
    $("image-model").value = defaults[$("image-provider").value];
  };
  $("image-key-forget").onclick = action(async () => {
    await api("/api/engine/key", {
      provider: $("image-settings-provider").value,
      key: "",
    });
    await refreshSettings();
    $("image-settings-status").textContent =
      "Clave API compartida retirada. Una clave de voz se administra desde Voz y lectura.";
  });
  $("image-key-save").onclick = action(async () => {
    const provider = $("image-settings-provider").value,
      key = $("image-key").value.trim();
    if (!key) throw Error("Ingresá una clave API.");
    await api("/api/engine/key", {
      provider,
      key,
      remember: $("image-remember").checked,
    });
    [providers, storage] = await Promise.all([
      api("/api/images/providers"),
      api("/api/engine-storage"),
    ]);
    providerFields();
    $("image-settings-status").textContent =
      "Clave preparada. El motor editorial del proyecto conserva su selección.";
  });
  $("image-form").onsubmit = action(async (event) => {
    event.preventDefault();
    if (!sameProject())
      throw Error("El proyecto cambió. Abrí de nuevo Imágenes.");
    const id = project;
    job = await api("/api/images/start", {
      project,
      provider: $("image-provider").value,
      model: $("image-model").value.trim(),
      prompt: $("image-prompt").value,
      shape: $("image-shape").value,
      consent: $("image-consent").checked,
    });
    if (id !== project || !sameProject()) return;
    controls();
    status("Generando imagen…");
    poll();
  });
  $("image-cancel").onclick = action(async () => {
    await api("/api/images/cancel", { project, id: job.id });
    await poll();
  });
  $("image-save").onclick = action(async () => {
    if (!sameProject()) throw Error("El proyecto cambió.");
    await api("/api/images/save", { project, id: job.id });
    await gallery();
    status(
      "Imagen guardada. No cambia el manuscrito ni la portada automáticamente.",
    );
  });
  $("image-download").onclick = action(async () => {
    const bytes = Uint8Array.from(atob(job.data), (c) => c.charCodeAt(0));
    await download(
      new Blob([bytes], { type: job.mime }),
      job.id + (job.mime === "image/png" ? ".png" : ".jpg"),
    );
  });
  return { open };
}
