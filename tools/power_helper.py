from pyVmomi import vim
from .obj_helper import *
import re


def power_state(si, folder_name, action: str, vm_names=None):
    """
    Manages the power state of virtual machines in the specified folder.

    :param si: service instance object connected to vCenter
    :param folder_name: name of the folder containing the virtual machines
    :param action: the action to be taken (On, Off, Suspend, Reboot, or Destroy)
    :param vm_names: list of virtual machine names to apply the action
    :return: list of virtual machines that are eligible for the action
    """
    content = si.RetrieveContent()

    if folder_name is None:
        folder = content.rootFolder
    else:
        # folder = get_single_obj(si, [vim.Folder], folder_name)
        container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.Folder], True)
        folders = list(container_view.view)

        folder = None
        # find the folder matching the provided folder name
        for folder_temp in folders:
            if folder_temp.name == folder_name:
                folder = folder_temp
                break
        container_view.Destroy()

        if not folder:
            raise ManagedObjectNotFoundError(
                f"Managed object of type '[vim.Folder]' with name '{folder_name}' not found."
            )

    vm_list = list()
    if vm_names is None:
        # vm_list = get_all_obj(si, [vim.VirtualMachine], folder=folder)
        container_view = content.viewManager.CreateContainerView(folder, [vim.VirtualMachine], True)
        vm_list = list(container_view.view)
        container_view.Destroy()

        if not vm_list:
            raise ManagedObjectNotFoundError(
                f"No managed objects of type '[vim.VirtualMachine]' found."
            )
    else:
        # vm_list = get_given_obj(si, [vim.VirtualMachine], vm_names, folder=folder)
        container_view = content.viewManager.CreateContainerView(folder, [vim.VirtualMachine], True)
        vms = list(container_view.view)

        for vm in vms:
            # add virtual machines to the list that match the provided names
            if vm.name in vm_names:
                vm_list.append(vm)
        container_view.Destroy()

        if not vm_list:
            raise ManagedObjectNotFoundError(
                f"Managed objects of type '[vim.VirtualMachine]' with names {', '.join(vm_names)} not found."
            )

    # map actions to their corresponding valid power states
    action_state_map = {
        "On": ["poweredOff", "suspended"],
        "Off": ["poweredOn"],
        "Suspend": ["poweredOn"],
        "Reboot": ["poweredOn"],
        "Destroy": ["poweredOn", "poweredOff", "suspended"]
    }
    # check if the action is valid and get the corresponding power states
    state = action_state_map.get(action)
    if state is None:
        # raise an exception if the action is not valid
        raise ValueError("Invalid action parameter")

    action_list = list()
    for vm in vm_list:
        current_power_state = vm.summary.runtime.powerState
        # add virtual machines to the action list if their current power state matches the desired state
        if current_power_state in state:
            action_list.append(vm)

    return action_list


def power_state_regex(si, folder_name, action: str, regex):
    """
    Manages the power state of virtual machines in the specified folder based on a regex match for VM names.

    :param si: service instance object connected to vCenter
    :param folder_name: name of the folder containing the virtual machines
    :param action: the action to be taken (On, Off, Suspend, Reboot, or Destroy)
    :param regex: regular expression to match virtual machine names
    :return: list of virtual machines that are eligible for the action
    """
    content = si.RetrieveContent()

    if folder_name is None:
        folder = content.rootFolder
    else:
        # folder = get_single_obj(si, [vim.Folder], folder_name)
        container_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.Folder], True)
        folders = list(container_view.view)

        folder = None
        for folder_temp in folders:
            # find the folder matching the provided folder name
            if folder_temp.name == folder_name:
                folder = folder_temp
                break
        container_view.Destroy()

        if not folder:
            raise ManagedObjectNotFoundError(
                f"Managed object of type '[vim.Folder]' with name '{folder_name}' not found."
            )

    vm_list = list()

    # vm_list = get_matched_obj(si, [vim.VirtualMachine], regex, folder=folder)
    container_view = content.viewManager.CreateContainerView(folder, [vim.VirtualMachine], True)
    vms = list(container_view.view)

    for vm in vms:
        # add virtual machines to the list that match the regex pattern
        if re.match(regex, vm.name):
            vm_list.append(vm)
    container_view.Destroy()

    if not vm_list:
        raise ManagedObjectNotFoundError(
            f"Managed objects of type '[vim.VirtualMachine]' matching regex '{regex}' found"
        )

    # map actions to their corresponding valid power states
    action_state_map = {
        "On": ["poweredOff", "suspended"],
        "Off": ["poweredOn"],
        "Suspend": ["poweredOn"],
        "Reboot": ["poweredOn"],
        "Destroy": ["poweredOn", "poweredOff", "suspended"]
    }
    # check if the action is valid and get the corresponding power states
    state = action_state_map.get(action)
    if state is None:
        # raise an exception if the action is not valid
        raise ValueError("Invalid action parameter")

    action_list = list()
    for vm in vm_list:
        current_power_state = vm.summary.runtime.powerState
        # add virtual machines to the action list if their current power state matches the desired state
        if current_power_state in state:
            action_list.append(vm)

    return action_list
