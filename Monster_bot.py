import os
import time
import sqlite3
import requests
from datetime import datetime

# --- KONFIGURACJA ---
TELEGRAM_BOT_TOKEN = "9254381219:AAH_heZCVsOzbxA1Li2U6rjFOm-yCYGj4t0"
TELEGRAM_CHAT_ID = "7221307802"
CHECK_INTERVAL = 7200  # Co 2 godziny (w sekundach)

# Inicjalizacja bazy danych SQLite do unikania duplikatów i rozliczeń
def init_db():
    conn = sqlite3.connect('monsters_bets.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posted_bets (
            match_id TEXT PRIMARY KEY,
            match_name TEXT,
            odds REAL,
            status TEXT DEFAULT 'PENDING'
        )
    ''')
    conn.commit()
    conn.close()

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Błąd wysyłania do Telegrama: {e}")

def check_duplicate(match_id):
    conn = sqlite3.connect('monsters_bets.db')
    cursor = conn.cursor()
    cursor.execute("SELECT match_id FROM posted_bets WHERE match_id = ?", (match_id,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def save_bet(match_id, match_name, odds):
    conn = sqlite3.connect('monsters_bets.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO posted_bets (match_id, match_name, odds) VALUES (?, ?, ?)", 
                   (match_id, match_name, odds))
    conn.commit()
    conn.close()

def fetch_value_bets():
    """
    Główna funkcja skanująca rynki (Betclic PLN / Agregatory kursów).
    Szuka dyscyplin: piłka, tenis, esport, baseball, dart, hokej, kosz, siata.
    Kryteria: Kurs zdarzenia > 1.20, budowanie AKO do max 3 zdarzeń.
    """
    # TUTAJ wpinamy właściwy endpoint / scraper danych Betclic PLN
    # Poniżej symulacja struktury zwracanej przez silnik analityczny:
    
    found_matches = [
        # Przykładowy format: {"id": "match_123", "sport": "Koszykówka (Filipiny)", "teams": "Barangay vs Ginebra", "pick": "Ginebra Win", "odds": 1.35}
    ]
    
    valid_picks = []
    for match in found_matches:
        if not check_duplicate(match['id']) and match['odds'] > 1.20:
            valid_picks.append(match)
            
    return valid_picks

def run_monster_bot():
    init_db()
    print("Monster's Bets wystartował i monitoruje rynki...")
    
    while True:
        print(f"[{datetime.now()}] Skanowanie rynków (Betclic - PLN)...")
        picks = fetch_value_bets()
        
        if not picks:
            send_telegram_message("🤖 **Monster's Bets** | Skan zakończony.\nStatus: `No matches` (brak spotkań spełniających rygorystyczne kryteria VIP).")
        else:
            # Tworzenie kuponu AKO (max 3 zdarzenia)
            ako_slip = picks[:3] 
            message = "🔥 **MONSTER'S BETS - VIP AKO KUPON** 🔥\n\n"
            total_odds = 1.0
            
            for p in ako_slip:
                message += f"📌 **[{p['sport']}]** {p['teams']}\n"
                message += f"🎯 Typ: `{p['pick']}` | Kurs: `{p['odds']}` (Betclic)\n\n"
                total_odds *= p['odds']
                save_bet(p['id'], p['teams'], p['odds'])
                
            message += f"💰 **Łączny kurs AKO:** `{total_odds:.2f}`\n"
            message += f"🏦 Stawka bazowa: **100 zł** | Potencjalna wygrana: **{(100 * total_odds):.2f} zł**"
            
            send_telegram_message(message)
            
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run_monster_bot()