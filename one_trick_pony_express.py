import streamlit as st
import pandas as pd
import io
from datetime import datetime
import base64

# Configuration de la page
st.set_page_config(
    page_title="One Trick pony express",
    page_icon="🎠",
    layout="wide",
)

# Fonction pour charger et nettoyer les données
def load_data(file):
    try:
        # Déterminer le type de fichier
        if file.name.endswith('.csv'):
            df = pd.read_csv(file, sep=None, engine='python')
        elif file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            st.error("Format de fichier non supporté. Veuillez charger un fichier CSV ou Excel.")
            return None
        
        # Vérifier si les colonnes nécessaires existent
        required_cols = ['pays', 'groupe_instructeur_label', 'date_depart']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            st.error(f"Les colonnes suivantes sont manquantes dans le fichier : {', '.join(missing_cols)}")
            return None
        
        # Nettoyer les données
        df['date_depart'] = pd.to_datetime(df['date_depart'], errors='coerce')
        df['annee'] = df['date_depart'].dt.year
        
        # Vérifier si la colonne libelle_etablissement existe
        if 'libelle_etablissement' not in df.columns:
            df['libelle_etablissement'] = "Non disponible"
            
        # Vérifier si la colonne demandeur_siret existe
        if 'demandeur_siret' not in df.columns:
            df['demandeur_siret'] = "Non disponible"
            
        return df
    
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier: {str(e)}")
        return None

# Fonction pour générer un lien de téléchargement
def get_download_link(df, filename):
    csv_buffer = io.BytesIO()
    excel_buffer = io.BytesIO()
    
    df.to_csv(csv_buffer, index=False)
    df.to_excel(excel_buffer, index=False)
    
    csv_b64 = base64.b64encode(csv_buffer.getvalue()).decode()
    excel_b64 = base64.b64encode(excel_buffer.getvalue()).decode()
    
    csv_href = f'<a href="data:file/csv;base64,{csv_b64}" download="{filename}.csv">Télécharger en CSV</a>'
    excel_href = f'<a href="data:file/excel;base64,{excel_b64}" download="{filename}.xlsx">Télécharger en Excel</a>'
    
    return csv_href, excel_href

# Titre principal
st.title("One Trick Pony express")

# Création des onglets
tabs = st.tabs(["Mobilité Apprenants", "Mobilité Personnel"])

# Dictionnaire pour stocker les dataframes
data = {"apprenants": None, "personnel": None}

# Onglet 1: Mobilité Apprenants
with tabs[0]:
    # Titre de l'onglet avec comptage
    if "apprenants" in data and data["apprenants"] is not None:
        total_count = len(data["apprenants"])
        st.header(f"Mobilité des Apprenants ({total_count})")
    
    # Zone de téléchargement de fichier
    uploaded_file = st.sidebar.file_uploader("Télécharger le fichier de mobilité apprenants", type=["csv", "xlsx", "xls"])
    
    if uploaded_file is not None:
        data["apprenants"] = load_data(uploaded_file)
        
        if data["apprenants"] is not None:
            st.sidebar.subheader("Filtres")
            
            # Filtre pour l'année d'abord
            all_years = sorted(data["apprenants"]["annee"].dropna().unique().astype(int))
            # Filtrer pour commencer à 2023
            available_years = [year for year in all_years if year >= 2023]
            if available_years:
                selected_year = st.sidebar.selectbox(
                    "Sélectionner l'année",
                    options=available_years,
                    index=0
                )
                
                # Filtrer les données par année et mettre à jour le titre avec le comptage
                year_data = data["apprenants"][data["apprenants"]["annee"] == selected_year]
                st.header(f"Mobilité des Apprenants ({len(year_data)})")
                
                # Filtrer les pays disponibles pour l'année sélectionnée
                # Convertir tous les pays en chaînes de caractères avant le tri
                available_countries = sorted([str(pays) for pays in year_data["pays"].unique()])
                selected_countries = st.sidebar.multiselect(
                    "Sélectionner les pays",
                    options=available_countries,
                    default=[]
                )
                
                # Mettre à jour le comptage si des pays sont sélectionnés
                if selected_countries:
                    countries_data = year_data[year_data["pays"].isin(selected_countries)]
                    st.header(f"Mobilité des Apprenants ({len(countries_data)})")
                
                # Seulement afficher le filtre de région si des pays sont sélectionnés
                selected_region = None
                if selected_countries:
                    country_year_data = year_data[year_data["pays"].isin(selected_countries)]
                    available_regions = ["France entière"] + sorted(country_year_data["groupe_instructeur_label"].unique())
                    selected_region = st.sidebar.selectbox(
                        "Sélectionner la région",
                        options=available_regions,
                        index=0
                    )
                    
                    # Mettre à jour le comptage si une région est sélectionnée
                    if selected_region != "France entière":
                        region_data = country_year_data[country_year_data["groupe_instructeur_label"] == selected_region]
                        st.header(f"Mobilité des Apprenants ({len(region_data)})")
                
                # Filtrer les données si tous les filtres nécessaires sont sélectionnés
                if selected_countries and selected_region is not None:
                    filtered_df = data["apprenants"][data["apprenants"]["annee"] == selected_year]
                    filtered_df = filtered_df[filtered_df["pays"].isin(selected_countries)]
                    
                    if selected_region != "France entière":
                        filtered_df = filtered_df[filtered_df["groupe_instructeur_label"] == selected_region]
                    
                    # Afficher le résultat
                    if not filtered_df.empty:
                        st.subheader(f"Mobilité des apprenants - {', '.join(selected_countries)} - {selected_year}")
                        
                        # Sélectionner uniquement les colonnes requises
                        display_columns = ["groupe_instructeur_label", "pays", "libelle_etablissement", "demandeur_siret"]
                        display_df = filtered_df[display_columns].copy()
                        display_df.columns = ["Region", "Pays", "Etablissement", "SIRET"]
                        
                        # Afficher le nombre total de lignes
                        st.info(f"Nombre total d'enregistrements : {len(display_df)}")
                        
                        # Afficher le tableau
                        st.dataframe(display_df)
                        
                        # Générer le lien de téléchargement
                        filename = f"mobilite_apprenants_{'-'.join(selected_countries)}_{selected_year}"
                        csv_link, excel_link = get_download_link(display_df, filename)
                        st.markdown(f"{csv_link} | {excel_link}", unsafe_allow_html=True)
                    else:
                        st.warning("Aucune donnée ne correspond aux filtres sélectionnés.")
                elif selected_countries:
                    st.info("Veuillez sélectionner une région pour afficher les résultats.")
                else:
                    st.info("Veuillez sélectionner au moins un pays pour continuer.")
            else:
                st.warning("Aucune donnée disponible pour les années à partir de 2023.")
    else:
        st.info("Veuillez télécharger un fichier de données pour commencer l'analyse.")

# Onglet 2: Mobilité Personnel
with tabs[1]:
    # Titre de l'onglet avec comptage
    if "personnel" in data and data["personnel"] is not None:
        total_count = len(data["personnel"])
        st.header(f"Mobilité du Personnel ({total_count})")
    
    # Zone de téléchargement de fichier
    uploaded_file = st.sidebar.file_uploader("Télécharger le fichier de mobilité personnel", type=["csv", "xlsx", "xls"])
    
    if uploaded_file is not None:
        data["personnel"] = load_data(uploaded_file)
        
        if data["personnel"] is not None:
            st.sidebar.subheader("Filtres")
            
            # Filtre pour l'année d'abord
            all_years = sorted(data["personnel"]["annee"].dropna().unique().astype(int))
            # Filtrer pour commencer à 2023
            available_years = [year for year in all_years if year >= 2023]
            if available_years:
                selected_year = st.sidebar.selectbox(
                    "Sélectionner l'année",
                    options=available_years,
                    index=0,
                    key="personnel_year"
                )
                
                # Filtrer les données par année et mettre à jour le titre avec le comptage
                year_data = data["personnel"][data["personnel"]["annee"] == selected_year]
                st.header(f"Mobilité du Personnel ({len(year_data)})")
                
                # Filtrer les pays disponibles pour l'année sélectionnée
                # Convertir tous les pays en chaînes de caractères avant le tri
                available_countries = sorted([str(pays) for pays in year_data["pays"].unique()])
                selected_countries = st.sidebar.multiselect(
                    "Sélectionner les pays",
                    options=available_countries,
                    default=[],
                    key="personnel_countries"
                )
                
                # Mettre à jour le comptage si des pays sont sélectionnés
                if selected_countries:
                    countries_data = year_data[year_data["pays"].isin(selected_countries)]
                    st.header(f"Mobilité du Personnel ({len(countries_data)})")
                
                # Seulement afficher le filtre de région si des pays sont sélectionnés
                selected_region = None
                if selected_countries:
                    country_year_data = year_data[year_data["pays"].isin(selected_countries)]
                    available_regions = ["France entière"] + sorted(country_year_data["groupe_instructeur_label"].unique())
                    selected_region = st.sidebar.selectbox(
                        "Sélectionner la région",
                        options=available_regions,
                        index=0,
                        key="personnel_region"
                    )
                    
                    # Mettre à jour le comptage si une région est sélectionnée
                    if selected_region != "France entière":
                        region_data = country_year_data[country_year_data["groupe_instructeur_label"] == selected_region]
                        st.header(f"Mobilité du Personnel ({len(region_data)})")
                
                # Filtrer les données si tous les filtres nécessaires sont sélectionnés
                if selected_countries and selected_region is not None:
                    filtered_df = data["personnel"][data["personnel"]["annee"] == selected_year]
                    filtered_df = filtered_df[filtered_df["pays"].isin(selected_countries)]
                    
                    if selected_region != "France entière":
                        filtered_df = filtered_df[filtered_df["groupe_instructeur_label"] == selected_region]
                    
                    # Afficher le résultat
                    if not filtered_df.empty:
                        st.subheader(f"Mobilité du personnel - {', '.join(selected_countries)} - {selected_year}")
                        
                        # Sélectionner uniquement les colonnes requises
                        display_columns = ["groupe_instructeur_label", "pays", "libelle_etablissement", "demandeur_siret"]
                        display_df = filtered_df[display_columns].copy()
                        display_df.columns = ["Region", "Pays", "Etablissement", "SIRET"]
                        
                        # Afficher le nombre total de lignes
                        st.info(f"Nombre total d'enregistrements : {len(display_df)}")
                        
                        # Afficher le tableau
                        st.dataframe(display_df)
                        
                        # Générer le lien de téléchargement
                        filename = f"mobilite_personnel_{'-'.join(selected_countries)}_{selected_year}"
                        csv_link, excel_link = get_download_link(display_df, filename)
                        st.markdown(f"{csv_link} | {excel_link}", unsafe_allow_html=True)
                    else:
                        st.warning("Aucune donnée ne correspond aux filtres sélectionnés.")
                elif selected_countries:
                    st.info("Veuillez sélectionner une région pour afficher les résultats.")
                else:
                    st.info("Veuillez sélectionner au moins un pays pour continuer.")
            else:
                st.warning("Aucune donnée disponible pour les années à partir de 2023.")
    else:
        st.info("Veuillez télécharger un fichier de données pour commencer l'analyse.")

# Ajouter un pied de page
st.markdown("---")
st.markdown("© 2025 - Application d'analyse de mobilité")
