import os
import huggingface_hub as hf
from common import settings


def get_sym_path(repo_path, commit_hash, file_path):
    return f"{repo_path}/snapshots/{commit_hash}/{file_path}"


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
    for f in rev_info.files:
        if get_sym_path(repo_path, commit_hash, file_name) == str(f.file_path):
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
