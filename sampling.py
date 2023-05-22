import streamlit as st
import pandas as pd
import numpy as np
import base64
import xlrd
from io import BytesIO
from datetime import datetime


# Fonction pour l'échantillonnage aléatoire simple
def random_sampling(data, sample_size):
    sample = data.sample(n=sample_size)
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

def download_excel(sample):
    # Générer le lien de téléchargement pour le fichier Excel
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Echantillon_{current_time}.xlsx"
    excel_data = BytesIO()
    with pd.ExcelWriter(excel_data, engine='xlsxwriter') as writer:
        sample.to_excel(writer, sheet_name='Echantillon', index=False)
    excel_data.seek(0)
    b64 = base64.b64encode(excel_data.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">Télécharger l\'échantillon.</a>'
    st.markdown(href, unsafe_allow_html=True)


def main():
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
        sampling_method = st.sidebar.selectbox("Choisissez la méthode d'échantillonnage",
                                       ["Aléatoire", "Systématique", "Stratifié"])

        # Taille de l'échantillon
        sample_size = st.sidebar.number_input("Taille de l'échantillon", min_value=1, max_value=len(data))

        # Si la méthode d'échantillonnage stratifié est sélectionnée, demander la colonne de stratification
        strata_col = ""
        if sampling_method == "Stratifié":
            strata_col = st.sidebar.selectbox("Choisissez la colonne de stratification", data.columns)

        # Bouton pour effectuer l'échantillonnage
        if st.sidebar.button("Effectuer l'échantillonnage"):
            if sampling_method == "Aléatoire":
                sample = random_sampling(data, sample_size)
            elif sampling_method == "Systématique":
                sample = systematic_sampling(data, sample_size)
            else:
                sample = stratified_sampling(data, sample_size, strata_col)

            # Affichage de l'échantillon
            # st.subheader("Échantillon")
            st.markdown('<h3 class="title">Échantillon</h3>', unsafe_allow_html=True)
            st.write(sample)

            # Code pour télécharger l'échantillon
            download_excel(sample)

if __name__ == "__main__":
    main()