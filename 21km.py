import streamlit as st
import sqlite3
from datetime import date

# --- DATENBANK FUNKTIONEN ---
def init_db():
    conn = sqlite3.connect('quest.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  firstname TEXT, 
                  lastname TEXT, 
                  start_date DATE,
                  points INTEGER DEFAULT 0)''')

    # Falls die Tabelle schon existiert, password-Spalte nachträglich hinzufügen
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]

    if "password" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN password TEXT")

    conn.commit()
    conn.close()



def save_user(fname, lname, password):
    conn = sqlite3.connect('quest.db')
    c = conn.cursor()
    try:
        # Wir fügen die Spalte 'password' zum Insert-Befehl hinzu
        c.execute("INSERT INTO users (firstname, lastname, password, start_date) VALUES (?, ?, ?, ?)", 
                  (fname, lname, password, date.today()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        st.error("Dieser Benutzername existiert bereits.")
        return False
    except Exception as e:
        st.error(f"Fehler beim Speichern: {e}")
        return False
    finally:
        conn.close()

def get_user_stats(username):
    """Holt Gesamtpunkte und Gesamtkilometer für einen User aus der DB."""
    conn = sqlite3.connect('quest.db')
    c = conn.cursor()
    
    # Wir holen Punkte direkt aus der Users-Tabelle und summieren die km aus Check-ins
    # Das setzt voraus, dass ihr gestern die Tabellen 'users' und 'checkins' erstellt habt.
    try:
        c.execute("""
            SELECT 
                u.points,
                COALESCE(SUM(c.actual_km), 0) as total_km
            FROM users u
            LEFT JOIN checkins c ON u.user_id = c.user_id
            WHERE u.username = ?
            GROUP BY u.user_id
        """, (username,))
        
        result = c.fetchone()
        
        # Fallback, falls der User noch keine Check-ins hat
        if result:
            return {"points": result[0], "kilometers": result[1]}
        else:
            return {"points": 0, "kilometers": 0}
            
    except Exception as e:
        st.error(f"Fehler beim Laden der Statistik: {e}")
        return {"points": 0, "kilometers": 0}
    finally:
        conn.close()

# --- APP INITIALISIERUNG ---
init_db()

# --- SIDEBAR NAVIGATION (User Story 2) ---
st.sidebar.title("🏃‍♂️ 21km-Challenge")
menu = ["Anmeldung", "Profil & Statistik", "Mein Trainingsplan", "Leaderboard", "Check-in"]
choice = st.sidebar.selectbox("Navigation", menu)

# --- SEITE: ANMELDUNG ---
if choice == "Anmeldung":
    st.title("Erstelle dein Läufer-Konto")
    
    # Hier werden die Variablen definiert:
    with st.form("registration_form"):
        col1, col2 = st.columns(2)
        with col1:
            firstname = st.text_input("Vorname") # Hier wird firstname definiert
        with col2:
            lastname = st.text_input("Nachname")
            
        password = st.text_input("Wähle ein Passwort", type="password")
        password_confirm = st.text_input("Passwort bestätigen", type="password")
        
        # Hier wird submit definiert:
        submit = st.form_submit_button("Konto erstellen")
        
        if submit:
            if not (firstname and lastname and password):
                st.error("Bitte alle Felder ausfüllen.")
            elif password != password_confirm:
                st.error("Die Passwörter stimmen nicht überein.")
            else:
                if save_user(firstname, lastname, password):
                    st.success(f"Konto für {firstname} erfolgreich erstellt!")
                    st.balloons()
                    st.session_state.user = firstname # Jetzt ist firstname bekannt!

# --- HIER EINFÜGEN: SEITE: PROFIL & STATISTIK ---
elif choice == "Profil & Statistik":
    st.title("🏃‍♂️ Dein Läufer-Profil")
    
    if 'user' in st.session_state:
        logged_in_user = st.session_state.user
        stats = get_user_stats(logged_in_user)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Gesamtleistung", value=f"{stats['kilometers']:.1f} km")
        with col2:
            st.metric(label="Gesammelte Punkte", value=f"{stats['points']} Pkt")
            
        st.divider()
        st.info("💡 Logge deinen nächsten Lauf im 'Check-in', um deine Statistik zu erhöhen!")
    else:
        st.warning("⚠️ Bitte logge dich zuerst unter 'Anmeldung' ein.")

# --- SEITE: TRAININGSPLAN (Hier geht dein alter Code weiter) ---
elif choice == "Mein Trainingsplan":
    st.title("🏃‍♂️ Dein 12-Wochen-Weg")
# ...
    st.title("Erstelle dein Läufer-Konto")
    st.markdown("Damit deine Fortschritte individuell gespeichert werden, erstelle bitte ein Profil.")
    
    with st.form("registration_form"):
        col1, col2 = st.columns(2)
        with col1:
            firstname = st.text_input("Vorname")
        with col2:
            lastname = st.text_input("Nachname")
            
        password = st.text_input("Wähle ein Passwort", type="password")
        password_confirm = st.text_input("Passwort bestätigen", type="password")
        
        submit = st.form_submit_button("Konto erstellen")
        
        if submit:
            if not (firstname and lastname and password):
                st.error("Bitte alle Felder ausfüllen.")
            elif password != password_confirm:
                st.error("Die Passwörter stimmen nicht überein.")
            else:
                if save_user(firstname, lastname, password):
                    st.success(f"Konto für {firstname} erfolgreich erstellt!")
                    st.balloons()
                    # Wir merken uns den User direkt für diese Session
                    st.session_state.user = firstname

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