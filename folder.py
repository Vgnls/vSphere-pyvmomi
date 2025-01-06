from pyVmomi import vim
from tools.obj_helper import *
from tools import task
from prettytable import PrettyTable
from tools.folder_helper import *


def add_to_folder(si, folder_name, parent_name=None):
    """
    Create a new folder under the specified parent folder or root.

    :param si: service instance object connected to vCenter
    :param folder_name: name of the folder to be created
    :param parent_name: name of the parent folder
    :return: none
    """
    content = si.RetrieveContent()

    parent = None
    # locate the parent folder or use the root folder
    if parent_name:
        # parent = get_single_obj(si, [vim.Folder], parent_name)
        container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.Folder], True)
        parents = list(container_view.view)

        for parent_temp in parents:
            if parent_temp.name == parent_name:
                parent = parent_temp
                break
        container_view.Destroy()

        if not parent:
            raise ManagedObjectNotFoundError(
                f"Managed object of type '[vim.Folder]' with name '{parent_name}' not found."
            )
    else:
        parent = content.rootFolder

    # create the new folder
    parent.CreateFolder(folder_name)
    print(f"Folder '{folder_name}' created successfully under '{parent_name}'.")


def add_to_datacenter(si, folder_name, folder_type, datacenter_name):
    """
    Create a new folder of the specified type in a datacenter.

    :param si: service instance object connected to vCenter
    :param folder_name: name of the folder to be created
    :param folder_type: type of the folder ('hostFolder', 'networkFolder', 'datastoreFolder', 'vmFolder')
    :param datacenter_name: name of the datacenter containing the folder
    :return: none
    """
    content = si.RetrieveContent()

    datacenter = None
    # locate the datacenter by name
    # datacenter = get_single_obj(si, [vim.Datacenter], datacenter_name)
    container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.Datacenter], True)
    datacenters = list(container_view.view)

    for datacenter_temp in datacenters:
        if datacenter_temp.name == datacenter_name:
            datacenter = datacenter_temp
            break
    container_view.Destroy()

    if not datacenter:
        raise ManagedObjectNotFoundError(
            f"Managed object of type '[vim.Datacenter]' with name '{datacenter_name}' not found."
        )

    # get the appropriate folder type
    folder_mapping = {
        'hostFolder': datacenter.hostFolder,
        'networkFolder': datacenter.networkFolder,
        'datastoreFolder': datacenter.datastoreFolder,
        'vmFolder': datacenter.vmFolder,
    }

    parent = folder_mapping.get(folder_type)
    if not parent:
        raise ValueError(f"Invalid folder type: '{folder_type}'.")

    # create the folder
    parent.CreateFolder(folder_name)
    print(f"Folder '{folder_name}' created successfully in '{folder_type}' of datacenter '{datacenter_name}'.")


def delete_from_folder(si, folder_name, parent_name=None):
    """
    Delete a folder under the specified parent folder or root.

    :param si: service instance object connected to vCenter
    :param folder_name: name of the folder to be deleted
    :param parent_name: name of the parent folder
    :return: none
    """
    content = si.RetrieveContent()

    parent = None
    # locate the parent folder or use the root folder
    if parent_name:
        # parent = get_single_obj(si, [vim.Folder], parent_name)
        container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.Folder], True)
        parents = list(container_view.view)

        for parent_temp in parents:
            if parent_temp.name == parent_name:
                parent = parent_temp
                break
        container_view.Destroy()

        if not parent:
            raise ManagedObjectNotFoundError(
                f"Managed object of type '[vim.Folder]' with name '{parent_name}' not found."
            )
    else:
        parent = content.rootFolder

    tasks = list()
    # locate and delete the folder
    for child in parent.childEntity:
        if isinstance(child, vim.Folder) and child.name == folder_name:
            tasks.append(child.Destroy_Task())

    if not tasks:
        raise ManagedObjectNotFoundError(
            f"Folder '{folder_name}' not found under '{parent_name}'."
        )

    task.wait_for_tasks(si, tasks)
    print(f"Folder '{folder_name}' deleted successfully from '{parent.name}'.")


def delete_from_datacenter(si, folder_name, folder_type, datacenter_name):
    """
    Delete a folder of the specified type from a datacenter.

    :param si: service instance object connected to vCenter
    :param folder_name: name of the folder to be deleted
    :param folder_type: type of the folder ('hostFolder', 'networkFolder', 'datastoreFolder', 'vmFolder')
    :param datacenter_name: name of the datacenter containing the folder
    :return: none
    """
    content = si.RetrieveContent()

    datacenter = None
    # locate the datacenter by name
    # datacenter = get_single_obj(si, [vim.Datacenter], datacenter_name)
    container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.Datacenter], True)
    datacenters = list(container_view.view)

    for datacenter_temp in datacenters:
        if datacenter_temp.name == datacenter_name:
            datacenter = datacenter_temp
            break
    container_view.Destroy()

    if not datacenter:
        raise ManagedObjectNotFoundError(
            f"Managed object of type '[vim.Datacenter]' with name '{datacenter_name}' not found."
        )

    # get the appropriate folder type
    folder_mapping = {
        'hostFolder': datacenter.hostFolder,
        'networkFolder': datacenter.networkFolder,
        'datastoreFolder': datacenter.datastoreFolder,
        'vmFolder': datacenter.vmFolder,
    }
    parent = folder_mapping.get(folder_type)

    if not parent:
        raise ValueError(f"Invalid folder type: '{folder_type}'.")

    # locate and delete the folder
    tasks = list()
    for child in parent.childEntity:
        if isinstance(child, vim.Folder) and child.name == folder_name:
            tasks.append(child.Destroy_Task())

    if not tasks:
        raise ManagedObjectNotFoundError(
            f"Folder '{folder_name}' not found in '{folder_type}' of datacenter '{datacenter_name}'."
        )

    task.wait_for_tasks(si, tasks)
    print(f"Folder '{folder_name}' deleted successfully from '{folder_type}' in datacenter '{datacenter_name}'.")


def info(si, folder_name, folder_type='dataFolder'):
    """
    Display information about a specified folder type in vCenter.

    :param si: the service instance connected to vCenter
    :param folder_name: the name of the folder to locate and analyze
    :param folder_type: the type of the folder
    :return: none
    """
    content = si.RetrieveContent()

    folder = None
    if folder_name:
        container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.Folder], True)
        folders = list(container_view.view)

        for folder_temp in folders:
            if folder_temp.name == folder_name and repr(folder_temp)[18] == get_folder_mapping(folder_type):
                folder = folder_temp
                break
        container_view.Destroy()

        if not folder:
            raise ManagedObjectNotFoundError(
                f"Managed object of type '[vim.Folder]' with name '{folder_name}' not found."
            )
    else:
        # default to the root folder if no name is provided
        folder = content.rootFolder

    # select the appropriate display function based on folder type
    display_functions = {
        'dataFolder': display_data_folder,
        'hostFolder': display_host_folder,
        'vmFolder': display_vm_folder,
        'datastoreFolder': display_datastore_folder,
        'networkFolder': display_network_folder,
    }

    display_function = display_functions.get(folder_type)
    if not display_function:
        raise ValueError(f"Invalid folder type: '{folder_type}'.")

    print(f"Folder '{folder_name}' information:")
    display_function(folder)


def rename(si, folder_name, new_name):
    content = si.RetrieveContent()

    folder = None
    # locate the folder folder or use the root folder
    if folder_name:
        # folder = get_single_obj(si, [vim.Folder], parent_name)
        container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.Folder], True)
        folders = list(container_view.view)

        for folder_temp in folders:
            if folder_temp.name == folder_name:
                folder = folder_temp
                break
        container_view.Destroy()

        if not folder:
            raise ManagedObjectNotFoundError(
                f"Managed object of type '[vim.Folder]' with name '{folder_name}' not found."
            )
    else:
        folder = content.rootFolder

    # locate and rename the folder
    tasks = [folder.Rename_Task(new_name)]
    task.wait_for_tasks(si, tasks)
    print(f"Folder '{folder_name}' renamed to '{new_name}' successfully.")
