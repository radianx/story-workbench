"""Prueba de la ventana Tauri real con corpus temporal; sin cuenta ni API; micrófono virtual de WebKit."""
import os,subprocess,tempfile,argparse,threading,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--binary',type=Path,default=ROOT/'src-tauri/target/debug/story-workbench')
parser.add_argument('--dialog-tool',type=Path,help='xdotool para comprobar Guardar/Cancelar en el diálogo GTK real')
args=parser.parse_args();command=args.binary.resolve()
with tempfile.TemporaryDirectory(prefix='sw-tauri-test-') as directory:
    env={**os.environ,'STORY_TEST_DATA':directory,'STORY_TAURI_SMOKE':'1','XDG_DATA_HOME':str(Path(directory)/'gtk-data')}
    stopped=threading.Event();dialog_errors=[];dialog_count=[];folder_count=[]
    original=Path(directory)/'original';original.mkdir();(original/'cuento.md').write_text('Ficción de carpeta.')
    def dialogs():
        try:
            while not stopped.wait(.2):
                result=subprocess.run([str(args.dialog_tool),'search','--onlyvisible','--name','Guardar exportación'],capture_output=True,text=True)
                folder=False
                if result.returncode:
                    result=subprocess.run([str(args.dialog_tool),'search','--onlyvisible','--name','Elegir carpeta'],capture_output=True,text=True)
                    if result.returncode:continue
                    folder=True
                window=result.stdout.splitlines()[-1]
                if folder:stopped.wait(.6) # La carpeta GTK aparece antes de que acepte la entrada.
                subprocess.run([str(args.dialog_tool),'windowfocus','--sync',window],check=True,capture_output=True)
                seen=folder_count if folder else dialog_count
                if window not in seen:seen.append(window)
                ordinal=seen.index(window)
                if folder:
                    if ordinal%2==0:
                        subprocess.run([str(args.dialog_tool),'key','--clearmodifiers','ctrl+l'],check=True)
                        subprocess.run([str(args.dialog_tool),'type','--clearmodifiers','--',str(original)],check=True)
                        subprocess.run([str(args.dialog_tool),'key','Return'],check=True)
                    else:subprocess.run([str(args.dialog_tool),'key','Escape'],check=True)
                elif ordinal%3!=1:
                    subprocess.run([str(args.dialog_tool),'key','--clearmodifiers','ctrl+l'],check=True)
                    subprocess.run([str(args.dialog_tool),'type','--clearmodifiers','--',str(Path(directory)/f'export-{ordinal}.{"docx" if ordinal%3==0 else "md"}')],check=True)
                    subprocess.run([str(args.dialog_tool),'key','Return'],check=True)
                else:subprocess.run([str(args.dialog_tool),'key','Escape'],check=True)
                for _ in range(50):
                    if stopped.wait(.1):break
                    visible=subprocess.run([str(args.dialog_tool),'search','--onlyvisible','--name','Elegir carpeta' if folder else 'Guardar exportación'],capture_output=True,text=True)
                    if window not in visible.stdout.splitlines():break
        except Exception as error:dialog_errors.append(error)
    if args.dialog_tool:
        env['STORY_TAURI_EXPORT_TEST']='1'
        driver=threading.Thread(target=dialogs,daemon=True);driver.start()
    try:
        for launch in range(2):
            result=subprocess.run([str(command)],env=env,capture_output=True,text=True,timeout=90)
            print(result.stdout,flush=True)
            if args.dialog_tool:print("Dialog actions:",len(dialog_count),"Errors:",dialog_errors,flush=True)
            if result.returncode or "Tauri smoke: OK" not in result.stdout:print(result.stderr[-3000:])
            assert result.returncode==0,result.returncode
            assert 'Tauri smoke: OK' in result.stdout
        for file in Path(directory).rglob('*'):
            if file.is_file():assert b'AQ.fixture-not-a-real-key-tauri' not in file.read_bytes(),file
        if args.dialog_tool:
            assert not dialog_errors,dialog_errors
            assert len(dialog_count)==6,dialog_count
            # GTK puede consumir Escape en su entrada de ubicación; los reintentos conservan la acción del mismo diálogo.
            assert len(set(folder_count))==4,folder_count
            assert (original/'cuento.md').read_text()=='Ficción de carpeta.'
            for file in Path(directory).glob('export-*.docx'):
                with zipfile.ZipFile(file) as archive:assert 'word/document.xml' in archive.namelist()
            assert len(list(Path(directory).glob('export-*.docx')))==2
            empty=list(Path(directory).glob('export-*.md'));assert len(empty)==2 and all(file.read_bytes()==b'' for file in empty)
            print('OK diálogos GTK reales: cuatro selectores de carpeta con copia/cancelación y seis exportaciones, en ambos arranques.')
    finally:
        stopped.set()
        if args.dialog_tool:driver.join(5)
        subprocess.run([str(command)],env={**env,'STORY_TAURI_CLEANUP':'1'},check=True,timeout=30)
    assert (Path(directory)/'projects').is_dir()
    assert not (Path(directory)/'codex/auth.json').exists()
print('OK Tauri: sidecar, interfaz WebKit, proyecto ficticio, editor, navegación, tema entre reinicios, libro y exportación HTTP. Claves ficticias guardadas/recuperadas/borradas en llavero nativo, audio virtual, cámara denegada, lectura local, transporte Gemini y lectura OpenAI/Gemini simulados. WebRTC se informa por separado.')
