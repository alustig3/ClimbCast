import datetime
import requests
import numpy as np
import json
import pytz
import calendar
import matplotlib.style as style
import matplotlib.pyplot as plt

style.use('fivethirtyeight')
tz = pytz.timezone('US/Eastern')

def getUnix(_date, fromPicker = False):
    if fromPicker:
        day = _date.value
    else:
        day = _date.date()
    return int(calendar.timegm(day.timetuple())) + 5*3600 # add 5 hours

def wrapText(sentence,limit):
    words = sentence.split(' ')
    newLength = 0
    oldLength = 0
    for i,word in enumerate(words):
        newLength += len(word)+1
        if newLength<limit:
            oldLength = newLength
    wrappedSentence = ('{}\n{}'.format(sentence[:oldLength],sentence[oldLength:]))
    return wrappedSentence

def threeDaySummary(location,firstDay):
    now = tz.normalize(datetime.datetime.now(tz))
    #create dictionary with relative dates. if today is Wednesday, the dictionary will have 'Tuesday':-1 and 'Friday':2
    dayNames = np.array(['monday','tuesday','wednesday','thursday','friday','saturday','sunday'])
    dayNameDict = {}
    for day,val in zip(np.roll(dayNames,-now.weekday()),[0,1,2,3,4,-2,-1]):
        dayNameDict[day] = val
    until_day_of_interest = dayNameDict[firstDay.lower()]
    dayOne = tz.normalize(now + datetime.timedelta(days=until_day_of_interest))
    dayTwo = tz.normalize(now + datetime.timedelta(days=until_day_of_interest+1))
    dayThree = tz.normalize(now + datetime.timedelta(days=until_day_of_interest+2))

    dayNames = ['Mon','Tues','Wed','Thurs','Fri','Sat','Sun']
    calendar = ['{} - {}/{}'.format(dayNames[dayOne.weekday()],dayOne.month,dayOne.day),
                '{} - {}/{}'.format(dayNames[dayTwo.weekday()],dayTwo.month,dayTwo.day),
                '{} - {}/{}'.format(dayNames[dayThree.weekday()],dayThree.month,dayThree.day)
               ]

    graphData = {
        'calendar':calendar,
        'title': location['name'],
        'timeList': np.array([]),
        'tempList': np.array([]),
        'precipList': np.array([]),
        'summaryList': np.array([]),
        'cloudList': np.array([]),
        'highList': np.array([]),
        'lowList': np.array([]),
        'rainList': [],
        'sunrise': np.array([]),
        'sunset': np.array([]),
    }

    for day in [dayOne,dayTwo,dayThree]:
        unixTime = getUnix(day)
        myurl = 'https://api.darksky.net/forecast/a5697e4c206dd1fe1f410c5c6fa7cd8d/{},{}?exclude=currently,minutely,alerts,flags'.format(location['coords'],unixTime)
        myPage = requests.get(myurl)
        weatherData = json.loads(myPage.content)

        # get hourly data points
        for hourData in weatherData['hourly']['data']:
            graphData['timeList'] = np.append(graphData['timeList'],datetime.datetime.fromtimestamp(hourData['time']).astimezone(tz))
            graphData['tempList'] = np.append(graphData['tempList'],hourData['temperature'])
            graphData['precipList'] = np.append(graphData['precipList'],hourData['precipIntensity'])
            graphData['cloudList'] = np.append(graphData['cloudList'],int(hourData['cloudCover']*100))

        # get daily data points
        dayData = weatherData['daily']['data'][0]
        graphData['summaryList'] = np.append(graphData['summaryList'],wrapText(dayData['summary'],30))
        graphData['highList'] = np.append(graphData['highList'],dayData['temperatureHigh'])
        graphData['lowList'] = np.append(graphData['lowList'],dayData['temperatureMin'])
        graphData['sunrise'] = np.append(graphData['sunrise'],datetime.datetime.fromtimestamp(dayData['sunriseTime']).astimezone(tz))
        graphData['sunset'] = np.append(graphData['sunset'],datetime.datetime.fromtimestamp(dayData['sunsetTime']).astimezone(tz))

        try:
            prob,accumulated = int(dayData['precipProbability']*100),dayData['precipIntensity']*24
        except:
            prob,accumulated = [0,0]
        graphData['rainList'].append((prob,round(accumulated,2)))

    return graphData

def formatter(_time):
    formattedTime = _time.strftime('%I\n%p').lower()
    if formattedTime[0]=='0': # remove leading 0
        formattedTime = formattedTime[1:]
    return formattedTime

def plot3Day(dataPts):
    timeList = dataPts['timeList']
    tempList = dataPts['tempList']
    precipList = dataPts['precipList']
    calendar = dataPts['calendar']
    summaryList = dataPts['summaryList']
    cloudList = dataPts['cloudList']
    rainList = dataPts['rainList']
    highList = dataPts['highList']
    lowList = dataPts['lowList']
    title = dataPts['title']
    sunrise = dataPts['sunrise']
    sunset = dataPts['sunset']

    theFigure = plt.figure()
    theFigure.set_size_inches(15,22)
    numRows,numColumns = 2,1

    plt.suptitle(title,fontsize=50,x=0.515, y=.93,ha='center')
    plt.subplots_adjust(right=.93)

    # Temperature
    tempColor = 'C2'
    tempPlot = plt.subplot2grid((numRows,numColumns), (0, 0),rowspan=1, colspan=1)
    tempPlot.plot(timeList,tempList,'-',color=tempColor,linewidth=2)
    tempPlot.set_xticks(timeList[::24])
    tickIndices = [6,10,14,18,30,34,38,42,54,58,62,66]
    tempPlot.set_xticks(timeList[tickIndices],minor=True)
    tempPlot.set_xticklabels([])
    tempPlot.tick_params(axis='y',labelsize=20, colors=tempColor)


    convertToHourString = np.vectorize(formatter)
    formatted_x_ticks = convertToHourString(timeList[tickIndices])
    tempPlot.set_xticklabels(formatted_x_ticks,minor=True)
    tempPlot.set_ylabel('Temperature (˚F)',color=tempColor,fontsize=30)
    tempPlot.set_ylim(25,105)
    timeOfUpdate = datetime.datetime.now(tz).strftime('%A %I:%M %p')
    tempPlot.set_title('As of {}'.format(timeOfUpdate),fontsize=25,ha='center',style='italic')
    tempPlot.grid(True,axis='both',which='both',linestyle='--')
    tempPlot.grid(True,axis='x',which='major',linestyle='-',lw=2)

    # Precipitation
    precipColor = 'C0'
    precipPlot = plt.subplot2grid((numRows,numColumns), (1, 0),rowspan=1, colspan=1)
    #add 0 to beginning and end for filling the rain plot
    filledTimeList = np.insert(timeList,0,timeList[0])
    filledTimeList = np.append(filledTimeList,timeList[-1])
    filledPrecipList = np.insert(precipList,0,0)
    filledPrecipList = np.append(filledPrecipList,0)
    precipPlot.fill(filledTimeList,filledPrecipList,alpha=.5,color=precipColor)
    precipPlot.set_ylabel('Rain Intensity (inches/hr)',color=precipColor,fontsize=30)
    precipPlot.set_ylim(-.01,.31)
    precipPlot.grid(True,axis='both',which='both',linestyle='--')
    precipPlot.grid(True,axis='x',which='major',linestyle='-',lw=2)
    precipPlot.tick_params(axis='y',labelsize=15,colors=precipColor)


    # Cloud
    cloudColor = 'C1'
    cloudPlot = precipPlot.twinx()
    cloudPlot.plot(timeList,cloudList,'-',color=cloudColor,linewidth=1)
    cloudPlot.set_ylabel('Cloud Cover (%)',color=cloudColor,rotation=270, va='bottom',labelpad=0,fontsize=30)
    cloudPlot.grid(None)
    cloudPlot.set_xticks(timeList[::24])
    cloudPlot.set_xticks(timeList[tickIndices],minor=True)
    cloudPlot.set_xticklabels([])
    cloudPlot.set_xticklabels(formatted_x_ticks,minor=True)
    cloudPlot.set_ylim(-5,105)
    cloudPlot.tick_params(axis='y',labelsize=15, colors=cloudColor, length=8, width=1,direction='in')

    for i,dayName in enumerate(calendar):
        # temperature
        cloudPlot.annotate('H - {}\nL - {}'.format(int(highList[i]),int(lowList[i])), xy=((i*2+1)/6*20.28/22+1/22, 1.28),
                           xycoords='axes fraction',ha='center',va='bottom',fontsize=35,color=tempColor)

        # date
        cloudPlot.annotate('{}\n'.format(dayName), xy=((i*2+1)/6*20.28/22+1/22, 1.24),
                           xycoords='axes fraction',ha='center',va='center',fontsize='20',fontweight='bold')

        # summary
        cloudPlot.annotate('\n{}\nsunrise @{}\nsunset @{}'.format(summaryList[i],sunrise[i].strftime('%-I:%M %p').lower(),sunset[i].strftime('%-I:%M %p').lower()), xy=((i*2+1)/6*20.28/22+1/22, 1.20),
                           xycoords='axes fraction',ha='center',va='center',fontsize='12')

        # rainfall
        cloudPlot.annotate('{}% chance of\n{} in'.format(rainList[i][0],rainList[i][1]),
                           xy=((i*2+1)/6*20.28/22+1/22, 1.12),xycoords='axes fraction',ha='center',va='top',
                           fontsize=rainList[i][1]/2.5*30+15,color=precipColor,alpha=rainList[i][0]/100)

    plt.subplots_adjust(hspace=.5)
    return theFigure