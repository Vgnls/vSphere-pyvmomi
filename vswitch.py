from pyVmomi import vim
from prettytable import PrettyTable
from tools.obj_helper import *


def add(si, vswitch_name: str, vnic_name: str, hosts_name: str):
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
            f"Managed object of type [vim.HostSystem] with name '{hosts_name}' not found."
        )

    for host in hosts:
        vswitch_spec = vim.host.VirtualSwitch.Specification()

        vswitch_spec.bridge = vim.host.VirtualSwitch.BondBridge(nicDevice=[vnic_name])
        vswitch_spec.numPorts = 1024
        vswitch_spec.mtu = 1500

        host.configManager.networkSystem.AddVirtualSwitch(vswitch_name, vswitch_spec)

    print(f"Virtual switch {vswitch_name} added successfully with uplink {vnic_name}.")


def delete(si, vswitch_name: str, hosts_name: list):
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
            f"Managed object of type [vim.HostSystem] with name '{hosts_name}' not found."
        )

    for host in hosts:
        host.configManager.networkSystem.RemoveVirtualSwitch(vswitch_name)

    print(f"Virtual switch {vswitch_name} deleted successfully.")


def show(si, hosts_name=None):
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
        hosts = host_view
    container_view.Destroy()

    if hosts is None:
        raise ManagedObjectNotFoundError(
            f"Managed object of type [vim.HostSystem] with name '{hosts_name}' not found."
        )

    host_switches_dict = {}
    for host in hosts:
        switches = host.config.network.vswitch
        host_switches_dict[host] = switches

    if host_switches_dict:
        table = PrettyTable()
        table.field_names = ["Host Name", "vSwitch Name", "Port Groups"]

        for host, vswithes in host_switches_dict.items():
            for vswitch in vswithes:
                portgroups = ", ".join([pg for pg in vswitch.portgroup])
                table.add_row([host.name, vswitch.name, portgroups])

        print("The vSwitches are:\n")
        print(table)
