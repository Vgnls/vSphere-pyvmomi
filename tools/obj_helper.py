import re


class ManagedObjectNotFoundError(Exception):
    """
    Raised when a managed object is not found.
    """
    pass


def get_all_obj(si, vim_type, folder=None, recurse=True):
    """
    Retrieves all managed objects of a specified type from vSphere.

    :param si: service instance object connected to vCenter
    :param vim_type: the type of managed object to retrieve
    :param folder: the folder to start the search from
    :param recurse: whether to search recursively
    :return: a list of managed objects of the specified type
    """
    content = si.RetrieveContent()

    # the root folder if no folder is specified
    if not folder:
        folder = content.rootFolder

    # create a container view to retrieve objects of the specified type
    container_view = content.viewManager.CreateContainerView(folder, vim_type, recurse)
    objs = list(container_view.view)

    # destroy the container view after use
    container_view.Destroy()

    # Raise an exception if no objects are found
    if not objs:
        raise ManagedObjectNotFoundError(
            f"No managed objects of type '{vim_type}' found."
        )

    return objs


def get_given_obj(si, vim_type, obj_names, folder=None, recurse=True):
    """
    Retrieves specific managed objects by name.

    :param si: service instance object connected to vCenter
    :param vim_type: the type of managed object to retrieve
    :param obj_names: list of object names to retrieve
    :param folder: the folder to start the search from
    :param recurse: whether to search recursively
    :return: a list of managed objects matching the specified names
    """
    content = si.RetrieveContent()

    # the root folder if no folder is specified
    if not folder:
        folder = content.rootFolder

    container_view = content.viewManager.CreateContainerView(folder, vim_type, recurse)
    objs = list(container_view.view)

    matched_objs = []
    for obj in objs:
        if obj.name in obj_names:
            matched_objs.append(obj)

    container_view.Destroy()

    if not matched_objs:
        raise ManagedObjectNotFoundError(
            f"Managed objects of type '{vim_type}' with names {', '.join(obj_names)} not found."
        )

    return matched_objs


def get_matched_obj(si, vim_type, regex, folder=None, recurse=True):
    """
    Retrieves managed objects whose names match a regex pattern.

    :param si: service instance object connected to vCenter
    :param vim_type: the type of managed object to retrieve
    :param regex: the regex pattern to match object names
    :param folder: the folder to start the search from
    :param recurse: whether to search recursively
    :return: a list of managed objects matching the regex pattern
    """
    content = si.RetrieveContent()

    # the root folder if no folder is specified
    if not folder:
        folder = content.rootFolder

    container_view = content.viewManager.CreateContainerView(folder, vim_type, recurse)
    objs = list(container_view.view)

    matched_objs = []
    for obj in objs:
        if re.match(regex, obj.name):
            matched_objs.append(obj)

    container_view.Destroy()

    if not matched_objs:
        raise ManagedObjectNotFoundError(
            f"No managed objects of type '{vim_type}' matching regex '{regex}' found."
        )

    return matched_objs


def get_single_obj(si, vim_type, obj_name, folder=None, recurse=True):
    """
    Retrieves a single managed object by name.

    :param si: service instance object connected to vCenter
    :param vim_type: the type of managed object to retrieve
    :param obj_name: name of the object to retrieve
    :param folder: the folder to start the search from
    :param recurse: whether to search recursively
    :return: the managed object matching the specified name
    """
    content = si.RetrieveContent()

    # the root folder if no folder is specified
    if not folder:
        folder = content.rootFolder

    container_view = content.viewManager.CreateContainerView(folder, vim_type, recurse)
    objs = list(container_view.view)
    obj = None

    for obj_temp in objs:
        if obj_temp.name == obj_name:
            obj = obj_temp
            break

    container_view.Destroy()

    if not obj:
        raise ManagedObjectNotFoundError(
            f"Managed object of type '{vim_type}' with name '{obj_name}' not found."
        )

    return obj
