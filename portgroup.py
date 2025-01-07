from pyVmomi import vim
import re
from prettytable import PrettyTable
from tools.obj_helper import *
from tools import task


def add(si, vswitch_name: str, portgroup_name: str, vlan_id: str, hosts_name: list):
    """
    Add a port group to the specified virtual switch on the hosts.

    :param si: service instance object connected to vCenter
    :param vswitch_name: name of the virtual switch to which the port group will be added
    :param portgroup_name: name of the port group to be created
    :param vlan_id: VLAN ID for the port group
    :param hosts_name: list of host names where the port group will be added
    :return: none
    """
    content = si.RetrieveContent()

    # hosts = get_given_obj(si, [vim.HostSystem], host_name)
    container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
    host_view = list(container_view.view)

    hosts = list()
    for host_temp in host_view:
        if host_temp.name in hosts_name:
            hosts.append(host_temp)
    container_view.Destroy()

    if hosts is None:
        raise ManagedObjectNotFoundError(
            f"Managed object of type [vim.HostSystem] with name '{', '.join(hosts_name)}' not found."
        )

    for host in hosts:
        # create the port group specification
        portgroup_spec = vim.host.PortGroup.Specification()

        portgroup_spec.vswitchName = vswitch_name
        portgroup_spec.name = portgroup_name
        portgroup_spec.vlanId = int(vlan_id)

        # set network policy for the port group
        network_policy = vim.host.NetworkPolicy()
        network_policy.security = vim.host.NetworkPolicy.SecurityPolicy()
        network_policy.security.allowPromiscuous = True
        network_policy.security.macChanges = False
        network_policy.security.forgedTransmits = False
        portgroup_spec.policy = network_policy

        # add the port group to the host's network system
        host.configManager.networkSystem.AddPortGroup(portgroup_spec)

    print(f"Virtual switch {vswitch_name} added successfully with port group {portgroup_name}.")


def delete(si, portgroup_name: str, hosts_name: str):
    """
    Delete a port group from the specified hosts.

    :param si: service instance object connected to vCenter
    :param portgroup_name: name of the port group to be deleted
    :param hosts_name: list of host names from which the port group will be removed
    :return: none
    """
    content = si.RetrieveContent()

    # hosts = get_given_obj(si, [vim.HostSystem], host_name)
    container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
    host_view = list(container_view.view)

    hosts = list()
    for host_temp in host_view:
        if host_temp.name in hosts_name:
            hosts.append(host_temp)
    container_view.Destroy()

    if hosts is None:
        raise ManagedObjectNotFoundError(
            f"Managed object of type [vim.HostSystem] with name '{', '.join(hosts_name)}' not found."
        )

    for host in hosts:
        # remove the port group from the host's network system
        host.configManager.networkSystem.RemovePortGroup(portgroup_name)

    print(f"Port group {portgroup_name} deleted successfully.")


def show(si, hosts_name=None):
    """
    Show the port groups on specified hosts.

    :param si: service instance object connected to vCenter
    :param hosts_name: list of host names to show the port groups
    :return: none
    """
    content = si.RetrieveContent()

    container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
    host_view = list(container_view.view)

    hosts = list()
    if hosts_name:
        # hosts = get_given_obj(si, [vim.HostSystem], host_name)
        for host_temp in host_view:
            if host_temp.name in hosts_name:
                hosts.append(host_temp)
    else:
        # hosts = get_all_obj(si, [vim.HostSystem])
        # if no host names are provided, show all hosts
        hosts = host_view
    container_view.Destroy()

    if hosts is None:
        raise ManagedObjectNotFoundError(
            f"Managed object of type [vim.HostSystem] with name '{', '.join(hosts_name)}' not found."
        )

    # create a dictionary to hold host-port group relationships
    host_port_groups_dict = {}
    for host in hosts:
        port_groups = host.config.network.portgroup
        host_port_groups_dict[host] = port_groups

    # if there are port groups to display, create a pretty table
    if host_port_groups_dict:
        table = PrettyTable()
        table.field_names = ["Host Name", "Port Group", "Vlan ID", "vSwitch Name"]

        for host, port_groups in host_port_groups_dict.items():
            for port_group in port_groups:
                portgroup_name = port_group.spec.name
                vswitch = port_group.spec.vswitchName
                vlan_id = port_group.spec.vlanId
                table.add_row([host.name, portgroup_name, vlan_id, vswitch])

        print("The port groups are:")
        print(table)


def rename(si, portgroup_name, new_name, host_name):
    """
    Rename a port group on a specified host in vCenter.

    :param si: service instance connected to vCenter
    :param portgroup_name: name of the existing port group
    :param new_name: new name for the port group
    :param host_name: name of the host containing the port group
    :return: none
    """
    content = si.RetrieveContent()

    container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
    host_view = list(container_view.view)

    host = None
    if host_name:
        # host = get_given_obj(si, [vim.HostSystem], host_name)
        for host_temp in host_view:
            if host_temp.name == host_name:
                host = host_temp
    else:
        # host = get_all_obj(si, [vim.HostSystem])
        # if no host names are provided, show all host
        host = host_view
    container_view.Destroy()

    if host is None:
        raise ManagedObjectNotFoundError(
            f"Managed object of type [vim.HostSystem] with name '{', '.join(host_name)}' not found."
        )

    port_group = None
    # find the specified port group on the host
    for pgroup in host.configManager.networkSystem.networkConfig.portgroup:
        if pgroup.spec.name == portgroup_name:
            port_group = pgroup
            break

    if not port_group:
        raise ManagedObjectNotFoundError(
            f"Port group '{portgroup_name}' not found on host '{host_name}'."
        )

    # prepare a new port group specification
    portgroup_spec = vim.host.PortGroup.Specification()

    portgroup_spec.vswitchName = port_group.spec.vswitchName
    portgroup_spec.name = new_name
    # ensure VLAN ID is an integer
    portgroup_spec.vlanId = int(port_group.spec.vlanId)

    # copy network policies
    network_policy = vim.host.NetworkPolicy()
    network_policy.security = vim.host.NetworkPolicy.SecurityPolicy()
    network_policy.security.allowPromiscuous = port_group.spec.policy.security.allowPromiscuous
    network_policy.security.macChanges = port_group.spec.policy.security.macChanges
    network_policy.security.forgedTransmits = port_group.spec.policy.security.forgedTransmits
    portgroup_spec.policy = network_policy

    # update the port group on the host
    host.configManager.networkSystem.UpdatePortGroup(portgroup_name, portgroup_spec)
    print(f"Port group {portgroup_name} renamed to '{new_name}' successfully.")
