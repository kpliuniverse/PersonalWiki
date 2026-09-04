import pkgutil


def get_data_and_raise_if_none(package, resource):
    """
        same as pkgutil.get_data, except if None, raises a FileNotFoundError
    """
    data = pkgutil.get_data(package, resource)

    if data is None:
        raise FileNotFoundError(f"Error getting data: likely {resource} from {package} not found")

    return data