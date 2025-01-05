from pyVmomi import vim
from prettytable import PrettyTable
from tools.obj_helper import *
from tools import task


def add(si, vm_name, disk_size, disk_mode='persistent', disk_provision='thin'):
    """
    Add a new virtual disk to a virtual machine.

    :param si: service instance object connected to vCenter
    :param vm_name: name of the virtual machine
    :param disk_size: size of the new disk in GB
    :param disk_mode: mode of the virtual disk
    :param disk_provision: disk provisioning type
    :return: none
    """
    content = si.RetrieveContent()

    vm = None
    # locate the virtual machine by name
    container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
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

    # prepare configuration specification for adding a disk
    spec = vim.vm.ConfigSpec()

    # determine the unit number and locate the SCSI controller
    next_unit_number = 0
    scsi_controller = None
    for device in vm.config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualDisk):
            next_unit_number = device.unitNumber + 1
            # skip number 7, reserved for SCSI controller
            if next_unit_number == 7:
                next_unit_number = 8
            # limit exceeded for SCSI devices
            elif next_unit_number > 64:
                raise ValueError(f"Maximum number of disks reached.")

        if isinstance(device, vim.vm.device.VirtualSCSIController):
            scsi_controller = device

    if scsi_controller is None:
        raise ValueError("No available SCSI controller found.")

    # configure the new disk
    device_changes = []
    disk_KB = int(disk_size) * (1024 ** 2)
    disk_spec = vim.vm.device.VirtualDeviceSpec()

    disk_spec.fileOperation = "create"
    disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    disk_spec.device = vim.vm.device.VirtualDisk()
    disk_spec.device.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()

    # set provisioning type and mode
    if disk_provision == 'thin':
        disk_spec.device.backing.thinProvisioned = True
    disk_spec.device.backing.diskMode = disk_mode
    disk_spec.device.unitNumber = next_unit_number
    disk_spec.device.capacityInKB = disk_KB
    disk_spec.device.controllerKey = scsi_controller.key
    device_changes.append(disk_spec)
    spec.deviceChange = device_changes

    # apply the configuration and add the disk
    task.wait_for_tasks(si, [vm.ReconfigVM_Task(spec=spec)])
    print(f"{disk_size} GB disk added to virtual machine '{vm_name}' successfully.")


def delete(si, vm_name, disk_index=None):
    """
    Delete a virtual disk from a virtual machine.

    :param si: service instance object connected to vCenter
    :param vm_name: name of the virtual machine
    :param disk_index: index of the virtual disk to delete
    :return: none
    """
    content = si.RetrieveContent()

    vm = None
    # locate the virtual machine by name
    container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
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

    disk_remove = None
    disk_prefix = "Hard disk "
    # locate the disk to delete
    for device in vm.config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualDisk) and device.deviceInfo.label[len(disk_prefix):] == str(
                disk_index):
            disk_remove = device
            break

    if not disk_remove:
        raise ManagedObjectNotFoundError(
            f"VirtualDisk {disk_index} of type '[vim.VirtualMachine]' with name '{vm_name}' not found."
        )

    # prepare configuration specification for removing the disk
    disk_spec = vim.vm.device.VirtualDeviceSpec()
    disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
    disk_spec.device = disk_remove

    spec = vim.vm.ConfigSpec()
    spec.deviceChange = [disk_spec]

    tasks = vm.ReconfigVM_Task(spec=spec)
    task.wait_for_tasks(si, [tasks])

    print(f"Virtual disk {disk_index} removed from virtual machine '{vm_name}' successfully.")


def customize(si, vm_name, disk_index=1, disk_size=None, disk_mode=None, scsi_controller=None):
    """
    Customize the configuration of a specified virtual disk in a virtual machine.

    :param si: service instance object connected to vCenter
    :param vm_name: name of the virtual machine
    :param disk_index: index of the virtual disk to customize
    :param disk_size: new size for the disk in GB; must be greater than the current size
    :param disk_mode: new disk mode
    :param scsi_controller: unit number for a specific SCSI controller
    :return: none
    """
    content = si.RetrieveContent()

    vm = None
    # locate the virtual machine by name
    container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
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

    disk_customize = None
    disk_prefix = "Hard disk "
    # locate the disk to customize
    for device in vm.config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualDisk) and device.deviceInfo.label[len(disk_prefix):] == str(
                disk_index):
            disk_customize = device

    if not disk_customize:
        raise ManagedObjectNotFoundError(
            f"VirtualDisk {disk_index} of type '[vim.VirtualMachine]' with name '{vm_name}' not found."
        )

    # prepare the device specification for customization
    disk_spec = vim.vm.device.VirtualDeviceSpec()
    disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
    disk_spec.device = disk_customize

    # validate the new disk size if provided
    if disk_size:
        new_disk_kb = int(disk_size) * (1024 ** 2)
        if new_disk_kb <= disk_spec.device.capacityInKB:
            raise ValueError(
                f"New disk size ({disk_size} GB) must be greater than the current size "
                f"({disk_spec.device.capacityInKB // (1024 ** 2)} GB)."
            )

        disk_spec.device.capacityInKB = new_disk_kb

    if disk_mode:
        disk_spec.device.backing.diskMode = disk_mode

    if scsi_controller:
        if scsi_controller not in range(65) or scsi_controller == 7:
            raise ValueError(
                f"SCSI controller unit number ({scsi_controller}) must be in the range 0-6 or 8-64."
            )
        disk_spec.device.unitNumber = scsi_controller

    spec = vim.vm.ConfigSpec()
    spec.deviceChange = [disk_spec]

    tasks = vm.ReconfigVM_Task(spec=spec)
    task.wait_for_tasks(si, [tasks])

    print(f"Virtual disk {disk_index} of virtual machine '{vm_name}' customized successfully.")
