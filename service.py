# -*- coding: utf-8 -*-

#############################
# Light IMDb Ratings Update #
# by axlt2002               #
#############################

import xbmc, xbmcaddon, xbmcvfs
import time, _strptime
from datetime import date, datetime, timedelta
from support.common import *
from main import StartUpdate

if not xbmcvfs.exists( addonProfile ): xbmcvfs.mkdir( addonProfile )

WeekDay = addonSettings.getSetting( "WeekDay" )
DayTime = addonSettings.getSetting( "DayTime" )

def UpdateSchedule():
    day_difference = date.weekday( date.today() ) - int( WeekDay )
    if day_difference < 0:
        day_difference = -day_difference
    elif day_difference > 0:
        day_difference = 7-day_difference
    elif day_difference == 0 and time.strftime("%H:%M:%S") >= DayTime:
        day_difference = day_difference+7
    nextrun = datetime.now() + timedelta( days = day_difference )
    nextruntime = DayTime
    addonSettings.setSetting( "ScheduledWeekDay", datetime.strftime(nextrun, "%Y-%m-%d") )
    statusLog( addonLanguage(32655) % ( datetime.strftime(nextrun, "%Y-%m-%d"), str( nextruntime ) ) )
    xbmc.sleep(2000)

def AutoStart():
    addonSettings.setSetting( "PerformingUpdate", "false" )
    addonSettings.setSetting( "LogDialog", "false" )
    start_StatusLog()
    monitor = xbmc.Monitor()
    while not monitor.abortRequested():
        monitor.waitForAbort(5)
        if addonSettings.getSetting( "ScheduleEnabled" ) == "true":
            global WeekDay
            global DayTime
            newWeekDay = addonSettings.getSetting( "WeekDay" )
            newScheduledTime = addonSettings.getSetting( "DayTime" )
            if ( WeekDay != newWeekDay ) or ( DayTime != newScheduledTime ) or ( addonSettings.getSetting( "ScheduledWeekDay" ) == "2000-01-01"):
                WeekDay = newWeekDay
                DayTime = newScheduledTime
                UpdateSchedule()
            try:
                ScheduledDay = datetime.strptime( addonSettings.getSetting( "ScheduledWeekDay" ), "%Y-%m-%d" )
            except TypeError:
                ScheduledDay = datetime(*(time.strptime( addonSettings.getSetting( "ScheduledWeekDay" ), "%Y-%m-%d" )[0:6]))
            if ( datetime.now() >= ScheduledDay ):
                if ( time.strftime("%H:%M:%S") >= addonSettings.getSetting( "DayTime" ) ):
                    StartUpdate()
                    UpdateSchedule()

if (__name__ == "__main__"):
    AutoStart()
