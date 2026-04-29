#!/usr/bin/env python3
# coding=utf-8
# File name   : APPServer.py
# Production  : picar-b2
# Website     : www.adeept.com
# Author      : Adeept
# Date        : 2025/05/16
import time
import threading
import move
import os
import info
import RPIservo

import functions
import robotLight
import switch
import socket


import asyncio
import websockets

import json
import app
import Voltage
import Buzzer
import subprocess
import speech_function

OLED_connection = 1
try:
    import OLED
    screen = OLED.OLED_ctrl()
    screen.start()
    screen.screen_show(1, 'ADEEPT.COM')
except:
    OLED_connection = 0
    print('OLED disconnected\n')
    pass


functionMode = 0
speed_set = 50
rad = 0.5
turnWiggle = 60

servoCtrl = RPIservo.ServoCtrl()
servoCtrl.moveInit()
servoCtrl.start()

fuc = functions.Functions()
fuc.setup()
fuc.start()

#buzzer
player = Buzzer.Player()
player.start()

batteryMonitor = Voltage.BatteryLevelMonitor()
batteryMonitor.start()

curpath = os.path.realpath(__file__)
thisPath = "/" + os.path.dirname(curpath)

def functionSelect(command_input, response):
    global functionMode
    if 'scan' == command_input:
        servoCtrl.moveAngle(2, 0)
        radar_send = fuc.radarScan()
        response['title'] = 'scanResult'
        response['data'] = radar_send
        time.sleep(0.3)

    elif 'findColor' == command_input:
        flask_app.modeselect('findColor')
        flask_app.modeselectApp('APP')

    elif 'motionGet' == command_input:
        flask_app.modeselect('watchDog')
        if OLED_connection:
            screen.screen_show(4,'MOTION GET')

    elif 'stopCV' == command_input:
        flask_app.modeselect('none')
        switch.switch(1,0)
        switch.switch(2,0)
        switch.switch(3,0)
        time.sleep(0.2)
        servoCtrl.moveInit()
        move.motorStop()
        if OLED_connection:
            screen.screen_show(4,'FUNCTION OFF')

    elif 'keepDistance' == command_input:
        servoCtrl.moveInit()
        fuc.keepDistance()
        if OLED_connection:
            screen.screen_show(4,'KEEP DISTANCE')

    elif 'keepDistanceOff' == command_input:
        fuc.pause()
        move.motorStop()
        if OLED_connection:
            screen.screen_show(4,'FUNCTION OFF')

    elif 'automatic' == command_input:
        servoCtrl.moveInit()
        fuc.automatic()
        if OLED_connection:
            screen.screen_show(4,'AUTOMATIC')

    elif 'automaticOff' == command_input:
        fuc.pause()
        servoCtrl.moveInit()
        move.motorStop()
        if OLED_connection:
            screen.screen_show(4,'FUNCTION OFF')

    elif 'trackLine' == command_input:
        servoCtrl.moveInit()
        fuc.trackLine()
        if OLED_connection:
            screen.screen_show(4,'TRACK LINE')

    elif 'trackLineOff' == command_input:
        fuc.pause()
        servoCtrl.moveInit()
        move.motorStop()
        if OLED_connection:
            screen.screen_show(4,'FUNCTION OFF')

    elif 'lightTrack' == command_input:
        servoCtrl.moveInit()
        fuc.trackLight()
        if OLED_connection:
            screen.screen_show(4,'LIGHT TRACK')


    elif 'lightTrackOff' == command_input:
        fuc.pause()
        servoCtrl.moveInit()
        move.motorStop()
        if OLED_connection:
            screen.screen_show(4,'FUNCTION OFF')

    elif 'speech' == command_input:
        speech.speech()
        if OLED_connection:
            screen.screen_show(4,'SPEECH')

    elif 'speechOff' == command_input:
        speech.pause()
        if OLED_connection:
            screen.screen_show(4,'FUNCTION OFF')   

    elif 'Buzzer_Music' == command_input:
        player.start_playing()
        if OLED_connection:
            screen.screen_show(4,'BUZZER MUSIC')

    elif 'Buzzer_Music_Off' == command_input:
        player.pause()
        if OLED_connection:
            screen.screen_show(4,'FUNCTION OFF')

def switchCtrl(command_input, response):
    if 'Switch_1_on' in command_input:
        switch.switch(1,1)

    elif 'Switch_1_off' in command_input:
        switch.switch(1,0)

    elif 'Switch_2_on' in command_input:
        switch.switch(2,1)

    elif 'Switch_2_off' in command_input:
        switch.switch(2,0)

    elif 'Switch_3_on' in command_input:
        switch.switch(3,1)

    elif 'Switch_3_off' in command_input:
        switch.switch(3,0) 


def robotCtrl(command_input, response):
    clen = len(command_input.split())
    if 'forward' in command_input and clen == 2:
        move.move(speed_set, 1, "mid")
    
    elif 'backward' in command_input and clen == 2:
        move.move(speed_set, -1, "mid")

    elif 'left' in command_input and clen == 2:
        servoCtrl.moveAngle(0, -50)
        time.sleep(0.15)
        move.move(speed_set, 1, "mid")
        time.sleep(0.15)

    elif 'right' in command_input and clen == 2:
        servoCtrl.moveAngle(0, 35)
        time.sleep(0.15)
        move.move(speed_set, 1, "mid")
        time.sleep(0.15)

    elif 'DTS' in command_input:
        servoCtrl.moveAngle(0, 0)
        move.motorStop()

    elif 'lookleft' == command_input:
        servoCtrl.singleServo(1, 1, 7)

    elif 'lookright' == command_input:
        servoCtrl.singleServo(1,-1, 7)

    elif 'LRStop' in command_input:
        servoCtrl.stopWiggle()

    elif 'up' == command_input:
        servoCtrl.singleServo(2, 1, 7)

    elif 'down' == command_input:
        servoCtrl.singleServo(2,-1, 7)

    elif 'UDstop' in command_input:
        servoCtrl.stopWiggle()

    elif 'home' == command_input:
        servoCtrl.moveServoInit([0,1,2])

def robotCtrl_speech(command_input, response):
    if 'forward' == command_input:
        servoCtrl.moveAngle(0, 0)
        move.move(speed_set, 1, "mid")
    
    elif 'backward' == command_input:
        servoCtrl.moveAngle(0, 0)
        move.move(speed_set, -1, "mid")

    elif 'DS' in command_input:
        move.motorStop()

    elif 'left' == command_input:
        servoCtrl.moveAngle(0, -50)
        time.sleep(0.15)
        move.move(speed_set, 1, "mid")

    elif 'right' == command_input:
        servoCtrl.moveAngle(0, 35)
        time.sleep(0.15)
        move.move(speed_set, 1, "mid")

    elif 'TS' in command_input:
        servoCtrl.moveAngle(0, 0)
        move.motorStop()

    elif 'lookleft' == command_input:
        servoCtrl.singleServo(1, 1, 7)

    elif 'lookright' == command_input:
        servoCtrl.singleServo(1,-1, 7)

    elif 'LRstop' in command_input:
        servoCtrl.stopWiggle()

    elif 'up' == command_input:
        servoCtrl.singleServo(2, 1, 7)

    elif 'down' == command_input:
        servoCtrl.singleServo(2,-1, 7)

    elif 'UDstop' in command_input:
        servoCtrl.stopWiggle()
    
    elif 'home' in command_input:
        servoCtrl.moveInit()
        time.sleep(0.1)



async def recv_msg(websocket):
    global speed_set, modeSelect
    move.setup()

    while True: 
        response = {
            'status' : 'ok',
            'title' : '',
            'data' : None
        }

        data = ''
        data = await websocket.recv()
        try:
            data = json.loads(data)
        except Exception as e:
            print('not A JSON')

        if not data:
            continue

        if isinstance(data,str):
            robotCtrl(data, response)

            switchCtrl(data, response)

            functionSelect(data, response)

            if 'get_info' == data:
                vol = batteryMonitor.get_battery_percentage()
                response['title'] = 'get_info'
                response['data'] = [info.get_cpu_tempfunc(), info.get_cpu_use(), info.get_ram_info(), vol]
                if OLED_connection:
                    screen.screen_show(5,f'bat level:{vol}%')

            if 'wsB' in data:
                try:
                    set_B=data.split()
                    speed_set = int(set_B[1])*10
                except:
                    pass

            #CVFL
            elif 'CVFL' == data:
                flask_app.modeselect('findlineCV')

            elif 'CVFLColorSet' in data:
                color = int(data.split()[1])
                flask_app.camera.colorSet(color)

            elif 'CVFLL1' in data:
                pos = int(data.split()[1])
                flask_app.camera.linePosSet_1(pos)

            elif 'CVFLL2' in data:
                pos = int(data.split()[1])
                flask_app.camera.linePosSet_2(pos)

        elif(isinstance(data,dict)):
            color = data['data']
            if "title" in data and data['title'] == "findColorSet":
                flask_app.colorFindSetApp(color[0],color[1],color[2])
            elif data['lightMode'] == "breath":  
                WS2812.breath(color[0],color[1],color[2])
            elif data['lightMode'] == "flowing":
                WS2812.flowing(color[0],color[1],color[2])
            elif data['lightMode'] == "rainbow":
                WS2812.rainbow(color[0],color[1],color[2])
            elif data['lightMode'] == "police":
                WS2812.police()

        print(data)
        response = json.dumps(response)
        await websocket.send(response)

async def main_logic(websocket, path):
    await recv_msg(websocket)

def show_wlan0_ip():
    try:
        if OLED_connection:
            result = subprocess.run(
                "ifconfig wlan0 | grep 'inet ' | awk '{print $2}'",
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8'
            ) 
            screen.screen_show(2, "IP:" + result.stdout.strip())
    except Exception as e:
        pass

def show_network_mode():
    try:
        if OLED_connection:
            result = subprocess.run(
                "if iw dev wlan0 link | grep -q 'Connected'; then echo 'Station Mode'; else echo 'AP Mode'; fi",
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8'
            )
            screen.screen_show(3, result.stdout.strip())
    except Exception as e:
        pass


if __name__ == '__main__':
    switch.switchSetup()
    switch.set_all_switch_off()

    show_wlan0_ip()
    time.sleep(0.5)
    show_network_mode()

    global flask_app
    flask_app = app.webapp()
    flask_app.startthread()

    try:
        # global WS2812
        WS2812 = robotLight.Adeept_SPI_LedPixel(16, 25)
        if WS2812.check_spi_state() != 0:
            WS2812.start()
            WS2812.breath(70,70,255)
        else:
            WS2812.led_close()
    except:
        WS2812.led_close()
        pass

    try:
        speech = speech_function.Speech(control_callback = robotCtrl_speech)
        speech.daemon = True
        speech.start()
    except Exception as e:
        pass

    while  1:
        try:                  #Start server,waiting for client
            start_server = websockets.serve(main_logic, '0.0.0.0', 8888)
            asyncio.get_event_loop().run_until_complete(start_server)
            print('waiting for connection...')
            break
        except Exception as e:
            print(e)
            WS2812.set_all_led_color_data(0,0,0)
            WS2812.show()

    try:
        asyncio.get_event_loop().run_forever()
    except Exception as e:
        print(e)
        WS2812.set_all_led_color_data(0,0,0)
        WS2812.show()
        move.destroy()
