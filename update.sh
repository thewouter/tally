#!/bin/bash

if [ -f "/data/RadixEnschedeBot/update_tally" ]; then
    cd /data/RadixEnschedeBot
    git pull| tee /home/wouter/tally.log
    rm /data/RadixEnschedeBot/update_tally
    python3 /data/RadixEnschedeBot/RadixEnschedeBot.py restart
fi