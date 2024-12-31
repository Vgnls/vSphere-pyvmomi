import re


class ManagedObjectNotFoundError(Exception):
    pass


def get_all_obj(si, vim_type, folder=None, recurse=True):
    content = si.RetrieveContent()

    if not folder:
        folder = content.rootFolder

    container_view = content.viewManager.CreateContainerView(folder, vim_type, recurse)
    objs = list(container_view.view)
    container_view.Destroy()

    if not objs:
        raise ManagedObjectNotFoundError(
            f"No managed objects of type '{vim_type}' found in the specified folder."
        )

    return objs


def get_given_obj(si, vim_type, obj_names: list, folder=None, recurse=True):
    content = si.RetrieveContent()

    if not folder:
        folder = content.rootFolder

    obj = list()
    container_view = content.viewManager.CreateContainerView(folder, vim_type, recurse)
    objs = list(container_view.view)

    for obj_temp in objs:
        if obj_temp.name in obj_names:
            obj.append(obj_temp)

    container_view.Destroy()

    if not obj:
        raise ManagedObjectNotFoundError(
            f"Managed objects of type '{vim_type}' with names {', '.join(obj_names)} not found in the specified folder."
        )

    return obj


def get_matched_obj(si, vim_type, regex: str, folder=None, recurse=True):
    content = si.RetrieveContent()

    if not folder:
        folder = content.rootFolder

    obj = list()
    container_view = content.viewManager.CreateContainerView(folder, vim_type, recurse)
    objs = list(container_view.view)

    for obj_temp in objs:
        if re.findall(r'%s.*' % regex, obj_temp.name):
            obj.append(obj_temp)

    container_view.Destroy()

    if not obj:
        raise ManagedObjectNotFoundError(
            f"No managed objects of type '{vim_type}' matching regex '{regex}' found in the specified folder."
        )

    return obj


def get_single_obj(si, vim_type, obj_name: str, folder=None, recurse=True):
    content = si.RetrieveContent()

    if not folder:
        folder = content.rootFolder

    obj = None
    container_view = content.viewManager.CreateContainerView(folder, vim_type, recurse)
    objs = list(container_view.view)

    for obj_temp in objs:
        if obj_temp.name == obj_name:
            obj = obj_temp
            break

    container_view.Destroy()

    if not obj:
        raise ManagedObjectNotFoundError(
            f"Managed object of type '{vim_type}' with name '{obj_name}' not found in the specified folder."
        )

    return obj
