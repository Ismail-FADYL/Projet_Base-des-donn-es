import streamlit as st
import sqlite3
import pandas as pd

# --- Configuration ---
DB_NAME = 'ma_base.db'
PAGE_TITLE = "Gestion Hôtel"
MENU_OPTIONS = {
    "Réservations": "Consulter et Ajouter Réservations",
    "Clients": "Consulter et Ajouter Clients",
    "Chambres": "Consulter Disponibilité Chambres"
}

# --- Database Connection ---
def get_connection():
    """Establishes and returns a database connection."""
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row  # Access results by column name
        return conn
    except sqlite3.Error as e:
        st.error(f"Erreur de connexion à la base de données: {e}")
        return None

# --- Data Retrieval Functions ---
def fetch_reservations(conn):
    """Retrieves all reservations with client and hotel details."""

    query = """
        SELECT r.Id_Reservation, c.Nom_complet AS Client, h.Ville AS Hotel, r.Date_arrivee, r.Date_depart
        FROM Reservation r
        JOIN Client c ON r.Id_Client = c.Id_Client
        JOIN Chambre ch ON r.Id_Chambre = ch.Id_Chambre
        JOIN Hotel h ON ch.Id_Hotel = h.Id_Hotel
    """
    return pd.read_sql_query(query, conn)

def fetch_clients(conn):
    """Retrieves all clients."""
    return pd.read_sql_query("SELECT * FROM Client", conn)

def fetch_available_rooms(conn, start_date, end_date):
    """Retrieves available rooms within a given date range."""

    query = f"""
        SELECT ch.Id_Chambre, h.Ville AS Hotel, tc.Type AS Chambre_Type
        FROM Chambre ch
        JOIN Hotel h ON ch.Id_Hotel = h.Id_Hotel
        JOIN Type_Chambre tc ON ch.Id_Type = tc.Id_Type
        WHERE ch.Id_Chambre NOT IN (
            SELECT DISTINCT ch.Id_Chambre
            FROM Chambre ch
            JOIN Reservation r ON ch.Id_Chambre = r.Id_Chambre
            WHERE r.Date_arrivee <= '{end_date}' AND r.Date_depart >= '{start_date}'
        )
    """
    return pd.read_sql_query(query, conn)

# --- Data Insertion Functions ---
def insert_client(conn, client_data):
    """Inserts a new client into the database."""

    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Client (Nom_complet, Adresse, Ville, Code_postal, Email, Numero_telephone)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', tuple(client_data.values()))
        conn.commit()
        st.success("Client ajouté!")
    except sqlite3.Error as e:
        st.error(f"Erreur lors de l'ajout du client: {e}")

def insert_reservation(conn, reservation_data):
    """Inserts a new reservation into the database."""

    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Reservation (Id_Client, Id_Chambre, Date_arrivee, Date_depart)
            VALUES (?, ?, ?, ?)
        ''', tuple(reservation_data.values()))
        conn.commit()
        st.success("Réservation ajoutée!")
    except sqlite3.Error as e:
        st.error(f"Erreur lors de l'ajout de la réservation: {e}")

# --- UI Components ---
def display_header(title):
    """Displays a consistent header."""
    st.header(title)
    st.markdown("---")  # Separator line

def display_reservations():
    """Displays the reservations table."""

    display_header(MENU_OPTIONS["Réservations"])
    conn = get_connection()
    if conn:
        df = fetch_reservations(conn)
        st.dataframe(df)
        conn.close()

def display_clients():
    """Displays the clients table."""

    display_header(MENU_OPTIONS["Clients"])
    conn = get_connection()
    if conn:
        df = fetch_clients(conn)
        st.dataframe(df)
        conn.close()

def display_available_rooms():
    """Displays available rooms with date range selection."""

    display_header(MENU_OPTIONS["Chambres"])
    conn = get_connection()
    if conn:
        start_date = st.date_input("Date d'arrivée")
        end_date = st.date_input("Date de départ")

        if start_date and end_date:
            df = fetch_available_rooms(conn, start_date, end_date)
            st.dataframe(df)
        conn.close()

def add_client_form():
    """Displays a form to add a new client."""

    display_header("Ajouter un Client")
    with st.form("add_client"):
        col1, col2 = st.columns(2)  # Create two columns for layout

        with col1:
            nom_complet = st.text_input("Nom Complet", max_chars=100,  help="Entrez le nom complet du client.")
            adresse = st.text_input("Adresse", max_chars=200, help="Entrez l'adresse du client.")
            ville = st.text_input("Ville", max_chars=50, help="Entrez la ville du client.")
            email = st.text_input("Email",  help="Entrez l'email du client.")

        with col2:
            code_postal = st.text_input("Code Postal", max_chars=10, help="Entrez le code postal du client.")
            numero_telephone = st.text_input("Numéro de Téléphone", max_chars=20, help="Entrez le numéro de téléphone du client.")
            submit_button = st.form_submit_button("Ajouter")

        if submit_button:
            if nom_complet and adresse and ville and code_postal and email and numero_telephone:
                new_client = {
                    "Nom_complet": nom_complet,
                    "Adresse": adresse,
                    "Ville": ville,
                    "Code_postal": code_postal,
                    "Email": email,
                    "Numero_telephone": numero_telephone
                }
                conn = get_connection()
                if conn:
                    insert_client(conn, new_client)
                    conn.close()
            else:
                st.warning("Veuillez remplir tous les champs.")

def add_reservation_form():
    """Displays a form to add a new reservation."""

    display_header("Ajouter une Réservation")
    conn = get_connection()
    if not conn:
        return  # Exit if no connection

    clients_data = pd.read_sql_query("SELECT Id_Client, Nom_complet FROM Client", conn)
    chambres_data = pd.read_sql_query("SELECT Id_Chambre FROM Chambre", conn)
    conn.close()

    with st.form("add_reservation"):
        client_id = st.selectbox("Client", clients_data['Id_Client'], format_func=lambda id: f"{clients_data[clients_data['Id_Client'] == id]['Nom_complet'].iloc[0]} ({id})")
        chambre_id = st.selectbox("Chambre", chambres_data['Id_Chambre'])
        date_arrivee = st.date_input("Date d'arrivée")
        date_depart = st.date_input("Date de départ")
        submit_button = st.form_submit_button("Ajouter")

        if submit_button:
            if client_id and chambre_id and date_arrivee and date_depart:
                new_reservation = {
                    "Id_Client": client_id,
                    "Id_Chambre": chambre_id,
                    "Date_arrivee": date_arrivee,
                    "Date_depart": date_depart
                }
                conn = get_connection()
                if conn:
                    insert_reservation(conn, new_reservation)
                    conn.close()
            else:
                st.warning("Veuillez remplir tous les champs.")

# --- Main Application ---
def main():
    st.set_page_config(page_title=PAGE_TITLE, layout="wide")  # Wider layout
    st.title(PAGE_TITLE)

    menu_choice = st.sidebar.selectbox("Navigation", list(MENU_OPTIONS.values()))

    if menu_choice == MENU_OPTIONS["Réservations"]:
        display_reservations()
        add_reservation_form()  # Add reservation form on the same page
    elif menu_choice == MENU_OPTIONS["Clients"]:
        display_clients()
        add_client_form()  # Add client form on the same page
    elif menu_choice == MENU_OPTIONS["Chambres"]:
        display_available_rooms()

if __name__ == "__main__":
    main()
