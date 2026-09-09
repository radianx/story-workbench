# Traducción y preparación de rol · 0.5.0

El wizard y Objetivo en la biblioteca distinguen historia/libro, traducción literaria y mundo para rol. Los proyectos existentes conservan Historia/libro. Cambiar objetivo conserva documentos e historial y abre otra entrevista. No se modifican libros vecinos ni se redistribuye build-novel.

## Traducción literaria

1. La entrevista aclara lectores, idiomas/variantes, voz e intención. Importar una copia del original y abrir Traducción.
2. Guardar unidad, idiomas, intención y glosario. La unidad admite hasta 12.000 caracteres; otras fuentes seleccionadas sirven como contexto. No hay división automática del original.
3. Marcar el original como fuente y traducir. Si falta criterio relevante, se presenta una pregunta, cita literal y dos o tres alternativas con efectos; no hay borrador aprobable en ese turno.
4. Registrar el criterio elegido o escrito por el autor. Continuar consume otro turno de Codex. No se salta una consulta pendiente del mismo original y encargo.
5. Comparar original congelado y borrador editable; aprobar crea una copia separada, no seleccionada para IA. Repetir abre la misma copia. Cambios de original, encargo o criterios entre generación y aprobación bloquean la aceptación desactualizada.
6. Si cambian el original, encargo o traducción guardada, la copia requiere revisión. Comparar ambas versiones actuales y aprobar de nuevo. Historial permite recuperar cambios del documento.
7. Exportar Markdown/DOCX incluye la última traducción revisada de cada unidad para el idioma del encargo, en orden de fuentes. Una unidad sin traducción no entra: no afirma que el libro esté completo. El ZIP conserva encargo, vínculos y criterios.

El esquema y comprobaciones exigen cita real y separan consulta de borrador. No prueban fidelidad semántica ni que la IA detecte todos los matices. Las traducciones de grandes libros, la alineación por oración y la sincronización automática entre idiomas quedan fuera del MVP.

## Mundo para rol · extra

Entrevista sobre experiencia, tono, límites, sistema/edición o reglas propias, escala y lugar inicial. El botón de inicio prepara una petición de mundo, tres PNJ, dos facciones, reglas y ganchos abiertos. El autor la revisa antes de enviar. Guardar material de rol crea un documento de planificación provisional sin seleccionarlo para IA.

Seis fichas propias: mundo, PNJ, facción, lugar, reglas y ganchos. Se reutilizan biblioteca, criterios, diagnóstico, propuestas y ZIP como dossier. No hay manuales de D&D incluidos, motor de reglas, dados, combate, VTT ni ejecución de partidas. Los secretos del director son secciones de texto, no permisos de acceso.

## Comprobación

`tests/test_modes.py` verifica consultas, criterios, copias, conflictos, revisión, exportación, compatibilidad y rutas HTTP. `tests/modes_browser_check.py` recorre wizard, encargo, alternativas, criterio recuperable, aprobación, revisión por versión, exportación y rol con respuestas simuladas y ficción temporal.

El 2026-09-09, `tests/live_modes_check.py` pasó tres turnos reales con la sesión ChatGPT: consulta de la intención de «Te quiero», borrador después de aclarar afecto amistoso y entrevista de rol con una sola pregunta. No se modificaron manuscritos originales; no se hicieron llamadas a APIs de pago. Esto valida un caso mínimo, no calidad editorial general.
