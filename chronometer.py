#!/usr/bin/python3
from datetime import datetime
import time
import os
import string
from myColors import colors
from pytz import timezone

dbg = False

STATIC=0
RELATIVE=1

def debug(text,var):
	if dbg:
		print("DEBUG>>> "+text + ": " + str(var))

def getRelativeDate(ordinal,weekday,month,year):
	firstday = (datetime(year,month,1).weekday() + 1)%7
	firstSunday = (7 - firstday) % 7 + 1
	return datetime(year,month,firstSunday + weekday + 7*(ordinal-1))

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
			
timeZoneList = [["GMT",			timezone("GMT")],
				["Eastern",		timezone("US/Eastern")],
				["Central",		timezone("US/Central")],
				["Mountain",	timezone("US/Mountain")],
				["Pacific",		timezone("US/Pacific")],
				["Australia",	timezone("Australia/Sydney")],
				["Germany",		timezone("Europe/Berlin")],
				["Hong Kong",	timezone("Asia/Hong_Kong")],
				["India",		timezone("Asia/Kolkata")],
				["Japan",		timezone("Asia/Tokyo")],
				["Singapore",	timezone("Singapore")],
				["UK",			timezone("Europe/London")],
				]


name = " Roth Fralick "

dbgyear		= 2019
dbgmonth	= 5
dbgday		= 5
dbghour		= 5
dbgminute	= 5
dbgsecond	= 5
dbgstart	= datetime.now()

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
columns = int(columns) - 2

def resetCursor():
	print("\033[0;0H", end="")

def color(bg,fg):
    return "\x1b[48;5;" + str(bg) + ";38;5;" + str(fg) + "m"

def drawProgressBar(width,min,max,value):
	level = int(width * (value-min)/(max-min) + .999999999999)
	return (chr(0x2550) * level + " " * (width-level))

theme =[[colors.bg.black + colors.fg.white, colors.bg.black + colors.fg.white],
		[colors.bg.black + colors.fg.white, colors.bg.black + colors.fg.white],
		[colors.bg.black + colors.fg.white, colors.bg.black + colors.fg.white],
		[colors.bg.black + colors.fg.white, colors.bg.black + colors.fg.white],
		[colors.bg.black + colors.fg.white, colors.bg.black + colors.fg.white],
		[colors.bg.black + colors.fg.white, colors.bg.black + colors.fg.white],
		[colors.bg.black + colors.fg.white, colors.bg.black + colors.fg.white],
		[colors.bg.black + colors.fg.white, colors.bg.black + colors.fg.white],
		[colors.bg.black + colors.fg.white, colors.bg.black + colors.fg.white],
		[colors.bg.black + colors.fg.white, colors.bg.black + colors.fg.white],
		[colors.bg.black + colors.fg.white, colors.bg.black + colors.fg.white],
		[colors.bg.black + colors.fg.red, colors.bg.black + colors.fg.green]]		

os.system("clear")
while True:
	
	now = datetime.now()
	if(dbg):
		now = (datetime.now()-dbgstart) + \
			  datetime(dbgyear,dbgmonth,dbgday,dbghour,dbgminute,dbgsecond)

	themeIndex = (now.month-1)%12	
	vBar = theme[themeIndex][0] + chr(0x2551) + theme[themeIndex][1]
	hBar = theme[themeIndex][0] + chr(0x2550) + theme[themeIndex][1]
	vBarUp = theme[themeIndex][0] + chr(0x00af) + theme[themeIndex][1]
	vBarDown = theme[themeIndex][0] + "_" + theme[themeIndex][1]
	llCorner = theme[themeIndex][0] + chr(0x0255A) + theme[themeIndex][1]
	lrCorner = theme[themeIndex][0] + chr(0x0255D) + theme[themeIndex][1]
	ulCorner = theme[themeIndex][0] + chr(0x02554) + theme[themeIndex][1]
	urCorner = theme[themeIndex][0] + chr(0x02557) + theme[themeIndex][1]

	screen = ""
	output = ""
	resetCursor()

	uSecond = now.microsecond/1000000

	if (now.month ==12):
		daysThisMonth = 31
	else:
		daysThisMonth = (datetime(now.year,now.month+1,1)- \
			datetime(now.year,now.month,1)).days
	
	dayOfYear = (now - datetime(now.year,1,1)).days
	daysThisYear = (datetime(now.year+1,1,1) - datetime(now.year,1,1)).days

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
			nextDate = datetime(now.year,dateList[i][2],dateList[i][3])
			if (nextDate-now).total_seconds()<0:
				nextDate = datetime(now.year+1,dateList[i][2],dateList[i][3])
		else:
			nextDate = getRelativeDate(dateList[i][2],dateList[i][3],dateList[i][4],now.year)
			if (nextDate-now).total_seconds()<0:
				nextDate = getRelativeDate(dateList[i][2],dateList[i][3],dateList[i][4],now.year+1)
	
		#screen += 	" {0:<13} ({1:^10}) | {2: <25}\n".format(
						#dateList[i][0],nextDate.strftime("%a %b %d"),\
						#str(nextDate-now).split(".")[0])
	
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
	#screen += 	" {0:<13} {1:<10} | {2: <25}\n".format(
	#					DST[isDaylightSavings][0],nextDate.strftime("%a %b %d"),\
	#					str(nextDate-now).split(".")[0])
	screen += " " + DST[isDaylightSavings][0] + " " + nextDate.strftime("%a %b %d") + \
				" (" + str(nextDate-now).split(".")[0] + ")\n\n"
		
	for i in range(0,len(timeZoneList),2):
		timeStr0 = datetime.now(timeZoneList[i][1]).strftime("%I:%M %p %b %d")
		timeStr1 = datetime.now(timeZoneList[i+1][1]).strftime("%I:%M %p %b %d")
		screen += (" {0:>9}: {1:} | ").format(timeZoneList[i][0],timeStr0)
		screen += (" {0:>9}: {1:}\n").format(timeZoneList[i+1][0],timeStr1)

	#draw a frame
	output = ulCorner + hBar * (columns) + urCorner + "\n"
	for line in screen.split("\n"):
		output += (vBar+"{:"+ str(columns)  +"}"+vBar).format(line) + "\n"

	output += (vBar + " "*int(columns) + vBar + "\n")*(rows-screen.count("\n")-3)
	output += llCorner + hBar * int((columns-len(name))/2-1) + " "+ name + " " + hBar * (columns-(int((columns-len(name))/2-1)) - len(name) -2) + lrCorner

	print(output,end="")
	if dbg:
		time.sleep(1)
	else:
		time.sleep(1/60)
