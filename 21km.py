import sqlite3
from datetime import date, datetime

import pandas as pd
import streamlit as st

DB_PATH = "quest.db"


# --- TRAININGSPLAN ---
TRAINING_PLAN = [
    {"Woche": 1, "Tag": "Mo", "Training": "Rest", "Ziel (km)": 0.0},
    {"Woche": 1, "Tag": "Di", "Training": "5 km lockerer Lauf", "Ziel (km)": 5.0},
    {"Woche": 1, "Tag": "Mi", "Training": "Rest", "Ziel (km)": 0.0},
    {"Woche": 1, "Tag": "Do", "Training": "4 x 800 m Intervalle", "Ziel (km)": 3.2},
    {"Woche": 1, "Tag": "Fr", "Training": "Rest", "Ziel (km)": 0.0},
    {"Woche": 1, "Tag": "Sa", "Training": "6 km lockerer Lauf", "Ziel (km)": 6.0},
    {"Woche": 1, "Tag": "So", "Training": "8 km langer Lauf", "Ziel (km)": 8.0},

    {"Woche": 2, "Tag": "Mo", "Training": "Rest", "Ziel (km)": 0.0},
    {"Woche": 2, "Tag": "Di", "Training": "5 km lockerer Lauf", "Ziel (km)": 5.0},
    {"Woche": 2, "Tag": "Mi", "Training": "Stabi & Mobility", "Ziel (km)": 0.0},
    {"Woche": 2, "Tag": "Do", "Training": "5 km Tempowechsel", "Ziel (km)": 5.0},
    {"Woche": 2, "Tag": "Fr", "Training": "Rest", "Ziel (km)": 0.0},
    {"Woche": 2, "Tag": "Sa", "Training": "7 km lockerer Lauf", "Ziel (km)": 7.0},
    {"Woche": 2, "Tag": "So", "Training": "9 km langer Lauf", "Ziel (km)": 9.0},

    # ... Wochen 3 bis 12 genauso wie im ZIP ...

    {"Woche": 12, "Tag": "Mo", "Training": "Rest", "Ziel (km)": 0.0},
    {"Woche": 12, "Tag": "Di", "Training": "6 km lockerer Lauf", "Ziel (km)": 6.0},
    {"Woche": 12, "Tag": "Mi", "Training": "Rest", "Ziel (km)": 0.0},
    {"Woche": 12, "Tag": "Do", "Training": "4 km locker + Steigerungen", "Ziel (km)": 4.0},
    {"Woche": 12, "Tag": "Fr", "Training": "Rest", "Ziel (km)": 0.0},
    {"Woche": 12, "Tag": "Sa", "Training": "Aktivierung 3 km", "Ziel (km)": 3.0},
    {"Woche": 12, "Tag": "So", "Training": "Halbmarathon / 21,1 km", "Ziel (km)": 21.1},
]


# --- DATENBANK FUNKTIONEN ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        """CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  firstname TEXT,
                  lastname TEXT,
                  start_date DATE,
                  points INTEGER DEFAULT 0)"""
    )

    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]

    if "password" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN password TEXT")

    conn.commit()
    conn.close()


def save_user(fname, lname, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (firstname, lastname, password, start_date) VALUES (?, ?, ?, ?)",
            (fname, lname, password, date.today().isoformat()),
        )
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Fehler beim Speichern: {e}")
        return False
    finally:
        conn.close()


def get_user(firstname):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT id, firstname, lastname, start_date, points FROM users WHERE firstname = ? ORDER BY id DESC LIMIT 1",
        (firstname,),
    )
    row = c.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "firstname": row[1],
        "lastname": row[2],
        "start_date": row[3],
        "points": row[4] or 0,
    }


def get_user_stats(firstname):
    user = get_user(firstname)
    if not user:
        return {"points": 0, "kilometers": 0}

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='checkins'")
        has_checkins_table = c.fetchone() is not None

        if not has_checkins_table:
            return {"points": user["points"], "kilometers": 0}

        c.execute(
            "SELECT COALESCE(SUM(actual_km), 0) FROM checkins WHERE user_id = ?",
            (user["id"],),
        )
        total_km = c.fetchone()[0]
        return {"points": user["points"], "kilometers": total_km}
    except Exception as e:
        st.error(f"Fehler beim Laden der Statistik: {e}")
        return {"points": user["points"], "kilometers": 0}
    finally:
        conn.close()


# --- ISSUE #7: HEUTIGEN LAUF BERECHNEN ---
def parse_start_date(start_date_value):
    if isinstance(start_date_value, date):
        return start_date_value
    return datetime.strptime(str(start_date_value), "%Y-%m-%d").date()


def get_today_training(start_date_value, today=None):
    today = today or date.today()
    start = parse_start_date(start_date_value)
    days_since_start = (today - start).days

    if days_since_start < 0:
        return {
            "status": "not_started",
            "days_until_start": abs(days_since_start),
            "start_date": start,
        }

    if days_since_start >= len(TRAINING_PLAN):
        return {
            "status": "finished",
            "days_since_start": days_since_start,
            "start_date": start,
        }

    training = TRAINING_PLAN[days_since_start].copy()
    training["status"] = "active"
    training["plan_day"] = days_since_start + 1
    training["start_date"] = start
    return training


def show_today_training(firstname):
    user = get_user(firstname)
    if not user or not user.get("start_date"):
        st.info("Erstelle zuerst ein Profil, damit dein heutiger Lauf berechnet werden kann.")
        return

    today_training = get_today_training(user["start_date"])

    st.subheader("📅 Dein heutiger Lauf")

    if today_training["status"] == "not_started":
        st.info(
            f"Dein Trainingsplan startet am {today_training['start_date'].strftime('%d.%m.%Y')}. "
            f"Noch {today_training['days_until_start']} Tag(e) bis zum Start."
        )
        return

    if today_training["status"] == "finished":
        st.success("Du hast den 12-Wochen-Plan abgeschlossen. Stark! 🎉")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Woche", today_training["Woche"])
    col2.metric("Plantag", today_training["plan_day"])
    col3.metric("Ziel", f"{today_training['Ziel (km)']:.1f} km")

    st.success(f"Heute steht an: **{today_training['Training']}**")


# --- APP INITIALISIERUNG ---
init_db()

st.sidebar.title("🏃‍♂️ 21km-Challenge")
menu = ["Anmeldung", "Profil & Statistik", "Mein Trainingsplan", "Leaderboard", "Check-in"]
choice = st.sidebar.selectbox("Navigation", menu)

if "user" in st.session_state:
    show_today_training(st.session_state.user)
    st.divider()


# --- SEITE: ANMELDUNG ---
if choice == "Anmeldung":
    st.title("Erstelle dein Läufer-Konto")

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
            elif save_user(firstname, lastname, password):
                st.success(f"Konto für {firstname} erfolgreich erstellt!")
                st.balloons()
                st.session_state.user = firstname
                st.rerun()


# --- SEITE: PROFIL & STATISTIK ---
elif choice == "Profil & Statistik":
    st.title("🏃‍♂️ Dein Läufer-Profil")

    if "user" in st.session_state:
        logged_in_user = st.session_state.user
        stats = get_user_stats(logged_in_user)

        col1, col2 = st.columns(2)

        with col1:
            st.metric(label="Gesamtleistung", value=f"{stats['kilometers']:.1f} km")

        with col2:
            st.metric(label="Gesammelte Punkte", value=f"{stats['points']} Pkt")

        st.info("💡 Logge deinen nächsten Lauf im 'Check-in', um deine Statistik zu erhöhen!")
    else:
        st.warning("⚠️ Bitte erst unter 'Anmeldung' ein Profil erstellen.")


# --- SEITE: TRAININGSPLAN ---
elif choice == "Mein Trainingsplan":
    st.title("🏃‍♂️ Dein 12-Wochen-Weg")
    st.markdown("Hier ist deine Roadmap zum Halbmarathon:")

    if "user" in st.session_state:
        show_today_training(st.session_state.user)

    df_plan = pd.DataFrame(TRAINING_PLAN)
    st.dataframe(df_plan, use_container_width=True, hide_index=True)

    st.info("💡 Tipp: Konsistenz ist wichtiger als Geschwindigkeit!")


# --- SEITE: LEADERBOARD ---
elif choice == "Leaderboard":
    st.title("🏆 Leaderboard")
    st.write("Wer führt die Challenge an?")


# --- SEITE: CHECK-IN ---
elif choice == "Check-in":
    st.title("Lauf loggen")
    st.write("Trage hier deine gelaufenen Kilometer ein.")