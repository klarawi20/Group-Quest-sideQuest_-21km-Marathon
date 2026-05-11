import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime

# --- DATENBANK FUNKTIONEN ---
def init_db():
    conn = sqlite3.connect('quest.db')
    c = conn.cursor()

    # USERS TABELLE
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firstname TEXT,
            lastname TEXT,
            password TEXT,
            start_date DATE,
            points INTEGER DEFAULT 0
        )
    ''')

    # Alte users-Tabelle prüfen und fehlende Spalten ergänzen
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]

    if "password" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN password TEXT")

    if "start_date" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN start_date DATE")

    if "points" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0")

    # CHECKINS TABELLE
    c.execute('''
        CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            run_date DATE,
            actual_km REAL,
            duration_min INTEGER,
            points_earned INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()


def save_user(fname, lname, password, start_date):
    conn = sqlite3.connect('quest.db')
    c = conn.cursor()

    try:
        c.execute(
            """
            INSERT INTO users 
            (firstname, lastname, password, start_date)
            VALUES (?, ?, ?, ?)
            """,
            (fname, lname, password, start_date)
        )

        conn.commit()
        return True

    except Exception as e:
        st.error(f"Fehler beim Speichern: {e}")
        return False

    finally:
        conn.close()


# --- APP INITIALISIERUNG ---
init_db()

# --- SIDEBAR ---
st.sidebar.title("🏃‍♂️ 21km-Challenge")

menu = [
    "Anmeldung",
    "Mein Trainingsplan",
    "Leaderboard",
    "Check-in"
]

choice = st.sidebar.selectbox("Navigation", menu)

# =========================================================
# ANMELDUNG
# =========================================================
if choice == "Anmeldung":

    st.title("🏃‍♂️ Erstelle dein Läufer-Konto")

    st.markdown(
        "Damit deine Fortschritte individuell gespeichert werden, "
        "erstelle bitte ein Profil."
    )

    with st.form("registration_form"):

        col1, col2 = st.columns(2)

        with col1:
            firstname = st.text_input("Vorname")

        with col2:
            lastname = st.text_input("Nachname")

        start_date = st.date_input("Startdatum auswählen")

        password = st.text_input(
            "Wähle ein Passwort",
            type="password"
        )

        password_confirm = st.text_input(
            "Passwort bestätigen",
            type="password"
        )

        submit = st.form_submit_button("Konto erstellen")

        if submit:

            if not (firstname and lastname and password):
                st.error("Bitte alle Felder ausfüllen.")

            elif password != password_confirm:
                st.error("Die Passwörter stimmen nicht überein.")

            else:

                if save_user(
                    firstname,
                    lastname,
                    password,
                    start_date
                ):

                    st.success(
                        f"Konto für {firstname} erfolgreich erstellt!"
                    )

                    st.balloons()

                    # User in Session speichern
                    st.session_state.user = firstname


# =========================================================
# TRAININGSPLAN
# =========================================================
elif choice == "Mein Trainingsplan":

    st.title("🏃‍♂️ Dein 3-Wochen-Trainingsplan")

    st.markdown(
        "Hier ist deine Roadmap zum Halbmarathon:"
    )

    # 3-WOCHEN TRAININGSPLAN
    plan_data = {
        "Woche": [
            1,1,1,1,1,1,1,
            2,2,2,2,2,2,2,
            3,3,3,3,3,3,3
        ],

        "Tag": [
            "Mo","Di","Mi","Do","Fr","Sa","So",
            "Mo","Di","Mi","Do","Fr","Sa","So",
            "Mo","Di","Mi","Do","Fr","Sa","So"
        ],

        "Training": [
            "Rest-Day",
            "5km Lauf",
            "Rest-Day",
            "4x800m Intervalle",
            "Rest",
            "Lockerer Lauf 6km",
            "Langer Lauf 8km",

            "Rest-Day",
            "6km Lauf",
            "Rest-Day",
            "5x800m Intervalle",
            "Rest-Day",
            "Lockerer Lauf 7km",
            "Langer Lauf 10km",

            "Rest-Day",
            "7km Lauf",
            "Rest-Day",
            "6x800m Intervalle",
            "Rest-Day",
            "Lockerer Lauf 8km",
            "Langer Lauf 12km"
        ],

        "Ziel (km)": [
            0,5.0,0,3.2,0,6.0,8.0,
            0,6.0,0,4.0,0,7.0,10.0,
            0,7.0,0,4.8,0,8.0,12.0
        ]
    }

    df_plan = pd.DataFrame(plan_data)

    # USER PRÜFEN
    if "user" not in st.session_state:

        st.warning(
            "Bitte erstelle zuerst ein Konto."
        )

    else:

        firstname = st.session_state.user

        conn = sqlite3.connect("quest.db")
        c = conn.cursor()

        c.execute(
            """
            SELECT start_date 
            FROM users 
            WHERE firstname = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (firstname,)
        )

        result = c.fetchone()

        conn.close()

        if result:

            start_date = datetime.strptime(
                result[0],
                "%Y-%m-%d"
            ).date()

            days_since_start = (
                date.today() - start_date
            ).days

            if days_since_start < 0:

                st.error(
                    "Dein Startdatum liegt in der Zukunft."
                )

            elif days_since_start >= len(df_plan):

                st.success(
                    "🎉 Dein 3-Wochen-Trainingsplan ist abgeschlossen!"
                )

            else:

                todays_training = df_plan.iloc[
                    days_since_start
                ]

                st.subheader("📌 Dein heutiger Lauf")

                st.info(
                    f"Tag {days_since_start + 1} "
                    f"({todays_training['Tag']}): "
                    f"{todays_training['Training']}"
                )

                if todays_training["Ziel (km)"] > 0:

                    st.write(
                        f"Ziel: "
                        f"**{todays_training['Ziel (km)']} km**"
                    )

                else:

                    st.write(
                        "Heute ist ein Ruhetag 💪"
                    )

    st.subheader("📅 Kompletter Trainingsplan")

    def highlight_rest_days(row):
       if row["Training"] == "Rest-Day":
            return ["background-color: #89986D"] * len(row)  # hellgrün
       else:
            return [""] * len(row)

    styled_df = df_plan.style.apply(
        highlight_rest_days,
        axis=1
    )

    st.dataframe(
        styled_df,
        use_container_width=True
    )
    

    st.info(
        "💡 Tipp: Konsistenz ist wichtiger als Geschwindigkeit!"
    )


# =========================================================
# LEADERBOARD
# =========================================================
elif choice == "Leaderboard":

    st.title("🏆 Leaderboard")

    conn = sqlite3.connect("quest.db")

    leaderboard = pd.read_sql_query(
        """
        SELECT firstname, lastname, points
        FROM users
        ORDER BY points DESC
        """,
        conn
    )

    conn.close()

    if leaderboard.empty:

        st.info("Noch keine Punkte vorhanden.")

    else:

        st.dataframe(
            leaderboard,
            use_container_width=True
        )


# =========================================================
# CHECK-IN
# =========================================================
elif choice == "Check-in":

    st.title("🏃‍♂️ Lauf loggen")

    if "user" not in st.session_state:

        st.warning(
            "Bitte erstelle zuerst ein Konto, "
            "um deine Läufe zu speichern."
        )

    else:

        st.write(
            f"Hallo **{st.session_state.user}**, "
            f"trage hier dein Training ein:"
        )

        with st.form("checkin_form"):

            run_date = st.date_input(
                "Wann bist du gelaufen?",
                date.today()
            )

            km = st.number_input(
                "Distanz in km",
                min_value=0.1,
                step=0.1
            )

            duration = st.number_input(
                "Dauer in Minuten",
                min_value=1,
                step=1
            )

            submit_run = st.form_submit_button(
                "Lauf speichern & Punkte sammeln"
            )

            if submit_run:

                # VALIDIERUNG: keine 0 oder negativen Werte erlauben
                if km <= 0:
                    st.error("Die Kilometer müssen größer als 0 sein.")

                elif duration <= 0:
                    st.error("Die Dauer muss größer als 0 sein.")

                else:
                    earned_points = int(km * 10)

                    try:
                        conn = sqlite3.connect("quest.db")
                        c = conn.cursor()

                        c.execute(
                            """
                            SELECT id 
                            FROM users 
                            WHERE firstname = ?
                            ORDER BY id DESC
                            LIMIT 1
                            """,
                            (st.session_state.user,)
                        )

                        user = c.fetchone()

                        if user is None:
                            st.error("Benutzer wurde nicht gefunden.")

                        else:
                            user_id = user[0]

                            c.execute(
                                """
                                INSERT INTO checkins
                                (
                                    user_id,
                                    run_date,
                                    actual_km,
                                    duration_min,
                                    points_earned
                                )
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (
                                    user_id,
                                    run_date,
                                    km,
                                    duration,
                                    earned_points
                                )
                            )

                            c.execute(
                                """
                                UPDATE users
                                SET points = points + ?
                                WHERE id = ?
                                """,
                                (
                                    earned_points,
                                    user_id
                                )
                            )

                            conn.commit()

                            st.success(
                                f"Super! Du hast {km} km geloggt "
                                f"und {earned_points} Punkte erhalten!"
                            )

                            st.balloons()

                        conn.close()

                    except Exception as e:
                        st.error(f"Fehler beim Speichern: {e}")
        # =====================================
        # LETZTE CHECK-INS ANZEIGEN
        # =====================================

        st.subheader("📋 Deine letzten Aktivitäten")

        conn = sqlite3.connect("quest.db")

        query = """
            SELECT 
                run_date AS Datum,
                actual_km AS Kilometer,
                duration_min AS Minuten,
                points_earned AS Punkte
            FROM checkins
            WHERE user_id = (
                SELECT id 
                FROM users
                WHERE firstname = ?
                ORDER BY id DESC
                LIMIT 1
            )
            ORDER BY run_date DESC
            LIMIT 5
        """

        history_df = pd.read_sql_query(
            query,
            conn,
            params=(st.session_state.user,)
        )

        conn.close()

        if history_df.empty:
            st.info("Noch keine Läufe gespeichert.")

        else:
            history_df.index = history_df.index + 1

            st.dataframe(
                history_df,
                use_container_width=True
            )