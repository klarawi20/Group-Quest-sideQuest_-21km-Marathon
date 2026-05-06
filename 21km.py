import streamlit as st
import sqlite3
from datetime import date

# --- DATENBANK FUNKTIONEN ---
def init_db():
    conn = sqlite3.connect('quest.db')
    c = conn.cursor()
    # Tabellen für User und den Plan erstellen
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  firstname TEXT, 
                  lastname TEXT, 
                  start_date DATE,
                  points INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def save_user(fname, lname):
    conn = sqlite3.connect('quest.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (firstname, lastname, start_date) VALUES (?, ?, ?)", 
                  (fname, lname, date.today()))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Fehler beim Speichern: {e}")
        return False
    finally:
        conn.close()

# --- APP INITIALISIERUNG ---
init_db()

# --- SIDEBAR NAVIGATION (User Story 2) ---
st.sidebar.title("🏃‍♂️ 21km-Challenge")
menu = ["Anmeldung", "Mein Trainingsplan", "Leaderboard", "Check-in"]
choice = st.sidebar.selectbox("Navigation", menu)

# --- SEITE: ANMELDUNG ---
if choice == "Anmeldung":
    st.title("Willkommen zur Challenge")
    st.markdown("Registriere dich hier, um deinen 12-Wochen-Plan zu starten.")
    
    with st.form("registration_form"):
        firstname = st.text_input("Vorname")
        lastname = st.text_input("Nachname")
        submit = st.form_submit_button("Jetzt registrieren")
        
        if submit:
            if firstname and lastname:
                if save_user(firstname, lastname):
                    st.success(f"Willkommen, {firstname}! Dein Training startet heute.")
                    st.balloons()
                    st.session_state.user = firstname
            else:
                st.error("Bitte beide Felder ausfüllen.")

# --- SEITE: TRAININGSPLAN ---
elif choice == "Mein Trainingsplan":
    st.title("🏃‍♂️ Dein 12-Wochen-Weg")
    st.markdown("Hier ist deine Roadmap zum Halbmarathon:")

    # Beispiel-Daten für den Plan (Woche 1)
    plan_data = {
        "Woche": [1, 1, 1, 1, 1, 1, 1],
        "Tag": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
        "Training": ["Rest", "5km Lauf", "Rest", "4x800m Intervalle", "Rest", "Lockerer Lauf 6km", "Langer Lauf 8km"],
        "Ziel (km)": [0, 5.0, 0, 3.2, 0, 6.0, 8.0]
    }
    
    import pandas as pd
    df_plan = pd.DataFrame(plan_data)
    
    # Anzeige als Tabelle
    st.table(df_plan)
    
    st.info("💡 Tipp: Konsistenz ist wichtiger als Geschwindigkeit!")


# --- SEITE: LEADERBOARD ---
elif choice == "Leaderboard":
    st.title("🏆 Leaderboard")
    st.write("Wer führt die Challenge an?")
    # Platzhalter für die Highscore-Tabelle (Sprint 3)

# --- SEITE: CHECK-IN ---
elif choice == "Check-in":
    st.title("Lauf loggen")
    st.write("Trage hier deine gelaufenen Kilometer ein.")