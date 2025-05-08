import streamlit as st
import sqlite3
import pandas as pd

# Fonction pour se connecter à la base de données
def get_db_connection():
    conn = sqlite3.connect('ma_base.db')  # Utilisation de 'ma_base.db'
    conn.row_factory = sqlite3.Row  # Pour accéder aux résultats par nom de colonne
    return conn

# 1. Consulter la liste des réservations
def consulter_reservations():
    st.header("Liste des Réservations")
    conn = get_db_connection()
    df = pd.read_sql_query('''
        SELECT r.Id_Reservation, c.Nom_complet AS Nom_Client, h.Ville AS Ville_Hotel, r.Date_arrivee, r.Date_depart
        FROM Reservation r
        JOIN Client c ON r.Id_Client = c.Id_Client
        JOIN Chambre ch ON r.Id_Chambre = ch.Id_Chambre
        JOIN Hotel h ON ch.Id_Hotel = h.Id_Hotel
    ''', conn)
    conn.close()
    st.dataframe(df)

# 2. Consulter la liste des clients
def consulter_clients():
    st.header("Liste des Clients")
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM Client", conn)
    conn.close()
    st.dataframe(df)

# 3. Consulter la liste des chambres disponibles pendant une période donnée
def consulter_chambres_disponibles():
    st.header("Chambres Disponibles")
    date_debut = st.date_input("Date de début")
    date_fin = st.date_input("Date de fin")

    if date_debut and date_fin:
        conn = get_db_connection()
        df = pd.read_sql_query(f'''
            SELECT ch.Id_Chambre, h.Ville AS Ville_Hotel, tc.Type AS Type_Chambre
            FROM Chambre ch
            JOIN Hotel h ON ch.Id_Hotel = h.Id_Hotel
            JOIN Type_Chambre tc ON ch.Id_Type = tc.Id_Type
            WHERE ch.Id_Chambre NOT IN (
                SELECT DISTINCT ch.Id_Chambre
                FROM Chambre ch
                JOIN Reservation r ON ch.Id_Chambre = r.Id_Chambre
                WHERE r.Date_arrivee <= '{date_fin}' AND r.Date_depart >= '{date_debut}'
            )
        ''', conn)
        conn.close()
        st.dataframe(df)

# 4. Ajouter un client
def ajouter_client():
    st.header("Ajouter un Client")
    with st.form("ajouter_client_form"):
        nom_complet = st.text_input("Nom Complet")
        adresse = st.text_input("Adresse")
        ville = st.text_input("Ville")
        code_postal = st.text_input("Code Postal")
        email = st.text_input("Email")
        numero_telephone = st.text_input("Numéro de Téléphone")
        submit_button = st.form_submit_button("Ajouter Client")

        if submit_button:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO Client (Nom_complet, Adresse, Ville, Code_postal, Email, Numero_telephone)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (nom_complet, adresse, ville, code_postal, email, numero_telephone))
            conn.commit()
            conn.close()
            st.success("Client ajouté avec succès!")

# 5. Ajouter une réservation
def ajouter_reservation():
    st.header("Ajouter une Réservation")
    conn = get_db_connection()
    cursor = conn.cursor()

    # Récupérer les clients et chambres pour les sélecteurs
    clients_data = cursor.execute("SELECT Id_Client, Nom_complet FROM Client").fetchall()
    chambres_data = cursor.execute("SELECT Id_Chambre FROM Chambre").fetchall()
    conn.close()

    clients = {row['Id_Client']: row['Nom_complet'] for row in clients_data}
    chambres = [row['Id_Chambre'] for row in chambres_data]

    with st.form("ajouter_reservation_form"):
        client_id = st.selectbox("Client", clients.keys(), format_func=lambda id: f"{clients[id]} ({id})")
        chambre_id = st.selectbox("Chambre", chambres)
        date_arrivee = st.date_input("Date d'Arrivée")
        date_depart = st.date_input("Date de Départ")
        submit_button = st.form_submit_button("Ajouter Réservation")

        if submit_button:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO Reservation (Id_Client, Id_Chambre, Date_arrivee, Date_depart)
                VALUES (?, ?, ?, ?)
            ''', (client_id, chambre_id, date_arrivee, date_depart))
            conn.commit()
            conn.close()
            st.success("Réservation ajoutée avec succès!")

def main():
    st.title("Gestion des Réservations d'Hôtel")
    menu = ["Consulter Réservations", "Consulter Clients", "Consulter Chambres Disponibles", "Ajouter Client", "Ajouter Réservation"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Consulter Réservations":
        consulter_reservations()
    elif choice == "Consulter Clients":
        consulter_clients()
    elif choice == "Consulter Chambres Disponibles":
        consulter_chambres_disponibles()
    elif choice == "Ajouter Client":
        ajouter_client()
    elif choice == "Ajouter Réservation":
        ajouter_reservation()

if __name__ == "__main__":
    main()
