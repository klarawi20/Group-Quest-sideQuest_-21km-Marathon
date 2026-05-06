import streamlit as st
import sqlite3
from datetime import date

# --- DATENBANK FUNKTIONEN ---
def init_db():
    conn = sqlite3.connect('quest.db')
    c = conn.cursor()
    # Tabelle erstellen, falls sie noch nicht existiert
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  firstname TEXT, 
                  lastname TEXT, 
                  start_date DATE)''')
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

# --- APP STARTEN ---
init_db()

st.title("🏃‍♂️ 21km-Challenge")
st.markdown("""
Herzlich Willkommen zur **Half-Marathon Quest**! 
Hier kannst du deinen Fortschritt verfolgen und dich mit anderen Teilnehmern messen. 
Viel Erfolg bei deinem Training!
""")

# --- REGISTRIERUNG (Sprint 1) ---
st.subheader("Anmeldung")

# Eingabefelder (Nur einmal definiert)
firstname = st.text_input("Vorname")
lastname = st.text_input("Nachname")

if st.button("Jetzt registrieren"):
    if firstname and lastname:
        success = save_user(firstname, lastname)
        if success:
            st.success(f"Willkommen im Team, {firstname}!")
            st.write(f"Dein Profil: **{firstname} {lastname.upper()}**")
            st.balloons()
            # Hier setzen wir den User in den Session State für Sprint 2
            st.session_state.user = firstname
    else:
        st.warning("Bitte gib sowohl Vorname als auch Nachname ein.")

# --- NAVIGATION (Vorschau für Sprint 2) ---
if 'user' in st.session_state:
    st.sidebar.success(f"Eingeloggt als: {st.session_state.user}")