import os
import random
import json
import pandas as pd
import numpy as np
import matplotlib as plt
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from itertools import combinations
import face_recognition
import mlflow

script_dir = os.path.dirname(os.path.abspath(__file__))
dataset_face = os.path.join(script_dir, "img_tests")

# Création de l'experiment dans mlflow
mlflow.set_experiment("brief17_face_verification")

PKL_FILE = "df_face_recognition.pkl" 
TOLERANCE_SEUIL = 0.6


def index_face_dataset(root_dir):
    """
    Indexes a facial recognition dataset stored in a directory structure.
    Args:
        root_dir (str): The root directory containing subdirectories for each person.
    Retunrs:
        dict: A dictionary mapping person names to lists of image file paths.
    """
    face_dict = {}
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if dirpath == root_dir:
            continue  # Skip the root directory itself

        person_name = os.path.basename(dirpath)
        image_paths = [
            os.path.join(dirpath, f)
            for f in filenames
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ]
        if image_paths:
            face_dict[person_name] = image_paths

    return face_dict

def generate_test_pairs(face_dict, num_pairs=600):
    match_pairs = []
    mismatch_pairs = []
    max_pairs_per_person=3

    for person, images in face_dict.items():
        # On ne garde que les personnes avec au moins 2 images
        if len(images) < 2:
            continue

        # Génère toutes les combinaisons possibles de 2 images
        all_pairs = list(combinations(images, 2))

        # Limite à max_pairs_per_person paires aléatoires
        selected_pairs = random.sample(
            all_pairs,
            min(len(all_pairs), max_pairs_per_person)
        )

        # Ajoute les paires sélectionnées à la liste globale
        match_pairs.extend(selected_pairs)

    people = list(face_dict.keys())
    # Filtrer les personnes sans images (bien que l'indexation le fasse déjà)
    people = [p for p in people if len(face_dict[p]) > 0] 
    if len(people) < 2:
        raise ValueError("Pas assez de personnes avec des images pour générer des mismatches.")

    # Assurer que le nombre de mismatch pairs n'excède pas num_pairs // 2
    target_mismatch_count = num_pairs // 2

    # Créer les paires de mismatch jusqu'à atteindre la cible
    while len(mismatch_pairs) < target_mismatch_count:
        p1, p2 = random.sample(people, 2)
        if p1 != p2 and face_dict[p1] and face_dict[p2]: # Ajout de p1 != p2 pour être sûr
            img1 = random.choice(face_dict[p1])
            img2 = random.choice(face_dict[p2])
            mismatch_pairs.append((img1, img2))

    # Limite le nombre de paires match à la même taille que mismatch_pairs (ou num_pairs // 2)
    match_pairs = match_pairs[:target_mismatch_count]
    
    # Créer un liste de tples avec label
    mix_pairs = [
        (img1, img2, True) for img1, img2 in match_pairs
    ] + [
        (img1, img2, False) for img1, img2 in mismatch_pairs
    ]
    # Mélanger les paires
    random.shuffle(mix_pairs)

    df_pairs = pd.DataFrame(mix_pairs, columns=["img1", "img2", "match"])

    return df_pairs

def add_face_embeddings(df):
    embeddings1 = []
    embeddings2 = []

    print("Calcul des embeddings en cours...")
    for idx, row in df.iterrows():
        # Chargement des images
        img1 = face_recognition.load_image_file(row["img1"])
        img2 = face_recognition.load_image_file(row["img2"])

        # Extraction des encodings
        encod1 = face_recognition.face_encodings(img1)
        encod2 = face_recognition.face_encodings(img2)

        # Si aucun visage n'est détecté, on met None
        embeddings1.append(encod1[0] if encod1 else None)
        embeddings2.append(encod2[0] if encod2 else None)

    # Ajouter des colonnes au Dataframe
    df["embedding1"] = embeddings1
    df["embedding2"] = embeddings2
    print("Calcul des embeddings terminé.")

    return df

def calculate_accuracy(df, tolerance_seuil):
    # Créer une copie du DataFrame pour éviter le SettingWithCopyWarning
    df_temp = df.copy() 
    
    print("=============================Calcul de la similarité et de l'accuracy...=============================")
    df_temp["predicted_match"] = df_temp.apply(
        lambda row: face_recognition.compare_faces(
            [row["embedding1"]], row["embedding2"], tolerance=tolerance_seuil
        )[0] if row["embedding1"] is not None and row["embedding2"] is not None else None,
        axis=1
    )

    valid_df_view = df_temp[df_temp["predicted_match"].notnull()]
    valid_df = valid_df_view.copy() 
    valid_df["predicted_match"] = valid_df["predicted_match"].astype(bool)
    
    # S'assurer qu'il y a des données valides pour le calcul
    if valid_df.empty:
         print("Aucune paire valide pour le calcul de l'accuracy (visages non détectés).")
         return 0, pd.DataFrame() # Retourne 0 et un DataFrame vide
         
    accuracy = accuracy_score(valid_df["match"], valid_df["predicted_match"])
    print(f"\nAccuracy: {accuracy:.2%}")
    return accuracy, valid_df


# ============================== PARTIE PRINCIPALE ==============================

# Vérifier si le fichier .pkl existe
if os.path.exists(PKL_FILE):
    print(f"Fichier PICK_FILE trouvé.")
    df_face_recognition = pd.read_pickle(PKL_FILE)
    print("Chargement terminé.")
else:
    print("Fichier .pkl non trouvé. Création et calcul des embeddings en cours...")
    # 1. Indexer les images
    dict_face = index_face_dataset(dataset_face)
    print(f"Nombre de personnes indexées : {len(dict_face)}")
    
    # 2. Générer les paires de test
    df_test = generate_test_pairs(dict_face)
    print(f"Nombre de paires générées : {len(df_test)}")
    
    # 3. Ajouter les embeddings
    df_face_recognition = add_face_embeddings(df_test)
    
    # 4. Sauvegarder le DataFrame
    df_face_recognition.to_pickle(PKL_FILE)
    print(f"DataFrame sauvegardé dans {PKL_FILE}.")

# ============================== PARAMÈTRES ET EXÉCUTION ==============================

with mlflow.start_run(run_name=f"Tolerance_{TOLERANCE_SEUIL}"):

    mlflow.log_param("tolerance", TOLERANCE_SEUIL)
    mlflow.log_param("dataset_size_pairs", len(df_face_recognition))

    # ============================== CALCUL DE L'ACCURACY ==============================

    accuracy, valid_df = calculate_accuracy(df_face_recognition, TOLERANCE_SEUIL)

    # Afficher les résultats si des données valides existent
    if not valid_df.empty:
        print("\n=============================ENREGISTREMENT DES MÉTRIQUES======================================")
        report_dict = classification_report(
            valid_df["match"],
            valid_df["predicted_match"],
            labels=[True, False],
            target_names=['Match', 'Non-Match'],
            output_dict=True
        )
        print(report_dict)
        mlflow.log_metric("precision_match", report_dict['Match']['precision'])
        mlflow.log_metric("recall_match", report_dict['Match']['recall'])
        mlflow.log_metric("f1_match", report_dict['Match']['f1-score'])

        # Enregistrement du F1-score pondéré comme métrique globale
        mlflow.log_metric("f1_weighted_avg", report_dict['weighted avg']['f1-score'])

        # Affichage du rapport (version texte pour la console)
        print("\n=============================RAPPORT DE CLASSIFICATION======================================")
        print(classification_report(
            valid_df["match"],
            valid_df["predicted_match"],
            labels=[True, False],
            target_names=['Match (True)', 'Non-Match (False)']
        ))

        with open("classification_report.json", "w") as f:
            json.dump(report_dict, f, indent=4)
        mlflow.log_artifact("classification_report.json")

        print("\n=============================MATRICE DE CONFUSION======================================")
        # Calcule et affiche la matrice de confusion
        conf_matrix = confusion_matrix(
            valid_df["match"], 
            valid_df["predicted_match"], 
            labels=[True, False] # Pour avoir Match/Non-Match dans cet ordre
        )
        # Renomme les axes pour l'affichage
        conf_matrix_df = pd.DataFrame(
            conf_matrix, 
            index=['True Positives (TP)', 'False Negatives (FN)'], 
            columns=['False Positives (FP)', 'True Negatives (TN']
        )
        conf_matrix_df.to_csv("confusion_matrix.csv")
        mlflow.log_artifact("confusion_matrix.csv")
        print(conf_matrix_df)
        
        # Interprétation de la matrice:
        # True Positives (TP) - Correctement identifiés comme la même personne.
        # False Negatives (FN) - Manqués (Type II Error).
        # False Positives (FP) - Fausses alarmes (Type I Error).
        # True Negatives (TN) - Correctement identifiés comme des personnes différentes.