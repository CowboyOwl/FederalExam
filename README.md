# FederalExam

Application locale pour s'entrainer en francais a l'examen federal suisse de pharmacie.

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
