# Reportar una vulnerabilidad

No publiques claves, sesiones, manuscritos ni instrucciones de explotación en un issue público.

En el repositorio de GitHub, usá **Security → Report a vulnerability** para enviar un informe privado al mantenedor. Este canal requiere activación por el propietario; la preparación local del repositorio no lo habilita. Si no aparece, solicitá en un issue únicamente un canal privado de contacto, sin detalles del fallo ni datos sensibles.

Incluí versión o commit, sistema operativo, pasos mínimos con material ficticio, resultado e impacto. Los tokens deben reemplazarse por valores de ejemplo. No hace falta demostrar el problema con archivos de otra persona ni acceder a un servicio ajeno.

El proyecto está en fase MVP. No hay un plazo de respuesta garantizado ni ramas antiguas con mantenimiento de seguridad comprometido. Indicá si el problema también se reproduce en la revisión más reciente.

La app escucha en loopback y almacena los proyectos localmente, pero la inferencia online envía el contexto seleccionado al proveedor autorizado. No está diseñada para exponerse como servidor público ni aislar procesos maliciosos que se ejecuten con el mismo usuario. Los controles existentes se describen en [README.md](README.md#datos-y-límites).
