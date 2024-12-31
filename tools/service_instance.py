import atexit
from pyVim.connect import SmartConnect, Disconnect


def connect(disable_ssl_verification=True):
    """

    :param disable_ssl_verification:
    :return:
    """
    host = '10.XXX.XXX.XXX'
    user = 'administrator@vsphere.local'
    password = 'XXXXXXX'
    port = 443

    service_instance = None

    try:
        if disable_ssl_verification:
            service_instance = SmartConnect(host=host,
                                            user=user,
                                            pwd=password,
                                            port=port,
                                            disableSslCertValidation=True)
        else:
            service_instance = SmartConnect(host=host,
                                            user=user,
                                            pwd=password,
                                            port=port)

        # doing this means you don't need to remember to disconnect your script/objects
        atexit.register(Disconnect, service_instance)
    except IOError as io_error:
        print(io_error)

    if not service_instance:
        raise SystemExit("Unable to connect to host with supplied credentials.")

    return service_instance
