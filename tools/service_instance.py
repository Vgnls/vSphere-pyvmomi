import atexit
from pyVim.connect import SmartConnect, Disconnect


def connect(disable_ssl_verification=True):
    """
    Establishes a connection to the vCenter server using the pyvmomi library.

    :param disable_ssl_verification: Whether to disable SSL certificate verification during the connection
    :return: an instance of the vCenter server connection object
    """
    # Connection parameters
    host = '192.168.25.132'  # Replace with the vCenter server's IP
    user = 'administrator@vsphere.local'  # Replace with the vCenter username
    password = 'BUPTwb407!'  # Replace with the vCenter password
    port = 443  # Default port for vSphere API

    service_instance = None

    try:
        # Attempt to establish the connection
        if disable_ssl_verification:
            service_instance = SmartConnect(
                host=host,
                user=user,
                pwd=password,
                port=port,
                disableSslCertValidation=True
            )
        else:
            service_instance = SmartConnect(
                host=host,
                user=user,
                pwd=password,
                port=port
            )

        # Register atexit handler to ensure proper disconnection
        atexit.register(Disconnect, service_instance)

    except IOError as io_error:
        print(f"IOError occurred: {io_error}")

    # Check if the connection was successful
    if not service_instance:
        raise SystemExit("Unable to connect to the vCenter server with the supplied credentials.")

    return service_instance
