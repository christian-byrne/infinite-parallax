import os

def check_make_dir(dir_path):
    """
    Checks if the given directory path exists. If it doesn't, creates the directory.

    Args:
        dir_path (str): The path of the directory to check/create.

    Returns:
        bool: True if the directory already exists, False if it was created.
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        return False
    return True