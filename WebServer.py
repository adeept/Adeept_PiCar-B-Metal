#!/usr/bin/env python3
# coding=utf-8
# File name   : webServer_HAT_V3.1.py
# Production  : picar-b2
# Website     : www.adeept.com
# Author      : Adeept
# Date        : 2025/05/16
import time
import move
import os
import info
import RPIservo

import functions
import robotLight
import switch
import asyncio
import websockets

import json
import app
import Voltage
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

servoCtrl = RPIservo.ServoCtrl()
servoCtrl.moveInit()
servoCtrl.start()

fuc = functions.Functions()
fuc.setup()
fuc.start()

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

    elif 'KD' == command_input:
        servoCtrl.moveInit()
        fuc.keepDistance()
        if OLED_connection:
            screen.screen_show(4,'KEEP DISTANCE')

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

    elif 'police' == command_input:
        WS2812.police()
        if OLED_connection:
            screen.screen_show(4,'POLICE')

    elif 'policeOff' == command_input:
        WS2812.breath(70,70,255)
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
    if 'forward' == command_input:
        move.move(speed_set, 1, "mid")
    
    elif 'backward' == command_input:
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

def configPWM(command_input):
    if 'SiLeft' in command_input:
        servo_index = int(command_input[7:])
        servoCtrl.adjust_init_angle(servo_index, 1)
    if 'SiRight' in command_input:
        servo_index = int(command_input[8:])
        servoCtrl.adjust_init_angle(servo_index, -1)
    if 'PWMMS' in command_input:
        servo_index = int(command_input[6:])
        servoCtrl.persist_Servos_init(servo_index)
    if 'PWMD' in command_input:    
        servo_index = int(command_input[5:])
        servoCtrl.init_single_servo(servo_index)

    
async def check_permit(websocket):
    while True:
        recv_str = await websocket.recv()
        print(recv_str)
        cred_dict = recv_str.split(":")
        if cred_dict[0] == "admin" and cred_dict[1] == "123456":
            response_str = "congratulation, you have connect with server\r\nnow, you can do something else"
            await websocket.send(response_str)
            return True
        else:
            response_str = "sorry, the username or password is wrong, please submit again"
            await websocket.send(response_str)

async def recv_msg(websocket):
    global speed_set
    move.setup()

    while True: 
        response = {
            'status' : 'ok',
            'title' : '',
            'data' : None
        }

        data = ''
        data = await websocket.recv()
        # print(f"Received data: {data}")
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

            configPWM(data)

            if 'get_info' == data:
                response['title'] = 'get_info'
                response['data'] = [info.get_cpu_tempfunc(), info.get_cpu_use(), info.get_ram_info()]
                if OLED_connection:
                    vol = batteryMonitor.get_battery_percentage()
                    screen.screen_show(5,f'bat level:{vol}%')
            if 'wsB' in data:
                try:
                    set_B=data.split()
                    speed_set = int(set_B[1])
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

            elif 'CVFLSP' in data:
                err = int(data.split()[1])
                flask_app.camera.errorSet(err)

        elif(isinstance(data,dict)):
            if data['title'] == "findColorSet":
                color = data['data']
                flask_app.colorFindSet(color[0],color[1],color[2])

        print(data)
        response = json.dumps(response)
        await websocket.send(response)

async def main_logic(websocket, path):
    await check_permit(websocket)
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
    global flask_app

    switch.switchSetup()
    switch.set_all_switch_off()

    show_wlan0_ip()
    time.sleep(0.5)
    show_network_mode()

    flask_app = app.webapp()
    flask_app.startthread()

    try:
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
        try:                 
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
