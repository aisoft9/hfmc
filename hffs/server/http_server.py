import asyncio
import json
import os
import logging
import re

from aiohttp import web
from aiohttp import streamer
from aiohttp.web_runner import GracefulExit
from contextvars import ContextVar

import huggingface_hub as hf
from .peer_prober import PeerProber
from ..common.peer_store import PeerStore
from ..common.hf_adapter import file_in_cache, load_repo_revision_info
from ..common.settings import save_local_service_port, HFFS_API_PING, HFFS_API_PEER_CHANGE, HFFS_API_ALIVE_PEERS
from ..common.settings import HFFS_API_STATUS, HFFS_API_STOP

ctx_var_peer_prober = ContextVar("PeerProber")


def extract_model_info(request):
    user = request.match_info['user']
    model = request.match_info['model']
    revision = request.match_info['revision']
    file_name = request.match_info['file_name']
    repo_id = f"{user}/{model}"
    return repo_id, file_name, revision


@streamer
async def file_sender(writer, file_path=None, file_range=()):
    """
    This function will read large file chunk by chunk and send it through HTTP
    without reading them into memory
    """
    file_start, file_end = file_range

    with open(file_path, 'rb') as f:
        if file_start is not None:
            f.seek(file_start)

        buf_size = 2 ** 18

        while True:
            to_read = min(buf_size, file_end + 1 - f.tell()
                          if file_end else buf_size)
            buf = f.read(to_read)

            if not buf:
                break

            await writer.write(buf)


async def download_file(request):

    def parse_byte_range(byte_range):
        """Returns the two numbers in 'bytes=123-456' or throws ValueError.

        The last number or both numbers may be None.
        """
        byte_range_re = re.compile(r'bytes=(\d+)-(\d+)?$')

        if not byte_range or byte_range.strip() == '':
            return None, None

        m = byte_range_re.match(byte_range)

        if not m:
            raise ValueError('Invalid byte range %s' % byte_range)

        first, last = [x and int(x) for x in m.groups()]

        if last and last < first:
            raise ValueError('Invalid byte range %s' % byte_range)

        return first, last

    try:
        file_start, file_end = parse_byte_range(request.headers.get("Range"))
    except Exception as e:
        err_msg = "Invalid file range! ERROR: {}".format(e)
        logging.warning(err_msg)
        return web.Response(body=err_msg, status=400)

    repo_id, file_name, revision = extract_model_info(request)
    cached = file_in_cache(repo_id, file_name, revision)

    if not cached:
        logging.error("download 404 not cached")
        return web.Response(
            body=f'File <{file_name}> is not cached',
            status=404)

    headers = {"Content-disposition": f"attachment; filename={file_name}"}

    file_path = cached["file_path"]

    if not os.path.exists(file_path):
        logging.error("download 404 not exist")
        return web.Response(
            body=f'File <{file_path}> does not exist',
            status=404
        )

    logging.debug("download 200")
    return web.Response(
        body=file_sender(file_path=file_path,
                         file_range=(file_start, file_end)),
        headers=headers
    )


async def pong(_):
    # logging.debug(f"[SERVER] seq={_.query['seq']}")
    return web.Response(text='pong')


async def alive_peers(_):
    peer_prober = ctx_var_peer_prober.get()
    peers = peer_prober.get_actives()
    return web.json_response([peer.to_dict() for peer in peers])


async def search_model(request):
    repo_id, file_name, revision = extract_model_info(request)
    cached = file_in_cache(repo_id, file_name, revision)

    if not cached:
        return web.Response(status=404)
    else:
        headers = {
            hf.constants.HUGGINGFACE_HEADER_X_REPO_COMMIT: cached["commit_hash"],
            "ETag": cached["etag"] if cached["etag"] else "",
            "Content-Length": str(cached["size"]),
            "Location": str(request.url),
        }
        logging.debug(f"search_model: {headers}")
        return web.Response(status=200, headers=headers)


async def get_repo_info(request):
    user = request.match_info['user']
    model = request.match_info['model']
    revision = "main"
    repo_id = f"{user}/{model}"

    try:
        repo_info = load_repo_revision_info(repo_id, revision)
        return web.json_response(data=repo_info)
    except (LookupError, ValueError) as lve:
        return web.Response(status=404, reason=f'{lve}')
    except Exception as e:
        return web.Response(status=500, reason=f'{e}')


async def get_repo_revision_info(request):
    user = request.match_info['user']
    model = request.match_info['model']
    revision = request.match_info['revision']
    repo_id = f"{user}/{model}"

    try:
        repo_info = load_repo_revision_info(repo_id, revision)
        return web.json_response(data=repo_info)
    except (LookupError, ValueError) as lve:
        return web.Response(status=404, reason=f'{lve}')
    except Exception as e:
        return web.Response(status=500, reason=f'{e}')


def get_peers():
    peers = set()
    with PeerStore() as peer_store:
        peers = peer_store.get_peers()
    return peers


async def on_peer_change(_):
    peers = get_peers()
    peer_prober: PeerProber = ctx_var_peer_prober.get()
    peer_prober.update_peers(peers)
    return web.Response(status=200)


async def get_service_status(_):
    return web.json_response(data={})


async def post_stop_service(request):
    resp = web.Response()
    await resp.prepare(request)
    await resp.write_eof()
    logging.warning("Received exit request, exit server!")
    raise GracefulExit()


async def start_server_safe(port):
    # set up context before starting the server
    peers = get_peers()
    peer_prober = PeerProber(peers)
    ctx_var_peer_prober.set(peer_prober)

    # start peer prober to run in the background
    asyncio.create_task(peer_prober.start_probe())

    # start aiohttp server
    app = web.Application()

    # HEAD requests
    app.router.add_head(
        '/{user}/{model}/resolve/{revision}/{file_name:.*}', search_model)

    app.router.add_get('/api/models/{user}/{model}', get_repo_info)
    app.router.add_get('/api/models/{user}/{model}/revision/{revision}', get_repo_revision_info)

    # GET requests
    app.router.add_get(HFFS_API_PING, pong)
    app.router.add_get(HFFS_API_ALIVE_PEERS, alive_peers)
    app.router.add_get(HFFS_API_PEER_CHANGE, on_peer_change)
    app.router.add_get(
        '/{user}/{model}/resolve/{revision}/{file_name:.*}', download_file)

    app.router.add_get(HFFS_API_STATUS, get_service_status)
    app.router.add_post(HFFS_API_STOP, post_stop_service)

    # start web server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner=runner, host='0.0.0.0', port=port)
    await site.start()

    save_local_service_port(port)

    logging.info(f"HFFS daemon started at port {port}!")

    # keep the server running
    while True:
        await asyncio.sleep(3600)


async def start_server(port):
    try:
        await start_server_safe(port)
    except OSError as e:
        if e.errno == 48:
            print(f"Daemon is NOT started: port {port} is already in use")
    except Exception as e:
        logging.error("Failed to start HFFS daemon")
        logging.error(e)
