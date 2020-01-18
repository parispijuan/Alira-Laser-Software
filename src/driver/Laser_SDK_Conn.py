import os
import sys
import platform
from ctypes import c_uint32, c_uint16, c_bool, pointer, CDLL


## Exception class indicating an issue interacting with or contacting the SDK.
class SDK_Exception(Exception):
    pass

## @brief Allows for establishment of connection to the SideKick SDK code.
#
#  As the SDK is written in C, this class acts as a go-between between it and
#  the pythonic driver.
class Laser_SDK_Conn:

    ## @brief Constructor for the connection object.
    #
    #  Attempts to initialize the laser and determines the SDK location. Using
    #  this location, the sdk object is created.
    def __init__(self, sdk_version):
        ## @vars The location of the sdk .dll file.
        self.loc = __acquire_sdk_file(sdk_version)

        ## @vars The sdk object to be used by the driver.
        self.connection = CDLL(self.sdk_location)

        ## @vars Constant for retries on finding the sdk.
        self.sidekick_sdk_ret_success = 0

        self.__call_sdk_bool(self.driver.SidekickSDK_Initialize,
                            'SDK initialization successful', 'Unable to initialize SDK')


    ## @brief Determinines the path to the SDK library c file.
    #
    #  Allows for the user to request a specific SDK version, otherwise adapts
    #  the choice to their machine's requirement.
    def __acquire_sdk_file(version):
        if version == 64:
            location = os.path.join(os.path.dirname(__file__), 'SidekickSDKx64.dll')
        elif version == 86:
            location = os.path.join(os.path.dirname(__file__), 'SidekickSDKx86.dll')
        elif platform.machine().endswith('64'):
            location = os.path.join(os.path.dirname(__file__), 'SidekickSDKx64.dll')
        else:
            location = os.path.join(os.path.dirname(__file__), 'SidekickSDKx86.dll')
        return location

    ## @Brief Connect to laser using USB port.
    #
    #  @exceptions SDK_Exception Thrown if __connect_laser does not establish connection.
    def connect_laser(self):
        num_devices_ptr = pointer(c_uint16())
        handle_ptr = pointer(c_uint32())
        self.__call_sdk_bool(self.sdk.SidekickSDK_SearchForUsbDevices,
                            'Found USB devices.', 'Error occured while searching for USB devices.')
        self.__call_sdk_bool(self.sdk.SidekickSDK_GetNumOfDevices,
                            'Got device count.', 'Error when getting device count.', num_devices_ptr)
        self.__call_sdk_bool(self.sdk.SidekickSDK_ConnectToDeviceNumber,
                            'Connected to laser.', 'Unable to connect to laser.',
                            handle_ptr, c_uint16(num_devices_ptr.contents.value - 1))
        self.handle = handle_ptr.contents
        self.sdk.SidekickSDK_ReadAdminQclParams(self.handle, 0)
        self.__call_sdk_bool_ptr(self.sdk.SidekickSDK_AdminQclIsAvailable,
                                'QCL installed and detected.', 'QCL not detected.')
        self.__call_sdk_bool_ptr(self.sdk.SidekickSDK_isInterlockedStatusSet,
                                'Interlock set.', 'Interlock not set.')
        self.__call_sdk_bool_ptr(self.sdk.SidekickSDK_isKeySwitchStatusSet,
                                'Keyswitch set.', 'Keyswitch not set.')

    ## @brief Call SDK function with optional arguments and check return value.
    #
    #  @param sdk_fn SDK function to call
    #  @param success_msg string message to print if function returns success
    #  @param error_msg string message to print if function fails
    #  @param *args optional arguments to pass to SDK function.
    #  @exceptions SDK_Exception Thrown if SDK function fails
    def __call_sdk_bool(self, sdk_fn, success_msg="Success", error_msg="Failure", *args):
        ret = sdk_fn() if not args else sdk_fn(*args)
        if ret == self.sidekick_sdk_ret_success:
            sys.stderr.write(success_msg)
        else:
            raise SDK_Exception(error_msg)


    ## @brief Call SDk function and check boolean status value set by reference.
    #
    #  @param sdk_fn SDK function to call
    #  @param success_msg string message to print if function returns success
    #  @param error_msg string message to print if function fails
    #  @exceptions SDK_Exception Thrown if SDK function fails
    def __call_sdk_bool_ptr(self, sdk_fn, success_msg, error_msg):
        ret_ptr = pointer(c_bool(False))
        sdk_fn(self.handle, ret_ptr)
        if ret_ptr.contents.value:
            sys.stderr.write(success_msg)
        else:
            self.sdk.SidekickSDK_Disconnect(self.handle)
            raise SDK_Exception(error_msg)
