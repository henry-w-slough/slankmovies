import os
import json

from .. import config

def attach_file(repository_dir:str, new_dir:str, read_size:int) -> None:

    #getting chunk order
    with open(os.path.join(repository_dir, config.MANIFEST_SRC)) as manifest_file:
        manifest_data = json.load(manifest_file)
    chunk_order = manifest_data[config.CHUNK_ORDER_KEY]

    with open(os.path.join(repository_dir, manifest_data[config.MOVIE_NAME_KEY]), "wb") as new_file:

        for chunk in chunk_order:
            with open(os.path.join(repository_dir, config.DATA_SRC, chunk), "rb") as chunk_file:
                new_file.write(chunk_file.read(read_size))

    



    
        