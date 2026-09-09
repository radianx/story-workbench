#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
use std::{collections::HashMap, io::Read, sync::{Arc, Mutex, Condvar, atomic::{AtomicBool, Ordering}}, time::Duration};
use serde::Deserialize;
use tauri::{Manager, WebviewUrl, WebviewWindowBuilder, webview::NewWindowResponse, http::{Request, Response}};
use tauri_plugin_shell::{ShellExt, process::{CommandChild, CommandEvent}};
use tauri_plugin_opener::OpenerExt;

#[derive(Clone, Deserialize)]
struct Backend { origin: String, token: String }
struct Runtime { backend: Mutex<Option<Backend>>, child: Mutex<Option<CommandChild>>, closing: AtomicBool, exited: (Mutex<bool>, Condvar) }

fn local_url(url: &tauri::Url) -> bool {
    if !url.username().is_empty() || url.password().is_some() || url.port().is_some() {return false}
    (url.scheme()=="workbench" && url.host_str()==Some("app")) ||
    (url.scheme()=="https" && url.host_str()==Some("workbench.app"))
}
fn auth_url(url: &tauri::Url) -> bool {
    url.scheme()=="https" && url.host_str()==Some("auth.openai.com") &&
    url.username().is_empty() && url.password().is_none() && url.port_or_known_default()==Some(443)
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
fn proxy(backend: &Backend, request: Request<Vec<u8>>) -> Response<Vec<u8>> {
    let Ok(url)=tauri::Url::parse(&request.uri().to_string()) else { return error_response(403,"Origen inválido.") };
    if !local_url(&url) || !["GET","POST"].contains(&request.method().as_str()) || request.body().len()>2_000_000 {
        return error_response(403,"Solicitud no permitida.")
    }
    let path=request.uri().path_and_query().map(|p|p.as_str()).unwrap_or("/").to_owned();
    if ["/api/voice-storage","/api/engine-storage"].contains(&url.path()) {
        if request.headers().get("Authorization").and_then(|v|v.to_str().ok())!=Some(&format!("Bearer {}",backend.token)) {
            return error_response(401,"Acceso no autorizado.")
        }
        if request.method()=="GET" {
            return Response::builder().header("Content-Type","application/json").header("Cache-Control","no-store")
                .body(serde_json::json!({"available":false,"stored":{},"reason":"Vista previa Tauri: claves solo en memoria. La migración del almacén nativo todavía no está habilitada."}).to_string().into_bytes()).unwrap()
        }
        return error_response(409,"El almacén persistente de esta vista previa aún no está habilitado.")
    }
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
fn main() {
    let runtime=Arc::new(Runtime {backend:Mutex::new(None),child:Mutex::new(None),closing:AtomicBool::new(false),exited:(Mutex::new(false),Condvar::new())});
    let bridge=runtime.clone();let startup=runtime.clone();let shutdown=runtime.clone();
    let smoke=std::env::var("STORY_TAURI_SMOKE").as_deref()==Ok("1");
    let app=tauri::Builder::default()
        .plugin(tauri_plugin_shell::init()).plugin(tauri_plugin_opener::init())
        .register_asynchronous_uri_scheme_protocol("workbench", move |ctx,request,responder| {
            let backend=bridge.backend.lock().unwrap().clone();let handle=ctx.app_handle().clone();
            std::thread::spawn(move || {
                let Some(backend)=backend else {responder.respond(error_response(503,"Iniciando servicio local."));return};
                if smoke && request.uri().path()=="/__smoke" && request.headers().get("Authorization").and_then(|v|v.to_str().ok())==Some(&format!("Bearer {}",backend.token)) {
                    let success=request.body()==b"ok";responder.respond(Response::new(b"ok".to_vec()));
                    println!("Tauri smoke: {}",if success {"OK"} else {"FAILED"});handle.exit(if success {0}else{2});return;
                }
                responder.respond(proxy(&backend,request));
            });
        })
        .setup(move |app| {
            let data=std::env::var_os("STORY_TEST_DATA").map(std::path::PathBuf::from).unwrap_or(app.path().app_data_dir()?);
            std::fs::create_dir_all(data.join("codex"))?;
            let resources=app.path().resource_dir()?.join("runtime");
            let env:HashMap<String,String>=std::env::vars().filter(|(key,_)|!["OPENAI_","AZURE_OPENAI_","CODEX_API_","CODEX_THREAD_"].iter().any(|prefix|key.starts_with(prefix))).collect();
            let (mut rx,child)=app.shell().sidecar("story-server")?.env_clear().envs(env)
                .env("STORY_DESKTOP","1").env("CODEX_HOME",data.join("codex"))
                .env("STORY_CODEX_BINARY",resources.join(if cfg!(windows){"codex/bin/codex.exe"}else{"codex/bin/codex"}))
                .env("STORY_VOICE_DIR",resources.join("voice"))
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
            *startup.backend.lock().unwrap()=Some(backend.clone());
            let handle=app.handle().clone();let watcher=startup.clone();
            tauri::async_runtime::spawn(async move {
                while let Some(event)=rx.recv().await {if matches!(event,CommandEvent::Terminated(_)){
                    *watcher.exited.0.lock().unwrap()=true;watcher.exited.1.notify_all();
                    if !watcher.closing.load(Ordering::SeqCst){handle.exit(1);}break;
                }}
            });
            let opener=app.handle().clone();
            let smoke_script=if smoke {include_str!("smoke.js").replace("__TOKEN__",&backend.token)}else{String::new()};
            let _window=WebviewWindowBuilder::new(app,"main",WebviewUrl::CustomProtocol(format!("workbench://app/#token={}",backend.token).parse()?))
                .data_directory(data.join("webview")).title("Story Workbench · Tauri Preview").inner_size(1440.0,1000.0).min_inner_size(380.0,600.0)
                .initialization_script(&smoke_script).use_https_scheme(true).on_navigation(local_url)
                .on_new_window(move |url,_|{if auth_url(&url){let _=opener.opener().open_url(url.as_str(),None::<&str>);}NewWindowResponse::Deny})
                .build()?;
            if smoke {
                let timeout=app.handle().clone();std::thread::spawn(move || {std::thread::sleep(Duration::from_secs(60));timeout.exit(3);});
            }
            Ok(())
        }).build(tauri::generate_context!()).expect("No se pudo iniciar la vista previa Tauri");
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
    #[test] fn origins_and_handshake() {
        assert!(valid_backend(&Backend{origin:"http://127.0.0.1:8765".into(),token:"a".repeat(43)}));
        for origin in ["http://evil.test:8765","http://127.0.0.1:8765/path","http://user@127.0.0.1:8765","http://127.0.0.1:8765?x=y"] {assert!(!valid_backend(&Backend{origin:origin.into(),token:"a".repeat(43)}));}
        assert!(local_url(&"workbench://app/".parse().unwrap()));
        for url in ["https://evil.test/","workbench://evil/","http://workbench.app/"] {assert!(!local_url(&url.parse().unwrap()));}
        assert!(auth_url(&"https://auth.openai.com/oauth/authorize".parse().unwrap()));
        for url in ["https://auth.openai.com.evil.test/","http://auth.openai.com/","https://user@auth.openai.com/","https://auth.openai.com:444/"] {assert!(!auth_url(&url.parse().unwrap()));}
    }
}
