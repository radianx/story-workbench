# Asistente de voz online · 0.5.0

Opción explícita en el chat: Asistente de voz → activar → elegir proveedor → ingresar clave en el diálogo → aceptar condiciones → Conversar por voz. Inicialmente desactivada; no conecta al abrir la app, guardar una clave o fallar el dictado. El dictado Vosk y la lectura del sistema siguen siendo locales.

| Voz | Credencial | Relación con la suscripción |
| --- | --- | --- |
| OpenAI `gpt-realtime` | Clave de la plataforma API | Facturación API separada de ChatGPT. El Codex incluido no permite usar la sesión ChatGPT para este transporte. |
| Google `gemini-3.1-flash-live-preview` | Clave Gemini de Google AI Studio | AI Plus no determina la cuota de la API; depende del proyecto de esa clave y su nivel de facturación. No requiere clave OpenAI para conversar o navegar. |

Google documenta un nivel gratuito para el modelo Live elegido, sujeto a cuota/disponibilidad, y uso de contenido para mejorar productos en ese nivel. El nivel pagado tiene otras condiciones. La app no verifica saldo, plan ni elegibilidad, no activa facturación y no cambia de proveedor/modelo en silencio. Revisar el proyecto de la clave en AI Studio antes de enviar material privado. [Precios Gemini](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.1-flash-live-preview), [facturación por proyecto y clave](https://ai.google.dev/gemini-api/docs/billing), [beneficios AI Plus](https://support.google.com/googleone/answer/16882689?hl=en).

## Qué puede hacer

Conversación de audio con interrupciones, pausa de micrófono, cierre visible en la cabecera y subtítulos de la respuesta. Si se habilitan acciones: consultar contexto, navegar a paneles, abrir documentos, cambiar tema, preparar un mensaje, preparar un criterio pendiente o iniciar una tarea de entrevista/revisión/redacción/traducción con Codex. Esta última usa la cuota de la cuenta ChatGPT conectada y conserva el resultado en el historial. Se puede pedir a la voz consultar el resultado cuando termine.

No aprueba propuestas ni traducciones, no registra decisiones, no guarda ni borra documentos y no ejecuta comandos. Respeta cambios pendientes del editor y mensajes sin enviar. Las funciones recibidas se validan contra una lista cerrada; las llamadas duplicadas no repiten acciones. La cancelación impide nuevas acciones que todavía no se enviaron, pero no revierte tareas ya iniciadas: pueden detenerse desde Codex.

La conversación oral y sus subtítulos son temporales, no un historial editorial completo. Para conservar trabajo, pedir una tarea de Codex o preparar una decisión y registrarla manualmente. No hay migración automática del diálogo oral al canon.

## Datos y conexión

Claves permanentes únicamente en memoria del servidor local; el campo se vacía al guardar/cerrar. Nunca se incluyen en proyectos, exportaciones o almacenamiento del navegador. Olvidar clave afecta al proveedor seleccionado. Cambiar proveedor requiere renovar el consentimiento y termina la conexión; no reutiliza la clave del otro proveedor.

Audio, título/idea, nombres de biblioteca, fuentes seleccionadas, decisiones y hasta ocho turnos compatibles con las fuentes/versiones actuales se envían al proveedor elegido. El contexto inicial tiene un límite de 60.000 caracteres serializados; se rechaza exceso. Retirar/cambiar fuentes o cambiar proyecto termina la conexión. No se envía cámara ni imágenes de maqueta.

OpenAI usa WebRTC nativo; el servidor negocia SDP con la clave y el audio viaja directamente. Gemini usa WebSocket con token temporal de un uso solicitado por el servidor, válido como máximo diez minutos y con sesenta segundos para iniciar. La clave permanente no aparece en la URL del WebSocket. Entrada PCM mono 16 kHz mediante el capturador local existente, salida PCM 24 kHz y reproducción con Web Audio. El renderer permite únicamente el endpoint WebSocket oficial de Gemini; mantiene aislamiento, sin Node ni IPC genérico.

Cada conexión se cierra a los diez minutos sin reconexión automática. Ese tiempo no es un presupuesto de gasto. Pausar el micrófono conserva conexión y recepción de voz; Terminar libera micrófono, audio y transporte. No se comprueba ni configura el presupuesto del proveedor desde la app.

## Evidencia y límites

El 2026-09-09 se probó Codex 0.153.4 con autenticación ChatGPT, `features.realtime_conversation=true` solo para ese proceso y un proyecto temporal vacío. `thread/realtime/start` terminó con `realtime conversation requires API key auth`. No se reutilizó el token ChatGPT ni se modificó configuración global. Es un resultado de esta integración/versión, no una predicción sobre futuras prestaciones del plan. [Autenticación Codex](https://learn.chatgpt.com/es-419/docs/auth), [OpenAI Realtime con WebRTC](https://developers.openai.com/api/docs/guides/realtime-webrtc).

Pruebas ejecutables sin cargos: `tests/test_realtime.py` (consentimiento, claves, contexto, peticiones y errores HTTP), `tests/realtime_browser_check.py` (WebRTC simulado y acciones), `tests/gemini_browser_check.py` (WebSocket simulado, PCM real de micrófono virtual, reproducción, interrupción, funciones y cierre). Los transportes externos usan dobles; no hubo claves reales disponibles y la conversación con cada proveedor real queda sin validar. No se presenta esta prueba simulada como aceptación de la API ni se promete acceso de una cuenta concreta.

Protocolo Gemini consultado el 2026-09-09: [inicio WebSocket](https://ai.google.dev/gemini-api/docs/live-api/get-started-websocket), [tokens temporales](https://ai.google.dev/gemini-api/docs/live-api/ephemeral-tokens), [referencia de mensajes y configuración](https://ai.google.dev/api/live). Se usa el contrato JSON de referencia (`generationConfig`, `bidiGenerateContentSetup`), no los nombres de opciones del SDK. Ambos modelos/transportes deben volver a comprobarse si el proveedor cambia su API.
