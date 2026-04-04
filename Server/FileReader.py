import hashlib


def get_chunk_name(data:bytes, length:int=8) -> str:
    return hashlib.sha256(data).hexdigest()[:length]


def file_to_chunk(src:str, path_to:str, read_size:int=1024*1024*32, name_size:int=8) -> None:
    
    #stores read data indexes with chunk name for chunk read order
    chunks = {
        
    }

    with open(src, "rb") as to_read:
        #iterating each chunk of data
        while chunk := to_read.read(read_size):

            chunk_name = get_chunk_name(chunk, name_size)
            #creating file for chunk
            with open(f"{path_to}/{chunk_name}", "wb") as to_write:
                to_write.write(chunk)

            #chunk at its write index for manifest
            chunks[len(chunks)] = chunk_name

    

    

        









            



