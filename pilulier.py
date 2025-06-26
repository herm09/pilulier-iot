# from machine import Pin; Pin(13, Pin.OUT).value(0)

from machine import Pin, RTC, I2C
import ssd1306
import time

# -------------------- RTC (Real-Time Clock) --------------------

rtc = RTC()

# Set the initial RTC time (change this only once)
rtc.datetime((2025, 3, 20, 3, 11, 41, 0, 0))  # (YYYY, MM, DD, Weekday, HH, MM, SS, MS)

# -------------------- DAILY ALERT TIMES --------------------

# Define 3 daily medication reminder times: (HH, MM, SS)
daily_alerts = [
    (11, 41, 10),     # 08:00:00
    (11, 41, 20),    # 13:00:00
    (11, 41, 30)     # 19:00:00
]

triggered_alerts = set()  # Keeps track of triggered alerts for the day

# -------------------- LED & MOTOR --------------------

led = Pin(13, Pin.OUT)    # LED connected to GPIO 13
moteur = Pin(16, Pin.OUT) # Motor connected to GPIO 16
led.value(0)
moteur.value(0)

# -------------------- OLED DISPLAY --------------------

i2c = I2C(0, scl=Pin(5), sda=Pin(4))  # I2C for OLED (SCL=GP5, SDA=GP4)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

def update_oled(message):
    """ Function to update the OLED display with a message """
    oled.fill(0)
    oled.text(message, 10, 30)
    oled.show()

# -------------------- MAIN LOOP --------------------

last_day = -1  # Tracks the last day to reset daily alerts

while True:
    now = rtc.datetime()
    current_time = (now[4], now[5], now[6])  # (HH, MM, SS)
    today = now[2]  # Day of the month

    # Reset triggered alerts at the start of a new day
    if today != last_day:
        triggered_alerts.clear()
        last_day = today

    # Display current time on OLED
    oled.fill(0)
    oled.text("Time:", 10, 10)
    oled.text(f"{now[4]:02}:{now[5]:02}:{now[6]:02}", 10, 30)
    oled.show()

    # Print to terminal
    print(f"Paris Time: {now[2]:02}/{now[1]:02}/{now[0]} {now[4]:02}:{now[5]:02}:{now[6]:02}")

    # Check if any alert time matches current time and hasn't triggered yet
    for alert_time in daily_alerts:
        if current_time == alert_time and alert_time not in triggered_alerts:
            led.value(1)
            moteur.value(1)
            print(f"🚨 Reminder at {alert_time[0]:02}:{alert_time[1]:02}:{alert_time[2]:02}")
            update_oled("MEDICATION TIME")
            time.sleep(5)
            led.value(0)
            moteur.value(0)
            triggered_alerts.add(alert_time)

    time.sleep(1)
