# Temas de apariencia

Configuración → Apariencia e inicio ofrece una sola lista, compartida con el asistente inicial. Incluye Sistema, las paletas originales, Neón y Vice City en claro y oscuro. Sol/luna conserva la última paleta elegida para cada modo.

En **Personalizar o compartir un tema**, pulsá **Personalizar tema actual** para copiar sus colores. Los cambios se aplican y guardan en este equipo; existe una paleta personalizada por modo. **Volver al tema original** activa salvia sin borrar la paleta personalizada. Revisá la legibilidad al cambiar colores: el texto de botones se ajusta al resalte, pero el resto de combinaciones depende de tu elección.

**Opacidad de la imagen de ambiente** va de 0 a 100% y se recuerda. Ambiente permite elegir la imagen PNG/JPEG/WebP de esta sesión; se retira al cambiar de proyecto. La imagen no forma parte del tema exportado.

## Compartir o escribir un tema

**Exportar tema JSON** guarda la paleta personalizada visible. **Importar tema JSON** valida el archivo completo antes de reemplazar la paleta de su modo, activa ese modo y aplica la opacidad. Hasta 20 KB; sin CSS, JavaScript, URLs ni imágenes incrustadas. Es un formato de datos, no un plugin ejecutable. Se puede escribir con cualquier editor:

```json
{
  "version": 1,
  "name": "Medianoche",
  "mode": "dark",
  "backgroundOpacity": 10,
  "colors": {
    "ink": "#f0edf5",
    "muted": "#b9b6c4",
    "line": "#3b3943",
    "paper": "#101014",
    "bg": "#09090c",
    "surface": "#151519",
    "field": "#1c1c22",
    "green": "#be99ff",
    "pale": "#292036"
  }
}
```

`mode` admite `light` o `dark`; todos los colores son obligatorios y usan `#RRGGBB`. `green` es el nombre histórico del color de resalte: puede ser cualquier color. El nombre admite hasta 80 caracteres. Las preferencias se guardan en el perfil de la app, fuera de los proyectos; no se sincronizan entre equipos.

Comprobación: `python3 tests/themes_archive_browser_check.py`, con ficción temporal y sin llamadas IA.
