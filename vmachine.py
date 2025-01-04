from pyVmomi import vim
import re
from prettytable import PrettyTable
from tools.obj_helper import *
from tools.power_helper import *
from tools import task


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


def show(si, folder_name=None):
    """
    Display brief information about virtual machines in a folder.

    :param si: service instance for vSphere connection
    :param folder_name: name of the folder containing virtual machines
    :return: none
    """
    # folder = get_single_obj(si, [vim.Folder], folder_name)
    content = si.RetrieveContent()

    # locate the specified folder
    folder = None
    if not folder_name:
        folder = content.rootFolder
    else:
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
    table.field_names = ['Name', 'Power State', 'Connection State', 'VMware Tools', 'Hard Disk', 'CPU Number', 'Memory']

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
