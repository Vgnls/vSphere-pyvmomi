from pyVmomi import vim
from prettytable import PrettyTable


def get_folder_mapping(folder_type):
    """
    Return the mapping character for the given folder type.

    :param folder_type: the type of the folder (e.g., 'dataFolder', 'hostFolder', etc.)
    :return: a single-character identifier for the folder type
    """
    folder_mapping = {
        'dataFolder': 'd',
        'hostFolder': 'h',
        'networkFolder': 'n',
        'datastoreFolder': 's',
        'vmFolder': 'v',
    }

    return folder_mapping[folder_type]


def display_data_folder(folder):
    """
    Display information about a data folder, including the number of datacenters it contains.

    :param folder: the folder object to analyze
    :return: none
    """
    table = PrettyTable()
    table.field_names = ['Name', 'Datacenter number']

    datacenter_num = 0
    # count the number of datacenters in the folder
    for child in folder.childEntity:
        if isinstance(child, vim.Datacenter):
            datacenter_num += 1

    table.add_row([folder.name, datacenter_num])
    print(table)


def display_host_folder(folder):
    """
    Display information about a host folder, including the number of clusters, hosts, and VMs.

    :param folder: the folder object to analyze
    :return: none
    """
    table = PrettyTable()
    table.field_names = ['Name', 'Cluster number', 'Host number', 'VM number']

    cluster_num = 0
    host_num = 0
    vm_num = 0

    # iterate through child entities to count clusters, hosts, and VMs
    for child in folder.childEntity:
        if isinstance(child, (vim.ComputeResource, vim.ClusterComputeResource)):
            cluster_num += 1
            for host in child.host:
                host_num += 1
                for vm in host.vm:
                    if not vm.config.template:
                        vm_num += 1

    table.add_row([folder.name, cluster_num, host_num, vm_num])
    print(table)


def display_vm_folder(folder):
    """
    Display information about a VM folder, including the number of VMs and templates.

    :param folder: the folder object to analyze
    :return: none
    """
    table = PrettyTable()
    table.field_names = ['Name', 'VM number', 'Template number']

    vm_num = 0
    template_num = 0
    # count the number of VMs and templates in the folder
    for child in folder.childEntity:
        if isinstance(child, vim.VirtualMachine):
            if child.config.template:
                template_num += 1
            else:
                vm_num += 1

    table.add_row([folder.name, vm_num, template_num])
    print(table)


def display_datastore_folder(folder):
    """
    Display information about a datastore folder, including the number of datastores and datastore clusters.

    :param folder: the folder object to analyze
    :return: none
    """
    table = PrettyTable()
    table.field_names = ['Name', 'Datastore number', 'Datastore cluster number']

    datastore_num = 0
    datastore_cluster_num = 0
    # count datastores and datastore clusters
    for child in folder.childEntity:
        if isinstance(child, vim.Datastore):
            datastore_num += 1
        elif isinstance(child, vim.StoragePod):
            datastore_cluster_num += 1

    table.add_row([folder.name, datastore_num, datastore_cluster_num])
    print(table)


def display_network_folder(folder):
    """
    Display information about a network folder, including the number of networks and distributed switches.

    :param folder: the folder object to analyze
    :return: none
    """
    table = PrettyTable()
    table.field_names = ['Name', 'Network number', 'Distributed switch number']

    network_num = 0
    dswitch_num = 0
    # count networks and distributed switches
    for child in folder.childEntity:
        if isinstance(child, vim.Network):
            network_num += 1
        elif isinstance(child, vim.dvs.VmwareDistributedVirtualSwitch):
            dswitch_num += 1

    table.add_row([folder.name, network_num, dswitch_num])
    print(table)
