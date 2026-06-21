# FederalExam

Application locale pour s'entrainer en francais a l'examen federal suisse de pharmacie.

## Run From Source

```powershell
python -m pip install -r requirements.txt
python app.py
```

Ouvrir ensuite `http://127.0.0.1:5000` si le navigateur ne s'ouvre pas automatiquement.

Par defaut, la base SQLite utilisee par l'application est stockee dans:

```text
%LOCALAPPDATA%\FederalExam\federal_exam.db
```

Les imports temporaires sont stockes dans:

```text
%LOCALAPPDATA%\FederalExam\uploads
```

## Build Windows Executable

Pour creer une version utilisable sans installer Python sur la machine de l'utilisateur:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

Le resultat attendu est:

```text
dist\FederalExam\FederalExam.exe
```

Distribuer le dossier complet `dist\FederalExam\`, par exemple sous forme de fichier zip. Ne distribuez pas seulement le fichier `.exe`, car le mode PyInstaller one-folder garde des ressources a cote de l'executable.

L'utilisateur final lance ensuite:

```text
FederalExam.exe
```

L'application demarre un serveur local, ouvre le navigateur par defaut et conserve les donnees dans `%LOCALAPPDATA%\FederalExam`.

## Importer Des Questions

Depuis l'interface, utiliser la page **Importation** avec un fichier CSV ou JSON.

Depuis la ligne de commande:

```powershell
python scripts\import_questions.py data\sample_questions_fr.csv
```

Le modele CSV se trouve dans `data/questions_template.csv`. Les questions non validees doivent garder le statut `brouillon` ou `a_verifier`.

## Banque Generee

Une banque de 1000 questions brouillon peut etre regeneree avec:

```powershell
python scripts\generate_draft_questions.py
python scripts\import_questions.py data\generated_questions_fr.csv
```

Le fichier genere est `data/generated_questions_fr.csv`. Toutes ces questions sont marquees `a_verifier`: elles servent de base de travail et doivent etre relues avant un usage serieux.

Au premier lancement d'une nouvelle installation, l'application cree automatiquement la base locale et importe cette banque de 1000 questions si aucune base n'existe encore.

## Tests

```powershell
python -m pytest -q
```
