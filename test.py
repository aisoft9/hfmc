import asyncio
from hffs.client.http_client import get_model_etag
from hffs.common.settings import HFFS_MODEL_DIR
from huggingface_hub import try_to_load_from_cache
from hffs.common.hf_adapter import try_to_load_etag, save_etag


async def test_fetch_etag():
    etag = await get_model_etag(
        "https://hf-mirror.com",
        "prajjwal1/bert-tiny",
        "pytorch_model.bin",
        "main"
    )
    print(etag)


async def test_write_etag():
    etag = await get_model_etag(
        "https://hf-mirror.com",
        "prajjwal1/bert-tiny",
        "pytorch_model.bin",
        "main"
    )
    save_etag(etag, "prajjwal1/bert-tiny", "pytorch_model.bin")


def test_get_etag():
    etag = try_to_load_etag("prajjwal1/bert-tiny", "pytorch_model.bin")
    
    print(etag)

# asyncio.run(test_fetch_etag())
asyncio.run(test_write_etag())
# test_get_etag()