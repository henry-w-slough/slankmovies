from . import FileReader
from .. import config

import os
import json


class Repository():


    def __init__(self, root_dir:str) -> None:
        """
            Manager of all information and data relating to the organization of files. This includes the data itself, it's location, and how data is handled in operations.
        """

        #the size of which chunks are created (default 32MB)
        self.read_size = (1024*1024*32)
        
        self.root = root_dir

        #data directory folder
        self.data_dir = os.path.join(self.root, config.DATA_SRC)
        os.makedirs(self.data_dir, exist_ok=True)

        #manifest file for metadata
        self.manifest_src = os.path.join(self.root, config.MANIFEST_SRC)

        with open(self.manifest_src, "w") as manifest:
            json.dump(config.MANIFEST_DEFAULTS, manifest)

    
    def set_read_size(self, size:int) -> None:
        """Sets the size in megabytes at which file chunks will be created."""
        #NOTE: May want to change this for more versatility of chunk data size
        self.read_size = (1024*1024*size)


    def add_file(self, src:str) -> None:
        """Converts the given file into chunks of hashed data in the Repository's data folder."""
        FileReader.chop_file(src, self.data_dir, self.manifest_src, self.read_size)

    
