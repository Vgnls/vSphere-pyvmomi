from pyVmomi import vim
import re
from prettytable import PrettyTable
from tools.obj_helper import *


def add(si, vswitch_name: str, vnic_name: str, hosts_name: list):
    """
    Add a virtual switch to specified hosts.

    :param si: service instance object connected to vCenter
    :param vswitch_name: name of the virtual switch to be added
    :param vnic_name: name of the virtual NIC to be used as the uplink
    :param hosts_name: list of host names to which the virtual switch will be added
    :return: none
    """
    content = si.RetrieveContent()

    # hosts = get_given_obj(si, [vim.HostSystem], host_name)
    container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
    host_view = list(container_view.view)

    hosts = list()
    for host_temp in host_view:
        # check if the host name matches the provided names
        if host_temp.name in hosts_name:
            hosts.append(host_temp)
    container_view.Destroy()

    # check if no hosts are found
    if hosts is None:
        raise ManagedObjectNotFoundError(
            f"Managed object of type [vim.HostSystem] with name '{', '.join(hosts_name)}' not found."
        )

    for host in hosts:
        # create the virtual switch specification
        vswitch_spec = vim.host.VirtualSwitch.Specification()

        # set the virtual NIC as the uplink
        vswitch_spec.bridge = vim.host.VirtualSwitch.BondBridge(nicDevice=[vnic_name])
        vswitch_spec.numPorts = 1024
        vswitch_spec.mtu = 1500

        # add the virtual switch to the host
        host.configManager.networkSystem.AddVirtualSwitch(vswitch_name, vswitch_spec)

    print(f"Virtual switch {vswitch_name} added successfully with uplink {vnic_name}.")


def delete(si, vswitch_name: str, hosts_name: list):
    """
    Delete a virtual switch from specified hosts.

    :param si: service instance object connected to vCenter
    :param vswitch_name: name of the virtual switch to be deleted
    :param hosts_name: list of host names from which the virtual switch will be deleted
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
        # remove the virtual switch from the host
        host.configManager.networkSystem.RemoveVirtualSwitch(vswitch_name)

    print(f"Virtual switch {vswitch_name} deleted successfully.")


def show(si, hosts_name=None):
    """
    Show the virtual switches on specified hosts.

    :param si: service instance object connected to vCenter
    :param hosts_name: list of host names to show the virtual switches
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

    # create a dictionary to store host-switch relationships
    host_switches_dict = {}
    for host in hosts:
        switches = host.config.network.vswitch
        host_switches_dict[host] = switches

    # if there are switches to display, create a pretty table
    if host_switches_dict:
        table = PrettyTable()
        table.field_names = ["Host Name", "vSwitch Name", "Port Groups"]

        for host, vswithes in host_switches_dict.items():
            for vswitch in vswithes:
                portgroup_names = []
                # extract the port group names
                for portgroup in vswitch.portgroup:
                    match = re.search(r"PortGroup-(.*)", portgroup)
                    portgroup_names.append(match.group(1))

                portgroups = ", ".join(portgroup_names)
                table.add_row([host.name, vswitch.name, portgroups])

        print("The vSwitches are:")
        print(table)
