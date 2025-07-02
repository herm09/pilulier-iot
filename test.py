from machine import Pin, RTC, I2C
import ssd1306
import time

# -------------------- RTC --------------------
rtc = RTC()
rtc.datetime((2025, 3, 20, 3, 11, 41, 0, 0))  # (année, mois, jour, jour_semaine, heure, minute, seconde, microseconde)

# -------------------- ALERTES --------------------
# Structure: {jour_semaine: [(heure, minute, seconde), ...]}
# jour_semaine: 0=Lundi, 1=Mardi, 2=Mercredi, 3=Jeudi, 4=Vendredi, 5=Samedi, 6=Dimanche
weekly_alerts = {
    0: [],  # Lundi
    1: [],  # Mardi
    2: [],  # Mercredi
    3: [],  # Jeudi
    4: [],  # Vendredi
    5: [],  # Samedi
    6: []   # Dimanche
}

triggered_alerts = set()
days_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

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
def update_oled(message, line=30):
    oled.fill(0)
    oled.text(message, 0, line)
    oled.show()

def update_oled_multi(lines):
    """Affiche plusieurs lignes sur l'OLED"""
    oled.fill(0)
    for i, line in enumerate(lines):
        if i < 8:  # Max 8 lignes sur l'écran
            oled.text(line, 0, i * 8)
    oled.show()

def wait_release(pin):
    while not pin.value():
        time.sleep(0.01)

def choose_yes_no(prompt):
    """Affiche une question et retourne True pour oui, False pour non"""
    choice = 0  # 0=Oui, 1=Non
    options = ["Oui", "Non"]
    
    while True:
        oled.fill(0)
        oled.text(prompt, 0, 10)
        oled.text(f"> {options[choice]}", 0, 30)
        oled.text("UP/DOWN: choisir", 0, 50)
        oled.show()

        if not btn_up.value():
            choice = choice - 1
            if choice < 0:
                choice = 1
            wait_release(btn_up)
        if not btn_down.value():
            choice = choice + 1
            if choice > 1:
                choice = 0
            wait_release(btn_down)
        if not btn_validate.value():
            wait_release(btn_validate)
            return choice == 0  # True pour "Oui", False pour "Non"
        time.sleep(0.1)

def choose_day():
    """Permet de choisir un jour de la semaine"""
    day_index = 0
    while True:
        oled.fill(0)
        oled.text("Choisir jour:", 0, 10)
        oled.text(f"> {days_names[day_index]}", 0, 30)
        oled.text(f"({len(weekly_alerts[day_index])} alertes)", 0, 45)
        oled.text("UP/DOWN + OK", 0, 55)
        oled.show()

        if not btn_up.value():
            day_index = (day_index - 1) % 7
            wait_release(btn_up)
        if not btn_down.value():
            day_index = day_index + 1
            if day_index > 6:
                day_index = 0
            wait_release(btn_down)
        if not btn_validate.value():
            wait_release(btn_validate)
            return day_index
        time.sleep(0.1)

def set_time():
    """Interface pour définir une heure personnalisée"""
    alert = [12, 0, 0]  # HH, MM, SS (commence par 12:00:00)
    field_index = 0
    fields = ["Heure", "Minute", "Seconde"]
    max_values = [23, 59, 59]  # Valeurs maximales pour chaque champ

    while field_index < 3:
        oled.fill(0)
        oled.text("Config. heure:", 0, 0)
        oled.text(f"{fields[field_index]}:", 0, 15)
        oled.text(f"> {alert[field_index]:02d}", 50, 15)
        
        # Afficher l'heure complète en cours
        oled.text(f"{alert[0]:02d}:{alert[1]:02d}:{alert[2]:02d}", 0, 35)
        
        # Instructions
        oled.text("UP:+  DOWN:-", 0, 50)
        oled.text("OK: suivant", 70, 50)
        oled.show()

        if not btn_up.value():
            alert[field_index] = (alert[field_index] + 1) % (max_values[field_index] + 1)
            wait_release(btn_up)
        if not btn_down.value():
            alert[field_index] = (alert[field_index] - 1) % (max_values[field_index] + 1)
            wait_release(btn_down)
        if not btn_validate.value():
            wait_release(btn_validate)
            field_index += 1

        time.sleep(0.1)

    return tuple(alert)



# -------------------- EDIT ALERTS --------------------
def edit_alerts():
    global weekly_alerts
    
    while True:
        if not choose_yes_no("Ajouter alerte?"):
            update_oled("Fin programmation")
            time.sleep(1)
            break

        # Choisir le jour
        selected_day = choose_day()
        
        # Configurer l'heure librement
        alert_time = set_time()

        # Vérifier si l'alerte existe déjà
        if alert_time in weekly_alerts[selected_day]:
            update_oled_multi([
                "Alerte existe",
                "deja!"
            ])
            time.sleep(2)
            continue

        # Ajouter l'alerte
        weekly_alerts[selected_day].append(alert_time)
        
        # Trier les alertes par ordre chronologique
        weekly_alerts[selected_day].sort()
        
        # Confirmation
        update_oled_multi([
            f"{days_names[selected_day]}",
            f"{alert_time[0]:02d}:{alert_time[1]:02d}:{alert_time[2]:02d}",
            "Alerte ajoutee!"
        ])
        time.sleep(2)

def view_alerts():
    """Affiche toutes les alertes programmées"""
    for day_idx, day_name in enumerate(days_names):
        if weekly_alerts[day_idx]:
            oled.fill(0)
            oled.text(f"{day_name}:", 0, 0)
            for i, alert in enumerate(weekly_alerts[day_idx][:7]):  # Max 7 alertes affichées
                oled.text(f"{alert[0]:02}:{alert[1]:02}:{alert[2]:02}", 0, 10 + i * 8)
            oled.show()
            time.sleep(3)
        else:
            update_oled_multi([day_name, "Aucune alerte"])
            time.sleep(1)

def delete_alerts():
    """Interface pour supprimer des alertes"""
    selected_day = choose_day()
    
    if not weekly_alerts[selected_day]:
        update_oled("Aucune alerte")
        time.sleep(1)
        return
    
    # Choix entre supprimer toutes ou une seule alerte
    if choose_yes_no("Suppr. toutes?"):
        weekly_alerts[selected_day].clear()
        update_oled("Toutes supprimees")
        time.sleep(1)
    else:
        # Supprimer une alerte spécifique
        if len(weekly_alerts[selected_day]) == 1:
            weekly_alerts[selected_day].clear()
            update_oled("Alerte supprimee")
            time.sleep(1)
        else:
            alert_index = 0
            alerts_list = weekly_alerts[selected_day]
            
            while True:
                oled.fill(0)
                oled.text("Supprimer:", 0, 0)
                oled.text(f"> {alerts_list[alert_index][0]:02d}:{alerts_list[alert_index][1]:02d}:{alerts_list[alert_index][2]:02d}", 0, 20)
                oled.text(f"({alert_index + 1}/{len(alerts_list)})", 0, 40)
                oled.show()
                
                if not btn_up.value():
                    alert_index = (alert_index - 1) % len(alerts_list)
                    wait_release(btn_up)
                if not btn_down.value():
                    alert_index = (alert_index + 1) % len(alerts_list)
                    wait_release(btn_down)
                if not btn_validate.value():
                    wait_release(btn_validate)
                    weekly_alerts[selected_day].pop(alert_index)
                    update_oled("Alerte supprimee")
                    time.sleep(1)
                    break
                time.sleep(0.1)

def menu_options():
    """Menu principal pour la gestion des alertes"""
    options = [
        ("Ajouter", edit_alerts),
        ("Voir", view_alerts),
        ("Supprimer", delete_alerts)
    ]
    
    option_index = 0
    while True:
        oled.fill(0)
        oled.text("Menu config:", 0, 0)
        oled.text(f"> {options[option_index][0]}", 0, 20)
        oled.text("UP/DOWN: nav", 0, 40)
        oled.text("Long OK: quit", 0, 50)
        oled.show()

        if not btn_up.value():
            option_index = option_index - 1
            if option_index < 0:
                option_index = 2
            wait_release(btn_up)
        if not btn_down.value():
            option_index = option_index + 1
            if option_index > 2:
                option_index = 0
            wait_release(btn_down)
        if not btn_validate.value():
            # Appui court: exécuter l'option
            press_start = time.ticks_ms()
            while not btn_validate.value():
                if time.ticks_diff(time.ticks_ms(), press_start) > 2000:
                    return  # Appui long: quitter le menu
                time.sleep(0.01)
            
            # Appui court: exécuter la fonction
            options[option_index][1]()
        time.sleep(0.1)

# -------------------- MAIN LOOP --------------------
last_day = -1

while True:
    now = rtc.datetime()
    current_time = (now[4], now[5], now[6])
    current_day = now[3]  # Jour de la semaine (0=Lundi)
    today = now[2]

    # Entrer en mode édition (appui long sur bouton validate)
    if not btn_validate.value():
        press_start = time.ticks_ms()
        while not btn_validate.value():
            if time.ticks_diff(time.ticks_ms(), press_start) > 3000:
                update_oled("Mode config...")
                time.sleep(1)
                menu_options()
                break
            time.sleep(0.01)
        time.sleep(0.5)

    # Réinitialiser les alertes déjà jouées chaque nouveau jour
    if today != last_day:
        triggered_alerts.clear()
        last_day = today

    # Afficher l'heure et le jour sur OLED
    oled.fill(0)
    oled.text(f"{days_names[current_day]}", 0, 0)
    oled.text(f"{now[4]:02}:{now[5]:02}:{now[6]:02}", 0, 20)
    
    # Afficher prochaine alerte
    today_alerts = weekly_alerts[current_day]
    if today_alerts:
        next_alert = None
        for alert in sorted(today_alerts):
            if alert > current_time and alert not in triggered_alerts:
                next_alert = alert
                break
        
        if next_alert:
            oled.text(f"Proch: {next_alert[0]:02}:{next_alert[1]:02}", 0, 40)
        else:
            oled.text("Aucune prochaine", 0, 40)
    else:
        oled.text("Pas d'alerte", 0, 40)
    
    oled.show()

    # Debug terminal
    print(f"{now[2]:02}/{now[1]:02}/{now[0]} {now[4]:02}:{now[5]:02}:{now[6]:02} - {days_names[current_day]}")

    # Vérifier les alertes du jour actuel
    for alert_time in weekly_alerts[current_day]:
        alert_key = (current_day, alert_time)
        if current_time == alert_time and alert_key not in triggered_alerts:
            led.value(1)
            moteur.value(1)
            update_oled_multi([
                "MEDICATION TIME!",
                f"{days_names[current_day]}",
                f"{alert_time[0]:02}:{alert_time[1]:02}:{alert_time[2]:02}"
            ])
            print(f"🚨 Alerte {days_names[current_day]} à {alert_time}")
            
            # Alerte pendant 10 secondes
            for _ in range(10):
                led.value(not led.value())  # Clignotement
                time.sleep(0.5)
            
            led.value(0)
            moteur.value(0)
            triggered_alerts.add(alert_key)

    time.sleep(1)
