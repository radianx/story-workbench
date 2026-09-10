"""Inicio/cancelación reales de OAuth en CODEX_HOME temporal, sin sesión del usuario."""
import asyncio, os, tempfile, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.codex_smoke import Server
from src.workbench_account import auth_url
async def main():
    with tempfile.TemporaryDirectory(prefix='sw-auth-check-') as directory:
        os.environ['CODEX_HOME']=directory
        async with Server(Path(directory),require_account=False) as server:
            assert (await server.rpc('account/read',{'refreshToken':False}))['account'] is None
            login=await server.rpc('account/login/start',{'type':'chatgpt'})
            assert login['type']=='chatgpt';auth_url(login['authUrl'])
            await server.rpc('account/login/cancel',{'loginId':login['loginId']})
            print('OK login real: cuenta aislada vacía, URL oficial recibida y login cancelado; no se autorizó otra cuenta.')
asyncio.run(main())
