import asyncio
import os

from aiohttp import web
from aiohttp import streamer
from contextvars import ContextVar
from huggingface_hub import HfApi
from common.peer_store import PeerStore
from server.peer_prober import PeerProber
from common.hf_adapter import file_in_cache

ctx_var_peer_prober = ContextVar("PeerProber")


@streamer
async def file_sender(writer, file_path=None):
    """
    This function will read large file chunk by chunk and send it through HTTP
    without reading them into memory
    """
    with open(file_path, 'rb') as f:
        chunk = f.read(2 ** 16)
        while chunk:
            await writer.write(chunk)
            chunk = f.read(2 ** 16)


async def download_file(request):
    file_name = request.match_info['file_name']  # Could be a HUGE file
    headers = {
        "Content-disposition": "attachment; filename={file_name}".format(file_name=file_name)
    }

    file_path = os.path.join('/home/sche/.cache/huggingface/hub', file_name)

    if not os.path.exists(file_path):
        return web.Response(
            body='File <{file_name}> does not exist'.format(
                file_name=file_path),
            status=404
        )

    return web.Response(
        body=file_sender(file_path=file_path),
        headers=headers
    )


async def pong(request):
    # print(f"[SERVER] seq={request.query['seq']}")
    return web.Response(text='pong')


async def alive_peers(request):
    peer_prober = ctx_var_peer_prober.get()
    peers = peer_prober.get_actives()
    return web.json_response([peer.to_dict() for peer in peers])


async def search_model(request):
    user = request.match_info['user']
    model = request.match_info['model']
    revision = request.match_info['revision']
    file_name = request.match_info['file_name']

    repo_id = f"{user}/{model}"
    cached = file_in_cache(repo_id, file_name, revision)

    status = 200 if cached else 404
    return web.Response(status=status)


async def start_server(port):
    # set up context before starting the server
    peer_store = PeerStore()
    peer_store.open()

    peer_prober = PeerProber(peer_store)
    ctx_var_peer_prober.set(peer_prober)

    # start aiohttp server
    app = web.Application()

    app.router.add_head(
        '/model/{user}/{model}/resolve/{revision}/{file_name}', search_model)
    app.router.add_get('/file/{file_name}', download_file)
    app.router.add_get('/ping', pong)
    app.router.add_get('/alive_peers', alive_peers)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner=runner, host='0.0.0.0', port=port)
    await site.start()

    # start peer prober to run in the background
    asyncio.create_task(peer_prober.start_probe())

    print(f"HFFS daemon started at port {port}!")

    # keep the server running
    while True:
        await asyncio.sleep(3600)
