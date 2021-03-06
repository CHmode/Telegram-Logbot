#!/usr/bin/env python3

import telegram
import tailer
import re
import urllib.request
import json
import sys
import configparser
import os

from telegram.ext import Updater
from telegram.ext import CommandHandler

with open(os.path.expanduser(sys.argv[1])) as fp:
    config = configparser.ConfigParser()
    config.read_file(fp)

token = None

try:
    token = config.get("settings", "token")
except (configparser.NoSectionError, configparser.NoOptionError):
    print("Invalid config file.")
    exit(1)

if not token or token == "":
    print("No telegram bot token, please speak to the botfather.")
    exit(1)

ipstack_token = None

try:
    ipstack_token = config.get("settings", "ipstack_token")
except (configparser.NoSectionError, configparser.NoOptionError):
    pass

path = None

if config.get("settings", "logpath"):
    path = config.get("settings", "logpath")
else:
    path = "/var/log/auth.log"

updater = Updater(token=token)
dispatcher = updater.dispatcher
bot = None
chatid = None

def sendIPOnMap(ip):

    global ipstack_token

    if ipstack_token:
        global bot

        try:
            with urllib.request.urlopen("http://api.ipstack.com/"+ip+"?access_key="+ipstack_token) as url:
                data = json.loads(url.read().decode())
                bot.send_location(chat_id=chatid, latitude=data["latitude"], longitude=data["longitude"])
        except HTTPError as e:
            print(e)
            sendMessage("Unable to locate IP")
         
def sendMessage(message):
    global bot
    global chatid
    
    bot.send_message(chat_id=chatid, text=message)
    
def start(abot, update):

    print("Starting")

    global bot
    bot = abot

    global chatid
    chatid = update.message.chat_id

    for line in tailer.follow(open(path)):

        match1 = re.search("authentication error for (.*) from (\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})", line)
        match2 = re.search("Failed password for (.*) from (\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})", line)
    
        match = None

        if match1:
            match = match1
        elif match2:
            match = match2

        if match:

            print("Authentication Failure")

            message = "Authentication failure for "

            nameArray = match.group(1).split()
        
            if not len(nameArray) == 1:
                name = nameArray[-1]

                message += "non-existent user "
                message +=  name
            
            else:
                message += "user "
                message += nameArray[0]
            
            message += " from "
            message += match.group(2)
    
            sendMessage(message)
            sendIPOnMap(match.group(2))

        else:

            match1 = None
            match2 = None
            match = None

            match1 = re.search("Accepted keyboard-interactive\/pam for (.*) from (\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})", line)
            match2 = re.search("Accepted password for (.*) from (\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})", line)

            match = None

            if match1:
                match = match1
            elif match2:
                match = match2

            if match:

                print("Authentication successfull")

                message = "User "
                name = match.group(1)

                message += name
                message += " logged in successfully from "

                ip = match.group(2)
                message += ip

                sendMessage(message)
                sendIPOnMap(ip)

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)
updater.start_polling()

print("Logbot initialized. send /start to it to begin")
