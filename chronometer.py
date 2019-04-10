#!/usr/bin/python3
import datetime
import time
import os
import sys
import string
import ephem
from myColors import colors
from pytz import timezone


dbg = False

STATIC=0
RELATIVE=1

def debug(text,var):
    if dbg:
        print("DEBUG>>> "+text + ": " + str(var))

def getRelativeDate(ordinal,weekday,month,year):
    firstday = (datetime.datetime(year,month,1).weekday() + 1)%7
    firstSunday = (7 - firstday) % 7 + 1
    return datetime.datetime(year,month,firstSunday + weekday + 7*(ordinal-1))
    
def solartime(observer, sun=ephem.Sun()):
    sun.compute(observer)
    # sidereal time == ra (right ascension) is the highest point (noon)
    hour_angle = observer.sidereal_time() - sun.ra
    return ephem.hours(hour_angle + ephem.hours('12:00')).norm  # norm for 24h
    
city = ephem.city("Atlanta")


            
timeZoneList = [["Eastern",        timezone("US/Eastern")],
                ["Central",        timezone("US/Central")],
                ["Mountain",    timezone("US/Mountain")],
                ["Pacific",        timezone("US/Pacific")],
                ["GMT",            timezone("GMT")],
                ["Australia",    timezone("Australia/Sydney")],
                ["Germany",        timezone("Europe/Berlin")],
                ["Hong Kong",    timezone("Asia/Hong_Kong")],
                ["India",        timezone("Asia/Kolkata")],
                ["Japan",        timezone("Asia/Tokyo")],
                ["Singapore",    timezone("Singapore")],
                ["UK",            timezone("Europe/London")]
                
                ]
                
themes =[colors.bg.black, colors.fg.white, colors.fg.lightblue, colors.bg.black, colors.bg.lightblue]
         
dbgyear        = 2019
dbgmonth    = 7
dbgday        = 1
dbghour        = 11
dbgminute    = 59
dbgsecond    = 55
dbgstart    = datetime.datetime.now()

SECOND  = 0
MINUTE  = 1
HOUR    = 2
DAY     = 3
MONTH   = 4
YEAR    = 5
CENTURY = 6

LABEL=0
VALUE=1
PRECISION=2

            #Label,value,precision
timeTable =[["Second",    0,    6],
            ["Minute",    0,    8],
            ["Hour",    0,    10],
            ["Day",        0,    10],
            ["Month",    0,    10],
            ["Year",    0,    10],
            ["Century",    0,    10]]

rows    = os.get_terminal_size().lines
columns = os.get_terminal_size().columns

def resetCursor():
    print("\033[0;0H", end="")

def color(bg,fg):
    return "\x1b[48;5;" + str(bg) + ";38;5;" + str(fg) + "m"

def drawProgressBar(width,min,max,value):
    level = int(width * (value-min)/(max-min) + .999999999999)
    #return (chr(0x2550) * level + (colors.fg.darkgray + chr(0x2500) + colors.reset.all) * (width-level))
    return (chr(0x2550) * level + colors.fg.darkgray + (chr(0x2500) * (width-level)) + colors.reset.all)

os.system("clear")
os.system("setterm -cursor off")
while True:
    try:
        rows    = os.get_terminal_size().lines
        columns = os.get_terminal_size().columns

        now = datetime.datetime.now()
        utcnow = datetime.datetime.utcnow()
        if(dbg):
            now = (datetime.datetime.now()-dbgstart) + \
                  datetime.datetime(dbgyear,dbgmonth,dbgday,dbghour,dbgminute,dbgsecond)
        screen = ""
        output = ""
        resetCursor()

        uSecond = now.microsecond/1000000
        
        
        highlight = [themes[3], themes[4]]
        print(themes[0],end="")
        
        vBar = themes[2] + chr(0x2551) + themes[1]
        vBar1 = themes[2] + chr(0x2502) + themes[1]
        hBar = themes[2] + chr(0x2550) + themes[1]
        vBarUp = themes[2] + chr(0x00af) + themes[1]
        vBarDown = themes[2] + "_" + themes[1]
        llCorner = themes[2] + chr(0x0255A) + themes[1]
        lrCorner = themes[2] + chr(0x0255D) + themes[1]
        ulCorner = themes[2] + chr(0x02554) + themes[1]
        urCorner = themes[2] + chr(0x02557) + themes[1]
        
        binary0 = chr(0x25cf)
        binary1 = chr(0x25cb)
        
        hourBinary0   = "{:>04b}".format(int(now.hour/10))
        hourBinary1   = "{:>04b}".format(int(now.hour%10))
        minuteBinary0 = "{:>04b}".format(int(now.minute/10))
        minuteBinary1 = "{:>04b}".format(int(now.minute%10))
        secondBinary0 = "{:>04b}".format(int(now.second/10))
        secondBinary1 = "{:>04b}".format(int(now.second%10))
        
        bClockMat = [hourBinary0,hourBinary1,minuteBinary0,minuteBinary1,secondBinary0,secondBinary1]
        bClockMatT = [*zip(*bClockMat)]
        bClockdisp = ['','','','']
        
        for i,row in enumerate(bClockMatT):
            bClockdisp[i] = ''.join(row).replace("0"," "+binary0).replace("1"," "+binary1)
        
        if (now.month ==12):
            daysThisMonth = 31
        else:
            daysThisMonth = (datetime.datetime(now.year,now.month+1,1)- \
                datetime.datetime(now.year,now.month,1)).days
        
        dayOfYear = (now - datetime.datetime(now.year,1,1)).days
        daysThisYear = (datetime.datetime(now.year+1,1,1) - datetime.datetime(now.year,1,1)).days

        timeTable[SECOND][VALUE]    = now.second + uSecond
        timeTable[MINUTE][VALUE]    = now.minute + timeTable[SECOND][VALUE]/60
        timeTable[HOUR][VALUE]        = now.hour + timeTable[MINUTE][VALUE]/60
        timeTable[DAY][VALUE]        = now.day + timeTable[HOUR][VALUE]/24
        timeTable[MONTH][VALUE]        = now.month + (timeTable[DAY][VALUE]-1)/daysThisMonth
        timeTable[YEAR][VALUE]        = now.year + (dayOfYear + timeTable[DAY][VALUE] - int(
                                        timeTable[DAY][VALUE]))/daysThisYear
        timeTable[CENTURY][VALUE]    = (timeTable[YEAR][VALUE]-1)/100 + 1

        screen += themes[4]
        screen += ("{: ^" + str(columns) +"}\n").format(now.strftime("%I:%M:%S %p - %A %B %d, %Y"))
        
        screen += vBarDown * columns + themes[0] + themes[1] + "\n"
        
        for i in range(7):
            percentValue = int(100*(timeTable[i][VALUE] - int(timeTable[i][VALUE])))
            screen +=  (" {0:>7} "+vBar+" {1:>15."+str(timeTable[i][PRECISION]) +"f}"+ vBar1 +"{2:}"+ vBar1 +"{3:02}% \n").format(
                timeTable[i][LABEL],timeTable[i][VALUE],drawProgressBar(
                    columns-32,0,100,percentValue),percentValue)

        screen += vBarUp * columns + "\n"

        
        DST =  [["DST Begins",    getRelativeDate(2,0,3,now.year).replace(hour=2)],
                ["DST Ends",    getRelativeDate(1,0,11,now.year).replace(hour=2)]]
            
                            
        if ((now - (DST[0][1])).total_seconds() > 0) & (((DST[1][1]) - now).total_seconds() > 0):
            isDaylightSavings = True
            nextDate = DST[1][1].replace(hour=2)
        else:
            isDaylightSavings = False
            if ((now - DST[0][1]).total_seconds() < 0):
                nextDate = getRelativeDate(2,0,3,now.year).replace(hour=2)
            else:
                nextDate = getRelativeDate(2,0,3,now.year+1).replace(hour=2)
                
        dstStr = " " + DST[isDaylightSavings][0] + " " + nextDate.strftime("%a %b %d") + \
                    " (" + str(nextDate-now).split(".")[0] + ")"
                
        

        unixStr = ("UNIX: {0}").format(int(datetime.datetime.utcnow().timestamp()))
        
        dayPercentComplete = timeTable[DAY][VALUE] - int(timeTable[DAY][VALUE])
        dayPercentCompleteUTC = (utcnow.hour*3600 + utcnow.minute*60 + utcnow.second + utcnow.microsecond/1000000)/86400
        metricHour = int(dayPercentComplete*10)
        metricMinute = int(dayPercentComplete*1000) % 100
        metricSecond = (dayPercentComplete*100000) % 100
        metricuSecond = int(dayPercentComplete*10000000000000) % 100
        metricStr = (" Metric: {0:02.0f}:{1:02.0f}:{2:02}").format(metricHour,metricMinute,int(metricSecond))
        
        city = ephem.city("Atlanta")
        
        solarStrTmp = str(solartime(city)).split(".")[0]
        solarStr = "  Solar: {0:>08}".format(solarStrTmp)        

        lstStrTmp = str(city.sidereal_time()).split(".")[0]
        lstStr = "    LST: {0:>08}".format(lstStrTmp)
        
        hexStrTmp = "{:>04}: ".format(hex(int(65536 * dayPercentComplete)).split("x")[1]).upper()
        hexStr = " Hex: " + hexStrTmp[0] + "_" + hexStrTmp[1:3] + "_" + hexStrTmp[3]
        
        netValue =  1296000 * dayPercentCompleteUTC
        netHour = int(netValue/3600)
        netMinute = int((netValue % 3600)/60)
        netSecond = int(netValue % 60)
        
        netStr = " NET: {0:>02}°{1:>02}\'{2:>02}\"".format(netHour,netMinute,netSecond)
        screen += dstStr + " "*(columns - len(dstStr + bClockdisp[0]) - 4) + bClockdisp[0]+ "    \n"
        screen += metricStr + " "+vBar+" " + unixStr + " "*(columns - len(metricStr + unixStr + bClockdisp[1]) - 7)  + bClockdisp[1]+ "    \n"
        screen += solarStr +" "+vBar+" "+ netStr + " " * (columns-len(solarStr + netStr + bClockdisp[2]) - 7) + bClockdisp[2] + "    \n"
        screen += lstStr + " "+vBar+" " +hexStr+ " " * (columns-(len(lstStr + hexStr + bClockdisp[3]) + 7 )) + bClockdisp[3] + "    \n"
        screen += vBarDown * columns + ""
            
        for i in range(0,len(timeZoneList),2):
            time0 = datetime.datetime.now(timeZoneList[i][1])
            time1 = datetime.datetime.now(timeZoneList[i+1][1])
            flash0 = False
            flash1 = False

            if (time0.weekday() < 5):
                if (time0.hour > 8 and time0.hour < 17):
                    flash0 = True
                elif (time0.hour == 8 or time0.hour == 17):
                    flash0 = (int(uSecond * 10) < 5 )

            if (time1.weekday() < 5):
                if (time1.hour > 8 and time1.hour < 17):
                    flash1 = True
                elif (time1.hour == 8 or time1.hour == 17):
                    flash1 = (int(uSecond * 10 ) < 5 )

            timeStr0 = time0.strftime("%I:%M %p %b %d")
            timeStr1 = time1.strftime("%I:%M %p %b %d")
            screen += highlight[flash0] + (" {0:>9}: {1:15}  ").format(timeZoneList[i][0],timeStr0) + highlight[0] + vBar
            screen += highlight[flash1] + (" {0:>9}: {1:15}  ").format(timeZoneList[i+1][0],timeStr1) + highlight[0]
            # Each Timezone column is 29 chars, and the bar is 1 = 59
            spacer = " " * (columns - 59)
            screen += spacer + "\n"

        # Draw the bar under the timezones
        screen += vBarUp * columns
        # Switch to the header color theme
        screen += themes[4]

        # Append blank lines to fill out the bottom of the screen
        for i in range(22,rows):
            screen += vBarUp * columns

        print(screen,end="")
        if dbg:
            time.sleep(1)
    except KeyboardInterrupt:
        os.system("clear")
        os.system("setterm -cursor on")
        print(colors.reset.all,end="")
        sys.exit(0)
