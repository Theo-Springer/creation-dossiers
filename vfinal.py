from pathlib import Path
import json
import os
import subprocess
import sys
import tkinter as tk
import urllib.request
from tkinter import ttk, messagebox

# Fait vérifier les certificats HTTPS par Windows plutôt que par Python :
# indispensable sur un réseau d'entreprise qui inspecte le trafic HTTPS
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

# ============================================================
# Réglages : lus depuis config.json
# ============================================================

# Le dossier du programme : à côté du .exe une fois compilé, à côté de main.py sinon
if getattr(sys, "frozen", False):
    DOSSIER_APP = Path(sys.executable).parent
else:
    DOSSIER_APP = Path(__file__).parent

INTERDITS = '\\/:*?"<>|'
VERSION = "v1.1.1"
URL_RELEASE = "https://api.github.com/repos/Theo-Springer/creation-dossiers/releases/latest"


# ============================================================
# Mise à jour automatique
# ============================================================

def version_en_nombres(version):
    """'v1.10.0' -> (1, 10, 0) : permet de comparer 1.10 et 1.9 correctement."""
    return tuple(int(morceau) for morceau in version.lstrip("vV").split("."))


def nettoyer_ancienne_version():
    """Supprime le .old laissé par la mise à jour précédente."""
    if not getattr(sys, "frozen", False):
        return
    ancien = Path(sys.executable).with_suffix(".old")
    try:
        ancien.unlink(missing_ok=True)
    except OSError:
        pass        # encore verrouillé : on réessaiera au prochain lancement


def installer_mise_a_jour(url_exe):
    """Télécharge le nouveau .exe, prend la place de l'ancien et relance le programme."""
    exe = Path(sys.executable)
    nouveau = exe.with_name(exe.stem + "_nouveau.exe")
    ancien = exe.with_suffix(".old")

    try:
        urllib.request.urlretrieve(url_exe, nouveau)
        ancien.unlink(missing_ok=True)
        exe.rename(ancien)          # Windows accepte de renommer un .exe en cours d'exécution
        nouveau.rename(exe)
    except OSError as erreur:
        # Échec : on remet tout en place et le programme continue normalement
        if not exe.exists() and ancien.exists():
            ancien.rename(exe)
        nouveau.unlink(missing_ok=True)
        messagebox.showerror("Mise à jour impossible", f"La mise à jour a échoué :\n\n{erreur}")
        return

    # Relance la nouvelle version (les deux réglages évitent qu'elle réutilise
    # les fichiers temporaires de l'ancienne version, propres à PyInstaller)
    env = os.environ.copy()
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    env.pop("_MEIPASS2", None)
    subprocess.Popen([str(exe)], env=env)
    fenetre.destroy()
    sys.exit()


def auto_update():
    """Vérifie sur GitHub si une version plus récente existe et propose de l'installer."""
    try:
        with urllib.request.urlopen(URL_RELEASE, timeout=5) as reponse:
            data = json.loads(reponse.read().decode("utf-8"))
        version_dispo = data["tag_name"]
        if version_en_nombres(version_dispo) <= version_en_nombres(VERSION):
            return
        url_exe = None
        for fichier in data["assets"]:
            if fichier["name"].lower().endswith(".exe"):
                url_exe = fichier["browser_download_url"]
                break
    except Exception as erreur:
        # Pas de réseau, GitHub indisponible, réponse inattendue :
        # la vérification ne doit jamais empêcher le programme de fonctionner
        print(f"Vérification de mise à jour impossible : {erreur}")
        return

    if url_exe is None:
        return      # release publiée sans .exe attaché : rien à installer

    if not getattr(sys, "frozen", False):
        # Lancé avec Python : on ne remplace rien (sys.executable serait python.exe)
        messagebox.showinfo("Mise à jour disponible", f"Version {version_dispo} disponible (mode script : pas d'installation).")
        return

    if messagebox.askyesno("Mise à jour disponible",
                           f"La version {version_dispo} est disponible (tu as la {VERSION}).\n\nL'installer maintenant ?"):
        installer_mise_a_jour(url_exe)


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

    if numero_valide:
        for dossier in BASE.glob(f"*/{numero}*"):
            if dossier.is_dir():
                erreurs.append(f"Le numéro d'affaire existe déjà chez {dossier.parent.name} : {dossier.name}")
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


nettoyer_ancienne_version()

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
fenetre.after(500, auto_update)     # vérifie les mises à jour une fois la fenêtre affichée
fenetre.mainloop()