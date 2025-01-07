from pyVmomi import vim
from tools.obj_helper import *
from tools import task
from prettytable import PrettyTable


def create(si, vm_name, snapshot_name, description=None, memory=False, quiesce=False):
    """
    Create a snapshot for a virtual machine.

    :param si: service instance object connected to vCenter
    :param vm_name: name of the virtual machine
    :param snapshot_name: name of the snapshot to be created
    :param description: description of the snapshot
    :param memory: whether to include the VM memory state in the snapshot
    :param quiesce: whether to quiesce the file system during snapshot creation
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

    tasks = [vm.CreateSnapshot(snapshot_name, description, memory, quiesce)]
    task.wait_for_tasks(si, tasks)

    print(f"Snapshot '{snapshot_name}' created successfully for virtual machine '{vm_name}'.")


def remove(si, vm_name, snapshot_name):
    """
    Remove a specific snapshot from a virtual machine.

    :param si: service instance object connected to vCenter
    :param vm_name: name of the virtual machine
    :param snapshot_name: name of the snapshot to be removed
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

    snapshot = None
    for snapshot_temp in vm.snapshot.rootSnapshotList:
        if snapshot_temp.name == snapshot_name:
            snapshot = snapshot_temp
            break

    if not snapshot:
        raise ManagedObjectNotFoundError(
            f"Snapshot '{snapshot_name}' not found for virtual machine '{vm_name}'."
        )

    tasks = [snapshot.snapshot.RemoveSnapshot_Task(True)]
    task.wait_for_tasks(si, tasks)

    print(f"Snapshot '{snapshot_name}' removed successfully from virtual machine '{vm_name}'.")


def revert(si, vm_name, snapshot_name=None):
    """
    Revert a virtual machine to a specified snapshot or the current snapshot.

    :param si: service instance object connected to vCenter
    :param vm_name: name of the virtual machine
    :param snapshot_name: name of the snapshot to revert to
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

    snapshot = None
    if snapshot_name:
        for snapshot_temp in vm.snapshot.rootSnapshotList:
            if snapshot_temp.name == snapshot_name:
                snapshot = snapshot_temp
                break

        if not snapshot:
            raise ManagedObjectNotFoundError(
                f"Snapshot '{snapshot_name}' not found for virtual machine '{vm_name}'."
            )

    if snapshot:
        tasks = [snapshot.snapshot.RevertToSnapshot_Task()]
    else:
        tasks = [vm.RevertToCurrentSnapshot()]

    task.wait_for_tasks(si, tasks)

    print(f"Virtual machine '{vm_name}' reverted to snapshot '{snapshot_name}' successfully." if snapshot_name else
          f"Virtual machine '{vm_name}' reverted to current snapshot successfully.")


def remove_all(si, vm_name):
    """
    Remove all snapshots for a virtual machine.

    :param si: service instance object connected to vCenter
    :param vm_name: name of the virtual machine
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

    tasks = [vm.RemoveAllSnapshots()]
    task.wait_for_tasks(si, tasks)

    print(f"All snapshots removed successfully from virtual machine '{vm_name}'.")


def rename(si, vm_name, snapshot_name, new_name):
    """
    Rename a snapshot of a virtual machine.

    :param si: service instance object connected to vCenter
    :param vm_name: name of the virtual machine
    :param snapshot_name: name of the snapshot to be renamed
    :param new_name: new name for the snapshot
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

    snapshot = None
    # locate the snapshot by name
    for snapshot_temp in vm.snapshot.rootSnapshotList:
        if snapshot_temp.name == snapshot_name:
            snapshot = snapshot_temp
            break

    if not snapshot:
        raise ManagedObjectNotFoundError(
            f"Snapshot '{snapshot_name}' not found for virtual machine '{vm_name}'."
        )

    # rename the snapshot
    snapshot.snapshot.Rename(new_name)
    print(f"Snapshot '{snapshot_name}' renamed to '{new_name}' successfully for virtual machine '{vm_name}'.")


def show(si, vm_name):
    """
    Display all snapshots of a virtual machine.

    :param si: service instance object connected to vCenter
    :param vm_name: name of the virtual machine
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

    table = PrettyTable()
    table.field_names = ["Name", "Description", "Quiesce", "State", "Created time"]

    for snapshot_temp in vm.snapshot.rootSnapshotList:
        snapshot_name = snapshot_temp.name
        snapshot_description = snapshot_temp.description
        snapshot_quiesced = snapshot_temp.quiesced
        snapshot_state = snapshot_temp.state
        snapshot_time = snapshot_temp.createTime

        table.add_row(
            [snapshot_name, snapshot_description, snapshot_quiesced, snapshot_state, str(snapshot_time).split('.')[0]]
        )

    print(f"Snapshots for virtual machine '{vm_name}':")
    print(table)
