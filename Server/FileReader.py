import hashlib
import json

from . import config


def get_chunk_name(data:bytes, length:int=8) -> str:
    """Returns a hash name based on the data and length provided."""
    return hashlib.sha256(data).hexdigest()[:length]


def chop_file(src:str, data_src:str, manifest_src:str, read_size:int, name_size:int=8) -> None:
    """Reads the file at the given path and creates data chunks based on it. Chunk names are has"""

    chunks = []

    with open(src, "rb") as to_read:
        #iterating each chunk of data
        while chunk := to_read.read(read_size):
            
            chunk_name = get_chunk_name(chunk, name_size)

            #creating file for chunk
            with open(f"{data_src}/{chunk_name}", "wb") as to_write:
                to_write.write(chunk)

            #adding chunk to chunk list for later manifest addition
            chunks.append(chunk_name)

    #opening manifest to read the metadata
    with open(manifest_src, "r") as manifest:
        manifest_data = json.load(manifest)

    manifest_data[config.CHUNK_ORDER_KEY] = chunks

    #opening manifest to write the updated metadata
    with open(manifest_src, "w") as manifest:
        json.dump(manifest_data, manifest, indent=2)

    



    

    

        









            



