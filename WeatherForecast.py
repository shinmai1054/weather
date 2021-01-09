#-*- coding: utf-8 -*-
from os import write
import urllib.request
import json
import csv
import os
import time
from datetime import date, datetime, timedelta

# 設定 -----------------------
areaCode = {'長崎南部': 420010, '長崎北部': 420020, '壱岐・対馬': 420030, '五島': 420040}
# データ取得間隔[時間]
interval = 1
# データ保存ディレクトリ
saveDir = './data'
# ログ出力するか
logEnable = True
# -----------------------------

# 初期化
APIURL = 'http://www.data.jma.go.jp/fcd/yoho/wdist/jp/data/wdist/VPFD/{}.json?_{}'
nextUpdate = None
latestTime = datetime(2020,1,1,0,0)


def init():
    global saveDir
    saveDir = saveDir + '/' if not saveDir[-1] == '/' else saveDir


def getData(target):
    d = round(time.time() / 6e4 * 1000)
    req = urllib.request.Request(APIURL.format(areaCode[target], d))
    with urllib.request.urlopen(req) as res:
        body = res.read().decode('utf-8')

    data = json.loads(body)
    areaData = data['areaTimeSeries']
    pointData = data['pointTimeSeries']

    result = []

    # Time
    time_def = areaData['timeDefines']
    timeList = ['time'] + [t['dateTime'].replace('+09:00', '').replace('T', ' ') for t in time_def]
    result.append(timeList)

    # Report time
    rtime = data['reportDateTime'].replace('+09:00', '').replace('T', ' ')
    result.append(['reportTime'] + [rtime] * (len(timeList) - 1))

    # Weather
    result.append(['weather'] + areaData['weather'])

    # Wind
    windList = [['direction'], ['level'], ['min_speed'], ['max_speed']]
    for d in areaData['wind']:
        r = d['range'].split()
        windList[0].append(d['direction'])
        windList[1].append(d['speed'])
        windList[2].append(r[0])
        windList[3].append(r[1])
    result.extend(windList)

    #Temperature
    tempList = ['temp']
    max_temp = None
    min_temp = None
    for i, d in enumerate(pointData['temperature']):
        t = pointData['timeDefines'][i]['dateTime'].replace('+09:00', '').replace('T', ' ')
        if t in timeList:
            tempList.append(d)
            if not pointData['maxTemperature'][i] == '':
                max_temp = pointData['maxTemperature'][i]
            if not pointData['minTemperature'][i] == '':
                min_temp = pointData['minTemperature'][i]
        elif i < len(timeList) - 1:
            tempList.append(None)
    result.append(tempList)
    result.append(['max_temp'] + [max_temp] * (len(tempList) - 1))
    result.append(['min_temp'] + [min_temp] * (len(tempList) - 1))
    return result, pointData["pointNameEN"]


def saveData(data, name):
    os.makedirs(saveDir, exist_ok=True)
    filename = f'{saveDir}/{name}.csv'
    try:
        with open(filename, 'r') as f:
            csvData = [l for l in csv.reader(f)]
        writeData = []
        top_time = datetime.strptime(data[1][0], r'%Y-%m-%d %H:%M:%S')
        for i, line in enumerate(csvData[1:]):  # データの日付を比較
            t = datetime.strptime(line[0], r'%Y-%m-%d %H:%M:%S')
            if t >= top_time:
                writeData = csvData[:i+1]
                break
        else:
            writeData = csvData
        # 既存データにくっつける
        writeData.extend(data[1:])
    except FileNotFoundError:
        writeData = data
    # 保存
    with open(filename, 'w') as f:
        writer = csv.writer(f)
        writer.writerows(writeData)


def saveData1(data, name):
    filename = f'{saveDir}/{name}1.csv'
    os.makedirs(saveDir, exist_ok=True)
    first_time = datetime.strptime(data[0][1], r'%Y-%m-%d %H:%M:%S')
    new_time = first_time.replace(hour=6, minute=0, second=0)
    last_time = new_time + timedelta(days=1, hours=15)
    shift = (first_time - new_time) // timedelta(hours=3)
    datelist = []
    while new_time <= last_time:
        datelist.append(new_time.strftime(r'%Y-%m-%d %H:%M:%S'))
        new_time += timedelta(hours=3)
    writeData = [[label[0]] for label in data]
    for date in datelist:
        if date in data[0]:
            j = data[0].index(date)
            for k, d in enumerate(data):
                writeData[k].append(d[j])
        else:
            for k in range(len(writeData)):
                writeData[k].append('-')
    writeData[0] = ['time'] + datelist
    # 保存
    with open(filename, 'a') as f:
        writer = csv.writer(f)
        writer.writerows(writeData)

def update(ippatume=False):
    global latestTime
    rdatetime = datetime(2020,1,1,0,0)
    for target in areaCode:
        data, name = getData(target)
        rtime = data[1][1]
        rdatetime = datetime.strptime(rtime, r'%Y-%m-%d %H:%M:%S')
        if latestTime < rdatetime:
            data_T = [list(x) for x in zip(*data)]
            saveData1(data, name)
            if rdatetime.hour == 5 or ippatume:
                saveData(data_T, name + '2')
            saveData(data_T, name + '3')
            if logEnable:
                t = time.localtime()
                print(f'[{t.tm_mon}-{t.tm_mday:02} {t.tm_hour}:{t.tm_min:02}] {target} 天気データ取得 （{rtime} 発表）')
    if latestTime < rdatetime:
        latestTime = rdatetime


def run():
    global nextUpdate
    init()
    if logEnable:
        t = time.localtime()
        print(f'[{t.tm_mon}-{t.tm_mday:02} {t.tm_hour}:{t.tm_min:02}] 開始: {interval}時間おきに更新（Ctrl+Cで終了）')
    update(True)
    try:
        while True:
            time.sleep(3600 * interval)
            update()
    except KeyboardInterrupt:
        if logEnable:
            t = time.localtime()
            print(f'\r[{t.tm_mon}-{t.tm_mday:02} {t.tm_hour}:{t.tm_min:02}] 終了')


if __name__ == '__main__':
    run()

