import streamlit as st
import pandas as pd
import numpy as np
import base64
import xlrd
import io
import os
import json
from datetime import datetime
from passlib.hash import pbkdf2_sha256

# Charger les informations d'identification à partir du fichier JSON
with open('credentials.json') as f:
    credentials = json.load(f)

# Récupérer les informations d'identification pour un accès spécifique
access_1_username = credentials['access_1']['username']
access_1_password = credentials['access_1']['password'] 
access_2_username = credentials['access_2']['username']
access_2_password = credentials['access_2']['password'] 
    

AUTHORIZED_USERS = {
    access_1_username: pbkdf2_sha256.hash(access_1_password),
    access_2_username: pbkdf2_sha256.hash(access_2_password)
    # Add more authorized users as needed
}

def authenticate(username, password):
    # Check if the username exists and the password matches
    if username in AUTHORIZED_USERS and pbkdf2_sha256.verify(password, AUTHORIZED_USERS[username]):
        return True
    return False

def random_sampling(data, sample_size):
    population_size = len(data)
    size = min(sample_size, population_size)
    sample = data.sample(n=size)
    return sample

# Fonction pour l'échantillonnage systématique
def systematic_sampling(data, sample_size):
    indices = np.arange(0, len(data), len(data)/sample_size)
    sample = data.iloc[indices]
    return sample

# Fonction pour l'échantillonnage stratifié
def stratified_sampling(data, sample_size, strata_col):
    strata = data.groupby(strata_col)
    sample = strata.apply(lambda x: x.sample(n=int(sample_size/len(strata)), replace=True))
    return sample

# Fonction pour l'échantillonnage par grappe à un dégré (cluster sampling one degree)
def cluster_sampling_1(data, cluster_col, sample_size):
    clusters = data[cluster_col].unique()
    selected_clusters = np.random.choice(clusters, size=sample_size, replace=False)
    sample = data[data[cluster_col].isin(selected_clusters)]
    return sample

# Fonction pour l'échantillonnage par grappe à un dégré avec échantillonnage aléatoire (cluster sampling one degree with random sampling)
def cluster_sampling_2(data, cluster_col, cluster_size, sample_size):
    clusters = data[cluster_col].unique()
    selected_clusters = np.random.choice(clusters, size=cluster_size, replace=False)
    sample_cluster = data[data[cluster_col].isin(selected_clusters)]
    
    # Calculer les tailles de chaque grappe échantillonnée
    cluster_sizes = sample_cluster.groupby(cluster_col).size()
    
    # Calculer le nombre d'échantillons à prélever proportionnellement à la taille de chaque grappe
    sample_sizes = (cluster_sizes / cluster_sizes.sum() * sample_size).astype(int)
    
    # Réinitialiser les index pour l'échantillonage aléatoire
    sample_cluster = sample_cluster.reset_index(drop=True)
    
    # Effectuer l'échantillonnage aléatoire proportionnellement à la taille de chaque grappe
    samples = []
    for _, group in sample_cluster.groupby(cluster_col):
        cluster_sample = random_sampling(group, sample_sizes[_])
        samples.append(cluster_sample)
    
    # Concaténer les échantillons de chaque grappe
    sample = pd.concat(samples)
    
    return sample

def download_excel(sample, file_name):
    # Générer le lien de téléchargement pour le fichier Excel
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Echantillon_{file_name}_{current_time}.xlsx"
    excel_data = io.BytesIO()
    with pd.ExcelWriter(excel_data, engine='xlsxwriter') as writer:
        sample.to_excel(writer, sheet_name='Echantillon', index=False)
    excel_data.seek(0)
    b64 = base64.b64encode(excel_data.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">Télécharger l\'échantillon.</a>'
    st.markdown(href, unsafe_allow_html=True)
    
# Fonction pour afficher la note en bas de l'application
def show_footer_note():
    st.markdown("---")
    st.write("Pour toute question ou demande d'accès, veuillez me contacter au **0544950675** ou via email **davidarnoldkouassi@gmail.com**")
    
def main():
    # Vérifier l'état de connexion
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        # Interface de connexion
        st.markdown('<h3 class="title">Connexion</h3>', unsafe_allow_html=True)

        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")

        if st.button("Se connecter"):
            if authenticate(username, password):
                st.session_state.logged_in = True
                # update_last_action_time()  # Mettre à jour le temps d'action
                # Forcer le rafraîchissement de l'application
                st.experimental_rerun()
            else:
                st.error("Nom d'utilisateur ou mot de passe incorrect")
        # Appel de la fonction pour afficher la note en bas de l'application
        show_footer_note()
    if st.session_state.logged_in:
        show_sampling_interface()
        # Vérifier le temps écoulé depuis la dernière action
        # elapsed_time = time.time() - last_action_time
        # if elapsed_time >= 15:  # 15 minutes en secondes
            # st.session_state.logged_in = False
            # st.experimental_rerun()
        # update_last_action_time()  # Mettre à jour le temps d'action
        # Bouton de déxconnexion
        if st.button("Se déconnecter"):
            st.session_state.logged_in = False
            st.experimental_rerun()

def show_sampling_interface():
    st.markdown('<h3 class="title">Application d\'échantillonnage</h3>', unsafe_allow_html=True)
    
    # Chargement des données
    uploaded_file = st.file_uploader("Importer le fichier de données (CSV, Excel)", type=["csv", "xls", "xlsx"])
    
    if uploaded_file is not None:
        try:
            data = pd.read_csv(uploaded_file)
        except Exception as e:
            try:
                data = pd.read_excel(uploaded_file)
            except Exception as e:
                data = pd.read_excel(uploaded_file, engine='xlrd')


        # Méthode d'échantillonnage choisie
        # sampling_method = st.sidebar.selectbox("Choisissez la méthode d'échantillonnage",
        # ["Aléatoire", "Systématique", "Stratifié", "Grappe"])
        sampling_method = st.sidebar.selectbox("Choisissez la méthode d'échantillonnage", 
                                               ["Aléatoire", "Systématique", "Stratifié", "Grappe à un degré", "Grappe à deux degrés"])


        # Taille de l'échantillon
        if sampling_method == "Aléatoire" or sampling_method == "Systématique":
            sample_size = st.sidebar.number_input("Taille de l'échantillon", min_value=1, max_value=len(data))

        # Si la méthode d'échantillonnage stratifié ou par grappe est sélectionnée, demander la colonne correspondante
        strata_col = ""
        cluster_col = ""
        # cluster_col_2 = ""
        
        if sampling_method == "Stratifié":
            strata_col = st.sidebar.selectbox("Choisissez la strate", data.columns)
            sample_size = st.sidebar.number_input("Taille de l'échantillon", min_value=1, max_value=len(data))
        elif sampling_method == "Grappe à un degré":
            cluster_col = st.sidebar.selectbox("Choisissez la grappe", data.columns)
            # Vérifier que la taille de l'échantillon est valide pour l'échantillonnage par grappe
            sample_size = st.sidebar.number_input("Taille de la grappe", min_value=1, max_value=len(data))
            cluster_count = len(data[cluster_col].unique())
            if sample_size < 1 or sample_size > cluster_count:
                st.error(f"La taille de l'échantillon doit être comprise entre 1 et {cluster_count} (le nombre de total de grappe).")
                return
        elif sampling_method == "Grappe à deux degrés":
            cluster_col = st.sidebar.selectbox("Choisissez la grappe", data.columns)
            cluster_size = st.sidebar.number_input("Taille de la grappe", min_value=1, max_value=len(data))
            sample_size = st.sidebar.number_input("Taille de l'échantillon", min_value=1, max_value=len(data))
            # Vérifier que la taille de l'échantillon est valide pour l'échantillonnage par grappe
            cluster_count = len(data[cluster_col].unique())
            if cluster_size < 1 or cluster_size > cluster_count:
                st.error(f"La taille de l'échantillon doit être comprise entre 1 et {cluster_count} (le nombre de total de grappe).")
                return

        # Bouton pour effectuer l'échantillonnage
        if st.sidebar.button("Effectuer l'échantillonnage"):
            if sampling_method == "Aléatoire":
                sample = random_sampling(data, sample_size)
            elif sampling_method == "Systématique":
                sample = systematic_sampling(data, sample_size)
            elif sampling_method == "Stratifié":
                sample = stratified_sampling(data, sample_size, strata_col)
            elif sampling_method == "Grappe à un degré":
                sample = cluster_sampling_1(data, cluster_col, sample_size)
            else:
                sample = cluster_sampling_2(data, cluster_col, cluster_size, sample_size)
                
            # Récupérer le nom de la base chargée
            base_name = os.path.splitext(uploaded_file.name)[0]

            # Affichage de l'échantillon
            st.markdown('<h3 class="title">Échantillon</h3>', unsafe_allow_html=True)
            st.write(sample)

            # Code pour télécharger l'échantillon en utilisant le nom de la base chargée
            download_excel(sample, base_name)

if __name__ == "__main__":
    main()
