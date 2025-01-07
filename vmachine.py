from pyVmomi import vim
import re
from prettytable import PrettyTable
from tools.obj_helper import *
from tools.power_helper import *
from tools import task
from tools.vm_helper import *


def power_on(si, folder_name, vm_names=None, regex=None):
    """
    Power on specified virtual machines.

    :param si: service instance object connected to vCenter
    :param folder_name: name of the folder containing virtual machines
    :param vm_names: list of virtual machine names to power on
    :param regex: regular expression to match virtual machine names
    :return: none
    """
    if vm_names:
        # get virtual machines to power on using exact names
        action_vms = power_state(si, folder_name, 'On', vm_names=vm_names)
    elif regex:
        # get virtual machines to power on using regex
        action_vms = power_state_regex(si, folder_name, 'On', regex=regex)
    else:
        raise ValueError(f"No virtual machine specified to power on.")

    if action_vms:
        # create and execute power-on tasks
        task_list = [vm.PowerOn() for vm in action_vms]
        task.wait_for_tasks(si, task_list)

        print(f"Virtual machines {', '.join(vm.name for vm in action_vms)} powered on successfully")
    else:
        print("Specified virtual machines could not be powered on.")


def power_off(si, folder_name, vm_names=None, regex=None):
    """
    Power off specified virtual machines.

    :param si: service instance object connected to vCenter
    :param folder_name: name of the folder containing virtual machines
    :param vm_names: list of virtual machine names to power off
    :param regex: regular expression to match virtual machine names
    :return: none
    """
    if vm_names:
        # get virtual machines to power off using exact names
        action_vms = power_state(si, folder_name, 'Off', vm_names=vm_names)
    elif regex:
        # get virtual machines to power off using regex
        action_vms = power_state_regex(si, folder_name, 'Off', regex=regex)
    else:
        raise ValueError(f"No virtual machine specified to power off.")

    if action_vms:
        # create and execute power-off tasks
        task_list = [vm.PowerOff() for vm in action_vms]
        task.wait_for_tasks(si, task_list)

        print(f"Virtual machines {', '.join(vm.name for vm in action_vms)} powered off successfully.")
    else:
        print("Specified virtual machines could not be powered off.")


def suspend(si, folder_name, vm_names=None, regex=None):
    """
    Suspend specified virtual machines.

    :param si: service instance object connected to vCenter
    :param folder_name: name of the folder containing virtual machines
    :param vm_names: list of virtual machine names to suspend
    :param regex: regular expression to match virtual machine names
    :return: none
    """
    if vm_names:
        action_vms = power_state(si, folder_name, 'Suspend', vm_names=vm_names)
    elif regex:
        action_vms = power_state_regex(si, folder_name, 'Suspend', regex=regex)
    else:
        raise ValueError(f"No virtual machine specified to suspend")

    if action_vms:
        task_list = [vm.Suspend() for vm in action_vms]
        task.wait_for_tasks(si, task_list)

        print(f"Virtual machines {', '.join(vm.name for vm in action_vms)} suspended successfully.")
    else:
        print("Specified virtual machines could not be suspended.")


def reboot(si, folder_name, vm_names=None, regex=None):
    """
    Reboot specified virtual machines.

    :param si: service instance object connected to vCenter
    :param folder_name: name of the folder containing virtual machines
    :param vm_names: list of virtual machine names to reboot
    :param regex: regular expression to match virtual machine names
    :return: none
    """
    if vm_names:
        action_vms = power_state(si, folder_name, 'Reboot', vm_names=vm_names)
    elif regex:
        action_vms = power_state_regex(si, folder_name, 'Reboot', regex=regex)
    else:
        raise ValueError(f"No virtual machine specified to reboot.")

    if action_vms:
        task_list = [vm.Reset() for vm in action_vms]
        task.wait_for_tasks(si, task_list)

        print(f"Virtual machines {', '.join(vm.name for vm in action_vms)} rebooted successfully.")
    else:
        print("Specified virtual machines could not be rebooted.")


def destroy(si, folder_name, vm_names=None, regex=None):
    """
    Destroy specified virtual machines.

    :param si: service instance object connected to vCenter
    :param folder_name: name of the folder containing virtual machines
    :param vm_names: list of virtual machine names to destroy
    :param regex: regular expression to match virtual machine names
    :return: none
    """
    if vm_names:
        action_vms = power_state(si, folder_name, 'Destroy', vm_names=vm_names)
    elif regex:
        action_vms = power_state_regex(si, folder_name, 'Destroy', regex=regex)
    else:
        raise ValueError(f"No virtual machine specified to destroy.")

    action_names = [vm.name for vm in action_vms]

    # power off virtual machines if necessary
    power_list = list()
    for vm in action_vms:
        if vm.summary.runtime.powerState == "poweredOn":
            power_list.append(vm)

    if power_list:
        task_list = [vm.PowerOff() for vm in power_list]
        task.wait_for_tasks(si, task_list)
        print(f"Powered off virtual machines: {', '.join(vm.name for vm in power_list)}.")

    # destroy the specified virtual machines
    task_list = [vm.Destroy() for vm in action_vms]
    task.wait_for_tasks(si, task_list)
    print(f"Virtual machines: {', '.join(action_names)} destroyed successfully.")


def rename(si, vm_name, new_name, folder_name=None):
    """
    Rename a virtual machine.

    :param si: service instance object connected to vCenter
    :param vm_name: the current name of the VM to be renamed
    :param new_name: the new name to assign to the VM
    :param folder_name: the folder name containing the VM
    :return:
    """
    content = si.RetrieveContent()

    # locate the specified folder
    folder = None
    if not folder_name:
        folder = content.rootFolder
    else:
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

    # locate the virtual machine by its name in the specified folder
    # vms = get_all_obj(si, [vim.VirtualMachine], folder_name)
    container_view = content.viewManager.CreateContainerView(folder, [vim.VirtualMachine], True)
    vms = list(container_view.view)

    vm = None
    for vm_temp in vms:
        # exclude templates from the search
        if vm_temp.name == vm_name and not vm_temp.summary.config.template:
            vm = vm_temp
            break
    container_view.Destroy()

    if not vm:
        raise ManagedObjectNotFoundError(
            f"Managed object of type '[vim.VirtualMachine]' with name '{vm_name}' not found."
        )

    # initiate the rename task for the virtual machine
    tasks = [vm.Rename_Task(new_name)]
    task.wait_for_tasks(si, tasks)
    print(f"Virtual machine '{vm_name}' renamed to '{new_name}' successfully.")


def show(si, folder_name=None):
    """
    Display brief information about virtual machines in a folder.

    :param si: service instance object connected to vCenter
    :param folder_name: name of the folder containing virtual machines
    :return: none
    """
    content = si.RetrieveContent()

    # locate the specified folder
    folder = None
    if not folder_name:
        folder = content.rootFolder
    else:
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

    # vms = get_all_obj(si, [vim.VirtualMachine], folder_name)
    container_view = content.viewManager.CreateContainerView(folder, [vim.VirtualMachine], True)
    vms = list(container_view.view)
    container_view.Destroy()

    if not vms:
        raise ManagedObjectNotFoundError(
            f"No managed objects of type '[vim.VirtualMachine]' found."
        )

    # display virtual machine details
    vm_count = 0
    table = PrettyTable()
    table.field_names = ['Name', 'Power State', 'Connection State', 'VMware Tools', 'Disk space', 'CPU Number',
                         'Memory']

    for vm in vms:
        if vm.summary.config.template:
            continue

        vm_count += 1
        vm_name = vm.config.name
        vm_power_state = vm.runtime.powerState
        vm_connection_state = vm.runtime.connectionState
        vm_tools = vm.guest.toolsStatus

        disk_space = vm.storage.perDatastoreUsage[0].committed + vm.storage.perDatastoreUsage[0].uncommitted
        vm_storage = '%.2f' % (disk_space / (1024 ** 3))

        vm_cpu = vm.config.hardware.numCPU
        vm_memory = vm.config.hardware.memoryMB / 1024

        table.add_row([vm_name, vm_power_state, vm_connection_state, vm_tools, str(vm_storage) + ' GB', vm_cpu,
                       str(vm_memory) + 'GB'])

    print(f"The Virtual Machines are: {vm_count}")
    print(table)


def info(si, vm_name, folder_name=None):
    """
    Display detailed information of a virtual machine.

    :param si: service instance object connected to vCenter
    :param vm_name: name of the virtual machine
    :param folder_name: name of the folder containing the virtual machine
    :return: none
    """
    content = si.RetrieveContent()

    # locate the specified folder
    folder = None
    if not folder_name:
        folder = content.rootFolder
    else:
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

    # locate the virtual machine by its name in the specified folder
    # vms = get_all_obj(si, [vim.VirtualMachine], folder_name)
    container_view = content.viewManager.CreateContainerView(folder, [vim.VirtualMachine], True)
    vms = list(container_view.view)

    vm = None
    for vm_temp in vms:
        # exclude templates from the search
        if vm_temp.name == vm_name and not vm_temp.summary.config.template:
            vm = vm_temp
            break
    container_view.Destroy()

    if not vm:
        raise ManagedObjectNotFoundError(
            f"Managed object of type '[vim.VirtualMachine]' with name '{vm_name}' not found."
        )

    # gather virtual machine details
    vm_power_state = vm.runtime.powerState
    vm_os = vm.config.guestFullName
    vm_hostname = vm.guest.hostName
    vm_ip = vm.guest.ipAddress

    # gather resource usage information
    cpu_usage = vm.summary.quickStats.overallCpuUsage  # CPU usage in MHz
    cpu_num = vm.config.hardware.numCPU
    memory_usage = vm.summary.quickStats.guestMemoryUsage  # memory usage in MB
    memory_space = vm.config.hardware.memoryMB / 1024  # total memory in GB
    disk_usage = vm.storage.perDatastoreUsage[0].committed
    disk_space = disk_usage + vm.storage.perDatastoreUsage[0].uncommitted
    vm_disk_usage = '%.2f' % (disk_usage / (1024 ** 3))  # used disk space in GB
    vm_disk_space = '%.2f' % (disk_space / (1024 ** 3))  # total disk space in GB

    # gather additional information about network adapters
    vm_adapter = dict()
    vm_net = vm.guest.net
    for vm_network in vm_net:
        vm_adapter[vm_network.network] = {'ip': vm_network.ipAddress[0], 'mac': vm_network.macAddress}
    vm_version = vm.guest.hwVersion  # virtual machine version

    # table 1: basic information
    basic_table = PrettyTable()
    basic_table.field_names = ["VM Name", "Power State", "Operating System", "Hostname", "IP Address"]
    basic_table.add_row([vm_name, vm_power_state, vm_os, vm_hostname, vm_ip])

    # table 2: resource usage details
    resource_table = PrettyTable()
    resource_table.field_names = ["CPU Usage", "Memory Usage", "Disk Usage"]
    resource_table.add_row([str(cpu_usage) + " MHz", str(memory_usage) + " MB", str(vm_disk_usage) + " GB"])

    # table 3: dynamic hardware table
    hardware_table = PrettyTable()

    # base fields for hardware information
    base_fields = ["CPU Number", "Memory", "Disk space"]
    adapter_fields = [f"Network adapter {i + 1}" for i in range(len(vm_adapter))]  # dynamic fields for adapters
    version_fields = ["Virtual machine version"]

    # combine base fields with adapter fields
    hardware_table.field_names = base_fields + adapter_fields + version_fields

    # prepare the row data
    row_data = [cpu_num, str(memory_space) + " GB", str(vm_disk_space) + " GB"]
    for name, address in vm_adapter.items():
        adapter_info = (f"{name} | "
                        f"{address['ip']} | "
                        f"{address['mac']}")
        row_data.append(adapter_info)
    row_data.append(vm_version)

    # fill the table
    hardware_table.add_row(row_data)

    # Print the results
    print("Virtual Machine Basic Information:")
    print(basic_table)
    print("\nVirtual Machine Resource Usage:")
    print(resource_table)
    print("\nVirtual Machine Additional Information:")
    print(hardware_table)


def clone(si, vm_name, template_name, datacenter_name=None, folder_name=None, datastore_name=None, cluster_name=None,
          resource_pool_name=None, esxi_name=None, power_on=False):
    """
    clone a virtual machine from a template.

    :param si: service instance object connected to vCenter
    :param vm_name: name of the new virtual machine
    :param template_name: name of the template to clone from
    :param datacenter_name: optional name of the datacenter
    :param folder_name: optional name of the folder to store the new VM
    :param datastore_name: optional name of the datastore
    :param cluster_name: optional name of the cluster
    :param resource_pool_name: optional name of the resource pool
    :param esxi_name: optional name of the target ESXi host
    :param power_on: whether to power on the new VM after creation
    :return: None
    """
    content = si.RetrieveContent()

    # locate the template
    # template = get_single_obj(si, [vim.VirtualMachine], template_name)
    container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
    objs = list(container_view.view)

    template = None
    for obj_temp in objs:
        if obj_temp.name == template_name and obj_temp.summary.config.template:
            template = obj_temp
            break
    container_view.Destroy()

    if not template:
        raise ManagedObjectNotFoundError(
            f"Managed object of type '[vim.VirtualMachine]' with name '{template_name}' not found."
        )

    # locate the datacenter
    # datacenter = get_single_obj(si, [vim.Datacenter], datacenter_name)
    container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.Datacenter], True)
    datacenters = list(container_view.view)

    datacenter = None
    if datacenter_name:
        for datacenter_temp in datacenters:
            if datacenter_temp.name == datacenter_name:
                datacenter = datacenter_temp
                break

        if not datacenter:
            raise ManagedObjectNotFoundError(
                f"Managed object of type '[vim.Datacenter]' with name '{datacenter_name}' not found."
            )
    else:
        datacenter = datacenters[0]

    container_view.Destroy()

    # locate the folder
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
        folder = datacenter.vmFolder

    # determine datastore
    if datastore_name is None:
        datastore_name = template.datastore[0].info.name

    # locate the datastore
    # datastore = get_single_obj(si, [vim.Datastore], datastore_name)
    container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.Datastore], True)
    datastores = list(container_view.view)

    datastore = None
    for datastore_temp in datastores:
        if datastore_temp.name == datastore_name:
            datastore = datastore_temp
            break
    container_view.Destroy()

    if not datastore:
        raise ManagedObjectNotFoundError(
            f"Managed object of type '[vim.Datastore]' with name '{datastore_name}' not found."
        )

    # locate the cluster
    cluster = None
    if cluster_name:
        # cluster = get_single_obj(si, [vim.ClusterComputeResource], cluster_name, folder=datacenter.hostFolder)
        container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.ClusterComputeResource], True)
        clusters = list(container_view.view)

        for cluster_temp in clusters:
            if cluster_temp.name == cluster_name:
                cluster = cluster_temp
                break
        container_view.Destroy()

        if not cluster:
            raise ManagedObjectNotFoundError(
                f"Managed object of type '[vim.ClusterComputeResource]' with name '{cluster_name}' not found."
            )
    else:
        # clusters = get_all_obj(si, [vim.ClusterComputeResource])
        container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.ClusterComputeResource], True)
        clusters = list(container_view.view)

        if len(clusters) > 0:
            cluster = clusters[0]
        container_view.Destroy()

    # locate the resource pool
    resource_pool = None
    if resource_pool_name:
        # resource_pool = get_single_obj(si, [vim.ResourcePool], resource_pool_name, folder=None)
        container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.ResourcePool], True)
        resource_pools = list(container_view.view)

        for resource_temp in resource_pools:
            if resource_temp.name == resource_pool_name:
                resource_pool = resource_temp
                break
        container_view.Destroy()

        if not resource_pool:
            raise ManagedObjectNotFoundError(
                f"Managed object of type '[vim.ResourcePool]' with name '{resource_pool_name}' not found."
            )
    else:
        # resource_pools = get_all_obj(si, [vim.ResourcePool])
        if cluster:
            resource_pool = cluster
        else:
            container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.ResourcePool], True)
            resource_pools = list(container_view.view)

            if len(resource_pools) > 0:
                resource_pool = resource_pools[0]
            container_view.Destroy()

    # check if the VM name already exists
    # vms = get_all_obj(si, [vim.VirtualMachine], folder=folder)
    container_view = content.viewManager.CreateContainerView(folder, [vim.VirtualMachine], True)
    vms = list(container_view.view)
    container_view.Destroy()

    vms_name = [vm.name for vm in vms]
    if vm_name in vms_name:
        raise ValueError(f"Managed Object of type '[vim.VirtualMachine]' with name {vm_name} has existed.")

    # locate the ESXi host
    esxi = None
    if esxi_name:
        # host = get_single_obj(si, [vim.HostSystem], EXSi_name, folder=None)
        container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
        esxis = list(container_view.view)

        for esxi_temp in esxis:
            if esxi_temp.name == esxi_name:
                esxi = esxi_temp
                break
        container_view.Destroy()

        if not esxi:
            raise ManagedObjectNotFoundError(
                f"Managed object of type '[vim.HostSystem]' with name '{esxi_name}' not found."
            )
    else:
        # hosts = get_all_obj(si, [vim.HostSystem], folder=None)
        container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
        esxis = list(container_view.view)

        esxi = esxis[0]
        container_view.Destroy()

    # create relocation spec
    relospec = vim.vm.RelocateSpec()
    relospec.datastore = datastore
    relospec.pool = resource_pool
    relospec.host = esxi

    # create clone spec
    clonespec = vim.vm.CloneSpec()
    clonespec.location = relospec
    clonespec.powerOn = power_on

    # clone the VM
    tasks = [template.Clone(folder=folder, name=vm_name, spec=clonespec)]
    task.wait_for_tasks(si, tasks)
    print(f"Virtual machines: {vm_name} cloned successfully.")


def customize(si, vm_name, vm_ip, vm_mask, vm_gateway, vm_dns, vm_hostname, network_name=None, folder_name=None):
    """
    Modify the network configuration of a virtual machine, including IP, subnet mask, gateway, DNS, and hostname.

    :param si: service instance object connected to vCenter
    :param vm_name: name of the virtual machine
    :param vm_ip: IP address to assign to the virtual machine
    :param vm_mask: subnet mask for the IP address
    :param vm_gateway: gateway for the virtual machine
    :param vm_dns: DNS server address
    :param vm_hostname: hostname for the virtual machine
    :param network_name: specific network name for multi-NIC virtual machines
    :param folder_name: name of the folder containing the virtual machine
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

    vm = None
    container_view = content.viewManager.CreateContainerView(folder, [vim.VirtualMachine], True)
    vms = list(container_view.view)

    for vm_temp in vms:
        if vm_temp.name == vm_name and not vm_temp.summary.config.template:
            vm = vm_temp
            break
    container_view.Destroy()

    if not vm:
        raise ManagedObjectNotFoundError(
            f"Managed object of type '[vim.VirtualMachine]' with name '{vm_name}' not found."
        )

    # create adapter mappings
    adaptermaps = []
    for net in vm.guest.net:
        adapter_map = vim.vm.customization.AdapterMapping()
        adapter_map.adapter = vim.vm.customization.IPSettings()
        adapter_map.adapter.ip = vim.vm.customization.FixedIp()

        # configure the adapter based on whether a specific network is provided
        if network_name:
            if net.network == network_name:
                # if a specific network matches, assign the given or default IP configuration
                adapter_map.adapter.ip.ipAddress = vm_ip or net.ipAddress[0]
                adapter_map.adapter.subnetMask = vm_mask or gen_mask(net.ipConfig.ipAddress[0].prefixLength)
                adapter_map.adapter.gateway = vm_gateway or vm.guest.ipStack[0].ipRouteConfig.ipRoute[
                    0].gateway.ipAddress
            else:
                # for other nic, retain their original configuration
                adapter_map.adapter.ip.ipAddress = net.ipAddress[0]
                adapter_map.adapter.subnetMask = gen_mask(net.ipConfig.ipAddress[0].prefixLength)
                adapter_map.adapter.gateway = vm.guest.ipStack[0].ipRouteConfig.ipRoute[0].gateway.ipAddress
        else:
            # for single NIC without network_name, use the provided IP configuration
            adapter_map.adapter.ip.ipAddress = vm_ip
            adapter_map.adapter.subnetMask = vm_mask
            adapter_map.adapter.gateway = vm_gateway

        adaptermaps.append(adapter_map)

    # reverse the adapter mappings to maintain the correct order for customization
    adaptermaps.reverse()

    # set global IP settings
    global_ip = vim.vm.customization.GlobalIPSettings()
    if vm_dns:
        global_ip.dnsServerList = [vm_dns]
    elif vm.guest.ipStack:
        global_ip.dnsServerList = vm.guest.ipStack[0].dnsConfig.ipAddress

    # configure the identity settings for Linux virtual machines
    ident = vim.vm.customization.LinuxPrep()
    ident.hostName = vim.vm.customization.FixedName()
    ident.hostName.name = vm_hostname if vm_hostname else vm.guest.ipStack[0].dnsConfig.hostName

    # create the customization specification
    custom_spec = vim.vm.customization.Specification()
    custom_spec.nicSettingMap = adaptermaps
    custom_spec.globalIPSettings = global_ip
    custom_spec.identity = ident

    # Power off the virtual machine if it is powered on
    if vm.runtime.powerState != "poweredOff":
        power_off(si, folder_name, vm_name)

    # apply the customization specification to the virtual machine
    tasks = [vm.Customize(spec=custom_spec)]
    task.wait_for_tasks(si, tasks)

    print(f"Virtual machines with name '{vm_name}' customization completed successfully.")
