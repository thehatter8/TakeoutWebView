#!/bin/bash

killall screen
# Probably remove that eventually

screen -dmS backend
screen -S backend -X stuff 'python3 ~/testproject/mapsite/backend/app.py\n'
echo 'Backend Started!'
