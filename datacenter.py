from pyVmomi import vim
from tools.obj_helper import *
from tools import task
from prettytable import PrettyTable


def add(si, datacenter_name, folder_name=None):
    """
    Create a datacenter with the specified name.

    :param si: service instance object connected to vCenter
    :param datacenter_name: name of the datacenter to create
    :param folder_name: optional name of the folder where the datacenter will be created
    :return: none
    """
    content = si.RetrieveContent()

    if len(datacenter_name) > 80:
        raise ValueError("Datacenter name exceeds the maximum allowed length of 80 characters")

    folder = None
    # locate the folder by name
    if folder_name:
        # folder = get_single_obj(si, [vim.Folder], folder_name)
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

    folder.CreateDatacenter(datacenter_name)
    print(f"Datacenter '{datacenter_name}' created successfully.")


def delete(si, datacenter_name, folder_name=None):
    """
    Delete a datacenter by its name.

    :param si: service instance object connected to vCenter
    :param datacenter_name: name of the datacenter to delete
    :param folder_name: optional name of the folder containing the datacenter
    :return: none
    """
    content = si.RetrieveContent()

    folder = None
    if folder_name:
        # folder = get_single_obj(si, [vim.Folder], folder_name)
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

    # locate the datacenter by name
    container_view = content.viewManager.CreateContainerView(folder, [vim.Datacenter], True)
    datacenters = list(container_view.view)

    datacenter = list()
    for datacenter_temp in datacenters:
        if datacenter_temp.name == datacenter_name:
            datacenter.append(datacenter_temp)
    container_view.Destroy()

    if not datacenter:
        raise ManagedObjectNotFoundError(
            f"Managed object of type '[vim.Datacenter]' with name '{datacenter_name}' not found."
        )

    tasks = list()
    for datacenter_temp in datacenter:
        tasks.append(datacenter_temp.Destroy_Task())

    task.wait_for_tasks(si, tasks)
    print(f"Datacenter '{datacenter_name}' deleted successfully.")


def rename(si, datacenter_name, new_name, folder_name=None):
    """
    Rename a datacenter by new name.

    :param si: service instance object connected to vCenter
    :param datacenter_name: current name of the datacenter
    :param new_name: new name for the datacenter
    :param folder_name: optional name of the folder containing the datacenter
    :return: none
    """
    content = si.RetrieveContent()

    folder = None
    if folder_name:
        # folder = get_single_obj(si, [vim.Folder], folder_name)
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

    # locate the datacenter by name
    container_view = content.viewManager.CreateContainerView(folder, [vim.Datacenter], True)
    datacenters = list(container_view.view)

    datacenter = list()
    for datacenter_temp in datacenters:
        if datacenter_temp.name == datacenter_name:
            datacenter.append(datacenter_temp)
    container_view.Destroy()

    if not datacenter:
        raise ManagedObjectNotFoundError(
            f"Managed object of type '[vim.Datacenter]' with name '{datacenter_name}' not found."
        )

    tasks = list()
    for datacenter_temp in datacenter:
        tasks.append(datacenter_temp.Rename_Task(new_name))

    task.wait_for_tasks(si, tasks)
    print(f"Datacenter '{datacenter_name}' renamed to '{new_name}' successfully.")


def info(si, datacenter_name, folder_name=None):
    """
    Display information about a datacenter.

    :param si: service instance object connected to vCenter
    :param datacenter_name: name of the datacenter
    :param folder_name: optional name of the folder containing the datacenter
    :return: none
    """
    content = si.RetrieveContent()

    folder = None
    if folder_name:
        # folder = get_single_obj(si, [vim.Folder], folder_name)
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

    # locate the datacenter by name
    container_view = content.viewManager.CreateContainerView(folder, [vim.Datacenter], True)
    datacenters = list(container_view.view)

    datacenter = None
    for datacenter_temp in datacenters:
        if datacenter_temp.name == datacenter_name:
            datacenter = datacenter_temp
            break
    container_view.Destroy()

    if not datacenter:
        raise ManagedObjectNotFoundError(
            f"Managed object of type '[vim.Datacenter]' with name '{datacenter_name}' not found."
        )

    table = PrettyTable()
    table.field_names = ["Datacenter Name", "Host number", "Machine number", "Cluster Number", "Network Number",
                         "Datastore number", "Template number"]

    # collect information
    host_num = 0
    cluster_num = 0
    for host in datacenter.hostFolder.childEntity:
        if isinstance(host, vim.ClusterComputeResource):
            cluster_num += 1
        elif isinstance(host, vim.ComputeResource):
            host_num += 1

    machine_num = 0
    template_num = 0
    for vm in datacenter.vmFolder.childEntity:
        if isinstance(vm, vim.VirtualMachine):
            if vm.config.template:
                template_num += 1
            else:
                machine_num += 1

    network_num = len(datacenter.networkFolder.childEntity)
    datastore_num = len(datacenter.datastoreFolder.childEntity)
    table.add_row([datacenter_name, host_num, machine_num, cluster_num, network_num, datastore_num, template_num])

    print(f"Datacenter with name '{datacenter_name}' information:")
    print(table)
