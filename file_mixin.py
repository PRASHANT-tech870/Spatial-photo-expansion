from abc import abstractproperty
import os
import random
import string
from pathlib import Path
import logging


class FileMixin:
    def get_directory_name(self) -> str:
        """Make a folder based on the input filename to store all the processed files
        """
        if self.directory == None:
            # Get the base directory of the original file
            directory = os.path.dirname(self.filename)
            
            # Get the base filename without extension
            base_filename = os.path.splitext(os.path.basename(self.filename))[0]
            
            # Create a directory with the filename
            new_directory = f"{directory}/{base_filename}_output"
            logging.info(f"Generating output directory: {new_directory}")
            self.directory = new_directory
            Path(new_directory).mkdir(parents=True, exist_ok=True)
        return self.directory
