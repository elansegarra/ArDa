from ArDa.arda_db import *

class ArDa_DB_Obsid(ArDa_DB):
    """
        This is a subclass of ArDa_DB which implements a back-end
        of ArDa where all data is stored in obsidian (ie txt) files.    
    """

    def __init__(self):
        self.db_type = "obsidian"
        self.db_path = None

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
    
    def open_db(self, db_path):
        # First execute all commands common across db types
        super().open_db(db_path)

        # Now we read and load the doc info from the obsidian files

    
    def parse_obsid_file(self, file_path):
        # Reads an obsidian file and returns a dictionary of the contents

        # Check if file exists (either as is or relative to db_path)
        if (self.db_path is not None) and (exists(self.db_path+"/"+file_path)):
            file_path = self.db_path+"/"+file_path
        elif (exists(file_path)):   pass
        else:                       raise FileNotFoundError

        # Read the file
        file_contents = {}
        with open(file_path) as f:
            lines = f.readlines()

        # Parse the yml
        assert lines[0].strip() == "---"
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                yml_line_end = i
                break
            line_vals = lines[i].split(":")
            file_contents[line_vals[0].strip()] = line_vals[1].strip()
            if len(line_vals) > 2:
                raise NotImplementedError

        # Parse the rest of the file (break up by headings)
        h_num, h_title, h_body = 0, "No heading", ""
        for i in range(yml_line_end+1, len(lines)):
            line = lines[i]
            if (len(line)>0) and (line[0] == "#"):
                file_contents["note_"+str(h_num)] = {"title": h_title, "body": h_body}
                h_num += 1
                h_title = line[1:]
                h_body = ""
            else:
                h_body += line
        # Storing last group 
        file_contents["note_"+str(h_num)] = {"title": h_title, "body": h_body}

        return file_contents


