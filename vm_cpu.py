from pyVmomi import vim
from tools.obj_helper import *
from tools import task


def customize(si, vm_name, cpu_num, core_num, folder_name=None):
    """
    Customize the CPU configuration of a virtual machine, including the number of CPUs and cores per CPU.

    :param si: service instance object connected to vCenter
    :param vm_name: name of the virtual machine to be customized
    :param cpu_num: number of CPUs to be configured
    :param core_num: number of cores per CPU to be configured
    :param folder_name: optional folder name where the virtual machine is located
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

    # prepare the configuration specification
    config_spec = vim.vm.ConfigSpec()

    config_spec.annotation = vm.config.annotation
    # set the new number of CPU
    config_spec.numCPUs = cpu_num
    # set the new number of cores per CPU
    config_spec.numCoresPerSocket = core_num
    config_spec.memoryMB = vm.config.hardware.memoryMB
    config_spec.memoryHotAddEnabled = vm.config.memoryHotAddEnabled
    config_spec.cpuHotAddEnabled = vm.config.cpuHotAddEnabled
    config_spec.cpuHotRemoveEnabled = vm.config.cpuHotRemoveEnabled

    # reconfigure the VM with the new configuration
    tasks = [vm.Reconfigure(spec=config_spec)]
    task.wait_for_tasks(si, tasks)

    print(f"Customize the number of CPUs for VM '{vm_name}' to {cpu_num}, cores per CPU to {core_num} successfully.")
