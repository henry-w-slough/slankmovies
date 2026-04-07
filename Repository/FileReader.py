import hashlib
import json
import os
import pathlib

from .. import config


def get_chunk_id(data:bytes, length:int=8) -> str:
    """Returns a hash id based on the data and length provided."""
    return hashlib.sha256(data).hexdigest()[:length]


def chop_file(file_src:str, data_dir:str, manifest_src:str, read_size:int, id_length:int=8) -> None:
    """Reads the file at the given path and creates data chunks based on it."""

    #clearing the entire data folder
    folder = pathlib.Path(data_dir)
    for file in folder.iterdir():
        if file.is_file():
            file.unlink()

    new_chunk_order = []


    #opening where to read
    with open(file_src, "rb") as file:
        
        #iterating through the entire file given
        while chunk := file.read(read_size):
            #getting a hashed id for the chunk
            chunk_id = get_chunk_id(chunk, id_length)
            #for the manifest.json and reading data in order
            new_chunk_order.append(chunk_id)

            #creating the new file for the chunk
            with open(os.path.join(data_dir, chunk_id), "wb") as chunk_file:
                chunk_file.write(chunk)


    #getting old manifest data
    with open(manifest_src, "r") as manifest:
        manifest_data = json.load(manifest)

    #setting the new chunk order
    manifest_data[config.CHUNK_ORDER_KEY] = new_chunk_order
    manifest_data[config.MOVIE_NAME_KEY] = file_src

    #directly updating the new chunk order
    with open(manifest_src, "w") as manifest:
        json.dump(manifest_data, manifest, indent=config.MANIFEST_INDENT)


        

    



    

    

        









            



