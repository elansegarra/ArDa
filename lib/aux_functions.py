from PyQt5 import QtGui

# This file houses auxiliary functions used by the main class
def addChildrenOf(parent_proj_id, project_df, ind_txt, proj_id_list,
                    ignore_list = []):
    """
        Returns a list of all descendants of passed id (found recursively)

        :param ignore_list: any id's in this list will be ignored (along with their children)
    """
    child_list = []

    # Select only the children of the current parent
    children = project_df[project_df.parent_id==parent_proj_id]\
                        .sort_values('proj_text')
    # Add each child and any of their children (and their children...)
    for p in range(children.shape[0]):
        child_id = children.iloc[p]['proj_id']
        # Skip any children in the ignore list
        if child_id in ignore_list:
            continue
        # Adding the project text and id
        child_list += [ind_txt+children.iloc[p]['proj_text']]
        proj_id_list += [children.iloc[p]['proj_id']]
        # Getting texts and ids for descendants
        new_child_list, new_proj_id = addChildrenOf(child_id,
                                                    project_df,
                                                    ind_txt+"  ",
                                                    [],
                                                    ignore_list=ignore_list)
        # Adding them to our current lists
        child_list += new_child_list
        proj_id_list += new_proj_id
    return child_list, proj_id_list

def getAuthorLastNames(full_names):
    """
        This function takes a list of full names (or single string) and extracts
        the last names of the authors.

        :param fullnames: Either a list with the form
                    ["lastname, firstname", "lastname2, firstname2", ...]
                    Or a string with the form
                    "lastname, firstname; lastname2, firstname2; ..."

        :return: a list if sent a list and a string if sent a string.
    """
    if type(full_names) == list:
        full_names_list = full_names
    elif type(full_names) == str:
        full_names_list = full_names.split(";")
    else:
        print(f"Unrecognized type ({type(full_names)}) sent to this function."+\
               "Returning the argument.")
        return full_names

    result_list = [x[:x.find(",")].strip() for x in full_names_list]

    if type(full_names) == list:
        return result_list
    elif type(full_names) == str:
        return "; ".join(result_list)
    return result

def autoResizeTextWidget(my_widget, resize_height=True, height_padding=0, resize_width=False, width_padding=0):
    """
        This function will take the passed widget and resize the height and width
        to fit the text within.
        :param my_widget: Widget to be resized (must have a text attribute)
        """
    # text = my_widget.toPlainText()
    # font = my_widget.document().defaultFont()    # or another font if you change it
    # fontMetrics = QtGui.QFontMetrics(font)      # a QFontMetrics based on our font
    # textSize = fontMetrics.size(0, text)
    #
    # textWidth = textSize.width() + 30       # constant may need to be tweaked
    # textHeight = textSize.height() + 30     # constant may need to be tweaked
    #
    # my_widget.setMinimumSize(textWidth, textHeight)  # good if you want to insert this into a layout
    # my_widget.resize(textWidth, textHeight)
    textWidth = my_widget.document().size().width()
    textHeight = my_widget.document().size().height()
    print(f"Resizing to W:{textWidth} and H:{textHeight}")
    #my_widget.resize(textWidth, textHeight)
    #my_widget.setFixedWidth(textWidth + 30)
    my_widget.setFixedHeight(textHeight + 10)
    textWidth = my_widget.document().size().width()
    textHeight = my_widget.document().size().height()
    print(f"After resizing W:{textWidth} and H:{textHeight}")
    #my_widget.updateGeometry()
