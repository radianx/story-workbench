'use strict';
let book = null, bookProject = null, bookDirty = false;
function renderBook() {
  const w = Number($('book-width').value), h = Number($('book-height').value), d = Number($('book-thickness').value);
  if (w >= 80 && w <= 300 && h >= 100 && h <= 400 && d >= 2 && d <= 100) {
    const scale = Math.min(280 / h, 205 / w), model = $('book-model');
    model.style.setProperty('--bw', `${w * scale}px`);
    model.style.setProperty('--bh', `${h * scale}px`);
    model.style.setProperty('--bd', `${d * scale}px`);
  }
  $('book-model').style.transform = `rotateX(${$('book-tilt').value}deg) rotateY(${$('book-rotation').value}deg)`;
  $('book-angle').textContent = `${$('book-rotation').value}°`;
  $('book-cover-title').textContent = $('book-name').value;
  $('book-cover-author').textContent = $('book-author').value;
  $('book-spine-title').textContent = $('book-name').value;
  for (const [key, id] of [['front','book-front'], ['back','book-back'], ['spineImage','book-spine']]) {
    // Only locally decoded JPEG previews enter these style properties.
    const value = book[key];
    $(id).style.backgroundImage = value && /^data:image\/jpeg;base64,[A-Za-z0-9+/=]+$/.test(value) ? `url("${value}")` : '';
    $(id).firstElementChild.hidden = !!value;
  }
}
$('book-open').onclick = () => {
  if (!state) return;
  bookProject = state.id;
  book = {width:152.4, height:228.6, spine:20, title:state.title, author:'', front:'', back:'', spineImage:'', ...state.production};
  for (const [id, key] of [['width','width'],['height','height'],['thickness','spine'],['name','title'],['author','author']]) $(`book-${id}`).value = book[key];
  $('book-rotation').value = -28; $('book-tilt').value = 8;
  $('book-save-state').textContent = state.production ? 'Maqueta guardada localmente.' : 'Medidas de ejemplo. Ajustalas a tu edición.';
  bookDirty = false; renderBook(); $('book-dialog').showModal();
};
function closeBook(event) {
  if (bookDirty && !confirm('La maqueta tiene cambios sin guardar. ¿Querés descartarlos?')) { event?.preventDefault(); return; }
  $('book-dialog').close(); book = null;
}
$('book-close').onclick = closeBook; $('book-dialog').oncancel = closeBook;
$('book-form').oninput = () => { bookDirty = true; $('book-save-state').textContent = 'Cambios sin guardar'; renderBook(); };
for (const id of ['book-rotation','book-tilt']) $(id).oninput = renderBook;
document.querySelectorAll('[data-angle]').forEach(button => button.onclick = () => { $('book-rotation').value = button.dataset.angle; renderBook(); });
document.querySelectorAll('[data-clear-face]').forEach(button => button.onclick = () => { book[button.dataset.clearFace] = ''; bookDirty = true; renderBook(); $('book-save-state').textContent = 'Cambios sin guardar'; });
for (const [id, key] of [['front','front'], ['back','back'], ['spine','spineImage']]) {
  $(`book-${id}-file`).onchange = action(async event => {
    const file = event.target.files[0], target = book;
    event.target.value = '';
    if (!file) return;
    if (!['image/png','image/jpeg','image/webp'].includes(file.type) || file.size > 10_000_000) throw new Error('Usá PNG, JPEG o WebP de hasta 10 MB.');
    const bitmap = await createImageBitmap(file);
    try {
      const canvas = document.createElement('canvas'), scale = Math.min(1, 1000 / Math.max(bitmap.width, bitmap.height));
      canvas.width = Math.max(1, Math.round(bitmap.width * scale)); canvas.height = Math.max(1, Math.round(bitmap.height * scale));
      const ctx = canvas.getContext('2d'); ctx.fillStyle = '#fff'; ctx.fillRect(0,0,canvas.width,canvas.height); ctx.drawImage(bitmap,0,0,canvas.width,canvas.height);
      const data = canvas.toDataURL('image/jpeg', .8);
      if (data.length > 410000) throw new Error('La vista previa es demasiado pesada. Probá una imagen más pequeña.');
      if (book !== target) return;
      book[key] = data; bookDirty = true; renderBook(); $('book-save-state').textContent = 'Imagen lista; guardá la maqueta para conservarla.';
    } finally { bitmap.close(); }
  });
}
$('book-form').onsubmit = action(async event => {
  event.preventDefault();
  if (state.id !== bookProject) throw new Error('El proyecto cambió. Abrí nuevamente la maqueta.');
  const production = {...book, width:Number($('book-width').value), height:Number($('book-height').value), spine:Number($('book-thickness').value), title:$('book-name').value, author:$('book-author').value};
  $('book-save').disabled = true;
  try {
    const result = await api('/api/project/production', {project:bookProject, production});
    if (state.id === bookProject) state.production = result.production;
    book = production; bookDirty = false; $('book-save-state').textContent = 'Maqueta guardada en este proyecto.';
  } finally { $('book-save').disabled = false; }
});
