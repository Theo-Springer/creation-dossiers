from pathlib import Path
import json
import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox


# ============================================================
# Réglages : lus depuis config.json
# ============================================================

# Le dossier du programme : à côté du .exe une fois compilé, à côté de main.py sinon
if getattr(sys, "frozen", False):
    DOSSIER_APP = Path(sys.executable).parent
else:
    DOSSIER_APP = Path(__file__).parent

INTERDITS = '\\/:*?"<>|'


def erreur_fatale(titre, message):
    """Affiche une erreur puis ferme le programme (utilisée avant que la fenêtre existe)."""
    racine = tk.Tk()
    racine.withdraw()       # cache la fenêtre vide que tkinter crée pour la boîte de dialogue
    messagebox.showerror(titre, message)
    sys.exit()


chemin_config = DOSSIER_APP / "config.json"
try:
    with open(chemin_config, encoding="utf-8") as fichier:
        config = json.load(fichier)
    BASE = DOSSIER_APP / config["chemin_devis"]     # le dossier où se trouvent les dossiers clients
    SOUS_DOSSIERS = config["sous_dossiers"]
except FileNotFoundError:
    erreur_fatale("Configuration introuvable", f"Le fichier {chemin_config} est introuvable.")
except json.JSONDecodeError as erreur:
    erreur_fatale("Configuration invalide", f"config.json est mal écrit (ligne {erreur.lineno}).\n\nVérifie les virgules et les guillemets.")
except KeyError as erreur:
    erreur_fatale("Configuration incomplète", f"Il manque la clé {erreur} dans config.json.")


# ============================================================
# Logique
# ============================================================

def nettoyer(texte):
    """Met en majuscules et ne garde qu'un espace entre les mots."""
    return " ".join(texte.upper().split())


def liste_clients():
    """Renvoie les noms des dossiers clients, triés par ordre alphabétique."""
    clients = []
    for dossier in BASE.iterdir():
        if dossier.is_dir():
            clients.append(dossier.name)
    return sorted(clients, key=str.upper)   # key=str.upper : trie sans tenir compte des majuscules


def nom_interdit(texte):
    """True si le texte ne peut pas servir de nom de dossier Windows."""
    for lettre in texte:
        if lettre in INTERDITS:
            return True
    return texte.endswith(".")


def verifier(client, numero, initiales, objet):
    """Renvoie la liste des erreurs. Liste vide = tout est bon."""
    erreurs = []
    numero_valide = len(numero) == 5 and numero.isdigit()

    if client == "":
        erreurs.append("Le client est vide")
    elif nom_interdit(client):
        erreurs.append(f"Le nom du client contient un caractère interdit ({INTERDITS}) ou finit par un point")

    if not numero_valide:
        erreurs.append("Le numéro d'affaire doit contenir 5 chiffres")

    if not initiales.isalpha():
        erreurs.append("Les initiales doivent contenir uniquement des lettres")

    if objet == "":
        erreurs.append("L'objet est vide")
    elif nom_interdit(objet):
        erreurs.append(f"L'objet contient un caractère interdit ({INTERDITS}) ou finit par un point")

    dossier_client = BASE / client
    if numero_valide and client != "" and dossier_client.is_dir():
        for dossier in dossier_client.iterdir():
            if dossier.is_dir() and dossier.name.startswith(numero):
                erreurs.append(f"Le numéro d'affaire existe déjà : {dossier.name}")
                break

    return erreurs


def creer_affaire(client, numero, initiales, objet):
    """Crée le dossier d'affaire et ses sous-dossiers. Renvoie son chemin."""
    dossier_affaire = BASE / client / f"{numero}{initiales} {objet}"
    dossier_affaire.mkdir(parents=True)     # parents=True : crée aussi le client s'il est nouveau
    for sous_dossier in SOUS_DOSSIERS:
        (dossier_affaire / sous_dossier).mkdir()
    return dossier_affaire


def ouvrir_dossier(chemin):
    """Ouvre le dossier dans l'Explorateur (Windows) ou le Finder (Mac)."""
    if sys.platform == "win32":
        os.startfile(chemin)
    else:
        subprocess.run(["open", str(chemin)])


# ============================================================
# Interface graphique
# ============================================================

def filtrer_clients(event):
    """À chaque touche tapée dans le champ client, ne garde que les clients qui contiennent la saisie."""
    if event.keysym in ("Up", "Down", "Return", "Escape", "Tab"):
        return      # ces touches servent à naviguer, pas à écrire
    saisie = champ_client.get().upper().strip()
    resultats = []
    for client in tous_les_clients:
        if saisie in client.upper():
            resultats.append(client)
    champ_client["values"] = resultats


def activer_saut_clavier(combobox):
    """Liste ouverte : taper des lettres saute au premier client qui commence par ces lettres."""
    # La liste qui s'ouvre sous la Combobox est un widget interne de tkinter : on récupère son nom
    liste = combobox.tk.call("ttk::combobox::PopdownWindow", combobox) + ".f.l"
    memoire = {"texte": "", "temps": 0}

    def sauter(lettre, temps):
        temps = int(temps)
        if lettre == "" or not lettre.isprintable():
            return      # Entrée, flèches, Maj... : on laisse tkinter les gérer
        if temps - memoire["temps"] > 1000:     # plus d'une seconde depuis la dernière touche : on repart de zéro
            memoire["texte"] = ""
        memoire["texte"] += lettre.upper()
        memoire["temps"] = temps
        for i, client in enumerate(combobox["values"]):
            if client.upper().startswith(memoire["texte"]):
                combobox.tk.call(liste, "selection", "clear", 0, "end")
                combobox.tk.call(liste, "selection", "set", i)
                combobox.tk.call(liste, "activate", i)
                combobox.tk.call(liste, "see", i)
                break

    commande = combobox.register(sauter)
    combobox.tk.call("bind", liste, "<KeyPress>", f"+{commande} %A %t")


def on_creer():
    """Lancée au clic sur le bouton Créer."""
    global tous_les_clients
    client = nettoyer(champ_client.get())
    numero = champ_numero.get().strip()
    initiales = nettoyer(champ_initiales.get())
    objet = nettoyer(champ_objet.get())

    erreurs = verifier(client, numero, initiales, objet)
    if erreurs:
        messagebox.showerror("Saisie incorrecte", "\n".join(erreurs))
        return

    if not (BASE / client).is_dir():
        reponse = messagebox.askyesno("Nouveau client", f"Le client {client} n'existe pas.\n\nLe créer ?")
        if not reponse:
            return

    try:
        chemin = creer_affaire(client, numero, initiales, objet)
    except OSError as erreur:
        messagebox.showerror("Création impossible", str(erreur))
        return

    tous_les_clients = liste_clients()      # pour qu'un nouveau client apparaisse dans la liste
    champ_client["values"] = tous_les_clients
    champ_numero.delete(0, tk.END)
    champ_objet.delete(0, tk.END)

    if messagebox.askyesno("Dossier créé", f"{chemin.name} a été créé.\n\nOuvrir le dossier ?"):
        ouvrir_dossier(chemin)


fenetre = tk.Tk()
fenetre.title("Création de dossier d'affaire")

if not BASE.is_dir():
    messagebox.showerror("Dossier introuvable", f"Le dossier {BASE} est introuvable.")
    sys.exit()

tous_les_clients = liste_clients()      # la liste complète, lue une fois au démarrage

ttk.Label(fenetre, text="Client :").grid(row=0, column=0, sticky="w", padx=8, pady=5)
champ_client = ttk.Combobox(fenetre, values=tous_les_clients, width=40)
champ_client.grid(row=0, column=1, padx=8, pady=5)
champ_client.bind("<KeyRelease>", filtrer_clients)
activer_saut_clavier(champ_client)

ttk.Label(fenetre, text="N° d'affaire :").grid(row=1, column=0, sticky="w", padx=8, pady=5)
champ_numero = ttk.Entry(fenetre, width=43)
champ_numero.grid(row=1, column=1, padx=8, pady=5)

ttk.Label(fenetre, text="Initiales :").grid(row=2, column=0, sticky="w", padx=8, pady=5)
champ_initiales = ttk.Entry(fenetre, width=43)
champ_initiales.grid(row=2, column=1, padx=8, pady=5)

ttk.Label(fenetre, text="Objet :").grid(row=3, column=0, sticky="w", padx=8, pady=5)
champ_objet = ttk.Entry(fenetre, width=43)
champ_objet.grid(row=3, column=1, padx=8, pady=5)

bouton = ttk.Button(fenetre, text="Créer", command=on_creer)
bouton.grid(row=4, column=1, sticky="e", padx=8, pady=10)

champ_client.focus()
fenetre.mainloop()