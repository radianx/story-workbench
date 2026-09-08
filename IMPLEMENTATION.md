# Implementación y comprobación

## Corte 0: validar el motor antes del editor

Crear una prueba mínima con Codex App Server por stdio, usando el protocolo documentado y comprobando la versión instalada. Registrar solo diagnóstico no sensible.

Criterios: inicialización, estado de cuenta ChatGPT sin exponer tokens, crear sesión en carpeta ficticia, respuesta en streaming, detener tarea, cerrar y reanudar sesión; mostrar errores de autenticación y límites sin recurrir a una clave API. Comprobar carga de build-novel y permisos con un documento ficticio, no con los originales. Estado: pendiente.

## Arquitectura inicial propuesta

Interfaz en navegador y un servicio local que inicia Codex App Server. Elegir dependencias cuando se implemente este corte, no generar ahora un monorepo vacío. Archivos Markdown como fuente de verdad; metadatos pequeños cuando sean necesarios. Git para historial local, no como sustituto de copias de seguridad.

El servicio escucha solo en loopback; valida origen y autentica peticiones del navegador. Restringe rutas al proyecto elegido, resuelve enlaces simbólicos, impide traversal y no expone tokens de Codex. No permitir ejecución arbitraria por un endpoint genérico. Las aprobaciones de herramientas y las aprobaciones editoriales son controles diferentes y ambos deben ser visibles.

Las modificaciones propuestas viven separadas del manuscrito aprobado. Antes de aceptar, comprobar que el archivo base no cambió; guardar atómicamente, conservar una versión recuperable y fallar sin sobrescribir si hay conflicto. No implementar aceptación como escritura directa del agente en los originales.

## Corpus privado y adaptación

Inspección inicial de documentos y estructura, no auditoría de los cuatro manuscritos:

- Plan humano: colección con manuscritos, biblia, estilo, imágenes aprobadas y producción editorial.
- Lattice: tres directorios books con planificación, canon, manuscritos y producción; traducciones en translations/en-US con manifiesto de fuentes. El manifiesto documenta sincronizaciones, pero eso no se verificó capítulo por capítulo.

Importación por selección y mapeo de archivos; no imponer migraciones destructivas. Primeras pruebas en copias privadas externas al repositorio de software. Conservar hashes de origen para demostrar que los originales no se alteraron. No rastrear manuscritos, credenciales, conversaciones ni rutas personales en el repositorio público.

## Pruebas de aceptación pendientes

| Caso | Resultado exigido |
| --- | --- |
| Reinicio de sesión | Recupera decisiones aprobadas y pendientes con fuentes; no presenta propuestas rechazadas como canon. |
| Revisión mínima | Autor verifica voz conservada; ningún cambio fuera del alcance aceptado. |
| Cambio de canon entre libros | Lista impactos con pasajes y motivos; mide omisiones y falsos positivos contra casos anotados. |
| Traducción desactualizada | Detecta cambio de fuente y propone revisión; no reemplaza la traducción sin aprobación. |
| Archivos editados externamente | Conflicto visible, sin pérdida silenciosa de cambios. |
| Cancelación o desconexión | Manuscrito aprobado intacto y tarea recuperable o claramente incompleta. |
| Cambio de proyecto | No recupera material del universo anterior. |
| Rutas hostiles y enlaces | No lee ni escribe fuera del proyecto autorizado. |
| Sin cuenta o sin cuota | Error comprensible, sin cargos API alternativos. |
| Teclado y modo foco | Acciones accesibles, foco recuperable, lectura legible. |

Progresión: documento ficticio → un cuento en copia → colección → cada volumen de Lattice → cambios entre volúmenes y traducciones → piloto con otro autor. Registrar resultados reales; «exhaustivo» no se deduce de tener cuatro libros ni de pasar una única prueba.
