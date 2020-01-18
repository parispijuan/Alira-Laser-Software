import time
import zhinst
import zhinst.ziPython
import zhinst.utils

## @brief Allows for establishment of connection to the Zurich Instruments Lock-in.
#
#  Connects to the Lock-in amplifier to ensure that the laser signals are clearly
#  interpretted and separated from teh noise.
class Laser_Lockin_Conn:

    ## @brief Constructor for the Lock-in Connection class.
    #
    #  Sets all required communication constants for interacting
    #  with the Lock-in.
    def __init__():

        ##
        # @defgroup Lockin_Parameters
        # All necessary communication information for the Lock In.
        ##@{
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
        ##@}

        ## @vars Sets up Zurich Instruments SDK.
        self.zi_sdk = zhinst

        ## @vars DAQ for access to lock-in by driver.
        self.daq = None

        ## @vars Device ID for access to lock-in by driver.
        self.device = None


    ## @brief Connect to lock-in amplifier.
    def connect_to_lockin(self):
        self.daq = self.zi_sdk.ziPython.ziDAQServer(self.lockin_ip, self.lockin_port)
        self.device = self.zi_sdk.utils.autoDetect(self.daq)
        sys.stderr.write('Connected to lock-In device {}.'.format(self.device))

    ## @brief Initialize lock-in amplifier.
    def initialize_lockin(self):
        sys.stderr.write("Initializing lock-in amp")

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


    ## @brief Collects observed laser emission data.
    #
    #   Function for gathering data from detector via lock-in amp. Appends
    #   data collected (1D list), time axis (1D list)
    # 
    #  @param data_list List object to which the data is appended.
    #  @param time_list List object to which the time series for the data is appended.
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
                        sys.stderr.write('warning: Sample loss detected.')
        else:
            data = []
            time_axis = []
        self.daq.unsubscribe('*')
        data_list.append(data)
        time_list.append(time_axis)
