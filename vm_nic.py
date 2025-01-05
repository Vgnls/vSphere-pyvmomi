from pyVmomi import vim
from tools.obj_helper import *
from tools import task


def add(si, vm_name: str, portgroup_name: str, datacenter_name=None, folder_name=None):
    """
    Add a network adapter to a virtual machine.

    :param si: service instance object connected to vCenter
    :param vm_name: name of the virtual machine
    :param portgroup_name: name of the port group to connect the network adapter
    :param datacenter_name: (optional) name of the datacenter containing the virtual machine
    :param folder_name: (optional) name of the folder containing the virtual machine
    :return: none
    """
    content = si.RetrieveContent()

    datacenter = None
    # locate the datacenter
    if datacenter_name:
        # datacenter = get_single_obj(si, [vim.Datacenter], datacenter_name, folder=None)
        container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.Datacenter], True)
        datacenters = list(container_view.view)

        for datacenter_temp in datacenters:
            if datacenter_temp.name == datacenter_name:
                datacenter = datacenter_temp
                break

        if not datacenter:
            raise ManagedObjectNotFoundError(
                f"Managed object of type '[vim.Datacenter]' with name '{datacenter_name}' not found."
            )
        container_view.Destroy()

    folder = None
    # locate the folder
    if folder_name:
        if datacenter:
            search_folder = datacenter.vmFolder
        else:
            search_folder = content.rootFolder

        # folder = get_single_obj(si, [vim.Folder], folder_name, folder=datacenter.vmFolder)
        container_view = content.viewManager.CreateContainerView(search_folder, [vim.Folder], True)
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

    # locate the virtual machine
    # vm = get_given_obj(si, [vim.VirtualMachine], vm_name, folder=folder)
    container_view = content.viewManager.CreateContainerView(folder, [vim.VirtualMachine], True)
    vm_view = list(container_view.view)

    vms = list()
    for vm_temp in vm_view:
        if vm_temp.name == vm_name:
            vms.append(vm_temp)
    container_view.Destroy()

    if not vms:
        raise ManagedObjectNotFoundError(
            f"Managed object of type '[vim.VirtualMachine]' with name '{vm_name}' not found."
        )

    # locate the portgroup
    # network = get_single_obj(content, [vim.Network], portgroup_name)
    container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.Network], True)
    networks = list(container_view.view)

    network = None
    for network_temp in networks:
        if network_temp.name == portgroup_name:
            network = network_temp
            break

    if not network:
        raise ManagedObjectNotFoundError(
            f"Managed object of type '[vim.Network]' with name '{portgroup_name}' not found."
        )

    # prepare the network adapter spec
    nic_spec = vim.vm.device.VirtualDeviceSpec()
    nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add

    nic_spec.device = vim.vm.device.VirtualE1000()
    nic_spec.device.deviceInfo = vim.Description()
    nic_spec.device.deviceInfo.summary = portgroup_name

    if isinstance(network, vim.OpaqueNetwork):
        nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.OpaqueNetworkBackingInfo(
            opaqueNetworkType=network.summary.opaqueNetworkType,
            opaqueNetworkId=network.summary.opaqueNetworkId
        )
    else:
        nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo(
            useAutoDetect=False,
            deviceName=portgroup_name
        )

    nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo(
        startConnected=True,
        allowGuestControl=True,
        connected=False,
        status='untried'
    )

    nic_spec.device.wakeOnLanEnabled = True
    nic_spec.device.addressType = 'assigned'

    # reconfigure the virtual machines
    spec = vim.vm.ConfigSpec(deviceChange=[nic_spec])

    tasks = list()
    for vm in vms:
        tasks.append(vm.ReconfigVM_Task(spec=spec))
    task.wait_for_tasks(si, tasks)
    print(f"Network adapter {portgroup_name} added to virtual machine {vm_name} successfully.")


def delete(si, vm_name: str, portgroup_name: str, datacenter_name=None, folder_name=None):
    """
    Remove a network adapter from a virtual machine.

    :param si: service instance object connected to vCenter
    :param vm_name: name of the virtual machine
    :param portgroup_name: name of the port group associated with the network adapter
    :param datacenter_name: (optional) name of the datacenter containing the virtual machine
    :param folder_name: (optional) name of the folder containing the virtual machine
    :return: none
    """
    content = si.RetrieveContent()

    datacenter = None
    # locate the datacenter
    if datacenter_name:
        # datacenter = get_single_obj(si, [vim.Datacenter], datacenter_name, folder=None)
        container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.Datacenter], True)
        datacenters = list(container_view.view)

        for datacenter_temp in datacenters:
            if datacenter_temp.name == datacenter_name:
                datacenter = datacenter_temp
                break

        if not datacenter:
            raise ManagedObjectNotFoundError(
                f"Managed object of type '[vim.Datacenter]' with name '{datacenter_name}' not found."
            )
        container_view.Destroy()

    folder = None
    # locate the folder
    if folder_name:
        if datacenter:
            search_folder = datacenter.vmFolder
        else:
            search_folder = content.rootFolder

        # folder = get_single_obj(si, [vim.Folder], folder_name, folder=datacenter.vmFolder)
        container_view = content.viewManager.CreateContainerView(search_folder, [vim.Folder], True)
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

    # locate the virtual machine
    # vm = get_given_obj(si, [vim.VirtualMachine], vm_name, folder=folder)
    container_view = content.viewManager.CreateContainerView(folder, [vim.VirtualMachine], True)
    vm_view = list(container_view.view)

    vms = list()
    for vm_temp in vm_view:
        if vm_temp.name == vm_name:
            vms.append(vm_temp)
    container_view.Destroy()

    if not vms:
        raise ManagedObjectNotFoundError(
            f"Managed object of type '[vim.VirtualMachine]' with name '{vm_name}' not found."
        )

    tasks = list()
    # locate and remove the network adapter
    for vm in vms:
        virtual_nic_device = None
        for dev in vm.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualEthernetCard) and dev.deviceInfo.summary == portgroup_name:
                virtual_nic_device = dev

        if not virtual_nic_device:
            raise ManagedObjectNotFoundError(
                f"Network adapter with name {portgroup_name} not found in virtual machine {vm_name}."
            )

        nic_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.remove,
            device=virtual_nic_device
        )

        spec = vim.vm.ConfigSpec(deviceChange=[nic_spec])
        tasks.append(vm.ReconfigVM_Task(spec=spec))

    task.wait_for_tasks(si, tasks)
    print(f"Network adapter {portgroup_name} removed from virtual machine {vm_name} successfully.")
