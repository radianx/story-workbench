# Asistente de voz y lectura online

Configuración (tuerca) → Asistente de voz → activar → elegir proveedor → ingresar clave → aceptar condiciones → Guardar. El micrófono junto a Enviar alterna escucha continua/pausa. Mantener Espacio escucha hasta soltar sin cortar la respuesta; con texto escrito, Espacio conserva su función normal. Inicialmente desactivada; no conecta al abrir la app, guardar una clave o fallar el dictado. El dictado Vosk sigue siendo local. La lectura puede usar el proveedor online autorizado y vuelve al TTS local si no está disponible.

| Voz | Credencial | Relación con la suscripción |
| --- | --- | --- |
| OpenAI `gpt-realtime` | Clave de la plataforma API | Facturación API separada de ChatGPT. El Codex incluido no permite usar la sesión ChatGPT para este transporte. |
| Google `gemini-3.1-flash-live-preview` | Clave Gemini de Google AI Studio | AI Plus no determina la cuota de la API; depende del proyecto de esa clave y su nivel de facturación. No requiere clave OpenAI para conversar o navegar. |

Google documenta un nivel gratuito para el modelo Live elegido, sujeto a cuota/disponibilidad, y uso de contenido para mejorar productos en ese nivel. El nivel pagado tiene otras condiciones. La app no verifica saldo, plan ni elegibilidad, no activa facturación y no cambia de proveedor/modelo en silencio. Revisar el proyecto de la clave en AI Studio antes de enviar material privado. [Precios Gemini](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.1-flash-live-preview), [facturación por proyecto y clave](https://ai.google.dev/gemini-api/docs/billing), [beneficios AI Plus](https://support.google.com/googleone/answer/16882689?hl=en).

## Qué puede hacer

Conversación de audio con interrupciones, pausa de micrófono, cierre visible en la cabecera y subtítulos de la respuesta. Si se habilitan acciones: consultar contexto, navegar a paneles, abrir documentos, cambiar tema, preparar un mensaje, preparar un criterio pendiente o iniciar una tarea de entrevista/revisión/redacción/traducción con Codex. Esta última usa la cuota de la cuenta ChatGPT conectada y conserva el resultado en el historial. Se puede pedir a la voz consultar el resultado cuando termine.

No aprueba propuestas ni traducciones, no registra decisiones, no guarda ni borra documentos y no ejecuta comandos. Respeta cambios pendientes del editor y mensajes sin enviar. Las funciones recibidas se validan contra una lista cerrada; las llamadas duplicadas no repiten acciones. La cancelación impide nuevas acciones que todavía no se enviaron, pero no revierte tareas ya iniciadas: pueden detenerse desde Codex.

La conversación oral y sus subtítulos son temporales, no un historial editorial completo. Para conservar trabajo, pedir una tarea de Codex o preparar una decisión y registrarla manualmente. No hay migración automática del diálogo oral al canon.

## Lectura de respuestas

Configuración → Voz y lectura → **Leer respuestas con** permite usar el proveedor de voz autorizado (predeterminado) o elegir **Siempre voz local**. La preferencia se recuerda en el equipo; recordar una clave no reactiva el consentimiento. Escuchar y la lectura automática de respuestas nuevas comparten este comportamiento.

La casilla **Leer respuestas**, junto al micrófono del chat, activa la lectura de las nuevas respuestas editoriales. Desmarcarla detiene la lectura actual. No reproduce el historial al activarla y se desactiva al cambiar de proyecto. También funciona cuando termina una tarea iniciada por voz: cierra la conversación oral para narrar sin eco; pulsá el micrófono para retomarla.

Con voz online habilitada, clave configurada y consentimiento de esta ejecución, intenta `gpt-realtime` o Gemini Live. Sin esos requisitos usa directamente TTS local. Si falla la preparación, el transporte o la respuesta de audio, cierra la conexión online y retoma el fragmento actual con voz local; informa el respaldo y no intenta otro proveedor API. Detener cancela sin activar el respaldo ni abrir conexiones tardías. Una interrupción a mitad del fragmento puede repetir sus primeras palabras al pasar a local.

La lectura crea una conexión independiente **sin abrir el micrófono, herramientas ni contexto del proyecto**: solo envía los fragmentos de texto elegidos. Escuchar durante una conversación oral la cierra para evitar audios superpuestos. El texto se solicita sin resumir ni reescribir; la pronunciación, entonación y fidelidad de un modelo generativo requieren criterio humano. No modifica el texto en pantalla ni el canon.

OpenAI usa un token temporal de 60 segundos emitido por el backend y WebSocket con audio PCM; puede funcionar aunque el entorno no exponga WebRTC. Esto es independiente del transporte WebRTC que todavía usa la conversación oral. Gemini reutiliza los tokens temporales existentes con configuración de lectura y entrada `realtimeInput.text`. La lectura tiene un máximo de diez minutos por conexión y usa el respaldo local para el resto si lo supera; no es un presupuesto de gasto. [Tokens Realtime](https://developers.openai.com/api/reference/resources/realtime/subresources/client_secrets/methods/create), [WebSocket en navegador](https://developers.openai.com/api/docs/guides/realtime-websocket), [texto en Gemini Live](https://ai.google.dev/gemini-api/docs/live-api/capabilities).

Comprobaciones sin servicios externos: `tests/test_realtime.py` verifica consentimiento, tokens sin herramientas y errores sin secretos; `tests/reading_browser_check.py` verifica ambos proveedores simulados, fragmentos completos, ausencia de micrófono, respaldo, cancelación y preferencia persistida. Las pruebas de transporte simulado no equivalen a una lectura real con el proveedor.

## Datos y conexión

Claves permanentes en memoria por defecto; en Tauri, Recordar las guarda en el llavero nativo fuera de los proyectos (Credential Manager en Windows; Secret Service en Linux), mediante keyring. Sin un almacén seguro disponible el guardado se deshabilita; no hay respaldo en texto plano. El arranque restaura la clave, pero no el consentimiento ni la conexión. Olvidar elimina memoria y entrada del llavero; el campo se vacía al guardar/cerrar. Nunca se incluyen en proyectos, exportaciones o almacenamiento del navegador. Olvidar clave afecta al proveedor seleccionado. Cambiar proveedor requiere renovar el consentimiento y termina la conexión; no reutiliza la clave del otro proveedor.

Audio, título/idea, nombres de biblioteca, fuentes seleccionadas, decisiones y hasta ocho turnos compatibles con las fuentes/versiones actuales se envían al proveedor elegido. El contexto inicial tiene un límite de 60.000 caracteres serializados; se rechaza exceso. Retirar/cambiar fuentes o cambiar proyecto termina la conexión. No se envía cámara ni imágenes de maqueta.

OpenAI usa WebRTC nativo; el servidor negocia SDP con la clave y el audio viaja directamente. Gemini usa WebSocket con token temporal de un uso solicitado por el servidor, válido como máximo diez minutos y con sesenta segundos para iniciar. La clave permanente no aparece en la URL del WebSocket. Entrada PCM mono 16 kHz mediante el capturador local existente, salida PCM 24 kHz y reproducción con Web Audio. El renderer permite los endpoints WebSocket oficiales de Gemini y OpenAI Realtime; mantiene aislamiento, sin Node ni IPC genérico.

Cada conexión se cierra a los diez minutos sin reconexión automática. Ese tiempo no es un presupuesto de gasto. Pausar el micrófono conserva conexión y recepción de voz; Terminar libera micrófono, audio y transporte. No se comprueba ni configura el presupuesto del proveedor desde la app.

## Evidencia y límites

El 2026-09-09 se probó Codex 0.153.4 con autenticación ChatGPT, `features.realtime_conversation=true` solo para ese proceso y un proyecto temporal vacío. `thread/realtime/start` terminó con `realtime conversation requires API key auth`. No se reutilizó el token ChatGPT ni se modificó configuración global. Es un resultado de esta integración/versión, no una predicción sobre futuras prestaciones del plan. [Autenticación Codex](https://learn.chatgpt.com/es-419/docs/auth), [OpenAI Realtime con WebRTC](https://developers.openai.com/api/docs/guides/realtime-webrtc).

Pruebas ejecutables sin cargos: `tests/test_realtime.py` (consentimiento, claves, contexto, peticiones y errores HTTP), `tests/realtime_browser_check.py` (WebRTC simulado y acciones), `tests/gemini_browser_check.py` (WebSocket simulado, PCM real de micrófono virtual, reproducción, interrupción, funciones y cierre). Los recorridos ordinarios usan dobles. La prueba optativa `tests/live_gemini_check.py` recibe una clave por stdin sin eco y usa audio sintético temporal; OpenAI real continúa sin validar. La respuesta del modelo y su interpretación de una orden oral no son deterministas.

Protocolo Gemini consultado el 2026-09-09: [inicio WebSocket](https://ai.google.dev/gemini-api/docs/live-api/get-started-websocket), [tokens temporales](https://ai.google.dev/gemini-api/docs/live-api/ephemeral-tokens), [referencia de mensajes y configuración](https://ai.google.dev/api/live). Se usa el contrato JSON de referencia (`generationConfig`, `bidiGenerateContentSetup`), no los nombres de opciones del SDK. Ambos modelos/transportes deben volver a comprobarse si el proveedor cambia su API.

Claves Gemini: se admiten las nuevas auth keys `AQ.` y las claves `AIza`, con validación de longitud y caracteres antes de delegar autenticación al proveedor; se informa si se eligió OpenAI por error. [Formato oficial](https://ai.google.dev/gemini-api/docs/api-key). [Almacenes nativos de keyring](https://docs.rs/keyring/3.6.3/keyring/).
