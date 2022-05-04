#!/bin/bash

set -ue

cron_Hour="5,7,11,13,17,19,23"
cron_Min="30"

current_Dir="$HOME/weather"
exec_file="GetWeatherForecast.py"
log_file="gwf.log"

if [ -d $current_Dir ]; then
    cd $current_Dir
    git pull
else
    git clone -q https://github.com/machan1054/weather.git $current_Dir
fi

echo "$HOME/weather にソースコードを保存しました 消さないでね"
echo "観測地点や出力フォルダを変更するときはここを変えてね"

set +ue
if [ -e $current_Dir/$exec_file ] && ! (crontab -l 2>/dev/null | grep -q "$current_Dir/$exec_file") ; then
    cron_job="$cron_Min $cron_Hour * * * cd $current_Dir ; $(which python) $current_Dir/$exec_file >> $current_Dir/$log_file"

    echo "$cron_job" | crontab

    if [ $? = 0 ]; then
        echo "$cron_Hour 時 $cron_Min 分 にデータを取得するように設定しました"
        echo "変更時は 'crontab -e' を使ってください 詳しくはGoogleで検索して"
        exit 0
    else
        echo "失敗"
        echo "macOS の場合は、'xcode-select --install' が効くかも"
        exit 1
    fi
else
    echo "cron に登録しませんでした"
    exit 0
fi
