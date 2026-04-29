from gpiozero import DigitalInputDevice
import time
import move
import RPIservo
import subprocess
import functions


IR_GPIO = 12  # GPIO pin
TOLERANCE = 0.5  # tolerance for NEC decoding
MIN_NORMAL_PULSES = 20  # minimum pulses for valid NEC code
REPEAT_PULSES = 25

repeat_code = "repeat"
# Robot movement parameters
speed_set = 30
# Store pulse data: (signal_level, timestamp_microsec)
pulse_timestamps = []

# Key mapping 
key_map = {
    0xA2: "A",
    0x62: "B",
    0xE2: "C",
    0x22: "D",
    0x02: "UP",
    0xC2: "E",
    0xE0: "LEFT",
    0xA8: "OK",
    0x90: "RIGHT",
    0x68: "0",
    0x98: "DOWN",
    0xB0: "F",
    0x30: "1",
    0x18: "2",
    0x7A: "3",
    0x10: "4",
    0x38: "5",
    0x5A: "6",
    0x42: "7",
    0x4A: "8",
    0x52: "9"
}

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


def pulse_callback(level):
    timestamp = time.time_ns() // 1000
    pulse_timestamps.append((level, timestamp))
    #print(f"[RAW] Level: {level}, Timestamp: {timestamp}μs | Pulses captured: {len(pulse_timestamps)}")
    if len(pulse_timestamps) > 200:
        pulse_timestamps.pop(0)


def calculate_time_diff(t1, t2):
    if t1 > t2:
        return (0xFFFFFFFF - t1) + t2
    return t2 - t1


def is_within_tolerance(measured, expected):
    min_val = expected * (1 - TOLERANCE)
    max_val = expected * (1 + TOLERANCE)
    return min_val <= measured <= max_val


def decode_nec_debug():
    """
    Returns (address, data) if decoding succeeds; None otherwise.
    """
    global pulse_timestamps
    # Skip if not enough pulses 
    if len(pulse_timestamps) < 4:
        return None

    # Copy and clear pulse buffer
    pulses = pulse_timestamps.copy()
    pulse_timestamps = []
    pulse_count = len(pulses)
    #print(f"[DEBUG] Processing {pulse_count} pulses")

    # Skip NEC repeat codes
    if pulse_count == 4:
        return None

    # Skip if pulse count is too low
    if pulse_count < MIN_NORMAL_PULSES:
        return None
    
    if pulse_count <= REPEAT_PULSES:
        return repeat_code

    # Verify NEC header (9ms high + 4.5ms low)
    t0, t1, t2 = [p[1] for p in pulses[:3]] 
    hdr_mark = calculate_time_diff(t0, t1)
    hdr_space = calculate_time_diff(t1, t2)
    if not (is_within_tolerance(hdr_mark, 9000) and is_within_tolerance(hdr_space, 4500)):
        return None

    # Decode 32-bit NEC data
    data_bits = []
    valid_bits = 0
    for i in range(2, pulse_count - 2, 2):
        # Extract timestamps for current bit (high + low)
        t_prev = pulses[i][1]
        t_curr = pulses[i+1][1]
        t_next = pulses[i+2][1]

        # Check bit high time (must be ~560μs)
        bit_mark = calculate_time_diff(t_prev, t_curr)
        if not is_within_tolerance(bit_mark, 560):
            continue

        # Determine bit value (0 = ~560μs low, 1 = ~1690μs low)
        bit_space = calculate_time_diff(t_curr, t_next)
        if is_within_tolerance(bit_space, 1690):
            data_bits.append(1)
            valid_bits += 1
        elif is_within_tolerance(bit_space, 560):
            data_bits.append(0)
            valid_bits += 1

    # Skip if incomplete data (less than 32 valid bits)
    if valid_bits < 32:
        return None

    # Convert bits to address/data 
    address = int(''.join(map(str, data_bits[0:8])), 2)
    address_inv = int(''.join(map(str, data_bits[8:16])), 2)
    data = int(''.join(map(str, data_bits[16:24])), 2)
    data_inv = int(''.join(map(str, data_bits[24:32])), 2)

    # Verify data integrity (XOR check)
    if (address ^ address_inv) == 0xFF and (data ^ data_inv) == 0xFF:
        return (address, data)
    else:
        return None


def robotCtrl(command):
    global scGear, fuc
    if 'UP' == command:
        scGear.moveAngle(0, 0)
        move.move(speed_set, 1, "mid")
        print("forward")
    
    elif 'DOWN' == command:
        scGear.moveAngle(0, 0)
        move.move(speed_set, -1, "mid")
        print("backward")

    elif 'LEFT' == command:
        scGear.moveAngle(0, -50)
        move.move(speed_set, 1, "mid")
        print("turn_left")        

    elif 'RIGHT' == command:
        scGear.moveAngle(0, 35)
        move.move(speed_set, 1, "mid")
        print("turn_right")

    elif 'DTS' in command:
        scGear.moveAngle(0, 0)
        move.motorStop()
        print('stop')

    elif '4' == command:
        scGear.singleServo(1, 1, 7)
        print("head_left")

    elif '6' == command:
        scGear.singleServo(1, -1, 7)
        print("head_right")
        
    elif '2' == command:
        scGear.singleServo(2, 1, 7)
        print("head_up")

    elif '8' == command:
        scGear.singleServo(2, -1, 7)
        print("head_down")

    elif 'HSTOP' in command:
        scGear.stopWiggle()

    elif 'A' == command:
        scGear.moveInit()
        fuc.keepDistance()
        print("keepDistance")
        if OLED_connection:
            screen.screen_show(4,'KEEP DISTANCE')

    elif 'C' == command:
        scGear.moveInit()
        fuc.automatic()
        print("automatic")
        if OLED_connection:
            screen.screen_show(4,'AUTOMATIC')

    elif 'OK' == command:    
        fuc.pause()
        scGear.moveInit()
        move.motorStop()
        print("stop")
        if OLED_connection:
            screen.screen_show(4,'FUNCTION OFF')


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


def main(): 
    global scGear, fuc
    # GPIOZero IR Receiver Initialization
    ir_receiver = DigitalInputDevice(
        pin=IR_GPIO,
        pull_up=True,  
        bounce_time=0.0003  # 300μs debounce (filters noise)
    )
    ir_receiver.when_activated = lambda: pulse_callback(1)
    ir_receiver.when_deactivated = lambda: pulse_callback(0)

    scGear = RPIservo.ServoCtrl()
    scGear.moveInit()
    scGear.start()

    show_wlan0_ip()
    time.sleep(0.5)
    show_network_mode()

    fuc = functions.Functions()
    fuc.setup()
    fuc.start()

    print("IR Robot Controller Started")
    print("Press Ctrl+C to exit...")
    button_command = "OK"
    try:
        while True:
            time.sleep(0.4)
            result = decode_nec_debug()
            if result is not None:
                if repeat_code not in result:
                    address, data = result
                    button_command = key_map.get(data, f"unknown key(0x{data:02X})")
                    print(f"command：{button_command} ")

                robotCtrl(button_command)
                if button_command.endswith("4") or button_command.endswith("6") or button_command.endswith("2") or button_command.endswith("8"):
                    time.sleep(0.5)
                    robotCtrl("HSTOP")

    except KeyboardInterrupt:
        print("\nexit")
    finally:
        ir_receiver.close()  

if __name__ == "__main__":
    main()