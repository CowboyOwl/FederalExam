# FederalExam

Application locale en Python pour s'entraîner en français à l'examen fédéral suisse de pharmacie.

## Installation

```powershell
python -m pip install -r requirements.txt
```

## Lancer l'application

```powershell
python app.py
```

Ouvrir ensuite `http://127.0.0.1:5000`.

## Importer des questions

Depuis l'interface, utiliser la page **Importation** avec un fichier CSV ou JSON.

Depuis la ligne de commande:

```powershell
python scripts\import_questions.py data\sample_questions_fr.csv
```

Le modèle CSV se trouve dans `data/questions_template.csv`. Les questions non validées doivent garder le statut `brouillon` ou `a_verifier`.

## Banque générée

Une banque de 1000 questions brouillon peut être régénérée avec:

```powershell
python scripts\generate_draft_questions.py
python scripts\import_questions.py data\generated_questions_fr.csv
```

Le fichier généré est `data/generated_questions_fr.csv`. Toutes ces questions sont marquées `a_verifier`: elles servent de base de travail et doivent être relues avant un usage sérieux.

## Tests

```powershell
python -m pytest -q
```
