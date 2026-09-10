// Inherit the pipe: closing Tauri's stdin also stops Python and releases its data lock.
fn main() {
    let root = std::path::PathBuf::from(std::env::var_os("STORY_SERVER_RUNTIME").expect("Runtime requerido"));
    let mut command = std::process::Command::new(root.join("python/python.exe"));
    command.args(["-m", "src.app"]).args(std::env::args_os().skip(1));
    #[cfg(windows)] {
        use std::os::windows::process::CommandExt;
        command.creation_flags(0x08000000); // CREATE_NO_WINDOW; retain inherited stdin/stdout.
    }
    let status = command.status().expect("No se pudo iniciar Python");
    std::process::exit(status.code().unwrap_or(1));
}
