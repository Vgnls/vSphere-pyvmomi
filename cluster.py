from pyVmomi import vim
from tools.obj_helper import *
from tools import task
from prettytable import PrettyTable


def add(si, cluster_name, datacenter_name):
    """
    Create a new cluster in a specified datacenter.

    :param si: service instance object connected to vCenter
    :param cluster_name: name of the cluster to be created
    :param datacenter_name: name of the datacenter where the cluster will be created
    :return: none
    """
    content = si.RetrieveContent()

    container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.Datacenter], True)
    datacenters = list(container_view.view)

    datacenter = None
    # locate the datacenter by its name
    for datacenter_temp in datacenters:
        if datacenter_temp.name == datacenter_name:
            datacenter = datacenter_temp
    container_view.Destroy()

    if not datacenter:
        raise ManagedObjectNotFoundError(
            f"Managed object of type '[vim.Datacenter]' with name '{datacenter_name}' not found."
        )

    # create a cluster specification
    cluster_spec = vim.cluster.ConfigSpec()
    # create the cluster within the specified datacenter
    datacenter.hostFolder.CreateCluster(cluster_name, cluster_spec)
    print(f"Cluster {cluster_name} created successfully.")


def delete(si, cluster_name, datacenter_name):
    """
    Delete a specified cluster from a given datacenter.

    :param si: service instance object connected to vCenter
    :param cluster_name: name of the cluster to be deleted
    :param datacenter_name: name of the datacenter containing the cluster
    :return:
    """
    content = si.RetrieveContent()

    container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.Datacenter], True)
    datacenters = list(container_view.view)

    datacenter = None
    # locate the datacenter by its name
    for datacenter_temp in datacenters:
        if datacenter_temp.name == datacenter_name:
            datacenter = datacenter_temp
    container_view.Destroy()

    if not datacenter:
        raise ManagedObjectNotFoundError(
            f"Managed object of type '[vim.Datacenter]' with name '{datacenter_name}' not found."
        )

    container_view = content.viewManager.CreateContainerView(datacenter.hostFolder, [vim.ClusterComputeResource], True)
    clusters = list(container_view.view)

    cluster = None
    # locate the cluster by its name within the datacenter
    for cluster_temp in clusters:
        if cluster_temp.name == cluster_name:
            cluster = cluster_temp
    container_view.Destroy()

    if not cluster:
        raise ManagedObjectNotFoundError(
            f"Managed object of type '[vim.ClusterComputeResource]' with name '{cluster_name}' not found."
        )

    # delete the cluster
    tasks = [cluster.Destroy_Task()]
    task.wait_for_tasks(si, tasks)
    print(f"Cluster {cluster_name} deleted successfully.")


def rename(si, cluster_name, new_name, datacenter_name):
    """
    Rename a cluster in a given datacenter.

    :param si: service instance object connected to vCenter
    :param cluster_name: current name of the cluster to be renamed
    :param new_name: new name for the cluster
    :param datacenter_name: name of the datacenter containing the cluster
    :return: none
    """
    content = si.RetrieveContent()

    container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.Datacenter], True)
    datacenters = list(container_view.view)

    datacenter = None
    # locate the datacenter by its name
    for datacenter_temp in datacenters:
        if datacenter_temp.name == datacenter_name:
            datacenter = datacenter_temp
    container_view.Destroy()

    if not datacenter:
        raise ManagedObjectNotFoundError(
            f"Managed object of type '[vim.Datacenter]' with name '{datacenter_name}' not found."
        )

    container_view = content.viewManager.CreateContainerView(datacenter.hostFolder, [vim.ClusterComputeResource], True)
    clusters = list(container_view.view)

    cluster = None
    # locate the cluster by its name within the datacenter
    for cluster_temp in clusters:
        if cluster_temp.name == cluster_name:
            cluster = cluster_temp
    container_view.Destroy()

    if not cluster:
        raise ManagedObjectNotFoundError(
            f"Managed object of type '[vim.ClusterComputeResource]' with name '{cluster_name}' not found."
        )

    # rename the cluster
    tasks = [cluster.Rename_Task(new_name)]
    task.wait_for_tasks(si, tasks)
    print(f"Cluster {cluster_name} renamed to '{new_name}' successfully.")


def info(si, cluster_name, datacenter_name):
    """
    Display information about a specified cluster in a given datacenter.

    :param si: service instance object connected to vCenter
    :param cluster_name: name of the cluster whose information is to be retrieved
    :param datacenter_name: name of the datacenter containing the cluster
    :return: none
    """
    content = si.RetrieveContent()

    container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.Datacenter], True)
    datacenters = list(container_view.view)

    datacenter = None
    # locate the datacenter by its name
    for datacenter_temp in datacenters:
        if datacenter_temp.name == datacenter_name:
            datacenter = datacenter_temp
    container_view.Destroy()

    if not datacenter:
        raise ManagedObjectNotFoundError(
            f"Managed object of type '[vim.Datacenter]' with name '{datacenter_name}' not found."
        )

    container_view = content.viewManager.CreateContainerView(datacenter.hostFolder, [vim.ClusterComputeResource], True)
    clusters = list(container_view.view)

    cluster = None
    # locate the cluster by its name within the datacenter
    for cluster_temp in clusters:
        if cluster_temp.name == cluster_name:
            cluster = cluster_temp
    container_view.Destroy()

    if not cluster:
        raise ManagedObjectNotFoundError(
            f"Managed object of type '[vim.ClusterComputeResource]' with name '{cluster_name}' not found."
        )

    # create a table to display cluster information
    table = PrettyTable()
    table.field_names = ["Cluster Name", "Total CPU", 'Total memory', 'vMotion number']

    # retrieve cluster summary details
    cpu_num = cluster.summary.totalCpu
    memory_size = cluster.summary.totalMemory
    vmotion_num = cluster.summary.numVmotions

    # add the cluster details to the table
    table.add_row([cluster.name, cpu_num, memory_size, vmotion_num])
    print(f"Cluster with name '{cluster_name}' information:")
    print(table)
