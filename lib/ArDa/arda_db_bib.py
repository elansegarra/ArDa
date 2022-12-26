from ArDa.arda_db import *

class ArDa_DB_Bib(ArDa_DB):
    """
        This is a subclass of ArDa_DB which implements a back-end
        of ArDa where all data is stored in bib files.    
    """

    def __init__(self):
        self.db_type = "bibtex"

    def make_new_db(self, db_path):
        # Make the folder if it doesn't exist (and check if empty if it does exist)
        if exists(db_path):
            num_files = len([name for name in listdir(db_path) if isfile(join(db_path, name))])
            logging.debug(f"Found {num_files} files in {db_path}.")
            if num_files > 0:
                raise FileExistsError
        else:
            makedirs(db_path)
        self.db_path = db_path

    def parse_bib_file(self, file_path):
        # Reads a bib file and returns a dictionary of the contents
        raise NotImplementedError