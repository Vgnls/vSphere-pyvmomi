from pyVmomi import vim
from tools.obj_helper import *
from tools import task
from prettytable import PrettyTable


def info(si, datastore_name, datacenter_name):
    """
    Display information about a specific datastore in a datacenter.

    :param si: service instance object connected to vCenter
    :param datastore_name: name of the datastore
    :param datacenter_name: name of the datacenter containing the datastore
    :return: none
    """
    content = si.RetrieveContent()

    # locate the datacenter by name
    container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.Datacenter], True)
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

    datastore = None
    # locate the datastore by name
    datastores = datacenter.datastore
    for datastore_temp in datastores:
        if datastore_temp.name == datastore_name:
            datastore = datastore_temp
            break

    if not datastore:
        raise ManagedObjectNotFoundError(
            f"Managed object of type '[vim.Datastore]' with name '{datastore_name}' not found in datacenter"
            f" '{datacenter_name}'."
        )

    table = PrettyTable()
    table.field_names = ["Datacenter Name", "Host number", "Machine number", "Cluster Number", "Network Number",
                         "Datastore number", "Template number"]

    # retrieve datastore details
    datastore_type = datastore.info.vmfs.type + " " + str(datastore.info.vmfs.majorVersion)
    host_num = len(datastore.host)
    location = datastore.info.url

    machine_num = 0
    template_num = 0
    for vm in datastore.vm:
        if isinstance(vm, vim.VirtualMachine):
            if vm.config.template:
                template_num += 1
            else:
                machine_num += 1

    free_space = '%.2f' % (datastore.info.freeSpace / (1024 ** 3))
    capacity = '%.2f' % (datastore.info.vmfs.capacity / (1024 ** 3))
    usage = '%.2f' % ((datastore.info.vmfs.capacity - datastore.info.freeSpace) / (1024 ** 3))

    # create and display tables
    info_table = PrettyTable()
    info_table.field_names = ["Datastore Name", "Type", "Host number", "VM number", "Template Number", "Location"]
    info_table.add_row([datastore_name, datastore_type, host_num, machine_num, template_num, location])

    space_table = PrettyTable()
    space_table.field_names = ["Free Space", "Used Space", "Capacity"]
    space_table.add_row([free_space + " GB", usage + " GB", capacity + " GB"])

    print(f"Datastore with name '{datastore_name}' information:")
    print(info_table)
    print("\nSpace usage:")
    print(space_table)
