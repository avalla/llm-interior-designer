//! Desktop shell (docs/desktop-app.md, D6): the window and the bridge to the Python sidecar, which does all the work
//! (recognition, semantics, checks). The sidecar speaks JSON lines over stdio: one request per line, one answer per
//! line with the same id (app/sidecar/server.py). It is started on the first request, kept alive, and restarted after a
//! failure.
//!
//! Which sidecar runs, in order: the command in INTERIORS_SIDECAR (program and arguments separated by spaces); the
//! bundled `interiors-sidecar` executable next to the app; in development, `uv run ... python -m app.sidecar.server`
//! in the repository this crate was built from.
use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};
use std::sync::{Arc, Mutex};

use serde_json::{json, Value};
use tauri::State;

struct Sidecar {
    child: Child,
    stdin: ChildStdin,
    stdout: BufReader<ChildStdout>,
    next: u64,
}

impl Drop for Sidecar {
    fn drop(&mut self) {
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}

#[derive(Default)]
struct Engine(Arc<Mutex<Option<Sidecar>>>);

fn sidecar_command() -> Command {
    if let Ok(line) = std::env::var("INTERIORS_SIDECAR") {
        let mut parts = line.split_whitespace();
        if let Some(program) = parts.next() {
            let mut cmd = Command::new(program);
            cmd.args(parts);
            return cmd;
        }
    }
    let bundled = std::env::current_exe().ok().and_then(|exe| {
        let name = if cfg!(windows) { "interiors-sidecar.exe" } else { "interiors-sidecar" };
        let path = exe.parent()?.join(name);
        path.exists().then_some(path)
    });
    if let Some(path) = bundled {
        return Command::new(path);
    }
    let repo = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../..");
    let mut cmd = Command::new("uv");
    cmd.args(["run", "--with", "ezdxf", "--with", "shapely", "python", "-m", "app.sidecar.server"])
        .current_dir(repo);
    cmd
}

fn spawn() -> Result<Sidecar, String> {
    let mut cmd = sidecar_command();
    #[cfg(windows)]
    {
        // the sidecar is a console program: without this flag Windows opens a console window next to the app
        use std::os::windows::process::CommandExt;
        cmd.creation_flags(0x0800_0000); // CREATE_NO_WINDOW
    }
    let mut child = cmd
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::inherit())
        .spawn()
        .map_err(|e| format!("cannot start the analysis engine: {e}"))?;
    let stdin = child.stdin.take().ok_or("no stdin to the analysis engine")?;
    let stdout = BufReader::new(child.stdout.take().ok_or("no stdout from the analysis engine")?);
    Ok(Sidecar { child, stdin, stdout, next: 0 })
}

fn exchange(sc: &mut Sidecar, id: u64, line: &str) -> Result<Value, String> {
    writeln!(sc.stdin, "{line}").map_err(|e| format!("analysis engine not reachable: {e}"))?;
    sc.stdin.flush().map_err(|e| e.to_string())?;
    let mut buf = String::new();
    loop {
        buf.clear();
        if sc.stdout.read_line(&mut buf).map_err(|e| e.to_string())? == 0 {
            return Err("the analysis engine stopped (see the terminal for its error)".into());
        }
        let v: Value = serde_json::from_str(&buf).map_err(|e| format!("bad answer from the engine: {e}"))?;
        if v["id"] == json!(id) {
            return Ok(v);
        }
    }
}

fn call(engine: &Mutex<Option<Sidecar>>, method: &str, params: Value) -> Result<Value, String> {
    let mut guard = engine.lock().map_err(|_| "engine lock poisoned".to_string())?;
    // a sidecar that died since the last request is replaced once; a fresh one that fails reports the error
    for attempt in 0..2 {
        let fresh = guard.is_none();
        if fresh {
            *guard = Some(spawn()?);
        }
        let sc = guard.as_mut().expect("sidecar just started");
        sc.next += 1;
        let id = sc.next;
        let line = json!({"id": id, "method": method, "params": params}).to_string();
        match exchange(sc, id, &line) {
            Err(e) => {
                *guard = None;
                if fresh || attempt == 1 {
                    return Err(e);
                }
            }
            Ok(v) => {
                return match v.get("error") {
                    Some(err) => Err(err.as_str().unwrap_or("engine error").to_string()),
                    None => Ok(v["result"].clone()),
                };
            }
        }
    }
    Err("the analysis engine could not be restarted".into())
}

/// Forwards one request to the sidecar, off the main thread (an analysis takes seconds).
#[tauri::command]
async fn sidecar(engine: State<'_, Engine>, method: String, params: Value) -> Result<Value, String> {
    let inner = engine.0.clone();
    let what = format!("{method} {}", params.get("path").and_then(Value::as_str).unwrap_or(""));
    let t0 = std::time::Instant::now();
    let out = tauri::async_runtime::spawn_blocking(move || call(&inner, &method, params))
        .await
        .map_err(|e| e.to_string())?;
    match &out {
        // one line per request in the terminal of `tauri dev`: what was asked, how it went, how big, how long
        Ok(v) => eprintln!("[sidecar] {what} -> ok, {} bytes, {:?}", v.to_string().len(), t0.elapsed()),
        Err(e) => eprintln!("[sidecar] {what} -> error: {e}"),
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn engine_that_dies_is_restarted_and_errors_pass_through() {
        let script = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("tests/fake_sidecar.py");
        // SAFETY: the only test touching the environment; set before any sidecar starts
        unsafe { std::env::set_var("INTERIORS_SIDECAR", format!("python3 {}", script.display())) };
        let engine = Mutex::new(None);
        assert_eq!(call(&engine, "echo", json!({"n": 1})).unwrap(), json!({"echo": {"n": 1}}));
        // the fake answered once and exited: the next request goes to a new sidecar
        assert_eq!(call(&engine, "echo", json!({"n": 2})).unwrap(), json!({"echo": {"n": 2}}));
        assert_eq!(call(&engine, "fail", json!({})).unwrap_err(), "ValueError: asked to fail");
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .manage(Engine::default())
        .invoke_handler(tauri::generate_handler![sidecar])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
