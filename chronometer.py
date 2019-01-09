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

dateList = 	[
			["Roth's B'day",	STATIC,10,20],
			["Lori's B'day",	STATIC,6,28],
			["Anniversary",		STATIC,10,5],
			["Cinco de Mayo",	STATIC,5,5],
			["July 4th",		STATIC,7,4],
			["Labor Day",		RELATIVE,1,1,9],
			["New Year's",		STATIC,1,1],
			["Thanksgiving",	RELATIVE,3,4,11]
			]
			
timeZoneList = [["Eastern",		timezone("US/Eastern")],
				["Central",		timezone("US/Central")],
				["Mountain",	timezone("US/Mountain")],
				["Pacific",		timezone("US/Pacific")],
				["GMT",			timezone("GMT")],
				["Australia",	timezone("Australia/Sydney")],
				["Germany",		timezone("Europe/Berlin")],
				["Hong Kong",	timezone("Asia/Hong_Kong")],
				["India",		timezone("Asia/Kolkata")],
				["Japan",		timezone("Asia/Tokyo")],
				["Singapore",	timezone("Singapore")],
				["UK",			timezone("Europe/London")]
				
				]
				
themes =[[colors.bg.black,colors.fg.white,colors.fg.lightblue,colors.fg.cyan], # JAN
		 [colors.bg.black,colors.fg.magenta,colors.fg.lightblue,colors.fg.lightyellow], # FEB
		 [colors.bg.black,colors.fg.white,colors.fg.lightblue,colors.fg.cyan], # MAR
		 [colors.bg.black,colors.fg.lightred,colors.fg.yellow,colors.fg.lightyellow], # APR
		 [colors.bg.black,colors.fg.lightyellow,colors.fg.lightred,colors.fg.lightgreen], # MAY
		 [colors.bg.black,colors.fg.white,colors.fg.lightblue,colors.fg.cyan], # JUN
		 [colors.bg.black,colors.fg.white,colors.fg.lightred,colors.fg.lightblue], # JUL
		 [colors.bg.black,colors.fg.white,colors.fg.lightgray,colors.fg.cyan], # AUG
		 [colors.bg.black,colors.fg.white,colors.fg.lightgray,colors.fg.cyan], # SEP
		 [colors.bg.black,colors.fg.white,colors.fg.lightgray,colors.fg.cyan], # OCT
		 [colors.bg.black,colors.fg.white,colors.fg.lightgray,colors.fg.cyan], # NOV
		 [colors.bg.black,colors.fg.lightgreen,colors.fg.red,colors.fg.white]] # DEC
		 
name = " Roth Fralick "

dbgyear		= 2019
dbgmonth	= 7
dbgday		= 1
dbghour		= 11
dbgminute	= 59
dbgsecond	= 55
dbgstart	= datetime.datetime.now()

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
timeTable =[["Second",	0,	6],
			["Minute",	0,	8],
			["Hour",	0,	10],
			["Day",		0,	10],
			["Month",	0,	10],
			["Year",	0,	10],
			["Century",	0,	10]]

rows, columns = os.popen('stty size', 'r').read().split()
rows = int(rows)
columns = int(columns)

def resetCursor():
	print("\033[0;0H", end="")

def color(bg,fg):
    return "\x1b[48;5;" + str(bg) + ";38;5;" + str(fg) + "m"

def drawProgressBar(width,min,max,value):
	level = int(width * (value-min)/(max-min) + .999999999999)
	return (chr(0x2550) * level + " " * (width-level))

os.system("clear")
os.system("setterm -cursor off")
while True:
	try:
		now = datetime.datetime.now()
		utcnow = datetime.datetime.utcnow()
		if(dbg):
			now = (datetime.datetime.now()-dbgstart) + \
				  datetime.datetime(dbgyear,dbgmonth,dbgday,dbghour,dbgminute,dbgsecond)
		screen = ""
		output = ""
		resetCursor()

		uSecond = now.microsecond/1000000
		
		
		themeIndex = now.month - 1
		highlight = [themes[themeIndex][1], themes[themeIndex][3]]
		print(themes[themeIndex][0],end="")
		
		vBar = themes[themeIndex][2] + chr(0x2551) + themes[themeIndex][1]
		hBar = themes[themeIndex][2] + chr(0x2550) + themes[themeIndex][1]
		vBarUp = themes[themeIndex][2] + chr(0x00af) + themes[themeIndex][1]
		vBarDown = themes[themeIndex][2] + "_" + themes[themeIndex][1]
		llCorner = themes[themeIndex][2] + chr(0x0255A) + themes[themeIndex][1]
		lrCorner = themes[themeIndex][2] + chr(0x0255D) + themes[themeIndex][1]
		ulCorner = themes[themeIndex][2] + chr(0x02554) + themes[themeIndex][1]
		urCorner = themes[themeIndex][2] + chr(0x02557) + themes[themeIndex][1]
		
		hourBinary 	 = "{:06b}".format(now.hour).replace("0","-").replace("1","+")
		minuteBinary = "{:06b}".format(now.minute).replace("0","-").replace("1","+")
		secondBinary = "{:06b}".format(now.second).replace("0","-").replace("1","+")
		
		if (now.month ==12):
			daysThisMonth = 31
		else:
			daysThisMonth = (datetime.datetime(now.year,now.month+1,1)- \
				datetime.datetime(now.year,now.month,1)).days
		
		dayOfYear = (now - datetime.datetime(now.year,1,1)).days
		daysThisYear = (datetime.datetime(now.year+1,1,1) - datetime.datetime(now.year,1,1)).days

		timeTable[SECOND][VALUE]	= now.second + uSecond
		timeTable[MINUTE][VALUE]	= now.minute + timeTable[SECOND][VALUE]/60
		timeTable[HOUR][VALUE]		= now.hour + timeTable[MINUTE][VALUE]/60
		timeTable[DAY][VALUE]		= now.day + timeTable[HOUR][VALUE]/24
		timeTable[MONTH][VALUE]		= now.month + (timeTable[DAY][VALUE]-1)/daysThisMonth
		timeTable[YEAR][VALUE]		= now.year + (dayOfYear + timeTable[DAY][VALUE] - int(
										timeTable[DAY][VALUE]))/daysThisYear
		timeTable[CENTURY][VALUE]	= timeTable[YEAR][VALUE]/100 + 1

		screen += ("{: ^" + str(columns) +"}\n").format(now.strftime("%I:%M:%S %p - %A %B %d, %Y"))

		screen += vBarDown * columns + "\n"

		for i in range(7):
			percentValue = int(100*(timeTable[i][VALUE] - int(timeTable[i][VALUE])))
			screen +=  (" {0:>7} "+vBar+"{1:>15."+str(timeTable[i][PRECISION]) +"f}|{2:}|{3:02}% \n").format(
				timeTable[i][LABEL],timeTable[i][VALUE],drawProgressBar(
					columns-31,0,100,percentValue),percentValue)

		screen += vBarUp * columns + "\n"

		for i in range(len(dateList)):
			if dateList[i][1] == STATIC:
				nextDate = datetime.datetime(now.year,dateList[i][2],dateList[i][3])
				if (nextDate-now).total_seconds()<0:
					nextDate = datetime.datetime(now.year+1,dateList[i][2],dateList[i][3])
			else:
				nextDate = getRelativeDate(dateList[i][2],dateList[i][3],dateList[i][4],now.year)
				if (nextDate-now).total_seconds()<0:
					nextDate = getRelativeDate(dateList[i][2],dateList[i][3],dateList[i][4],now.year+1)
		
		DST =  [["DST Begins",	getRelativeDate(2,0,3,now.year).replace(hour=2)],
				["DST Ends",	getRelativeDate(1,0,11,now.year).replace(hour=2)]]
			
							
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
		screen += dstStr + " "*(columns - len(dstStr + hourBinary) - 2) + hourBinary + "  \n"
		screen += metricStr + " "+vBar+" " + unixStr + " "*(columns - len(metricStr + unixStr+ minuteBinary) - 5) + minuteBinary + "  \n"
		screen += solarStr +" "+vBar+" "+ netStr + " " * (columns-len(solarStr + netStr + secondBinary)-5) + secondBinary + "  \n"
		screen += lstStr + " "+vBar+" " +hexStr+ " " * (columns-(len(lstStr + hexStr) + 3)) + "\n"
		screen += vBarDown * columns + ""
			
		for i in range(0,len(timeZoneList),2):
			time0 = datetime.datetime.now(timeZoneList[i][1])
			time1 = datetime.datetime.now(timeZoneList[i+1][1])
		
			if (time0.weekday() < 5):
				if (time0.hour > 8 and time0.hour < 17):
					flash0 = True
				elif (time0.hour == 8 or time0.hour == 17):
					flash0 = (int(uSecond*10) < 1 )
				else: 
					flash0 = False
					
			if (time1.weekday() < 5):
				if (time1.hour > 8 and time1.hour < 17):
					flash1 = True
				elif (time1.hour == 8 or time1.hour == 17):
					flash1 = (int(uSecond*10)< 1 )
				else: 
					flash1 = False

			timeStr0 = time0.strftime("%I:%M %p %b %d")
			timeStr1 = time1.strftime("%I:%M %p %b %d")
			screen += highlight[flash0] + (" {0:>9}: {1:15}  "+vBar+" ").format(timeZoneList[i][0],timeStr0) + themes[themeIndex][1]
			screen += highlight[flash1] + (" {0:>9}: {1:15}  ").format(timeZoneList[i+1][0],timeStr1) + themes[themeIndex][1]
			screen += "\n"
			
		screen += vBarUp * columns
		
		print(screen,end="")
		if dbg:
			time.sleep(.5)
	except KeyboardInterrupt:
		os.system("clear")
		os.system("setterm -cursor on")
		print(colors.reset.all,end="")
		sys.exit(0)
