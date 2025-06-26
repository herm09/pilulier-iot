from machine import Pin, RTC, I2C
import ssd1306
import time

# -------------------- RTC --------------------
rtc = RTC()
rtc.datetime((2025, 3, 20, 3, 11, 41, 0, 0))

# -------------------- ALERTES --------------------
daily_alerts = []
triggered_alerts = set()

# -------------------- IO --------------------
led = Pin(13, Pin.OUT)
moteur = Pin(16, Pin.OUT)
led.value(0)
moteur.value(0)

# OLED
i2c = I2C(0, scl=Pin(5), sda=Pin(4))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# Boutons
btn_up = Pin(15, Pin.IN, Pin.PULL_UP)
btn_down = Pin(16, Pin.IN, Pin.PULL_UP)
btn_validate = Pin(17, Pin.IN, Pin.PULL_UP)

# -------------------- UTIL --------------------
def update_oled(message):
    oled.fill(0)
    oled.text(message, 0, 30)
    oled.show()

def wait_release(pin):
    while not pin.value():
        time.sleep(0.01)

def choose_yes_no(prompt):
    """Affiche une question et retourne True pour oui, False pour non"""
    choice = 0  # 0=Oui, 1=Non
    while True:
        oled.fill(0)
        oled.text(prompt, 0, 10)
        oled.text("Oui" if choice == 0 else "Non", 50, 40)
        oled.show()

        if not btn_up.value():
            choice = 0
            wait_release(btn_up)
        if not btn_down.value():
            choice = 1
            wait_release(btn_down)
        if not btn_validate.value():
            wait_release(btn_validate)
            return choice == 0
        time.sleep(0.1)

# -------------------- EDIT ALERTS --------------------
def edit_alerts():
    global daily_alerts
    while True:
        if not choose_yes_no("Programmer alerte?"):
            update_oled("Fin programmation")
            time.sleep(1)
            break

        alert = [0, 0, 0]  # HH, MM, SS
        field_index = 0
        fields = ["Heure", "Minute", "Seconde"]

        while field_index < 3:
            oled.fill(0)
            oled.text(f"{fields[field_index]}:", 0, 10)
            oled.text(f"{alert[field_index]:02}", 60, 30)
            oled.show()

            if not btn_up.value():
                alert[field_index] = (alert[field_index] + 1) % (24 if field_index == 0 else 60)
                wait_release(btn_up)
            if not btn_down.value():
                alert[field_index] = (alert[field_index] - 1) % (24 if field_index == 0 else 60)
                wait_release(btn_down)
            if not btn_validate.value():
                wait_release(btn_validate)
                field_index += 1

            time.sleep(0.1)

        daily_alerts.append(tuple(alert))
        update_oled("Alerte ajoutee")
        time.sleep(1)

# -------------------- MAIN LOOP --------------------
last_day = -1

while True:
    now = rtc.datetime()
    current_time = (now[4], now[5], now[6])
    today = now[2]

    # Entrer en mode édition (appui long sur bouton 3)
    if not btn_validate.value():
        press_start = time.ticks_ms()
        while not btn_validate.value():
            if time.ticks_diff(time.ticks_ms(), press_start) > 3000:
                update_oled("Mode modif...")
                edit_alerts()
                break
        time.sleep(0.5)

    # Réinitialiser les alertes déjà jouées
    if today != last_day:
        triggered_alerts.clear()
        last_day = today

    # Afficher l'heure sur OLED
    oled.fill(0)
    oled.text("Heure:", 10, 10)
    oled.text(f"{now[4]:02}:{now[5]:02}:{now[6]:02}", 10, 30)
    oled.show()

    # Debug terminal
    print(f"{now[2]:02}/{now[1]:02}/{now[0]} {now[4]:02}:{now[5]:02}:{now[6]:02}")

    # Vérifier les alertes
    for alert_time in daily_alerts:
        if current_time == alert_time and alert_time not in triggered_alerts:
            led.value(1)
            moteur.value(1)
            update_oled("MEDICATION TIME")
            print(f"🚨 Alerte à {alert_time}")
            time.sleep(5)
            led.value(0)
            moteur.value(0)
            triggered_alerts.add(alert_time)

    time.sleep(1)

