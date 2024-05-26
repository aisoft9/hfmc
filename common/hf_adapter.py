import huggingface_hub as hf
from common import settings


def file_in_cache(repo_id, file_name, revision="main"):
    cache_info = hf.scan_cache_dir(settings.HFFS_MODEL_DIR)

    repos = list(filter(lambda r: r.repo_id == repo_id, cache_info.repos))

    revisions = []
    for repo in repos:
        matched = list(filter(lambda r: r.commit_hash == revision
                              or revision in r.refs, repo.revisions))
        revisions.extend(matched)

    files = []
    for rev in revisions:
        matched = filter(lambda f: f.file_name == file_name, rev.files)
        files.extend(matched)

    assert len(files) == 0 or len(files) == 1
    return files[0] if len(files) == 1 else None
