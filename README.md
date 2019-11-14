# Raspberry Pi Chronometer

![Chronometer Display](screen.jpg "Chronometer Display")

Turn your RaspberryPi in to an [Internet Chronometer](https://www.reddit.com/r/raspberry_pi/comments/bb8ddc/made_a_rpi_desk_clock_as_a_means_of_learning/).

Display is a [UCTRONICS 3.5 Inch HDMI display](https://www.amazon.com/gp/product/B076M399XX).

### Features:

+ Utilizes system time via NTP.  All you need to provide is an internet connection.
+ Customizable banner that can be changed in `config.xml`
+ Customizable world clock timezones that can be changed in `config.xml`.  Timezones must be in pytz format:
    ```
    import pytz
    for tz in pytz.all_timezones:
        print(tz)
    ```

### Description
+ TOP
    * Progress chart for current time units (**S**econd, **M**inute, **H**our, **D**ay, **M**onth, **Y**ear, **C**entury).
+ MIDDLE
    * World Clock
+ BOTTOM
    * UTC - [Coordinated Universal Time](https://en.wikipedia.org/wiki/Coordinated_Universal_Time)
    * MET - [Metric Time](https://en.wikipedia.org/wiki/Metric_time)
    * SOL - [Solar Time](https://en.wikipedia.org/wiki/Solar_time)
    * LST - [Local Sidereal Time](https://en.wikipedia.org/wiki/Sidereal_time)
    * UNX - [Unix Epoch Time](https://en.wikipedia.org/wiki/Unix_time)
    * SIT - [Swatch Internet Time](https://en.wikipedia.org/wiki/Swatch_Internet_Time)
    * NET - [New Earth Time](https://en.wikipedia.org/wiki/New_Earth_Time)
    * HEX - [Hexadecimal Time](https://en.wikipedia.org/wiki/Hexadecimal_time)
    * [Binary Clock](https://en.wikipedia.org/wiki/Binary_clock)
    * INT FIX - [International Fixed Calendar](https://en.wikipedia.org/wiki/International_Fixed_Calendar)
    * RED JDN - [Reduced Julian Date Number](https://en.wikipedia.org/wiki/Julian_day)
    * NTP Status (Server, Stratum, Delay, Offset)


### Notes:

* In order to get the display to work with this code, you need to set the resolution to 480x320, and set the console font to VGA 8x14.
* `longitude` value needs to updated in `chrono-config` to ensure accurate solar time and sidereal time values.  West longitude is indicated by a negative value.
* NTP daemon needs to be running as a background service: `sudo apt install ntp`

### Required Python modules:

* `pytz`

Modules can be install using `pip install [module]` or from your distros repositories.
