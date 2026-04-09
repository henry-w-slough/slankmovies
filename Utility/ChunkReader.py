
import os
import json

from .. import config


def copy_repository_data(repository_dir:str, new_dir:str) -> None:
    """Takes a repository directory and attaches all it's data chunks back together, puts the result in the new directory. Also migrates the manifest.json for metadata."""

    #getting chunk order
    with open(os.path.join(repository_dir, config.MANIFEST_SRC)) as manifest_file:
        manifest_data = json.load(manifest_file)

    chunk_order = manifest_data[config.CHUNK_ORDER_KEY]

    #copying manifest data
    with open(os.path.join(new_dir, config.MANIFEST_SRC), "w") as new_manifest:
        json.dump(manifest_data, new_manifest, indent=config.MANIFEST_INDENT)

    #opening the new directory, note that the file name is the same as seen in manifest.json
    with open(os.path.join(new_dir, manifest_data[config.MOVIE_NAME_KEY]), "wb") as new_file:
        #writing each chunk in order
        for chunk in chunk_order:
            with open(os.path.join(repository_dir, config.DATA_DIR, chunk), "rb") as chunk_file:
                new_file.write(chunk_file.read())
