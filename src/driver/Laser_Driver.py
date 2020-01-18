import Laser_SDK_Conn
import Laser_Lockin_Conn
import time
import sys
from ctypes import pointer, c_uint32, c_uint16, c_uint8, c_bool, c_float, c_char


## Exception class indicating an issue with laser-centric systems.
class Laser_Exception(Exception):
    pass

## Exception class indicating an issue with the QCL controller.
class QCL_Exception(Exception):
    pass


## @brief Driver for controlling the Daylight solutions laser through the SideKick SDK.
#
#  Driver for controlling physical functions of the laser, allowing complete
#  control over emission.
class Laser_Driver:

    ## @brief Initialize SDKs and provide hook for testing.
    #
    # @param testing_sdk SideKickSDK library if None, else class with equivalent methods for testing.
    # @param testing_zisdk ZI library if None, else class with equivalent methods for testing.
    # @param sdk_version 86 or 64 (which version of Sidekick sdk to load).
    # @exceptions SDK_Exception if SDK cannot be initialized.
    def __init__(self, sdk_version=None):
        sdk_conn = Laser_SDK_Conn(sdk_version)
        lockin_conn = Laser_Lockin_Conn()
        self.sdk = sdk_conn.connection

        ##
        # @defgroup Timing_Variables
        # Variables for timing of setting parameters. Names indicate function.
        ##@{
        ## Time allowed for QCL parameter or wavelength to be set. TODO: Maybe 5?
        self.parameter_timeout = 20
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
        ##@}

        ##
        # @defgroup Set_Parameter_Constants
        # Constants required for setting laser parameters.
        ##@{
        # Reading requires passing false to readwrite functions.
        self.qcl_read = c_bool(False)
        # Writing requires passing true to readwrite functions.
        self.qcl_write = c_bool(True)
        # Sets up SIDEKICK_SDK_SCAN_START_STEP_MEASURE as operation.
        self.scan_operation = c_uint8(7)
        # Does not permit bidirectional scans.
        self.bidirectional_scans = c_uint8(0)
        # Performs just a single scan per call.
        self.scan_count = c_uint16(1)
        # Maintains laser emission between steps.
        self.keep_on = c_uint8(1)
        # Dummy parameter for function which is meant for non SideKick Projects.
        self.pref_qcl = c_uint8(0)
        ##@}

        ##
        # @defgroup Laser_State
        # State of all variable laser parameters.
        ##@{
        ## Whether or not the laser is on.
        self.laser_on = False
        ## Current from the QCL in MilliAmps
        self.qcl_current = 0
        ## Pulse rate of the laser in Hertz according to the QCL.
        self.qcl_pulserate = 0
        ## Pulse width of the laser in nanoseconds according to the QCL.
        self.qcl_pulsewidth = 0
        ## Laser wavelength in the units specified by the next parameter.
        self.qcl_wavelength = 0
        ## Wavelength units, as specified by an integer corresponding to each type of unit.
        self.qcl_wvlen_units = c_uint8()
        ## QCL temperature, kept constant. In Degrees Celsius.
        self.qcl_temp = 17
        ###@}

        ## @vars Handle pointer for the laser object.
        self.handle = None


    ## @brief Attempts to start the laser with the given system parameters.
    #
    #  @param wave Wavelength, units specified by waveunit.
    #  @param waveunit Integer specifying unit for wavelength (2: Wavenumber).
    #  @param current QCL current in MilliAmps.
    #  @param pulsewid Pulse width in Nanoseconds.
    #  @param pulserate Pulse rate in Hz.
    #  @exceptions QCL_Exception Thrown if errors arrise in this portion of the process.
    #  @exceptions Laser_Exception Thrown if errors arrise in this portion of the process.
    #  @exceptions SDK_Exception Thrown if errors arrise in this portion of the process.
    def startup(self, wave, waveunit, current, pulsewid, pulserate):

        # Set all system parameters to the desired initial values
        self.qcl_wavelength = wave
        self.qcl_wvlen_units = waveunit
        self.qcl_current = current
        self.qcl_pulsewidth = pulsewid
        self.qcl_pulserate = pulserate

        # Begin firing the physical system
        try:
            self.__connect_laser()
            self.__arm_laser()
            self.__set_qcl_params()
            self.__cool_tecs()
            self.__turn_on_laser()
            lockin_conn.connect_to_lockin()
            lockin_conn.initialize_lockin()
        except:
            e = sys.exc_info()[0]
            self.turn_off_laser()
            raise e

    ## @Brief Connect to laser using USB port.
    #
    #  @exceptions SDK_Exception Thrown if __connect_laser does not establish connection.
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
    #  @exceptions Laser_Exception Thrown if __arm_laser unable to arm the laser within timeout period.
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
        sys.stderr.write("Laser is armed.")

    ## @brief Set wavelength for the laser emission.
    #
    #  @param units Integer specifying unit for wavelength (2: Wavenumber).
    #  @param value Wavelength value to which the laser will be tuned.
    #  @exceptions Laser_Exception Thrown if set_wavelength does not tune the device to the desired value.
    def set_wavelength(self, units, value):
        self.wavelength = value
        self.wvlen_units = units
        set_ptr = pointer(c_bool(False))
        self.sdk.SidekickSDK_SetTuneToWW(self.handle, c_uint8(units), c_float(value), c_uint8(0))
        self.sdk.SidekickSDK_ExecTuneToWW(self.handle)
        self.sdk.SidekickSDK_isTuned(self.handle, set_ptr)
        old_t = time.time()
        while not set_ptr.contents.value:
            time.sleep(1)
            self.sdk.SidekickSDK_ExecTuneToWW(self.handle)
            self.sdk.SidekickSDK_isTuned(self.handle, set_ptr)
            curr_t = time.time()
            if curr_t - old_t > self.parameter_timeout:
                raise Laser_Exception("Wavelength not tuned.")
        sys.stderr.write("Laser wavelength set successfully.")

    ## @brief Wait for TECs to cool to correct temp.
    #
    #  @exceptions Laser_Exception Thrown if the TECs are unable to cool to the desired temperature.
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
                raise HardwareException("TECs are not cooled.")
        time.sleep(self.cool_tecs_additional)
        sys.stderr.write('TECs are at the desired temperature.')

    ## @brief Turn on the actual laser and begin emitting.
    #
    #  @exceptions Laser_Exception if laser does not turn on within a certain number of attempts.
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
            sys.stderr.write("Turn on attempts: {}.".format(attempts))

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
            sys.stderr.write('Status Word is {}, Error Word is {}, Warning Word is {}.'.format(
                status_word_ptr.contents.value, error_word_ptr.contents.value,
                warning_word_ptr.contents.value))

            if trial_fail:
                trial_fail = False
                continue

            self.laser_on = True

        if not is_emitting_ptr.contents.value:
            raise Laser_Exception("Laser did not turn on.")
        sys.stderr.write("Laser is firing.")
        self.laser_on = True

    ## @brief Turn off and disconnect from laser.
    def turn_off_laser(self):
        turn_on = False
        arm = False
        self.sdk.SidekickSDK_SetLaserOnOff(self.handle, 0, turn_on)
        self.sdk.SidekickSDK_ExecLaserOnOff(self.handle)
        self.sdk.SidekickSDK_SetLaserArmDisarm(self.handle, arm)
        self.sdk.SidekickSDK_ExecLaserArmDisarm(self.handle)
        self.sdk.SidekickSDK_Disconnect(self.handle)
        sys.stderr.write("Laser has been turned off.")

    ## @brief Set relevant parameters of the QCL controller.
    #
    #  @exceptions QCL_Exception Thrown if __set_qcl_params unable to set the parameters within the given time.
    def __set_qcl_params(self):
        qcl_params = self.__read_qcl_params()
        qcl_params['pulse_rate_hz_ptr'].contents = c_uint32(self.qcl_pulserate)
        qcl_params['temp_c_ptr'].contents = c_float(self.qcl_temp)
        qcl_params['current_ma_ptr'].contents = c_uint16(self.qcl_current)
        qcl_params['pulse_width_ns_ptr'].contents = c_uint32(self.qcl_pulsewidth)
        self.__update_qcl_params(qcl_params)
        old_t = time.time()
        while (qcl_params['pulse_rate_hz_ptr'].contents.value != self.qcl_pulserate or
               qcl_params['temp_c_ptr'].contents.value != self.qcl_temp or
               qcl_params['current_ma_ptr'].contents.value != self.qcl_current or
               qcl_params['pulse_width_ns_ptr'].contents.value != self.qcl_pulsewidth):
            qcl_params = self.__read_qcl_params()
            curr_t = time.time()
            if curr_t - old_t > self.parameter_timeout:
                raise QCL_Exception("Laser parameters not set.")
            time.sleep(1)
        sys.stderr.write("Laser parameters have been set successfully.")

    ## @brief Read QCL parameters into dictionary.
    #
    #  @returns Dictionary of QCL parameter pointers
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


    ## @brief Collects observed laser emission data.
    #
    #   Function for gathering data from detector via lock-in amp. Appends
    #   data collected (1D list), time axis (1D list)
    #
    #  @param data_list List object to which the data is appended.
    #  @param time_list List object to which the time series for the data is appended.
    def collect_data(self, data_list, time_list):



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
