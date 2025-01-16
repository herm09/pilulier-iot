from machine import RTC, Pin
import time

# Configuration de l'horloge en temps réel (RTC)
rtc = RTC()
rtc.datetime((2024, 12, 12, 0, 16, 37, 0, 0))  # (année, mois, jour, jour_semaine, heure, minute, seconde, milliseconde)

# Configuration de la LED
led = Pin(13, Pin.OUT)
moteur = Pin(16, Pin.OUT)
led.value(0)
moteur.value(0)

# Heure cible
target_time = (16, 37, 5)  # Heure, minute, seconde

while True:
    # Obtenir l'heure actuelle depuis le RTC
    now = rtc.datetime()
    current_time = (now[4], now[5], now[6])  # Heure, minute, seconde
    print(current_time)
    if current_time == target_time:
        print("LED allumée à", current_time)
        for i in range(0, 10):
            led.value(1)
            time.sleep(0.5)
            led.value(0)
            time.sleep(0.5)
        led.value(0)
        break  # Arrêter la boucle
    
    time.sleep(1)  # Attendre une seconde
