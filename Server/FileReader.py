import hashlib
import json
import os

from . import config


def get_chunk_id(data:bytes, length:int=8) -> str:
    """Returns a hash id based on the data and length provided."""
    return hashlib.sha256(data).hexdigest()[:length]


def chop_file(file_src:str, data_dir:str, manifest_src:str, read_size:int, id_length:int=8) -> None:
    """Reads the file at the given path and creates data chunks based on it."""

    #holds chunk id and chunk data. We use a dict in order
    #to easily compare the previous and new chunks without having to read
    #or write multiple times.
    chunks = {

    }

    with open(file_src, "rb") as to_read:
        #iterating each chunk of data and creating new chunk
        while chunk := to_read.read(read_size):
            chunk_id = get_chunk_id(chunk, id_length)
            chunks[chunk_id] = chunk

    #checks to see if we need to purge the data directory
    data_list = os.listdir(data_dir)
    if len(chunks) != len(data_list):
        #purge. it. all.
        for file in data_list:
            os.remove(os.path.)

    #opening manifest to read the metadata. We open it here so we can compare the old data to the new reads
    with open(manifest_src, "r") as manifest:
        manifest_data = json.load(manifest)

    #updating metadata chunk order
    manifest_data[config.CHUNK_ORDER_KEY] = chunks

    #opening manifest to write the updated metadata
    with open(manifest_src, "w") as manifest:
        json.dump(manifest_data, manifest, indent=config.MANIFEST_INDENT)

    



    

    

        









            



