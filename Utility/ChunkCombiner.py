
from ..Models import Movie

import os
import json

from .. import config

def chunks_to_file(movie:Movie.Movie, chunks_dir:str, new_dir:str) -> None:

    os.makedirs(new_dir, exist_ok=True)
    
    #opening new directory for writing to
    with open(os.path.join(new_dir, "video.mp4"), "wb") as new_file:
        #iterates in order of the chunk order read, meaning true data order.
        for chunk_id in movie.chunk_order:
            #wriitng read data to new file
            with open(os.path.join(chunks_dir, chunk_id), "rb") as chunk:
                new_file.write(chunk.read(config.DEFAULT_READ_SIZE))