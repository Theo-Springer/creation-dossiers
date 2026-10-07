# Création de dossiers d'affaire

Version 1.3.0

Petite application Windows qui crée les dossiers d'affaire dans le dossier DEVIS, toujours avec le même nom et les mêmes sous-dossiers. Elle peut aussi comparer l'Excel de suivi des devis aux dossiers existants et créer ceux qui manquent.

Exemple de dossier créé :

```
DEVIS/
└── DUPONT INDUSTRIE/
    └── 52017ELS REV 2 SOUPAPES/
        ├── BORDEREAUX DE PRIX/
        ├── CDC/
        ├── MAIL/
        ├── OFFRE COMMERCIALE/
        ├── OFFRE FOURNISSEUR/
        └── PHOTOS/
```

Le nom du dossier d'affaire assemble le numéro (5 chiffres), les initiales RS, un espace, puis l'objet en majuscules.

---

## Utilisation

### Créer une affaire à la main

1. Choisis le client dans la liste.
   - Tape quelques lettres dans le champ : la liste ne garde que les clients qui contiennent ce texte (`chim` trouve `MARTIN CHIMIE`).
   - Ou ouvre la liste et tape les premières lettres du nom : la sélection saute au premier client qui commence par elles.
2. Saisis le numéro d'affaire (5 chiffres), tes initiales et l'objet.
3. Clique sur **Créer**.

Si le client n'a pas encore de dossier, l'application te demande si tu veux le créer. Après la création, elle te propose d'ouvrir le dossier.

L'application vide le numéro et l'objet après chaque création, mais garde le client et les initiales.

### Comparer avec l'Excel

1. Enregistre l'Excel : l'application lit la dernière version enregistrée.
2. Clique sur **Comparer avec l'Excel**.
3. Une fenêtre affiche deux listes :
   - **Dossiers à créer** : lignes complètes et valides, sans dossier existant.
   - **Lignes à corriger** : numéro de ligne Excel et problème rencontré.
4. Vérifie la liste, puis clique sur **Créer les N dossiers**.

L'application ignore les lignes dont le numéro a déjà un dossier, et les lignes où il manque le client, le numéro ou l'objet.

En mode Excel, l'application ne crée jamais de client. Si le nom du client dans l'Excel ne correspond à aucun dossier, corrige l'Excel ou crée l'affaire à la main. La comparaison ne tient pas compte des majuscules : `dupont industrie` trouve `DUPONT INDUSTRIE`.

---

## Contrôles effectués

Avant chaque création, l'application refuse :

| Cas | Message |
|---|---|
| Client vide | Le client est vide |
| Numéro autre que 5 chiffres | Le numéro d'affaire doit contenir 5 chiffres |
| Initiales vides ou avec des chiffres | Les initiales doivent contenir uniquement des lettres |
| Objet vide | L'objet est vide |
| Caractère interdit par Windows (`\ / : * ? " < > \|`) ou nom qui finit par un point | ... contient un caractère interdit |
| Numéro déjà utilisé, chez n'importe quel client | Le numéro d'affaire existe déjà chez ... |
| Même numéro sur deux lignes de l'Excel | Le numéro ... apparaît plusieurs fois dans l'Excel |

L'application met l'objet en majuscules et retire les espaces en trop.

---

## Fichiers

```
CreationAffaire.exe   (ou main.py pendant le développement)
config.json           à placer dans le même dossier que le programme
```

### config.json

```json
{
  "chemin_devis": "S:/DEVIS",
  "sous_dossiers": [
    "BORDEREAUX DE PRIX",
    "CDC",
    "MAIL",
    "OFFRE COMMERCIALE",
    "OFFRE FOURNISSEUR",
    "PHOTOS"
  ],
  "excel": {
    "chemin": "S:/Suivi devis.xlsx",
    "feuille": "",
    "premiere_ligne": 2,
    "colonne_client": "A",
    "colonne_affaire": "B",
    "colonne_objet": "C"
  }
}
```

| Clé | Rôle |
|---|---|
| `chemin_devis` | Dossier qui contient les dossiers clients. Chemin complet (`S:/DEVIS`) ou relatif au programme (`test-DEVIS`). |
| `sous_dossiers` | Sous-dossiers créés dans chaque affaire. Pour imposer un ordre dans l'Explorateur, numérote-les (`01 - CDC`). |
| `excel` | Facultatif. Sans cette section, le bouton Excel affiche un message d'erreur et le reste fonctionne. |
| `excel.chemin` | Chemin du fichier `.xlsx` ou `.xlsm`. Les anciens `.xls` ne passent pas. |
| `excel.feuille` | Nom de la feuille. Laisse `""` pour prendre la feuille ouverte par défaut. |
| `excel.premiere_ligne` | Première ligne de données, sous les en-têtes. Augmente-la pour ignorer les anciennes affaires. |
| `excel.colonne_*` | Lettre de la colonne du client, du numéro d'affaire (format `52017ELS`) et de l'objet. |

Écris les chemins avec des `/`. Avec des `\`, il faut les doubler (`S:\\DEVIS`).

Une modification de `config.json` prend effet au prochain lancement, sans regénérer le `.exe`.

---

## Installation pour le développement

Il faut Python 3.10 ou plus récent, et la bibliothèque `openpyxl` pour la lecture de l'Excel.

```
python3 -m pip install openpyxl
python3 main.py
```

Sur Mac, installe Python depuis python.org : le Python 3.9 fourni par Apple a un tkinter trop ancien.

Pour tester sans toucher au vrai DEVIS, crée un dossier `test-DEVIS` à côté de `main.py` avec quelques dossiers clients, et mets `"chemin_devis": "test-DEVIS"` dans `config.json`.

---

## Générer le .exe

Sur une machine Windows avec Python installé (case « Add python.exe to PATH » cochée) :

```
py -m pip install pyinstaller openpyxl
py -m PyInstaller --onefile --windowed --name CreationAffaire main.py
```

Le fichier se trouve dans `dist/CreationAffaire.exe`. PyInstaller ne fabrique pas de `.exe` depuis un Mac.

Regénère le `.exe` à chaque modification de `main.py`.

### Déploiement

1. Copie `CreationAffaire.exe` et `config.json` dans le même dossier du lecteur partagé.
2. Mets le vrai chemin de DEVIS et de l'Excel dans `config.json`.
3. Crée un raccourci vers le `.exe` sur le bureau de chaque poste.

Au premier lancement, Windows affiche « Windows a protégé votre ordinateur » parce que le `.exe` n'est pas signé. Clique sur « Informations complémentaires », puis « Exécuter quand même ».

---

## Dépannage

| Problème | Solution |
|---|---|
| « Configuration introuvable » | `config.json` doit être dans le même dossier que le `.exe`. |
| « Configuration invalide (ligne N) » | Virgule ou guillemet manquant dans `config.json` à cette ligne. |
| « Dossier introuvable » au lancement | Le lecteur réseau est déconnecté, ou `chemin_devis` est faux. |
| « Excel inaccessible » | Le fichier est verrouillé sur le réseau. Réessaie dans un instant. |
| « Feuille introuvable » | Le nom dans `excel.feuille` ne correspond à aucune feuille. |
| Une ligne Excel n'apparaît pas | La ligne n'est pas enregistrée, ou il manque le client, le numéro ou l'objet. |
| Le `.exe` se ferme sans message | Regénère-le sans `--windowed` : la console affichera l'erreur. |
| L'antivirus bloque le `.exe` | Demande au service informatique d'autoriser le fichier. |

---

## Organisation du code

Le fichier `main.py` se découpe en quatre blocs.

**Réglages** : lecture de `config.json`, avec un message d'erreur clair si le fichier manque ou contient une faute.

**Logique dossiers**

| Fonction | Rôle |
|---|---|
| `nettoyer(texte)` | Met en majuscules et retire les espaces en trop. |
| `liste_clients()` | Liste les dossiers clients, triés sans tenir compte des majuscules. |
| `nom_interdit(texte)` | Détecte un nom que Windows refuse. |
| `affaire_existe(numero)` | Cherche un dossier qui commence par ce numéro, chez tous les clients. |
| `numeros_existants()` | Renvoie tous les numéros déjà utilisés, en un seul passage. |
| `verifier(...)` | Renvoie la liste des erreurs de saisie. |
| `creer_affaire(...)` | Crée le dossier d'affaire et ses sous-dossiers. |
| `ouvrir_dossier(chemin)` | Ouvre le dossier dans l'Explorateur (ou le Finder sur Mac). |

**Logique Excel**

| Fonction | Rôle |
|---|---|
| `lire_excel()` | Lit les lignes complètes de l'Excel. Charge `openpyxl` seulement à ce moment. |
| `comparer_excel()` | Trie les lignes en « à créer » et « à corriger ». |

**Interface**

| Fonction | Rôle |
|---|---|
| `filtrer_clients(event)` | Filtre la liste des clients à chaque touche tapée. |
| `activer_saut_clavier(combobox)` | Saut au clavier dans la liste ouverte, branché à la première ouverture. |
| `on_creer()` | Bouton Créer. |
| `on_comparer()` / `surveiller()` | Bouton Excel. La lecture tourne dans un thread séparé pour que la fenêtre ne se fige pas. |
| `afficher_apercu(...)` | Fenêtre d'aperçu de la comparaison. |
| `tableau(...)` | Crée un tableau avec barre de défilement. |