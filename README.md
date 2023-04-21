# Raspberry Pi Internet Chronometer

![Chronometer Display](https://user-images.githubusercontent.com/11377430/233668284-af71e1e1-1659-4ad9-b0de-973f98da791a.png "Chronometer Display")

Turn your RaspberryPi in to an [Internet Chronometer](https://www.reddit.com/r/raspberry_pi/comments/bb8ddc/made_a_rpi_desk_clock_as_a_means_of_learning) .

Display is a [UCTRONICS 3.5 Inch HDMI display](https://www.amazon.com/gp/product/B076M399XX).

# Features:

+ Utilizes system time via NTP.  All you need to provide is an internet connection.
+ Customizable world clock timezones

## Description / Abbreviations
+ TOP
   * Completion chart for current time units([S]econd, [M]inute, [H]our, [D]ay, [W]eek, [M]onth, [Y]ear, [C]entury).

+ MIDDLE
   * Left: Time Systems
        * UTC - [Coordinated Universal Time](https://en.wikipedia.org/wiki/Coordinated_Universal_Time)
        * DEC - [Decimal Time](https://en.wikipedia.org/wiki/Decimal_time)
        * SOL - [Solar Time](https://en.wikipedia.org/wiki/Solar_time)
        * LST - [Local Sidereal Time](https://en.wikipedia.org/wiki/Sidereal_time)
        * UNX - [Unix Epoch Time](https://en.wikipedia.org/wiki/Unix_time)
        * SIT - [Swatch Internet Time](https://en.wikipedia.org/wiki/Swatch_Internet_Time)
        * NET - [New Earth Time](https://en.wikipedia.org/wiki/New_Earth_Time)
        * HEX - [Hexadecimal Time](https://en.wikipedia.org/wiki/Hexadecimal_time)
        * [Binary Clock](https://en.wikipedia.org/wiki/Binary_clock)
    * Right: Date Systems
        * IFC - [International Fixed Calendar](https://en.wikipedia.org/wiki/International_Fixed_Calendar)
        * TWC - [The World Calendar](https://en.wikipedia.org/wiki/World_Calendar)
        * PAX - [Pax Calendar](https://myweb.ecu.edu/mccartyr/colligan.html)
        * JUL - [Julian Date](https://en.wikipedia.org/wiki/Julian_day)
+ BOTTOM
   * Left: World Clock
    * Right: Leap Statistics
        * DFT - Leap Drift - Current time offset that has to be corrected by the[leap cycle](https://en.wikipedia.org/wiki/Leap_year)
        * NXT - Next Leap Day
        * PER - Leap Period, percentage elapsed of current period between leap days
        * CYC - Leap Cycle, percentage elapsed of total 400 year leap cycle
    * [NTP](https://en.wikipedia.org/wiki/Network_Time_Protocol) Status (Server, Stratum, Delay, Offset)


# Requirements

* In order to get the HDMI display to work with this code, you need to set the resolution to 480x320 and set the console font to VGA 8x14.  Run `sudo dpkg-reconfigure console-setup` to configure these settings.

* NTP daemon needs to be running as a background service: `sudo apt install ntp`
* Python 3 (Should already be installed on RPi): `sudo apt install python3`
* `pytz` module for python3: `pip3 install pytz` or from your distro's repositories.

# Installation for Raspberry Pi
1. Download and install via pip:
   ```
    pip install git+https://github.com/rothman857/chronometer.git
    ```
2. Running for the first time will generate a .chrono_config file with default values:
    ```
    python -m chronometer
    ```
3. Update .chrono_config with relavent values.
 
4. Update time zones as desired.  Timezones must be in pytz format.  To see a list of available options, run the following:
    ```
    python -m chronometer.timezones <optional country name>
    ```

    For example, to find a timezone value for Japan, run `python -m chronometer.timezones japan`.  The ouptut will look like:
    ```
    Country: Japan
        Asia/Tokyo: +0900
    ```
    The correct value to use for .chrono_config is `Japan = Asia/Tokyo`
5. Start the chronometer:
    ```
    python -m chronometer
    ```

6. If you wish to have the chronometer start at boot, add the above command to your .bashrc
