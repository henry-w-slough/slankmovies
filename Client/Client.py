from . import FileReader
from .. import config


class Client():


    def __init__(self) -> None:
        
        #the size of which chunks are created (default 32MB)
        self.read_size = (1024*1024*32)


    def set_read_size(self, size:int) -> None:
        """Sets the size in megabytes at which file chunks will be created."""
        #NOTE: May want to change this for more versatility of chunk data size
        self.read_size = (1024*1024*size)


    def attach_file(self, new_dir:str, file_repository:str) -> None:
        FileReader.attach_file(file_repository, new_dir, self.read_size)