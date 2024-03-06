
def update_path_parts(dict_to_update: dict, path: str) -> None:
    print(f"inpute path: {path}")
    new_properties = {
        "filname": path.split("/")[-1],
        "basename": ".".join(path.split("/")[-1].split(".")[:-1]),
        "ext": path.split("/")[-1].split(".")[-1],
        "path": "/".join(path.split("/")[:-1]),
        "fullpath": path,
    }
    print(f"new_properties: {new_properties}")
    dict_to_update.update(new_properties)
    