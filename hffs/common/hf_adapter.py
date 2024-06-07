import os
import huggingface_hub as hf
from . import settings


def get_sym_path(repo_path, commit_hash, file_path):
    return os.path.normpath(f"{repo_path}/snapshots/{commit_hash}/{file_path}")


def file_in_cache(repo_id, file_name, revision="main"):
    # see https://huggingface.co/docs/huggingface_hub/v0.23.0/en/package_reference/cache
    # for API about HFCacheInfo, CachedRepoInfo, CachedRevisionInfo, CachedFileInfo

    cache_info = hf.scan_cache_dir(settings.HFFS_MODEL_DIR)

    repo_info = None
    repo_path = None
    for repo in cache_info.repos:
        if repo.repo_id == repo_id:
            repo_info = repo
            repo_path = repo.repo_path
            break

    if repo_info is None:
        return None  # no matching repo

    commit_hash = None
    rev_info = None
    for rev in repo_info.revisions:
        if rev.commit_hash.startswith(revision) or revision in rev.refs:
            commit_hash = rev.commit_hash
            rev_info = rev
            break

    if commit_hash is None:
        return None  # no matching revision

    etag = None
    size = None
    file_path = None
    sym_path = get_sym_path(repo_path, commit_hash, file_name)

    for f in rev_info.files:
        if sym_path == str(f.file_path):
            size = f.size_on_disk
            etag = os.path.basename(os.path.normpath(f.blob_path))
            file_path = f.file_path
            break

    if file_path is None:
        return None  # no matching file

    return {
        "etag": etag,
        "commit_hash": commit_hash,
        "size": size,
        "file_path": file_path
    }


def get_etag_path(repo_id, filename, revision="main"):
    model_path = hf.try_to_load_from_cache(
        repo_id=repo_id,
        filename=filename,
        cache_dir=settings.HFFS_MODEL_DIR,
        revision=revision,
    )

    if model_path == hf._CACHED_NO_EXIST:
        return None

    file_path = os.path.relpath(model_path, settings.HFFS_MODEL_DIR)
    return os.path.join(settings.HFFS_ETAG_DIR, file_path)


def try_to_load_etag(repo_id, filename, revision="main"):
    etag_path = get_etag_path(repo_id, filename, revision)

    if not etag_path or not os.path.exists(etag_path):
        return None

    with open(etag_path, "r") as f:
        return f.read().strip()


def save_etag(etag, repo_id, filename, revision="main"):
    etag_path = get_etag_path(repo_id, filename, revision)

    if not etag_path:
        raise ValueError(
            f"Failed to get etag path for repo={repo_id}, file={filename}, revision={revision}")

    os.makedirs(os.path.dirname(etag_path), exist_ok=True)

    with open(etag_path, "w+") as f:
        f.write(etag)
