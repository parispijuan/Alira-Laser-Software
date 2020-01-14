import time
import os
import sys
import platform
from ctypes import CDLL, pointer, c_uint32, c_uint16, c_uint8, c_bool, c_float, c_char
from threading import Thread
import zhinst
import zhinst.ziPython
import zhinst.utils
import numpy as np

## Exception class indicating an issue with laser-centric systems.
class Laser_Exception(Exception):
    pass

## Exception class indicating an issue with the QCL controller.
class QCL_Exception(Exception):
    pass

## Exception class indicating an issue interacting with or contacting the SDK.
class SDK_Exception(Exception):
    pass

## Driver for controlling the Daylight solutions laser through the SideKick SDK,
#  as well as retrieving data from a reciever set up with the corresponding laser.
#  Singleton class to prevent program from having to drivers running simultaneously

__global_laser_do_not_touch = {
  '__instance': None,
  '__get_called': False,
}

def get():
  global __global_laser_do_not_touch
  __global_laser_do_not_touch['__get_called'] = True
  if __global_laser_do_not_touch['__instance'] is None:
    __global_laser_do_not_touch['__instance'] = Laser()
  return __global_laser_do_not_touch['__instance']

def set_for_test(laser_instance):
  global __global_laser_do_not_touch
  if __global_laser_do_not_touch['__get_called']:
    raise RuntimeError("Can not call set() after get()")
  __global_laser_do_not_touch['__instance'] = laser_instance

def reset_for_testing():
  global __global_laser_do_not_touch
  __global_laser_do_not_touch = {
    '__instance': None,
    '__get_called': False,
  }

class Laser_Driver:
    ##@brief Initialize SDKs and provide hook for testing.
    #
    # Constructor for the driver object. Links with driver C library and SDK to control hardware.
    #
    # @param testing_sdk SideKickSDK library if None, else class with equivalent methods for testing.
    # @param testing_zisdk ZI library if None, else class with equivalent methods for testing.
    # @param sdk_version 86 or 64 (which version of Sidekick sdk to load).
    # @exception SDK_Exception if SDK cannot be initialized.
    def __init__(self, testing_sdk=None, testing_zi_sdk=None, sdk_version=None):

        if sdk_version == 64:
            self.sdk_location = os.path.join(os.path.dirname(__file__), 'SidekickSDKx64.dll')
        elif sdk_version == 86:
            self.sdk_location = os.path.join(os.path.dirname(__file__), 'SidekickSDKx86.dll')
        elif platform.machine().endswith('64'):
            self.sdk_location = os.path.join(os.path.dirname(__file__), 'SidekickSDKx64.dll')
        else:
            self.sdk_location = os.path.join(os.path.dirname(__file__), 'SidekickSDKx86.dll')


        ## @name Timing_Variables
        # Variables for timing of setting parameters. Names indicate function.
        # @{


        ## Time allowed for QCL paramters to be set.
        self.qcl_set_params_timeout = 5
        ## Time allowed for the laser to be armed.
        self.arm_laser_timeout = 20
        ## Time allowed to attempt to cool the TECs to desired temperature.
        self.cool_tecs_timeout = 60
        ## Additional time allowed for cooling of the TECs.
        self.cool_tecs_additional = 10
        ## Time allowed to turn on the laser itself.
        self.turn_on_laser_timeout = 30
        ## Number of attempts allowed for trying to turn on the laser.
        self.laser_on_attempts = 3
        ## Time to wait after the laser has been turned on for normalization of operation.
        self.laser_on_wait = 5
        # @}


        ## @name Laser_State
        # State of all variable laser parameters.
        # @{

        ## Whether or not the laser is on.
        self.laser_on = False
        ## Current from the QCL in MilliAmps.
        self.qcl_current_ma = 0
        ## Pulse rate of the laser in Hertz according to the QCL.
        self.qcl_pulse_rate_hz = 0
        ## Pulse width of the laser in nanoseconds according to the QCL.
        self.qcl_pulse_width_ns = 0
        ## Laser wavelength in the units specified by the next parameter.
        self.wavelength = 0
        ## Wavelength units, as specified by an integer corresponding to each type of unit.
        self.qcl_wvlen_units = 0
        ## QCL temperature, kept constant. In Degrees Celsius.
        self.qcl_temp = 17

        #@}

        ## @name Lockin_Parameters
        # All necessary communication information for the Lock In.
        #@{

        ## IP of the device
        self.lockin_ip = '192.168.48.102'
        ## Port to use for communication
        self.lockin_port = 8004
        ## Amplitude modulation factor.
        self.lockin_amplitude = 1.0
        ## Poll sample length for the lock in.
        self.lockin_poll_length = 30
        ## Demod channel, for paths on the device.
        self.lockin_demod_c = '0'
        ## Signal input channel
        self.lockin_in_c = '0'
        ## Oscillator variable.
        self.lockin_osc_c = '0'
        ## Oscillation frequency, 30e5 #[Hz] this matches the laser controller
        self.lockin_osc_freq = 100000
        ## Time constant, set to 3e-3 # 0.0075 # 0.001  [s]
        self.lockin_time_constant = 1e-2 #
        ## Demod index for the channel.
        self.demod_idx = float(self.lockin_demod_c) + 1
        ## Time allowed to poll data in ms
        self.poll_timeout = 500
        ## Demod rate of 80 # 300 [samples / s]
        self.demod_rate = 2e3

        #@}

        ## @name Sidekick_SDK_Variables
        # Variables required for and set by Sidekick SDK setup.
        #@{

        ## Used to see if the SDK is indeed retrieved.
        self.sidekick_sdk_ret_success = 0
        ## SDK object used to access all laser operation functions.
        self.sdk = CDLL(self.sdk_location) if testing_sdk is None else testing_sdk
        ## Zurich Instrumentes SDK for lockin actions.
        self.zi_sdk = zhinst if testing_zi_sdk is None else testing_zi_sdk

        self.__call_sdk_bool(self.sdk.SidekickSDK_Initialize,
                            'SDK initialization successful', 'Unable to initialize SDK')
        ## Daylight SDK Object pointer to pass to laser functions.
        self.handle = None
        ## ZI sdk object pointer for lock-in function.
        self.device = None
        ## DAQ object for lockin setup.
        self.daq = None

        #@}

        ## @name Set_Parameter_Constants
        # Constants required for setting laser parameters.
        #@{

        ## Reading requires passing false to readwrite functions.
        self.qcl_read = c_bool(False)
        ## Writing requires passing true to readwrite functions.
        self.qcl_write = c_bool(True)
        ## Sets up SIDEKICK_SDK_SCAN_START_STEP_MEASURE as operation.
        self.scan_operation = c_uint8(7)
        ## Does not permit bidirectional scans.
        self.bidirectional_scans = c_uint8(0)
        ## Performs just a single scan per call.
        self.scan_count = c_uint16(1)
        ## Maintains laser emission between steps.
        self.keep_on = c_uint8(1)
        ## Dummy parameter for function which is meant for non SideKick Projects.
        self.pref_qcl = c_uint8(0)

        #@}

    ## @brief Attempts to start the laser with the given system parameters.
    #
    #  @param wave Wavelength, units specified by waveunit.
    #  @param current QCL current in MilliAmps.
    #  @param pulsewid Pulse width in Nanoseconds.
    #  @param pulserate Pulse rate in Hz.
    #  @param waveunit Integer specifying unit for wavelength. Defaults to 2: wavenumber.
    #  @exception QCL_Exception Thrown if errors arrise in this portion of the process.
    #  @exception Laser_Exception Thrown if errors arrise in this portion of the process.
    #  @exception SDK_Exception Thrown if errors arrise in this portion of the process.
    def startup(self, wave, current, pulsewid, pulserate, waveunit = 2):
        # Set all system parameters to the desired initial values
        self.wavelength = wave
        self.qcl_wvlen_units = waveunit
        self.qcl_current_ma = current
        self.qcl_pulse_width_ns = pulsewid
        self.qcl_pulse_rate_hz = pulserate

        # Begin firing the physical system
        try:
            self.__connect_laser()
            self.__arm_laser()
            self.__set_qcl_params()
            self.__cool_tecs()
            self.__turn_on_laser()
            self.__connect_to_lockin()
            self.__initialize_lockin()
        except:
            e = sys.exc_info()[0]
            self.turn_off_laser()
            raise e

    ## @Brief Connect to laser using USB port.
    #
    #  @exception SDK_Exception Thrown if __connect_laser does not establish connection.
    def __connect_laser(self):
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

    ## @brief Arm laser for general use.
    #
    #  @exception Laser_Exception Thrown if __arm_laser unable to arm the laser within timeout period.
    def __arm_laser(self):
        is_armed_ptr = pointer(c_bool(False))
        self.sdk.SidekickSDK_SetLaserArmDisarm(self.handle, True)
        self.sdk.SidekickSDK_ExecLaserArmDisarm(self.handle)
        self.sdk.SidekickSDK_ReadInfoStatusMask(self.handle)
        self.sdk.SidekickSDK_isLaserArmed(self.handle, is_armed_ptr)
        old_t = time.time()
        while not is_armed_ptr.contents.value:
            time.sleep(1)
            self.sdk.SidekickSDK_ReadInfoStatusMask(self.handle)
            self.sdk.SidekickSDK_isLaserArmed(self.handle, is_armed_ptr)
            curr_t = time.time()
            if curr_t - old_t > self.arm_laser_timeout:
                raise Laser_Exception("Laser not armed.")
        sys.stderr.write("Laser is armed.\n")

    ## @brief Set relevant parameters of the QCL controller.
    #
    #  @exception QCL_Exception Thrown if __set_qcl_params unable to set the parameters within the given time.
    def __set_qcl_params(self):
        qcl_params = self.__read_qcl_params()
        qcl_params['pulse_rate_hz_ptr'].contents = c_uint32(self.qcl_pulse_rate_hz)
        qcl_params['temp_c_ptr'].contents = c_float(self.qcl_temp)
        qcl_params['current_ma_ptr'].contents = c_uint16(self.qcl_current_ma)
        qcl_params['pulse_width_ns_ptr'].contents = c_uint32(self.qcl_pulse_width_ns)
        self.__update_qcl_params(qcl_params)
        old_t = time.time()
        while (qcl_params['pulse_rate_hz_ptr'].contents.value != self.qcl_pulse_rate_hz or
               qcl_params['temp_c_ptr'].contents.value != self.qcl_temp or
               qcl_params['current_ma_ptr'].contents.value != self.qcl_current_ma or
               qcl_params['pulse_width_ns_ptr'].contents.value != self.qcl_pulse_width_ns):
            qcl_params = self.__read_qcl_params()
            curr_t = time.time()
            if curr_t - old_t > self.qcl_set_params_timeout:
                raise QCL_Exception("Laser parameters not set.")
            time.sleep(1)
        sys.stderr.write("Laser parameters have been set successfully.\n")

    ## @brief Set wavelength for the laser emission in units stored by the object.
    #
    #  @param value Wavelength value to which the laser will be tuned.
    def set_wavelength(self, value):
        units = self.qcl_wvlen_units
        self.wavelength = value
        set_ptr = pointer(c_bool(True))
        self.sdk.SidekickSDK_SetTuneToWW(self.handle, c_uint8(2), c_float(value), c_uint8(0))
        self.sdk.SidekickSDK_ExecTuneToWW(self.handle)
        time.sleep(20)
        sys.stderr.write("Laser wavelength tuning to desired value.\n")

    ## @brief Set pulse width of the laser emission to value.
    #
    #  @param value Desired pulsewidth value in ns.
    #  @exception QCL_Exception Thrown if set_pulsewidth doesn't set the parameter within the required time.
    def set_pulsewidth(self, value):
        self.qcl_pulse_width_ns = value
        self.__set_qcl_params()

    ## @brief Set pulse rate of the laser emission to value.
    #
    #  @param value Desired pulse rate in Hz.
    #  @exception QCL_Exception Thrown if set_pulserate doesn't set the parameter within the required time.
    def set_pulserate(self, value):
        self.qcl_pulse_rate_hz = value
        self.__set_qcl_params()

    ## @brief Set current for the laser emission.
    #
    #  @param value Desired current in mA.
    #  @exception QCL_Exception Thrown if set_pulserate doesn't set the parameter within the required time.
    def set_current(self, value):
        self.qcl_current_ma = value
        self.__set_qcl_params()

    ## @brief Wait for TECs to cool to correct temp.
    #
    #  @exception Laser_Exception Thrown if the TECs are unable to cool to the desired temperature.
    def __cool_tecs(self):
        is_temp_set_ptr = pointer(c_bool(False))
        self.sdk.SidekickSDK_ReadInfoStatusMask(self.handle)
        self.sdk.SidekickSDK_isTempStatusSet(self.handle, is_temp_set_ptr)
        old_t = time.time()
        while not is_temp_set_ptr.contents.value:
            time.sleep(1)
            self.sdk.SidekickSDK_ReadInfoStatusMask(self.handle)
            self.sdk.SidekickSDK_isTempStatusSet(self.handle, is_temp_set_ptr)
            curr_t = time.time()
            if curr_t - old_t > self.cool_tecs_timeout:
                raise Laser_Exception("TECs are not cooled.")
        time.sleep(self.cool_tecs_additional)
        sys.stderr.write('TECs are at the desired temperature.\n')

    ## @brief Turn on the actual laser and begin emitting.
    #
    #  @exception Laser_Exception if laser does not turn on within a certain number of attempts.
    def __turn_on_laser(self):
        status_word_ptr = pointer(c_uint32())
        error_word_ptr = pointer(c_uint16())
        warning_word_ptr = pointer(c_uint16())
        is_emitting_ptr = pointer(c_bool(False))
        turn_on = True
        attempts = 0
        trial_fail = False

        while not self.laser_on and attempts < self.laser_on_attempts:
            attempts += 1
            self.sdk.SidekickSDK_SetLaserOnOff(self.handle, 0, turn_on)
            self.sdk.SidekickSDK_ExecLaserOnOff(self.handle)
            self.sdk.SidekickSDK_ReadInfoStatusMask(self.handle)
            self.sdk.SidekickSDK_isLaserFiring(self.handle, is_emitting_ptr)
            sys.stderr.write("Turn on attempts: {}.\n".format(attempts))

            old_t = time.time()
            curr_t = 0
            while not is_emitting_ptr.contents.value:
                time.sleep(self.laser_on_wait)
                self.sdk.SidekickSDK_isLaserFiring(self.handle, is_emitting_ptr)
                curr_t = time.time()
                if curr_t - old_t > self.turn_on_laser_timeout:
                    trial_fail = True
                    break
            self.sdk.SidekickSDK_ReadStatusMask(
                self.handle, status_word_ptr, error_word_ptr, warning_word_ptr)
            sys.stderr.write('Status Word is {}, Error Word is {}, Warning Word is {}.\n'.format(
                status_word_ptr.contents.value, error_word_ptr.contents.value,
                warning_word_ptr.contents.value))

            if trial_fail:
                trial_fail = False
                continue

            self.laser_on = True

        if not is_emitting_ptr.contents.value:
            raise Laser_Exception("Laser did not turn on.")
        sys.stderr.write("Laser is firing.\n")
        self.laser_on = True

    ## @brief Connect to lock-in amplifier.
    def __connect_to_lockin(self):
        self.daq = self.zi_sdk.ziPython.ziDAQServer(self.lockin_ip, self.lockin_port)
        self.device = self.zi_sdk.utils.autoDetect(self.daq)
        sys.stderr.write('Connected to lock-In device {}.\n'.format(self.device))

    ## @brief Initialize lock-in amplifier.
    def __initialize_lockin(self):
        sys.stderr.write("Initializing lock-in amp.\n")

        devtype = self.daq.getByte('/' + self.device + '/features/devtype')
        options = self.daq.getByte('/' + self.device + '/features/options')

        self.daq.setDouble('/' + self.device + '/demods/*/rate', 0.0)
        self.daq.setInt('/' + self.device + '/demods/*/trigger', 0)
        self.daq.setInt('/' + self.device + '/sigouts/*/enables/*', 0)

        if 'UHF' in devtype:
            self.daq.setInt('/' + self.device + '/demods/*/enable', 0)
            self.daq.setInt('/' + self.device + '/scopes/*/enable', 0)
        elif 'HF2' in devtype:
            self.daq.setInt('/' + self.device + '/scopes/*/trigchannel', -1)
        elif 'MF' in devtype:
            self.daq.setInt('/' + self.device + '/scopes/*/enable', 0)

        self.daq.setInt('/' + self.device + '/sigins/' + self.lockin_in_c + '/imp50', 0)
        self.daq.setInt('/' + self.device + '/sigins/' + self.lockin_in_c + '/ac', 1)
        self.daq.setInt('/' + self.device + '/sigins/' + self.lockin_in_c + '/diff', 0)
        self.daq.setInt('/' + self.device + '/sigins/' + self.lockin_in_c + '/float', 0)
        self.daq.setDouble('/' + self.device + '/sigins/' + self.lockin_in_c + '/range', 2.0)

        self.daq.setDouble('/' + self.device + '/demods/*/phaseshift', 0)
        self.daq.setInt('/' + self.device + '/demods/*/order', 4)
        self.daq.setDouble('/' + self.device + '/demods/' + self.lockin_demod_c + '/rate', self.demod_rate)
        self.daq.setInt('/' + self.device + '/demods/' + self.lockin_demod_c + '/harmonic', 1)
        if 'UHF' in devtype:
            self.daq.setInt('/' + self.device + '/demods/' + self.lockin_demod_c + '/enable', 1)
        if 'MF' in options:
            self.daq.setInt('/' + self.device + '/demods/*/oscselect', float(self.lockin_osc_c))
            self.daq.setInt('/' + self.device + '/demods/*/adcselect', float(self.lockin_in_c))
        self.daq.setDouble('/' + self.device + '/demods/*/timeconstant', self.lockin_time_constant)
        self.daq.setDouble('/' + self.device + '/oscs/' + self.lockin_osc_c + '/freq', self.lockin_osc_freq)

        self.daq.setInt('/' + self.device + '/extrefs/0/enable', 1)
        self.daq.setDouble('/' + self.device + '/triggers/in/0/level', 0.500)
        self.daq.setInt('/' + self.device + '/demods/0/adcselect', 1)  # trigger 1 rising edge for transfer
        self.daq.setInt('/' + self.device + '/demods/0/adcselect', 0)  # voltage signal in 1
        self.daq.setInt('/' + self.device + '/demods/1/adcselect', 2)  # ext ref = trigger 1
        self.daq.setInt('/' + self.device + '/demods/1/adcselect', 8)  # ext ref = aux in 1

        self.daq.unsubscribe('*')
        self.daq.sync()
        time.sleep(10 * self.lockin_time_constant)

    ## @brief Turn off and disconnect from laser.
    def turn_off_laser(self):
        turn_on = False
        arm = False
        self.sdk.SidekickSDK_SetLaserOnOff(self.handle, 0, turn_on)
        self.sdk.SidekickSDK_ExecLaserOnOff(self.handle)
        self.sdk.SidekickSDK_SetLaserArmDisarm(self.handle, arm)
        self.sdk.SidekickSDK_ExecLaserArmDisarm(self.handle)
        self.sdk.SidekickSDK_Disconnect(self.handle)
        sys.stderr.write("Laser has been turned off.\n")

    ## @brief Read QCL parameters into dictionary.
    #
    #  @returns Dictionary of QCL parameter pointer.
    def __read_qcl_params(self):
        params = {'qcl_slot_ptr': pointer(c_uint8()), 'pulse_rate_hz_ptr': pointer(c_uint32()),
                  'pulse_width_ns_ptr': pointer(c_uint32()), 'current_ma_ptr': pointer(c_uint16()),
                  'temp_c_ptr': pointer(c_float()), 'laser_mode_ptr': pointer(c_uint8()),
                  'pulse_mode_ptr': pointer(c_uint8()), 'vsrc_ptr': pointer(c_float())}
        self.sdk.SidekickSDK_ReadWriteLaserQclParams(self.handle, self.qcl_read, 0)
        self.sdk.SidekickSDK_GetLaserQclParams(
            self.handle, params['qcl_slot_ptr'], params['pulse_rate_hz_ptr'],
            params['pulse_width_ns_ptr'], params['current_ma_ptr'],
            params['temp_c_ptr'], params['laser_mode_ptr'],
            params['pulse_mode_ptr'], params['vsrc_ptr'])
        return params

    ## @brief Update QCL parameters with values in argument.
    #
    #  @param params Dictionary of pointers to QCL parameter values.
    def __update_qcl_params(self, params):
        self.sdk.SidekickSDK_SetLaserQclParams(
            self.handle, params['qcl_slot_ptr'].contents, params['pulse_rate_hz_ptr'].contents,
            params['pulse_width_ns_ptr'].contents, params['current_ma_ptr'].contents,
            params['temp_c_ptr'].contents, params['laser_mode_ptr'].contents,
            params['pulse_mode_ptr'].contents, params['vsrc_ptr'].contents)
        self.sdk.SidekickSDK_ReadWriteLaserQclParams(self.handle, self.qcl_write, 0)

    ## @brief Collects observed laser emission data.
    #
    #   Function for gathering data from detector via lock-in amp. Appends
    #   data collected (1D list), time axis (1D list), standard
    #   deviation (1D list) to arguments
    #  @param data_list List object to which the data is appended.
    #  @param time_list List object to which the time series for the data is appended.
    #  @returns 2 numpy arrays, first the observed data and second the corresponding time series.
    def collect_data(self, data_list, time_list):
        self.daq.sync()
        self.daq.subscribe('/' + self.device + '/demods/' + self.lockin_demod_c + '/sample')
        poll_data = self.daq.poll(self.lockin_poll_length, self.poll_timeout)

        if self.device in poll_data and 'demods' in poll_data[self.device]:
            if len(poll_data[self.device]['demods']) >= int(self.lockin_demod_c):
                if 'sample' in poll_data[self.device]['demods'][self.lockin_demod_c]:
                    sample = poll_data[self.device]['demods'][self.lockin_demod_c]['sample']
                    x = sample['x']
                    y = sample['y']
                    data = np.hypot(x, y)
                    clockbase = float(self.daq.getInt('/' + self.device + '/clockbase'))
                    time_axis = sample['timestamp'] / clockbase
                    if sample['time']['dataloss']:
                        sys.stderr.write('warning: Sample loss detected.\n')
        else:
            data = []
            time_axis = []
        self.daq.unsubscribe('*')
        return np.array(data), np.array(time_axis)

    ## @brief Call SDK function with optional arguments and check return value.
    #
    #  @param sdk_fn SDK function to call
    #  @param success_msg string message to print if function returns success
    #  @param error_msg string message to print if function fails
    #  @param *args optional arguments to pass to SDK function.
    #  @exception SDK_Exception Thrown if SDK function fails
    def __call_sdk_bool(self, sdk_fn, success_msg="Success", error_msg="Failure", *args):
        ret = sdk_fn() if not args else sdk_fn(*args)
        if ret == self.sidekick_sdk_ret_success:
            sys.stderr.write(success_msg + "\n")
        else:
            raise SDK_Exception(error_msg)

    ## @brief Call SDk function and check boolean status value set by reference.
    #
    #  @param sdk_fn SDK function to call
    #  @param success_msg string message to print if function returns success
    #  @param error_msg string message to print if function fails
    #  @exception SDK_Exception Thrown if SDK function fails
    def __call_sdk_bool_ptr(self, sdk_fn, success_msg, error_msg):
        ret_ptr = pointer(c_bool(False))
        sdk_fn(self.handle, ret_ptr)
        if ret_ptr.contents.value:
            sys.stderr.write(success_msg + "\n")
        else:
            self.sdk.SidekickSDK_Disconnect(self.handle)
            raise SDK_Exception(error_msg)
