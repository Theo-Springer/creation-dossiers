print ("Programme lancé")
from pathlib import Path
import tkinter as tk


client = input("Entrez le nom du client : ").upper().strip()
devis = input("Entrez le numéro du devis : ").strip()
initiales = input("Entrez les initiales RS : ").upper().strip()
objet = input("Entrez l'objet du devis : ").upper().split()
objet = " ".join(objet)

base = Path("test-DEVIS")
DOSSIER = base / client
SOUS_DOSSIERS = ["BORDEREAUX DE PRIX", "CDC", "MAIL", "OFFRE COMMERCIALE", "OFFRE FOURNISSEUR", "PHOTOS"]
INTERDITS = '\\/:*?"<>|'

num_affaire = f"{devis}{initiales} {objet}"

def cree_dossier_affaire():
    for sous_dossier in SOUS_DOSSIERS:
        Path(DOSSIER / num_affaire / sous_dossier).mkdir(parents=True, exist_ok=True)
        print("dossier créé : " + sous_dossier)

def verifier(client,devis, initiales, objet):
    erreurs = []
    numero = devis.strip()
    objet = objet.strip()
    numero_valide = len(numero) == 5 and numero.isdigit()
    dossier_client = base / client

    if not numero_valide:
        erreurs.append("Le numéro de devis doit contenir 5 numéros")
    if objet == "":
        erreurs.append("L'objet du devis est vide")
    if initiales == "":
        erreurs.append("Les initiales RS sont vides")
    if objet in INTERDITS:
        erreurs.append(f"L'objet du devis contient des caractères interdits : {INTERDITS}")
    for lettre in objet:
        if lettre in INTERDITS:
            erreurs.append(f"L'objet du devis contient des caractères interdits : {INTERDITS}")
            break
    if numero_valide and dossier_client.is_dir():
        for dossier in dossier_client.iterdir():
            if dossier.is_dir() and dossier.name.startswith(numero):
                erreurs.append(f"Le numéro d'affaire existe déjà : {dossier.name}")
                break
    return erreurs

erreurs = verifier(client, devis, initiales, objet)
if erreurs:
    for erreur in erreurs:
        print(erreur)
else:
    print("Aucune erreur trouvée.")
    cree_dossier_affaire()
    print("dossier créé : " + num_affaire)
