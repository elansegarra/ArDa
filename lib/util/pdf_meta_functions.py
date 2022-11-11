import os
import numpy as np
import pdb
from html.parser import HTMLParser

def pdf_to_html(pdf_file_path, html_file_path, first_x_pages = None):
    """
        This function takes a pdf and converts the first x pages into an html file.
        This utilizes the pdf2txt script created by pdfminer

        :param pdf_file_path: str path to the pdf file to be converted
        :param html_file_path: str path to where the output file should be saved
        :param first_x_pages: int indicating how many pages to convert
    """
    # First we specify the options
    options = f"-t html -o {html_file_path}"
    if first_x_pages != None:
        options = options + f" -m {first_x_pages}"
    # Add quotes to the filepaths (after removing any quotes present)
    pdf_file_path = '"'+pdf_file_path.replace('"', '')+'"'
    html_file_path = '"'+html_file_path.replace('"', '')+'"'
    # Now we run the script
    command = f"python lib/util/pdf2txt.py {options} {pdf_file_path}"
    # print(command)
    result = os.system(command)
    if result != 0:
        print(f"Pdf to html conversion failed. Command: {command}")
    return result

class MyHTMLParser(HTMLParser):
    """
        This class parses an html file and saves any tag information with a
        font-size attribute. It also saves the next text data that comes after
        it finds such a tag.
    """
    def __init__(self):
        # Some specific class variables
        self.div_objs = []          # Holds the found data
        self.rec_text = False       # indicates whether to grab the next text data
        self.prev_style_txt = None  # Holds last attr style (to compare tags to be merged)
        super(MyHTMLParser, self).__init__()

    def handle_starttag(self, tag, attrs):
        if (tag == "span") and ("font-size" in attrs[0][1]):
            # Verify that it is a style attribute
            if attrs[0][0] != "style":
                print(f"Non style attribute found ({attrs[0][0]})")
            style_txt = attrs[0][1]
            # Check if the same style as previous block
            if style_txt == self.prev_style_txt:
                # Then don't add another block (instead text will be appended to last one)
                pass
            else:
                # Grab the style attr text and extract the font-size
                self.prev_style_txt = style_txt
                temp = style_txt[style_txt.find("font-size")+10:]
                font_size = temp[:temp.find("px")]
                temp_dict = {'style':style_txt,
                             'font_size':float(font_size),
                             'text': ""}
                # Add this object onto the classes list of objects
                self.div_objs.append(temp_dict)
            # Toggle the record indicator on (so it grabs the next text it finds)
            self.rec_text = True

    def handle_data(self, data):
        # If we should record the next bit of data that comes in
        if self.rec_text:
            # Add the text data to the last div object and toggle off the record
            self.div_objs[-1]["text"] = self.div_objs[-1]["text"] + data
            self.rec_text= False

def extract_title_from_file(file_path, best_x_candidates = 1, search_x_pages = 3,
                            length_min = None):
    """
        This functions will parse an html file (after converting a pdf if need be)
        and return either the best candidate for the title text or a list of the
        best candidates (in order of potential).

        :param file_path: str of the path to the file to be parsed
        :param best_x_candidates: int indicating how many candidates to return
        :param search_x_pages: int indicating how many pages to search (really
                            onlt matters if pdf to html conversion is needed)
        :return: returns a list of str (or None if unsuccessful)
    """
    # First we extract and check what type of file was passed
    file_type = file_path[file_path.rfind("."):]

    if file_type == ".pdf":
        # Convert the pdf file to an html file
        html_file_path = os.getcwd()+"\\temp_file.html"
        res = pdf_to_html(file_path, html_file_path, first_x_pages=search_x_pages)
        # Check if conversion was not successful
        if res != 0:
            print(f"File conversion to html failed: {html_file_path}")
            return None
        else:
            print(f"File successfuly converted to html: {html_file_path}")
        delete_html_file = True
    elif file_type == ".html":
        html_file_path = file_path
        delete_html_file = False
        pass  # No need to do any conversion
    else:
        print(f"Cannot parse the passed file due to it's type: {file_type}")
        return None

    # Open the html file and read all lines
    file = open(html_file_path, encoding='utf-8')
    html_lines = file.readlines()
    file.close()
    html_lines = " ".join(html_lines)

    # Do some cleaning
    html_lines = html_lines.replace("<br>", "")
    html_lines = html_lines.replace("\n", " ")

    # Open the html parser and pass the html text to it
    parser = MyHTMLParser()
    parser.feed(html_lines)

    # Removing some objects that are clearly incorrect
    if length_min != None:
        # Dropping any div objects whose text is not at least above the minimum
        parser.div_objs = [item for item in parser.div_objs if len(item['text'])>=length_min]

    # Extracting the font sizes from the parser (same order they appear)
    font_sizes = np.array([item['font_size'] for item in parser.div_objs])

    # Checking if fewer than "best_x_candidates"
    if len(parser.div_objs) <= best_x_candidates:
        best_div_objs = parser.div_objs
    else:   # Subset to the largest "best_x_candidates" font-size objects
        inds = np.argpartition(font_sizes, -best_x_candidates)[-best_x_candidates:]
        div_objs = np.array(parser.div_objs)
        best_div_objs = list(div_objs[list(inds)].copy())

    # Check whether to delete the html file
    if delete_html_file:
        os.remove(html_file_path)

    # Returning the single text if only the best is to be found
    if best_x_candidates == 1:
        return best_div_objs[0]['text']

    # Sorting by the font size of each div object
    best_div_objs = sorted(best_div_objs, key=lambda k: k['font_size'], reverse=True)
    # print(best_div_objs)

    # Finally extracting the text and returning the results
    best_titles = [" ".join(item['text'].split()) for item in best_div_objs]
    return best_titles
