# FederalExam

Application locale pour s'entrainer en francais a l'examen federal suisse de pharmacie.

## Utilisation La Plus Simple

### Windows

Ouvrir `FederalExam.exe` dans le dossier `FederalExam`.

### macOS sans terminal

Option recommandee: ouvrir `FederalExam.app`. L'application demarre le serveur local et ouvre le navigateur automatiquement.

Si vous utilisez le dossier source au lieu de l'application empaquetee, double-cliquer sur:

```text
Lancer FederalExam.command
```

Au premier lancement, ce fichier prepare un environnement local dans `.venv`, installe Flask si necessaire, puis ouvre FederalExam dans le navigateur. Si Python 3 n'est pas installe, il ouvre la page de telechargement Python. Pour une utilisation sans Python, utilisez `FederalExam.app`.

Sur macOS, une application telechargee depuis Internet peut demander une confirmation de securite au premier lancement. Utiliser alors clic droit > Ouvrir une seule fois; les lancements suivants se font par double-clic.

## Run From Source

```powershell
python -m pip install -r requirements.txt
python app.py
```

Ouvrir ensuite `http://127.0.0.1:5000`.

Par defaut:

- Windows: `%LOCALAPPDATA%\FederalExam\federal_exam.db`
- macOS: `~/Library/Application Support/FederalExam/federal_exam.db`

## Build Windows Executable

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

Le resultat attendu est:

```text
dist\FederalExam\FederalExam.exe
```

Distribuer le dossier complet `dist\FederalExam\`, par exemple sous forme de zip.

## Build macOS App

Le build macOS doit etre lance sur un Mac:

```bash
chmod +x scripts/build_macos.sh
./scripts/build_macos.sh
```

Le resultat attendu est:

```text
dist/FederalExam.app
```

Le fichier `dist/FederalExam.app` est celui a ouvrir sur Mac. Il n'exige pas que l'utilisateur final installe Python.

## Build Automatique Sur GitHub

Le workflow **Build Packages** peut produire les archives Windows et macOS depuis GitHub Actions. Il genere:

```text
FederalExam-Windows.zip
FederalExam-macOS.zip
```

Distribuer ces archives aux utilisateurs finaux. Sur Mac, ils ouvrent simplement `FederalExam.app` apres extraction du zip.

## Questions Et Notes

Les PDF sources restent dans `notes/` et ne sont pas versionnes par Git.

Pour regenerer la banque active de 1000 questions et les cartes memoire depuis les notes:

```powershell
python -m pip install -r requirements-build.txt
python scripts\generate_draft_questions.py
python scripts\generate_flashcards.py
```

Le fichier genere est `data/generated_questions_fr.csv`. Les questions sont importees comme contenu actif; il n'y a plus de statut `a_verifier`, `brouillon` ou `valide`.

Le fichier `data/generated_flashcards_fr.csv` contient les cartes memoire Anki-style issues des faits extraits des notes.

Au premier lancement d'une nouvelle installation, l'application cree automatiquement la base locale et importe la banque de 1000 questions et le deck de cartes memoire si aucune base n'existe encore.

## Importer Des Questions

Depuis l'interface, utiliser la page **Importation** avec un fichier CSV ou JSON.

Depuis la ligne de commande:

```powershell
python scripts\import_questions.py data\sample_questions_fr.csv
python scripts\import_flashcards.py data\generated_flashcards_fr.csv
```

Le modele CSV se trouve dans `data/questions_template.csv`.

## Tests

```powershell
python -m pytest -q
```
