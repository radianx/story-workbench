#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
use std::{collections::HashMap, io::Read, sync::{Arc, Mutex, Condvar, atomic::{AtomicBool, Ordering}}, time::Duration};
mod vault;
use vault::Vault;
use serde::Deserialize;
use tauri::{Manager, WebviewUrl, WebviewWindowBuilder, webview::NewWindowResponse, http::{Request, Response}};
use tauri_plugin_shell::{ShellExt, process::{CommandChild, CommandEvent}};
use tauri_plugin_opener::OpenerExt;
use tauri_plugin_dialog::DialogExt;
use std::io::Write;

#[derive(Clone, Deserialize)]
struct Backend { origin: String, token: String }
struct Runtime { backend: Mutex<Option<Backend>>, child: Mutex<Option<CommandChild>>, vault: Mutex<Option<Vault>>, closing: AtomicBool, exited: (Mutex<bool>, Condvar) }

fn local_url(url: &tauri::Url) -> bool {
    if !url.username().is_empty() || url.password().is_some() || url.port().is_some() {return false}
    (url.scheme()=="workbench" && url.host_str()==Some("app")) ||
    (url.scheme()=="https" && url.host_str()==Some("workbench.app"))
}
fn external_url(url: &tauri::Url) -> bool {
    matches!(url.scheme(),"http"|"https") && url.host_str().is_some() &&
    url.username().is_empty() && url.password().is_none()
}
fn valid_backend(backend: &Backend) -> bool {
    let Ok(url)=tauri::Url::parse(&backend.origin) else { return false };
    url.scheme()=="http" && url.host_str()==Some("127.0.0.1") && url.port().is_some() &&
    url.username().is_empty() && url.password().is_none() && url.path()=="/" &&
    url.query().is_none() && url.fragment().is_none() && backend.token.len()==43 &&
    backend.token.bytes().all(|c|c.is_ascii_alphanumeric() || c==b'_' || c==b'-')
}
fn error_response(status: u16, text: &str) -> Response<Vec<u8>> {
    Response::builder().status(status).header("Content-Type","application/json")
        .header("Cache-Control","no-store").body(serde_json::json!({"error":text}).to_string().into_bytes()).unwrap()
}
fn proxy(backend: &Backend, vault: &Mutex<Option<Vault>>, request: Request<Vec<u8>>) -> Response<Vec<u8>> {
    let Ok(url)=tauri::Url::parse(&request.uri().to_string()) else { return error_response(403,"Origen inválido.") };
    if !local_url(&url) || !["GET","POST"].contains(&request.method().as_str()) || request.body().len()>request_limit(url.path()) {
        return error_response(403,"Solicitud no permitida.")
    }
    let storage=["/api/voice-storage","/api/engine-storage"].contains(&url.path());
    if storage || (request.method()=="POST" && ["/api/realtime/key","/api/engine/key"].contains(&url.path())) {
        if request.headers().get("Authorization").and_then(|v|v.to_str().ok())!=Some(&format!("Bearer {}",backend.token)) {
            return error_response(401,"Acceso no autorizado.")
        }
        // Serializa cambio en memoria + llavero para evitar carreras entre Guardar y Olvidar.
        let mut guard=vault.lock().unwrap();let Some(vault)=guard.as_mut() else {return error_response(503,"Iniciando llavero.")};
        let engine=url.path().starts_with("/api/engine");
        if request.method()=="GET" {return json_response(vault.status(engine))}
        if request.headers().get("Content-Type").and_then(|v|v.to_str().ok()).map(|v|v.split(';').next().unwrap())!=Some("application/json") {return error_response(415,"Se requiere JSON.")}
        if request.body().len()>10000 {return error_response(413,"Solicitud demasiado grande.")}
        let Ok(body)=serde_json::from_slice::<serde_json::Value>(request.body()) else {return error_response(400,"Solicitud inválida.")};
        if !body.is_object() || body.get("remember").is_some_and(|v|!v.is_boolean()) || body.get("provider").is_some_and(|v|!v.is_string()) {return error_response(400,"Solicitud inválida.")}
        let provider=body.get("provider").and_then(|v|v.as_str()).unwrap_or("openai");
        let account=match Vault::account(engine,provider) {Ok(value)=>value,Err(error)=>return error_response(400,error)};
        if storage {
            let Some(remember)=body.get("remember").and_then(|v|v.as_bool()) else {return error_response(400,"Preferencia inválida.")};
            return match vault.save(&account,remember) {Ok(())=>json_response(vault.status(engine)),Err(error)=>error_response(409,error)}
        }
        let Some(key)=body.get("key").and_then(|v|v.as_str()) else {return error_response(400,"Clave inválida.")};
        let key=key.to_owned();let remember=!key.is_empty() && body.get("remember").and_then(|v|v.as_bool())==Some(true);
        if remember && vault.load(&account).is_err() {return error_response(409,"No hay llavero disponible. Elegí uso solo en memoria.")}
        let response=forward(backend,request);
        if !response.status().is_success() {return response}
        vault.keys.insert(account.clone(),key.clone());
        if let Err(error)=vault.save(&account,remember) {return error_response(409,error)}
        return response
    }
    forward(backend,request)
}
fn json_response(body: serde_json::Value) -> Response<Vec<u8>> {
    Response::builder().header("Content-Type","application/json").header("Cache-Control","no-store").body(body.to_string().into_bytes()).unwrap()
}
fn forward(backend: &Backend, request: Request<Vec<u8>>) -> Response<Vec<u8>> {
    let path=request.uri().path_and_query().map(|p|p.as_str()).unwrap_or("/").to_owned();
    // El navegador no obtiene un proxy de red: destino único, surgido del sidecar validado.
    let result=(|| -> Result<Response<Vec<u8>>,Box<dyn std::error::Error>> {
        let client=reqwest::blocking::Client::builder().no_proxy().redirect(reqwest::redirect::Policy::none()).timeout(Duration::from_secs(60)).build()?;
        let mut outbound=client.request(request.method().clone(),format!("{}{}",backend.origin,path)).header("Origin",&backend.origin);
        for name in ["Authorization","Content-Type"] {
            if let Some(value)=request.headers().get(name) {outbound=outbound.header(name,value);}
        }
        let response=outbound.body(request.into_body()).send()?;
        let mut builder=Response::builder().status(response.status());
        for (name,value) in response.headers() {
            if !["content-length","transfer-encoding","connection"].contains(&name.as_str()) {builder=builder.header(name,value);}
        }
        let mut bytes=Vec::new();response.take(32_000_001).read_to_end(&mut bytes)?;
        if bytes.len()>32_000_000 {return Ok(error_response(413,"Respuesta local demasiado grande."))}
        Ok(builder.body(bytes)?)
    })();
    result.unwrap_or_else(|_|error_response(502,"No se pudo completar la petición al servicio local."))
}
fn request_limit(path: &str) -> usize {
    if ["/api/import/file", "/api/projects", "/api/document/import"].contains(&path) {40_000_000} else {2_000_000}
}
fn export_name(url: &tauri::Url) -> Option<String> {
    let name=url.query_pairs().find(|(key,_)|key=="name")?.1.into_owned();
    if name.is_empty() || name.len()>240 || name.chars().any(|c|c.is_control() || "/\\:<>\"|?*".contains(c)) ||
        !["md","docx","pdf","png","jpg","zip","json"].iter().any(|ext|name.ends_with(&format!(".{ext}"))) {return None}
    Some(name)
}
fn save_export(path: &std::path::Path, bytes: &[u8]) -> std::io::Result<()> {
    let mut file=tempfile::NamedTempFile::new_in(path.parent().ok_or(std::io::ErrorKind::InvalidInput)?)?;
    file.write_all(bytes)?;file.as_file().sync_all()?;
    file.persist(path).map_err(|error|error.error)?;Ok(())
}
fn desktop_request(app: &tauri::AppHandle, backend: &Backend, request: &Request<Vec<u8>>) -> Response<Vec<u8>> {
    let Ok(url)=tauri::Url::parse(&request.uri().to_string()) else {return error_response(403,"Origen inválido.")};
    if !local_url(&url) || request.method()!="POST" {return error_response(403,"Solicitud no permitida.")}
    if request.headers().get("Authorization").and_then(|v|v.to_str().ok())!=Some(&format!("Bearer {}",backend.token)) {return error_response(401,"Acceso no autorizado.")}
    if request.body().len()>32_000_000 {return error_response(413,"Archivo demasiado grande.")}
    if url.path()=="/api/desktop/close" {app.exit(0);return json_response(serde_json::json!({"ok":true}))}
    if url.path()=="/api/desktop/folder" {
        let Some(path)=app.dialog().file().set_title("Elegir carpeta").blocking_pick_folder() else {return json_response(serde_json::json!({"path":null}))};
        let Ok(path)=path.into_path() else {return error_response(400,"Carpeta no disponible.")};
        return json_response(serde_json::json!({"path":path.to_string_lossy()}))
    }
    if url.path()!="/api/desktop/save" {return error_response(404,"Acción no disponible.")}
    let Some(name)=export_name(&url) else {return error_response(400,"Nombre de exportación inválido.")};
    let Some(path)=app.dialog().file().set_title("Guardar exportación").set_file_name(&name).blocking_save_file() else {return json_response(serde_json::json!({"saved":false}))};
    let Ok(path)=path.into_path() else {return error_response(400,"Destino no disponible.")};
    match save_export(&path,request.body()) {
        Ok(())=>json_response(serde_json::json!({"saved":true})),
        Err(_)=>error_response(500,"No se pudo guardar la exportación. Elegí otro destino.")
    }
}
fn main() {
    if std::env::var("STORY_TAURI_CLEANUP").as_deref()==Ok("1") {
        let data=std::path::PathBuf::from(std::env::var_os("STORY_TEST_DATA").expect("Perfil de prueba requerido"));
        let data=std::fs::canonicalize(data).expect("Perfil de prueba inexistente");
        assert!(data.starts_with(std::env::temp_dir()) && data.file_name().unwrap().to_string_lossy().starts_with("sw-tauri-test-"));
        let vault=Vault::new(&data);
        for engine in [false,true] {for provider in if engine {vault::ENGINE} else {vault::VOICE} {
            assert!(vault.save(&Vault::account(engine,provider).unwrap(),false).is_ok(),"No se pudo limpiar el llavero de prueba");
        }}
        return
    }
    let runtime=Arc::new(Runtime {backend:Mutex::new(None),child:Mutex::new(None),vault:Mutex::new(None),closing:AtomicBool::new(false),exited:(Mutex::new(false),Condvar::new())});
    let bridge=runtime.clone();let startup=runtime.clone();let shutdown=runtime.clone();
    let smoke=std::env::var("STORY_TAURI_SMOKE").as_deref()==Ok("1");
    let app=tauri::Builder::default()
        .plugin(tauri_plugin_shell::init()).plugin(tauri_plugin_opener::init()).plugin(tauri_plugin_dialog::init())
        .register_asynchronous_uri_scheme_protocol("workbench", move |ctx,request,responder| {
            let runtime=bridge.clone();let backend=bridge.backend.lock().unwrap().clone();let handle=ctx.app_handle().clone();
            std::thread::spawn(move || {
                let Some(backend)=backend else {responder.respond(error_response(503,"Iniciando servicio local."));return};
                if smoke && request.uri().path()=="/__capabilities" && request.headers().get("Authorization").and_then(|v|v.to_str().ok())==Some(&format!("Bearer {}",backend.token)) {
                    let rtc=serde_json::from_slice::<serde_json::Value>(request.body()).ok().and_then(|v|v.get("webrtc").and_then(|b|b.as_bool()))==Some(true);
                    println!("WebRTC local: {}",if rtc {"oferta verificada"}else{"NO DISPONIBLE en este WebKit"});responder.respond(Response::new(b"ok".to_vec()));return;
                }
                if smoke && request.uri().path()=="/__smoke" && request.headers().get("Authorization").and_then(|v|v.to_str().ok())==Some(&format!("Bearer {}",backend.token)) {
                    let success=request.body()==b"ok";responder.respond(Response::new(b"ok".to_vec()));
                    println!("Tauri smoke: {}",if success {"OK"} else {"FAILED"});
                    if !success {println!("Stage: {}",String::from_utf8_lossy(request.body()).chars().filter(|c|c.is_ascii_alphanumeric()||*c=='-').take(40).collect::<String>());}handle.exit(if success {0}else{2});return;
                }
                if request.uri().path().starts_with("/api/desktop/") {responder.respond(desktop_request(&handle,&backend,&request));}
                else {responder.respond(proxy(&backend,&runtime.vault,request));}
            });
        })
        .setup(move |app| {
            let data=std::env::var_os("STORY_TEST_DATA").map(std::path::PathBuf::from).unwrap_or(app.path().config_dir()?.join("story-workbench"));
            std::fs::create_dir_all(data.join("codex"))?;
            let resources=app.path().resource_dir()?.join("runtime");
            let env:HashMap<String,String>=std::env::vars().filter(|(key,_)|!["OPENAI_","AZURE_OPENAI_","CODEX_API_","CODEX_THREAD_"].iter().any(|prefix|key.starts_with(prefix))).collect();
            let (mut rx,child)=app.shell().sidecar("story-server")?.env_clear().envs(env)
                .env("STORY_DESKTOP","1").env("CODEX_HOME",data.join("codex"))
                .env("STORY_CODEX_BINARY",resources.join(if cfg!(windows){"codex/bin/codex.exe"}else{"codex/bin/codex"}))
                .env("STORY_VOICE_DIR",resources.join("voice")).env("STORY_SERVER_RUNTIME",&resources)
                .args(["--port","0","--data-dir",data.join("projects").to_str().ok_or("Ruta inválida")?]).spawn()?;
            *startup.child.lock().unwrap()=Some(child);
            let backend=tauri::async_runtime::block_on(async {
                tokio::time::timeout(Duration::from_secs(30),async {
                    while let Some(event)=rx.recv().await {
                        if let CommandEvent::Stdout(line)=event {
                            if let Ok(backend)=serde_json::from_slice::<Backend>(&line) {
                                if valid_backend(&backend) {return Ok(backend)}
                            }
                        }
                    }
                    Err("No arrancó el servicio local")
                }).await.map_err(|_|"El servicio local no respondió a tiempo")?
            })?;
            let mut vault=Vault::new(&std::fs::canonicalize(&data)?);
            for engine in [false,true] {for provider in if engine {vault::ENGINE} else {vault::VOICE} {
                let account=Vault::account(engine,provider).unwrap();
                if let Ok(Some(key))=vault.load(&account) {
                    let path=if engine {"/api/engine/key"} else {"/api/realtime/key"};
                    let request=Request::builder().method("POST").uri(path).header("Authorization",format!("Bearer {}",backend.token)).header("Content-Type","application/json")
                        .body(serde_json::json!({"provider":provider,"key":key}).to_string().into_bytes())?;
                    if forward(&backend,request).status().is_success() {vault.keys.insert(account,key);}
                }
            }}
            *startup.vault.lock().unwrap()=Some(vault);
            *startup.backend.lock().unwrap()=Some(backend.clone());
            let handle=app.handle().clone();let watcher=startup.clone();
            tauri::async_runtime::spawn(async move {
                while let Some(event)=rx.recv().await {if matches!(event,CommandEvent::Terminated(_)){
                    *watcher.exited.0.lock().unwrap()=true;watcher.exited.1.notify_all();
                    if !watcher.closing.load(Ordering::SeqCst){handle.exit(1);}break;
                }}
            });
            let opener=app.handle().clone();
            let smoke_script=if smoke {include_str!("smoke.js").replace("__TOKEN__",&backend.token).replace("__FORMATS_ONLY__",if std::env::var("STORY_TAURI_FORMATS_ONLY").as_deref()==Ok("1"){"true"}else{"false"}).replace("__EXPORT_TEST__",if std::env::var("STORY_TAURI_EXPORT_TEST").as_deref()==Ok("1"){"true"}else{"false"})}else{String::new()};
            let ui_url=format!("workbench://app/#token={}",backend.token);
            // WebKit fija algunas capacidades al crear el documento: configurar antes de navegar.
            let initial=if cfg!(target_os="linux") {WebviewUrl::External("about:blank".parse()?)}else{WebviewUrl::CustomProtocol(ui_url.parse()?)};
            let window=WebviewWindowBuilder::new(app,"main",initial)
                .data_directory(data.join("webview")).title("Story Workbench").inner_size(1440.0,1000.0).min_inner_size(380.0,600.0)
                .initialization_script("window.storyDesktop = true;").initialization_script(&smoke_script).use_https_scheme(true).on_navigation(local_url)
                .on_new_window(move |url,_|{if external_url(&url){let _=opener.opener().open_url(url.as_str(),None::<&str>);}NewWindowResponse::Deny})
                .build()?;
            let close_window=window.clone();
            window.on_window_event(move |event| {if let tauri::WindowEvent::CloseRequested {api,..}=event {
                api.prevent_close();let _=close_window.eval("window.storyRequestClose?.()");
            }});
            #[cfg(target_os="linux")]
            window.with_webview(move |webview| {
                use webkit2gtk::{glib::prelude::*, WebViewExt, SettingsExt, PermissionRequestExt, UserMediaPermissionRequest, UserMediaPermissionRequestExt};
                let view=webview.inner();
                if let Some(settings)=view.settings() {
                    settings.set_enable_media_stream(true);
                    settings.set_enable_webrtc(true);
                    settings.set_enable_mock_capture_devices(smoke);
                    if smoke {settings.set_media_playback_requires_user_gesture(false);}
                }
                view.connect_permission_request(|view,request| {
                    let local=view.uri().and_then(|uri|tauri::Url::parse(&uri).ok()).is_some_and(|url|local_url(&url));
                    let audio=request.downcast_ref::<UserMediaPermissionRequest>().is_some_and(|media|media.is_for_audio_device()&&!media.is_for_video_device());
                    if local && audio {request.allow();}else{request.deny();}
                    true
                });
                view.load_uri(&ui_url);
            })?;
            if smoke {
                let timeout=app.handle().clone();std::thread::spawn(move || {std::thread::sleep(Duration::from_secs(60));timeout.exit(3);});
            }
            Ok(())
        }).build(tauri::generate_context!()).expect("No se pudo iniciar Story Workbench");
    app.run(move |_,event| {if matches!(event,tauri::RunEvent::Exit){
        shutdown.closing.store(true,Ordering::SeqCst);
        // Cerrar stdin deja terminar a Python y al lanzador onefile; kill dejaría un proceso huérfano.
        drop(shutdown.child.lock().unwrap().take());
        let _=shutdown.exited.1.wait_timeout_while(shutdown.exited.0.lock().unwrap(),Duration::from_secs(25),|done|!*done);
    }});
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn export_boundary_and_atomic_replace() {
        for name in ["../secret.md","a%2Fsecret.zip","a%5Cb.md","bad.exe","a%00.md"] {assert!(export_name(&format!("workbench://app/api/desktop/save?name={name}").parse().unwrap()).is_none());}
        assert_eq!(request_limit("/api/import/file"), 40_000_000);
        assert_eq!(request_limit("/api/engine/key"), 2_000_000);
        for name in ["libro.pdf", "imagen.png", "imagen.jpg"] {
            assert_eq!(export_name(&format!("workbench://app/api/desktop/save?name={name}").parse().unwrap()).as_deref(),Some(name));
        }
        assert_eq!(export_name(&"workbench://app/api/desktop/save?name=libro.docx".parse().unwrap()).as_deref(),Some("libro.docx"));
        assert_eq!(export_name(&"workbench://app/api/desktop/save?name=story-workbench-theme.json".parse().unwrap()).as_deref(),Some("story-workbench-theme.json"));
        let dir=tempfile::tempdir().unwrap();let path=dir.path().join("libro.md");
        save_export(&path,b"primero").unwrap();save_export(&path,b"segundo").unwrap();
        assert_eq!(std::fs::read(path).unwrap(),b"segundo");
    }
    #[test] fn vault_request_boundary() {
        let backend=Backend{origin:"http://127.0.0.1:1".into(),token:"a".repeat(43)};
        let vault=Mutex::new(Some(Vault::new(std::path::Path::new("/unused-test"))));
        for path in ["/api/voice-storage","/api/engine-storage","/api/realtime/key","/api/engine/key"] {
            let request=Request::builder().method("POST").uri(format!("workbench://app{path}")).body(Vec::new()).unwrap();
            assert_eq!(proxy(&backend,&vault,request).status(),401);
        }
        for body in ["null","[]",r#"{"provider":null,"remember":true}"#,r#"{"provider":"../openai","remember":true}"#,r#"{"remember":"true"}"#,r#"{"provider":"gemini"}"#] {
            let request=Request::builder().method("POST").uri("workbench://app/api/voice-storage")
                .header("Authorization",format!("Bearer {}",backend.token)).header("Content-Type","application/json").body(body.as_bytes().to_vec()).unwrap();
            assert_eq!(proxy(&backend,&vault,request).status(),400);
        }
    }
    #[test] fn origins_and_handshake() {
        assert!(valid_backend(&Backend{origin:"http://127.0.0.1:8765".into(),token:"a".repeat(43)}));
        for origin in ["http://evil.test:8765","http://127.0.0.1:8765/path","http://user@127.0.0.1:8765","http://127.0.0.1:8765?x=y"] {assert!(!valid_backend(&Backend{origin:origin.into(),token:"a".repeat(43)}));}
        assert!(local_url(&"workbench://app/".parse().unwrap()));
        for url in ["https://evil.test/","workbench://evil/","http://workbench.app/"] {assert!(!local_url(&url.parse().unwrap()));}
        for url in ["https://auth.openai.com/oauth/authorize","https://example.org/story","http://example.org/"] {assert!(external_url(&url.parse().unwrap()));}
        for url in ["file:///tmp/story","javascript:alert(1)","workbench://app/","https://user@auth.openai.com/"] {assert!(!external_url(&url.parse().unwrap()));}
    }
}
