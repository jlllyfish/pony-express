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
def load_data(file, type_mobilite="sortante"):
    try:
        # Déterminer le type de fichier
        if file.name.endswith('.csv'):
            df = pd.read_csv(file, sep=None, engine='python')
        elif file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            st.error("Format de fichier non supporté. Veuillez charger un fichier CSV ou Excel.")
            return None
        
        # Vérifier les colonnes nécessaires en fonction du type de mobilité
        if type_mobilite == "entrante":
            required_cols = ['pays', 'groupe_instructeur_label', 'date_debut_mobilite_entrante']
        else:
            required_cols = ['pays', 'groupe_instructeur_label', 'date_depart']
            
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            st.error(f"Les colonnes suivantes sont manquantes dans le fichier : {', '.join(missing_cols)}")
            return None
        
        # Nettoyer les données
        if type_mobilite == "entrante":
            df['date_debut_mobilite_entrante'] = pd.to_datetime(df['date_debut_mobilite_entrante'], errors='coerce')
            df['annee'] = df['date_debut_mobilite_entrante'].dt.year
        else:
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
tabs = st.tabs(["Mobilité Apprenants", "Mobilité Personnel", "Mobilité Collective", "Mobilité Entrante"])

# Dictionnaire pour stocker les dataframes
data = {"apprenants": None, "personnel": None, "collective": None, "entrante": None}

# Onglet 1: Mobilité Apprenants
with tabs[0]:
    # Titre de l'onglet
    st.header("Mobilité des Apprenants")
    
    # Zone de téléchargement de fichier (dans la page principale)
    col1, col2 = st.columns([1, 3])
    with col1:
        uploaded_file = st.file_uploader("Télécharger le fichier de mobilité apprenants", type=["csv", "xlsx", "xls"], key="apprenants_file")
    
    if uploaded_file is not None:
        data["apprenants"] = load_data(uploaded_file, type_mobilite="sortante")
        
        if data["apprenants"] is not None:
            st.write(f"Total des enregistrements: {len(data['apprenants'])}")
            
            # Filtres dans la page principale
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Filtre pour l'année d'abord
                all_years = sorted(data["apprenants"]["annee"].dropna().unique().astype(int))
                # Filtrer pour commencer à 2023
                available_years = [year for year in all_years if year >= 2023]
                if available_years:
                    selected_year = st.selectbox(
                        "Sélectionner l'année",
                        options=available_years,
                        index=0
                    )
                    
                    # Filtrer les données par année
                    year_data = data["apprenants"][data["apprenants"]["annee"] == selected_year]
                    
            with col2:
                if available_years:
                    # Filtrer les pays disponibles pour l'année sélectionnée
                    available_countries = sorted([str(pays) for pays in year_data["pays"].unique()])
                    selected_countries = st.multiselect(
                        "Sélectionner les pays",
                        options=available_countries,
                        default=[]
                    )
            
            with col3:
                # Seulement afficher le filtre de région si des pays sont sélectionnés
                selected_region = None
                if 'selected_countries' in locals() and selected_countries:
                    country_year_data = year_data[year_data["pays"].isin(selected_countries)]
                    available_regions = ["France entière"] + sorted(country_year_data["groupe_instructeur_label"].unique())
                    selected_region = st.selectbox(
                        "Sélectionner la région",
                        options=available_regions,
                        index=0
                    )
            
            # Filtrer les données si tous les filtres nécessaires sont sélectionnés
            if 'selected_countries' in locals() and 'selected_region' in locals() and selected_countries and selected_region is not None:
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
            elif 'selected_countries' in locals() and selected_countries:
                st.info("Veuillez sélectionner une région pour afficher les résultats.")
            else:
                st.info("Veuillez sélectionner au moins un pays pour continuer.")
            
            if available_years is not None and len(available_years) == 0:
                st.warning("Aucune donnée disponible pour les années à partir de 2023.")
    else:
        st.info("Veuillez télécharger un fichier de données pour commencer l'analyse.")

# Onglet 2: Mobilité Personnel
with tabs[1]:
    # Titre de l'onglet
    st.header("Mobilité du Personnel")
    
    # Zone de téléchargement de fichier (dans la page principale)
    col1, col2 = st.columns([1, 3])
    with col1:
        uploaded_file = st.file_uploader("Télécharger le fichier de mobilité personnel", type=["csv", "xlsx", "xls"], key="personnel_file")
    
    if uploaded_file is not None:
        data["personnel"] = load_data(uploaded_file, type_mobilite="sortante")
        
        if data["personnel"] is not None:
            st.write(f"Total des enregistrements: {len(data['personnel'])}")
            
            # Filtres dans la page principale
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Filtre pour l'année d'abord
                all_years = sorted(data["personnel"]["annee"].dropna().unique().astype(int))
                # Filtrer pour commencer à 2023
                available_years = [year for year in all_years if year >= 2023]
                if available_years:
                    selected_year = st.selectbox(
                        "Sélectionner l'année",
                        options=available_years,
                        index=0,
                        key="personnel_year"
                    )
                    
                    # Filtrer les données par année
                    year_data = data["personnel"][data["personnel"]["annee"] == selected_year]
            
            with col2:
                if available_years:
                    # Filtrer les pays disponibles pour l'année sélectionnée
                    available_countries = sorted([str(pays) for pays in year_data["pays"].unique()])
                    selected_countries = st.multiselect(
                        "Sélectionner les pays",
                        options=available_countries,
                        default=[],
                        key="personnel_countries"
                    )
            
            with col3:
                # Seulement afficher le filtre de région si des pays sont sélectionnés
                selected_region = None
                if 'selected_countries' in locals() and selected_countries:
                    country_year_data = year_data[year_data["pays"].isin(selected_countries)]
                    available_regions = ["France entière"] + sorted(country_year_data["groupe_instructeur_label"].unique())
                    selected_region = st.selectbox(
                        "Sélectionner la région",
                        options=available_regions,
                        index=0,
                        key="personnel_region"
                    )
            
            # Filtrer les données si tous les filtres nécessaires sont sélectionnés
            if 'selected_countries' in locals() and 'selected_region' in locals() and selected_countries and selected_region is not None:
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
            elif 'selected_countries' in locals() and selected_countries:
                st.info("Veuillez sélectionner une région pour afficher les résultats.")
            else:
                st.info("Veuillez sélectionner au moins un pays pour continuer.")
            
            if available_years is not None and len(available_years) == 0:
                st.warning("Aucune donnée disponible pour les années à partir de 2023.")
    else:
        st.info("Veuillez télécharger un fichier de données pour commencer l'analyse.")

# Onglet 3: Mobilité Collective
with tabs[2]:
    # Titre de l'onglet
    st.header("Mobilité Collective")
    
    # Zone de téléchargement de fichier (dans la page principale)
    col1, col2 = st.columns([1, 3])
    with col1:
        uploaded_file = st.file_uploader("Télécharger le fichier de mobilité collective", type=["csv", "xlsx", "xls"], key="collective_file")
    
    if uploaded_file is not None:
        data["collective"] = load_data(uploaded_file, type_mobilite="sortante")
        
        if data["collective"] is not None:
            st.write(f"Total des enregistrements: {len(data['collective'])}")
            
            # Filtres dans la page principale
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Filtre pour l'année d'abord
                all_years = sorted(data["collective"]["annee"].dropna().unique().astype(int))
                # Filtrer pour commencer à 2023
                available_years = [year for year in all_years if year >= 2023]
                if available_years:
                    selected_year = st.selectbox(
                        "Sélectionner l'année",
                        options=available_years,
                        index=0,
                        key="collective_year"
                    )
                    
                    # Filtrer les données par année
                    year_data = data["collective"][data["collective"]["annee"] == selected_year]
            
            with col2:
                if available_years:
                    # Filtrer les pays disponibles pour l'année sélectionnée
                    available_countries = sorted([str(pays) for pays in year_data["pays"].unique()])
                    selected_countries = st.multiselect(
                        "Sélectionner les pays",
                        options=available_countries,
                        default=[],
                        key="collective_countries"
                    )
            
            with col3:
                # Seulement afficher le filtre de région si des pays sont sélectionnés
                selected_region = None
                if 'selected_countries' in locals() and selected_countries:
                    country_year_data = year_data[year_data["pays"].isin(selected_countries)]
                    available_regions = ["France entière"] + sorted(country_year_data["groupe_instructeur_label"].unique())
                    selected_region = st.selectbox(
                        "Sélectionner la région",
                        options=available_regions,
                        index=0,
                        key="collective_region"
                    )
            
            # Filtrer les données si tous les filtres nécessaires sont sélectionnés
            if 'selected_countries' in locals() and 'selected_region' in locals() and selected_countries and selected_region is not None:
                filtered_df = data["collective"][data["collective"]["annee"] == selected_year]
                filtered_df = filtered_df[filtered_df["pays"].isin(selected_countries)]
                
                if selected_region != "France entière":
                    filtered_df = filtered_df[filtered_df["groupe_instructeur_label"] == selected_region]
                
                # Afficher le résultat
                if not filtered_df.empty:
                    st.subheader(f"Mobilité collective - {', '.join(selected_countries)} - {selected_year}")
                    
                    # Sélectionner uniquement les colonnes requises
                    display_columns = ["groupe_instructeur_label", "pays", "libelle_etablissement", "demandeur_siret"]
                    display_df = filtered_df[display_columns].copy()
                    display_df.columns = ["Region", "Pays", "Etablissement", "SIRET"]
                    
                    # Afficher le nombre total de lignes
                    st.info(f"Nombre total d'enregistrements : {len(display_df)}")
                    
                    # Afficher le tableau
                    st.dataframe(display_df)
                    
                    # Générer le lien de téléchargement
                    filename = f"mobilite_collective_{'-'.join(selected_countries)}_{selected_year}"
                    csv_link, excel_link = get_download_link(display_df, filename)
                    st.markdown(f"{csv_link} | {excel_link}", unsafe_allow_html=True)
                else:
                    st.warning("Aucune donnée ne correspond aux filtres sélectionnés.")
            elif 'selected_countries' in locals() and selected_countries:
                st.info("Veuillez sélectionner une région pour afficher les résultats.")
            else:
                st.info("Veuillez sélectionner au moins un pays pour continuer.")
            
            if available_years is not None and len(available_years) == 0:
                st.warning("Aucune donnée disponible pour les années à partir de 2023.")
    else:
        st.info("Veuillez télécharger un fichier de données pour commencer l'analyse.")

# Onglet 4: Mobilité Entrante
with tabs[3]:
    # Titre de l'onglet
    st.header("Mobilité Entrante")
    
    # Zone de téléchargement de fichier (dans la page principale)
    col1, col2 = st.columns([1, 3])
    with col1:
        uploaded_file = st.file_uploader("Télécharger le fichier de mobilité entrante", type=["csv", "xlsx", "xls"], key="entrante_file")
    
    if uploaded_file is not None:
        data["entrante"] = load_data(uploaded_file, type_mobilite="entrante")
        
        if data["entrante"] is not None:
            st.write(f"Total des enregistrements: {len(data['entrante'])}")
            
            # Filtres dans la page principale
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Filtre pour l'année d'abord
                all_years = sorted(data["entrante"]["annee"].dropna().unique().astype(int))
                # Filtrer pour commencer à 2023
                available_years = [year for year in all_years if year >= 2023]
                if available_years:
                    selected_year = st.selectbox(
                        "Sélectionner l'année",
                        options=available_years,
                        index=0,
                        key="entrante_year"
                    )
                    
                    # Filtrer les données par année
                    year_data = data["entrante"][data["entrante"]["annee"] == selected_year]
            
            with col2:
                if available_years:
                    # Filtrer les pays disponibles pour l'année sélectionnée
                    available_countries = sorted([str(pays) for pays in year_data["pays"].unique()])
                    selected_countries = st.multiselect(
                        "Sélectionner les pays",
                        options=available_countries,
                        default=[],
                        key="entrante_countries"
                    )
            
            with col3:
                # Seulement afficher le filtre de région si des pays sont sélectionnés
                selected_region = None
                if 'selected_countries' in locals() and selected_countries:
                    country_year_data = year_data[year_data["pays"].isin(selected_countries)]
                    available_regions = ["France entière"] + sorted(country_year_data["groupe_instructeur_label"].unique())
                    selected_region = st.selectbox(
                        "Sélectionner la région",
                        options=available_regions,
                        index=0,
                        key="entrante_region"
                    )
            
            # Filtrer les données si tous les filtres nécessaires sont sélectionnés
            if 'selected_countries' in locals() and 'selected_region' in locals() and selected_countries and selected_region is not None:
                filtered_df = data["entrante"][data["entrante"]["annee"] == selected_year]
                filtered_df = filtered_df[filtered_df["pays"].isin(selected_countries)]
                
                if selected_region != "France entière":
                    filtered_df = filtered_df[filtered_df["groupe_instructeur_label"] == selected_region]
                
                # Afficher le résultat
                if not filtered_df.empty:
                    st.subheader(f"Mobilité entrante - {', '.join(selected_countries)} - {selected_year}")
                    
                    # Sélectionner uniquement les colonnes requises
                    display_columns = ["groupe_instructeur_label", "pays", "libelle_etablissement", "demandeur_siret"]
                    display_df = filtered_df[display_columns].copy()
                    display_df.columns = ["Region", "Pays", "Etablissement", "SIRET"]
                    
                    # Afficher le nombre total de lignes
                    st.info(f"Nombre total d'enregistrements : {len(display_df)}")
                    
                    # Afficher le tableau
                    st.dataframe(display_df)
                    
                    # Générer le lien de téléchargement
                    filename = f"mobilite_entrante_{'-'.join(selected_countries)}_{selected_year}"
                    csv_link, excel_link = get_download_link(display_df, filename)
                    st.markdown(f"{csv_link} | {excel_link}", unsafe_allow_html=True)
                else:
                    st.warning("Aucune donnée ne correspond aux filtres sélectionnés.")
            elif 'selected_countries' in locals() and selected_countries:
                st.info("Veuillez sélectionner une région pour afficher les résultats.")
            else:
                st.info("Veuillez sélectionner au moins un pays pour continuer.")
            
            if available_years is not None and len(available_years) == 0:
                st.warning("Aucune donnée disponible pour les années à partir de 2023.")
    else:
        st.info("Veuillez télécharger un fichier de données pour commencer l'analyse.")

# Ajouter un pied de page
st.markdown("---")
st.markdown("© 2025 - Application d'analyse de mobilité")
