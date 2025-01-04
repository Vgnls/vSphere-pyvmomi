from pyVmomi import vim
from pyVmomi import vmodl


def wait_for_tasks(si, tasks):
    """
    Waits for all tasks to complete.

    :param si: service instance object connected to vCenter
    :param tasks: list of tasks to monitor
    :return: none
    """
    # retrieve the property collector from the service instance
    property_collector = si.content.propertyCollector

    # create a list of task for tracking
    task_list = [str(task) for task in tasks]

    # create the object specification for the tasks
    obj_specs = [vmodl.query.PropertyCollector.ObjectSpec(obj=task) for task in tasks]
    property_spec = vmodl.query.PropertyCollector.PropertySpec(type=vim.Task, pathSet=[], all=True)

    # create filter specification to monitor tasks
    filter_spec = vmodl.query.PropertyCollector.FilterSpec()
    filter_spec.objectSet = obj_specs
    filter_spec.propSet = [property_spec]

    # create the property collector filter
    pcfilter = property_collector.CreateFilter(filter_spec, True)

    try:
        version, state = None, None

        # continuously monitor tasks until they are completed
        while task_list:
            update = property_collector.WaitForUpdates(version)

            # process updates for each task
            for filter_set in update.filterSet:
                for obj_set in filter_set.objectSet:
                    task = obj_set.obj
                    for change in obj_set.changeSet:
                        if change.name == 'info':
                            state = change.val.state
                        elif change.name == 'info.state':
                            state = change.val
                        else:
                            continue

                        # skip tasks that are no longer in the task list
                        if str(task) not in task_list:
                            continue

                        # check task state and update task list
                        if state == vim.TaskInfo.State.success:
                            task_list.remove(str(task))
                        elif state == vim.TaskInfo.State.error:
                            raise task.info.error
            # move to next version
            version = update.version
    finally:
        if pcfilter:
            pcfilter.Destroy()
