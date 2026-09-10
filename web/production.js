"use strict";
let book = null,
  bookProject = null,
  bookDirty = false;
function sizeBook() {
  const sizing = $("book-sizing").value,
    w = Number($("book-width").value),
    h = Number($("book-height").value);
  $("book-pages").readOnly = sizing !== "pages";
  $("book-pages").required = sizing !== "manual";
  $("book-thickness").readOnly = sizing !== "manual";
  $("book-paper").disabled = sizing === "manual";
  let words = 0;
  if (sizing === "estimate") {
    words = manuscripts().reduce((n, d) => n + wordCount(d.content), 0);
    // ponytail: estimación de prosa sin maquetar; reemplazar por páginas del PDF cuando exista paginador.
    const perPage =
      (300 * ((w - 30) * (h - 30))) / ((152.4 - 30) * (228.6 - 30));
    $("book-pages").value =
      w >= 80 && h >= 100
        ? Math.max(24, Math.ceil(words / perPage / 2) * 2)
        : 24;
  }
  const pages = Number($("book-pages").value);
  $("book-pages").setCustomValidity(
    sizing !== "manual" &&
      (!Number.isInteger(pages) || pages < 1 || pages > 1500)
      ? "Usá entre 1 y 1500 páginas para esta maqueta."
      : "",
  );
  if (sizing !== "manual")
    $("book-thickness").value = (
      pages * ($("book-paper").value === "cream" ? 0.0635 : 0.0572)
    ).toFixed(2);
  $("book-estimate").textContent =
    sizing === "estimate"
      ? `${words.toLocaleString("es")} palabras guardadas · ${pages} páginas estimadas. Base: 300 palabras por página a 6 × 9, márgenes de 15 mm y mínimo visual de 24 páginas. No incluye portadillas ni imágenes.`
      : sizing === "pages"
        ? "Cantidad total de páginas de tu edición (cada cara cuenta), no cantidad de hojas."
        : "Se conserva el grosor indicado por tu imprenta.";
}
function renderBook() {
  sizeBook();
  const w = Number($("book-width").value),
    h = Number($("book-height").value),
    d = Number($("book-thickness").value);
  if (w >= 80 && w <= 300 && h >= 100 && h <= 400 && d >= 0.01 && d <= 100) {
    const scale = Math.min(280 / h, 205 / w),
      model = $("book-model");
    model.style.setProperty("--bw", `${w * scale}px`);
    model.style.setProperty("--bh", `${h * scale}px`);
    model.style.setProperty("--bd", `${d * scale}px`);
  }
  $("book-model").style.transform =
    `rotateX(${$("book-tilt").value}deg) rotateY(${$("book-rotation").value}deg)`;
  $("book-angle").textContent = `${$("book-rotation").value}°`;
  $("book-cover-title").textContent = $("book-name").value;
  $("book-cover-author").textContent = $("book-author").value;
  $("book-spine-title").textContent = $("book-name").value;
  for (const [key, id] of [
    ["front", "book-front"],
    ["back", "book-back"],
    ["spineImage", "book-spine"],
  ]) {
    // Only locally decoded JPEG previews enter these style properties.
    const value = book[key];
    $(id).style.backgroundImage =
      value && /^data:image\/jpeg;base64,[A-Za-z0-9+/=]+$/.test(value)
        ? `url("${value}")`
        : "";
    $(id).firstElementChild.hidden = !!value;
  }
}
$("book-open").onclick = () => {
  if (!state) return;
  bookProject = state.id;
  book = {
    width: 152.4,
    height: 228.6,
    spine: 20,
    sizing: state.production ? "manual" : "estimate",
    pages: 24,
    paper: "white",
    title: state.title,
    author: "",
    front: "",
    back: "",
    spineImage: "",
    ...state.production,
  };
  for (const [id, key] of [
    ["width", "width"],
    ["height", "height"],
    ["thickness", "spine"],
    ["name", "title"],
    ["author", "author"],
    ["sizing", "sizing"],
    ["pages", "pages"],
    ["paper", "paper"],
  ])
    $(`book-${id}`).value = book[key];
  $("book-rotation").value = -28;
  $("book-tilt").value = 8;
  $("book-save-state").textContent = state.production
    ? "Maqueta guardada localmente."
    : "Tamaño inicial: 6 × 9 pulgadas. Páginas estimadas del manuscrito guardado.";
  bookDirty = false;
  renderBook();
  showDialog($("book-dialog"));
};
function closeBook(event) {
  if (
    bookDirty &&
    !confirm("La maqueta tiene cambios sin guardar. ¿Querés descartarlos?")
  ) {
    event?.preventDefault();
    return;
  }
  $("book-dialog").close();
  book = null;
}
$("book-close").onclick = closeBook;
$("book-dialog").oncancel = closeBook;
$("book-default-size").onclick = () => {
  $("book-width").value = 152.4;
  $("book-height").value = 228.6;
  $("book-form").oninput();
};
$("book-form").oninput = () => {
  bookDirty = true;
  $("book-save-state").textContent = "Cambios sin guardar";
  renderBook();
};
for (const id of ["book-rotation", "book-tilt"]) $(id).oninput = renderBook;
document.querySelectorAll("[data-angle]").forEach(
  (button) =>
    (button.onclick = () => {
      $("book-rotation").value = button.dataset.angle;
      renderBook();
    }),
);
document.querySelectorAll("[data-clear-face]").forEach(
  (button) =>
    (button.onclick = () => {
      book[button.dataset.clearFace] = "";
      bookDirty = true;
      renderBook();
      $("book-save-state").textContent = "Cambios sin guardar";
    }),
);
for (const [id, key] of [
  ["front", "front"],
  ["back", "back"],
  ["spine", "spineImage"],
]) {
  $(`book-${id}-file`).onchange = action(async (event) => {
    const file = event.target.files[0],
      target = book;
    event.target.value = "";
    if (!file) return;
    if (
      !["image/png", "image/jpeg", "image/webp"].includes(file.type) ||
      file.size > 10_000_000
    )
      throw new Error("Usá PNG, JPEG o WebP de hasta 10 MB.");
    await setBookImage(file, key, target);
  });
}
async function setBookImage(file, key, target = book) {
  const bitmap = await createImageBitmap(file);
  try {
    const canvas = document.createElement("canvas"),
      scale = Math.min(1, 1000 / Math.max(bitmap.width, bitmap.height));
    canvas.width = Math.max(1, Math.round(bitmap.width * scale));
    canvas.height = Math.max(1, Math.round(bitmap.height * scale));
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    const data = canvas.toDataURL("image/jpeg", 0.8);
    if (data.length > 410000)
      throw new Error(
        "La vista previa es demasiado pesada. Probá una imagen más pequeña.",
      );
    if (book !== target) return;
    book[key] = data;
    bookDirty = true;
    renderBook();
    $("book-save-state").textContent =
      "Imagen lista; guardá la maqueta para conservarla.";
  } finally {
    bitmap.close();
  }
}
$("book-form").onsubmit = action(async (event) => {
  event.preventDefault();
  if (state.id !== bookProject)
    throw new Error("El proyecto cambió. Abrí nuevamente la maqueta.");
  const production = {
    ...book,
    sizing: $("book-sizing").value,
    pages: Number($("book-pages").value),
    paper: $("book-paper").value,
    width: Number($("book-width").value),
    height: Number($("book-height").value),
    spine: Number($("book-thickness").value),
    title: $("book-name").value,
    author: $("book-author").value,
  };
  $("book-save").disabled = true;
  try {
    const result = await api("/api/project/production", {
      project: bookProject,
      production,
    });
    if (state.id === bookProject) state.production = result.production;
    book = production;
    bookDirty = false;
    $("book-save-state").textContent = "Maqueta guardada en este proyecto.";
  } finally {
    $("book-save").disabled = false;
  }
});

let bookDrag = null;
const bookStage = $("book-stage");
bookStage.tabIndex = 0;
bookStage.setAttribute(
  "aria-label",
  "Vista 3D: arrastrá para girar o usá las flechas. Los controles de giro también están debajo.",
);
bookStage.onpointerdown = (event) => {
  if (event.button !== 0 || !book) return;
  bookDrag = {
    id: event.pointerId,
    x: event.clientX,
    y: event.clientY,
    rotation: Number($("book-rotation").value),
    tilt: Number($("book-tilt").value),
  };
  bookStage.setPointerCapture(event.pointerId);
  bookStage.classList.add("dragging");
};
function rotateBook(rotation, tilt) {
  $("book-rotation").value = Math.round(
    ((((rotation + 360) % 720) + 720) % 720) - 360,
  );
  $("book-tilt").value = Math.max(-35, Math.min(35, Math.round(tilt)));
  renderBook();
}
bookStage.onpointermove = (event) => {
  if (bookDrag?.id === event.pointerId && book)
    rotateBook(
      bookDrag.rotation + (event.clientX - bookDrag.x) * 0.65,
      bookDrag.tilt - (event.clientY - bookDrag.y) * 0.3,
    );
};
bookStage.onpointerup =
  bookStage.onpointercancel =
  bookStage.onlostpointercapture =
    () => {
      bookDrag = null;
      bookStage.classList.remove("dragging");
    };
bookStage.onkeydown = (event) => {
  if (
    !book ||
    !["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)
  )
    return;
  event.preventDefault();
  rotateBook(
    Number($("book-rotation").value) +
      (event.key === "ArrowRight" ? 10 : event.key === "ArrowLeft" ? -10 : 0),
    Number($("book-tilt").value) +
      (event.key === "ArrowDown" ? 5 : event.key === "ArrowUp" ? -5 : 0),
  );
};
