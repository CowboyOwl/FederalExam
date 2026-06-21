from __future__ import annotations

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from federal_exam.categories import CATEGORIES
from federal_exam.importer import REQUIRED_FIELDS


OUTPUT = PROJECT_ROOT / "data" / "generated_questions_fr.csv"

VARIANTS = [
    "Quel énoncé est correct concernant {concept} ?",
    "Dans une situation d'examen, quel point faut-il retenir à propos de {concept} ?",
    "Quelle proposition correspond le mieux à {concept} ?",
    "Quel élément est prioritaire lorsque l'on évalue {concept} ?",
    "Quelle affirmation est la plus juste au sujet de {concept} ?",
    "Pour une révision rapide, quelle réponse décrit correctement {concept} ?",
    "Quel choix serait attendu pour une question centrée sur {concept} ?",
    "Quelle notion est associée de façon pertinente à {concept} ?",
    "Quelle réponse doit être privilégiée concernant {concept} ?",
    "Quel rappel est utile pour maîtriser {concept} ?",
]

DIFFICULTIES = ["facile", "moyen", "difficile", "moyen", "facile"]

REFERENCES = {
    "Pharmacologie et thérapeutique": "Référence clinique à vérifier: pharmacologie générale et recommandations suisses applicables",
    "Pharmacie clinique": "Référence clinique à vérifier: pharmacie clinique, interactions, adaptation et suivi thérapeutique",
    "Galénique et technologie pharmaceutique": "Référence pharmaceutique à vérifier: pharmacopée, formes galéniques et bonnes pratiques de fabrication",
    "Chimie pharmaceutique et analyse": "Référence pharmaceutique à vérifier: chimie analytique, contrôle qualité et pharmacopée",
    "Pharmacognosie et phytothérapie": "Référence pharmaceutique à vérifier: pharmacognosie, monographies et sécurité des plantes médicinales",
    "Toxicologie": "Référence clinique à vérifier: toxicologie, centres antipoison et conduite d'urgence",
    "Microbiologie, infectiologie et vaccination": "Référence clinique à vérifier: microbiologie, infectiologie et recommandations vaccinales suisses",
    "Droit pharmaceutique suisse": "Référence légale à vérifier: Fedlex, LPTh, LPMéd, LStup, LAMal et ordonnances applicables",
    "Santé publique et système de santé suisse": "Référence à vérifier: OFSP, LAMal, prévention et organisation du système de santé suisse",
    "Communication, triage et conseil officinal": "Référence professionnelle à vérifier: triage officinal, communication clinique et bonnes pratiques suisses",
}


TOPICS = {
    "Pharmacologie et thérapeutique": [
        ("Antivitamines K", "le suivi de l'INR guide l'adaptation du traitement", ["le suivi repose surtout sur la kaliémie", "la surveillance n'est jamais nécessaire", "la dose est fixe pour tous les patients"], "Anticoagulants"),
        ("Inhibiteurs de l'enzyme de conversion", "une toux sèche persistante peut être un effet indésirable", ["ils provoquent toujours une hypoglycémie", "ils sont des antibiotiques", "ils s'administrent uniquement par voie inhalée"], "Cardiologie"),
        ("Bêtabloquants", "ils peuvent masquer certains signes adrénergiques d'hypoglycémie", ["ils augmentent toujours la fréquence cardiaque", "ils sont sans effet cardiovasculaire", "ils neutralisent directement l'acidité gastrique"], "Cardiologie"),
        ("AINS", "ils peuvent augmenter le risque digestif et rénal selon le patient", ["ils sont toujours indiqués en insuffisance rénale sévère", "ils remplacent une antibiothérapie documentée", "ils n'ont aucune interaction clinique"], "Douleur"),
        ("Paracétamol", "le risque hépatique augmente en cas de surdosage", ["la toxicité principale est l'ototoxicité immédiate", "il est toujours anti-inflammatoire puissant", "il impose une surveillance de l'INR chez tous les patients"], "Douleur"),
        ("Corticostéroïdes systémiques", "une interruption brutale peut poser problème après un traitement prolongé", ["ils n'ont aucun effet métabolique", "ils sont dépourvus d'effet immunologique", "ils s'utilisent uniquement comme antiseptiques"], "Inflammation"),
        ("Metformine", "la fonction rénale doit être prise en compte", ["elle est une insuline rapide", "elle se dose par l'INR", "elle est indiquée pour traiter une hypoglycémie aiguë"], "Diabète"),
        ("Insuline rapide", "elle est liée au risque d'hypoglycémie si l'apport glucidique est insuffisant", ["elle corrige une infection bactérienne", "elle se conserve toujours à température élevée", "elle supprime le besoin de surveillance glycémique"], "Diabète"),
        ("Statines", "des symptômes musculaires doivent faire évoquer un effet indésirable possible", ["elles sont des bronchodilatateurs", "elles traitent une crise d'asthme aiguë", "elles doivent être doublées après chaque repas gras"], "Lipides"),
        ("IPP", "ils diminuent la sécrétion acide gastrique", ["ils sont des anticoagulants injectables", "ils stimulent directement la toux", "ils remplacent toujours une exploration digestive"], "Gastroentérologie"),
    ],
    "Pharmacie clinique": [
        ("conciliation médicamenteuse", "elle vise à repérer divergences, omissions et doublons", ["elle remplace le diagnostic médical", "elle consiste uniquement à compter les boîtes", "elle interdit toute discussion avec le patient"], "Sécurité médicamenteuse"),
        ("interaction médicamenteuse", "elle peut être pharmacocinétique ou pharmacodynamique", ["elle concerne seulement les médicaments injectables", "elle n'a jamais d'impact clinique", "elle se limite aux allergies alimentaires"], "Interactions"),
        ("adaptation en insuffisance rénale", "certains médicaments nécessitent une adaptation ou une prudence accrue", ["la fonction rénale n'influence jamais la posologie", "tous les médicaments sont éliminés uniquement par voie pulmonaire", "seule la couleur du comprimé compte"], "Adaptation posologique"),
        ("observance thérapeutique", "elle peut être améliorée par une explication claire et un schéma adapté", ["elle se mesure seulement par la taille du comprimé", "elle est indépendante de la compréhension du patient", "elle ne concerne que les antibiotiques"], "Adhésion"),
        ("polymédication", "elle augmente le risque d'interactions et d'effets indésirables", ["elle supprime le besoin de suivi", "elle diminue toujours le risque de chute", "elle signifie automatiquement surdosage volontaire"], "Gériatrie"),
        ("effet indésirable", "il doit être recherché et documenté lorsqu'un symptôme apparaît après un traitement", ["il prouve toujours une erreur de fabrication", "il exclut toute autre cause", "il impose toujours l'arrêt définitif immédiat"], "Pharmacovigilance"),
        ("médicaments à marge thérapeutique étroite", "ils nécessitent souvent une attention particulière au suivi", ["ils sont toujours disponibles sans conseil", "ils ne présentent jamais de risque de surdosage", "ils sont uniquement des produits cosmétiques"], "Suivi thérapeutique"),
        ("grossesse et médicaments", "le rapport bénéfice-risque doit être évalué avec prudence", ["tous les médicaments sont formellement interdits", "aucune exposition médicamenteuse n'a d'importance", "la dose adulte standard suffit toujours"], "Populations particulières"),
        ("allergie médicamenteuse", "la nature de la réaction et le médicament suspect doivent être précisés", ["toute intolérance digestive est toujours une anaphylaxie", "elle ne doit jamais être notée", "elle autorise automatiquement tous les médicaments de la même classe"], "Sécurité"),
        ("analyse d'ordonnance", "elle vérifie notamment dose, indication, interactions et contre-indications", ["elle se limite au prix du traitement", "elle remplace tout suivi clinique", "elle ignore l'âge et les comorbidités"], "Ordonnance"),
    ],
    "Galénique et technologie pharmaceutique": [
        ("comprimé gastro-résistant", "il est conçu pour résister à l'acidité gastrique avant libération", ["il doit toujours être écrasé", "il libère tout le principe actif dans la bouche", "il est uniquement destiné à la voie injectable"], "Formes orales"),
        ("forme à libération prolongée", "elle ne doit généralement pas être écrasée sans vérification", ["elle agit toujours plus vite qu'une solution", "elle est faite pour une injection intraveineuse", "elle rend impossible tout surdosage"], "Formes orales"),
        ("suspension", "elle doit souvent être agitée pour homogénéiser la dose", ["elle est toujours stérile pour injection", "elle ne contient jamais de particules dispersées", "elle est identique à un gaz comprimé"], "Liquides"),
        ("émulsion", "elle associe deux phases liquides non miscibles stabilisées", ["elle est toujours un comprimé sec", "elle ne nécessite jamais d'agent stabilisant", "elle ne peut pas être appliquée sur la peau"], "Systèmes dispersés"),
        ("stérilité", "elle est essentielle pour les préparations parentérales et ophtalmiques concernées", ["elle est inutile pour toute injection", "elle signifie absence de principe actif", "elle se contrôle seulement par l'odeur"], "Qualité"),
        ("excipient", "il peut influencer stabilité, tolérance ou libération", ["il est toujours pharmacologiquement principal", "il doit être absent de toute forme orale", "il n'a jamais d'importance clinique"], "Formulation"),
        ("pommade", "elle est une forme semi-solide pour application cutanée ou muqueuse selon le cas", ["elle est toujours destinée à l'injection", "elle est forcément aqueuse à 100 %", "elle remplace une forme inhalée"], "Dermatologie"),
        ("conditionnement primaire", "il est en contact direct avec le médicament", ["il correspond uniquement au carton d'expédition", "il ne joue aucun rôle de protection", "il est toujours jeté avant fabrication"], "Conditionnement"),
        ("stabilité", "elle dépend notamment de la température, de la lumière et de l'humidité", ["elle est indépendante du stockage", "elle augmente toujours après péremption", "elle ne concerne que les dispositifs électroniques"], "Stabilité"),
        ("préparation magistrale", "elle est préparée pour un patient déterminé selon une prescription", ["elle est toujours fabriquée en millions d'unités", "elle n'exige aucune traçabilité", "elle est exclusivement vétérinaire"], "Préparations"),
    ],
    "Chimie pharmaceutique et analyse": [
        ("pH", "il exprime l'acidité ou la basicité d'une solution", ["il mesure la masse d'un comprimé", "il indique toujours la stérilité", "il remplace une chromatographie"], "Chimie générale"),
        ("chromatographie", "elle permet de séparer des constituants d'un mélange", ["elle sert uniquement à mesurer la pression artérielle", "elle détruit toujours l'échantillon sans analyse", "elle remplace la prescription médicale"], "Analyse"),
        ("spectrophotométrie UV-visible", "elle repose sur l'absorption de lumière par une substance", ["elle mesure directement la douleur", "elle classe les stupéfiants juridiquement", "elle produit une forme galénique"], "Analyse"),
        ("titrage acido-basique", "il permet de déterminer une quantité par réaction contrôlée", ["il sert à programmer une pompe à insuline", "il remplace une culture microbiologique", "il exige toujours un patient à jeun"], "Analyse quantitative"),
        ("impureté", "elle doit être contrôlée car elle peut influencer qualité et sécurité", ["elle est toujours bénéfique", "elle est ignorée en contrôle qualité", "elle correspond au principe actif recherché uniquement"], "Contrôle qualité"),
        ("substance chirale", "elle peut présenter des énantiomères aux propriétés différentes", ["elle est toujours radioactive", "elle ne peut pas être analysée", "elle est forcément gazeuse"], "Chiralité"),
        ("solubilité", "elle influence dissolution, formulation et biodisponibilité potentielle", ["elle est identique pour toutes les molécules", "elle ne dépend jamais du pH", "elle concerne seulement les emballages"], "Propriétés physicochimiques"),
        ("lot pharmaceutique", "il doit permettre une traçabilité en contrôle qualité", ["il est choisi au hasard par le patient", "il interdit tout rappel", "il n'a aucune utilité documentaire"], "Qualité"),
        ("étalon de référence", "il sert à comparer ou quantifier une substance analysée", ["il remplace toujours le médicament", "il correspond au prix public", "il est une forme de publicité"], "Métrologie"),
        ("validation analytique", "elle documente que la méthode est adaptée à son objectif", ["elle dispense de tout contrôle", "elle se limite au choix de la couleur", "elle est une étape de dispensation au comptoir"], "Méthodes"),
    ],
    "Pharmacognosie et phytothérapie": [
        ("millepertuis", "il est connu pour des interactions médicamenteuses par induction enzymatique", ["il est toujours sans interaction", "il est un antibiotique bêta-lactamine", "il annule tout risque de photosensibilité"], "Interactions plantes-médicaments"),
        ("ginkgo", "une prudence est souvent évoquée avec les traitements influençant l'hémostase", ["il garantit l'absence de saignement", "il est une insuline végétale", "il remplace une anticoagulation prescrite"], "Sécurité"),
        ("valériane", "elle est associée à un usage traditionnel dans les troubles du sommeil légers", ["elle traite une septicémie", "elle exige une injection intraveineuse", "elle neutralise tous les toxiques"], "Sédatifs végétaux"),
        ("séné", "il contient des dérivés anthracéniques à effet laxatif stimulant", ["il est un antitussif opioïde", "il est utilisé comme vaccin", "il corrige une hyperkaliémie par apport de potassium"], "Laxatifs végétaux"),
        ("huiles essentielles", "elles nécessitent une prudence particulière selon âge, grossesse et voie d'administration", ["elles sont toujours sûres chez le nourrisson", "elles sont identiques à l'eau purifiée", "elles remplacent toutes les antibiothérapies"], "Aromathérapie"),
        ("qualité botanique", "l'identification correcte de la plante est essentielle", ["le nom vernaculaire suffit toujours", "la confusion botanique est impossible", "elle ne concerne pas les préparations végétales"], "Qualité"),
        ("monographie", "elle peut décrire identité, qualité, usages et précautions", ["elle est un certificat de vaccination", "elle remplace le dossier patient", "elle interdit toute analyse"], "Documentation"),
        ("tanins", "ils peuvent avoir des propriétés astringentes", ["ils sont exclusivement des gaz anesthésiques", "ils sont toujours des hormones stéroïdiennes", "ils n'existent pas dans les plantes"], "Constituants"),
        ("alcaloïdes", "ils peuvent présenter une activité pharmacologique marquée", ["ils sont toujours inertes", "ils ne nécessitent jamais de prudence", "ils sont uniquement des sucres simples"], "Constituants"),
        ("phytothérapie", "elle doit tenir compte des indications, contre-indications et interactions", ["elle est automatiquement sans risque", "elle exclut tout conseil pharmaceutique", "elle ne concerne jamais les patients polymédiqués"], "Conseil"),
    ],
    "Toxicologie": [
        ("surdosage au paracétamol", "il expose à une toxicité hépatique potentiellement grave", ["il provoque uniquement une myopie transitoire", "il est toujours bénin", "il se traite par un antiacide seul"], "Antidotes"),
        ("charbon activé", "son intérêt dépend du toxique, du délai et du contexte clinique", ["il est indiqué pour toute intoxication sans exception", "il neutralise les métaux lourds dans tous les cas", "il remplace l'appel aux urgences"], "Décontamination"),
        ("intoxication aux opioïdes", "une dépression respiratoire est un signe majeur à rechercher", ["elle provoque toujours une hypertension isolée", "elle ne modifie jamais la conscience", "elle se confirme par la couleur du comprimé"], "Urgences"),
        ("toxidrome anticholinergique", "il peut associer sécheresse, confusion, mydriase et tachycardie", ["il se caractérise par myosis serré et bradycardie obligatoire", "il est toujours asymptomatique", "il n'existe que chez l'animal"], "Toxidromes"),
        ("intoxication au monoxyde de carbone", "elle nécessite une prise en charge urgente et de l'oxygène", ["elle se détecte toujours à l'odeur", "elle est traitée par restriction hydrique", "elle ne concerne jamais les lieux fermés"], "Gaz toxiques"),
        ("centre antipoison", "il peut aider à orienter la conduite à tenir", ["il remplace systématiquement les secours vitaux", "il sert uniquement aux questions administratives", "il interdit toute transmission d'information"], "Orientation"),
        ("corrosifs", "il faut éviter les conduites aggravantes et orienter rapidement", ["il faut toujours faire vomir", "il faut neutraliser avec un produit opposé sans avis", "il n'y a jamais d'urgence"], "Caustiques"),
        ("benzodiazépines", "elles peuvent entraîner sédation et dépression du système nerveux central", ["elles provoquent toujours une hyperthermie maligne", "elles sont des vaccins", "elles n'ont aucun effet neurologique"], "Psychotropes"),
        ("syndrome sérotoninergique", "il peut associer agitation, hyperréflexie, troubles autonomes et hyperthermie", ["il correspond toujours à une carence en fer", "il exclut toute urgence", "il est causé uniquement par les antiacides"], "Toxidromes"),
        ("exposition pédiatrique accidentelle", "elle doit être prise au sérieux même pour de petites quantités selon la substance", ["elle est toujours sans conséquence", "elle se gère toujours par attente passive", "elle ne nécessite jamais d'identification du produit"], "Pédiatrie"),
    ],
    "Microbiologie, infectiologie et vaccination": [
        ("antibiorésistance", "elle est favorisée par un usage inadéquat des antibiotiques", ["elle concerne uniquement les virus", "elle disparaît si la dose est oubliée", "elle n'a aucun impact de santé publique"], "Antibiotiques"),
        ("infection virale", "elle ne justifie pas automatiquement une antibiothérapie", ["elle impose toujours une pénicilline", "elle est toujours bactérienne", "elle se confirme par la couleur des symptômes"], "Triage infectieux"),
        ("vaccination", "elle vise à induire une réponse immunitaire protectrice", ["elle est une antibiothérapie curative", "elle remplace toute mesure d'hygiène", "elle agit par dissolution des bactéries"], "Vaccins"),
        ("chaîne du froid vaccinale", "elle protège la qualité des vaccins thermosensibles", ["elle est facultative pour tous les vaccins", "elle sert à accélérer l'injection", "elle est uniquement esthétique"], "Conservation"),
        ("désinfection des mains", "elle réduit la transmission de nombreux agents infectieux", ["elle remplace toujours la stérilisation des instruments", "elle augmente volontairement la charge microbienne", "elle n'a aucun rôle en officine"], "Hygiène"),
        ("spectre antibiotique", "il décrit les bactéries généralement ciblées par l'antibiotique", ["il indique le prix du médicament", "il mesure le pH urinaire", "il classe les comprimés par couleur"], "Antibiotiques"),
        ("mycose cutanée", "elle peut nécessiter un antifongique adapté et des conseils d'hygiène", ["elle est toujours traitée par antibiotique systémique", "elle interdit toute évaluation clinique", "elle est toujours une urgence vitale"], "Dermatologie infectieuse"),
        ("fièvre avec signes de gravité", "elle doit conduire à une orientation médicale urgente", ["elle se gère toujours par automédication prolongée", "elle exclut une infection sévère", "elle ne nécessite jamais de questionnement"], "Triage"),
        ("vaccin vivant atténué", "il peut être contre-indiqué dans certaines immunodépressions", ["il est toujours indiqué chez tous les patients", "il ne contient aucun élément immunogène", "il est identique à un antiseptique"], "Vaccins"),
        ("prélèvement microbiologique", "sa qualité influence l'interprétation du résultat", ["il est indépendant des conditions de recueil", "il donne toujours une réponse instantanée", "il remplace l'évaluation clinique"], "Diagnostic"),
    ],
    "Droit pharmaceutique suisse": [
        ("LPTh", "elle encadre les médicaments et dispositifs médicaux en Suisse", ["elle fixe uniquement les horaires scolaires", "elle remplace le code pénal dans tous les cas", "elle concerne seulement les impôts communaux"], "Produits thérapeutiques"),
        ("LPMéd", "elle concerne notamment les professions médicales universitaires", ["elle est une loi sur les transports publics", "elle définit uniquement la fiscalité cantonale", "elle remplace toutes les ordonnances pharmaceutiques"], "Professions médicales"),
        ("LStup", "elle concerne les stupéfiants et substances psychotropes", ["elle régit uniquement les assurances complémentaires", "elle interdit toute traçabilité", "elle s'applique seulement aux dispositifs dentaires"], "Stupéfiants"),
        ("LAMal", "elle organise notamment l'assurance obligatoire des soins", ["elle autorise les médicaments", "elle classe les alcaloïdes", "elle définit la stérilité des injections"], "Assurance maladie"),
        ("ordonnance médicale", "elle doit être analysée selon les exigences professionnelles et légales applicables", ["elle peut toujours être ignorée", "elle ne contient jamais d'information utile", "elle remplace toute responsabilité professionnelle"], "Dispensation"),
        ("Swissmedic", "l'autorité suisse joue un rôle central dans l'autorisation et la surveillance des produits thérapeutiques", ["c'est une caisse maladie cantonale", "c'est une chaîne de pharmacies", "c'est un laboratoire privé de chaque officine"], "Autorités"),
        ("pharmacovigilance", "elle vise notamment la surveillance des risques liés aux médicaments", ["elle sert à fixer le loyer de l'officine", "elle remplace la formation continue", "elle interdit le signalement d'effets indésirables"], "Surveillance"),
        ("remise de médicaments", "elle dépend notamment de la catégorie de remise et du cadre légal", ["elle est libre pour tous les médicaments", "elle ne dépend jamais du statut du produit", "elle est décidée par l'emballage seul"], "Remise"),
        ("protection des données", "elle impose une prudence dans le traitement des informations de santé", ["elle autorise l'affichage public des dossiers", "elle ne concerne jamais les pharmacies", "elle interdit toute confidentialité"], "Données patients"),
        ("responsabilité professionnelle", "elle implique documentation, compétence et respect du cadre légal", ["elle disparaît en cas d'automédication", "elle concerne uniquement le fabricant", "elle est sans rapport avec le conseil"], "Déontologie"),
    ],
    "Santé publique et système de santé suisse": [
        ("prévention primaire", "elle vise à éviter l'apparition d'une maladie", ["elle traite uniquement les complications tardives", "elle correspond toujours à une chirurgie", "elle exclut toute vaccination"], "Prévention"),
        ("prévention secondaire", "elle vise le dépistage ou l'intervention précoce", ["elle signifie soins palliatifs uniquement", "elle interdit le dépistage", "elle remplace toute prévention primaire"], "Prévention"),
        ("assurance obligatoire des soins", "elle fait partie du système organisé par la LAMal", ["elle est toujours facultative pour tous les résidents", "elle dépend uniquement de l'employeur", "elle est une autorisation Swissmedic"], "LAMal"),
        ("promotion de la santé", "elle cherche à renforcer les ressources et comportements favorables", ["elle se limite à vendre un médicament", "elle interdit l'éducation thérapeutique", "elle n'a aucun lien avec la pharmacie"], "Promotion"),
        ("vaccination de population", "elle combine bénéfice individuel et impact collectif", ["elle augmente toujours la transmission", "elle ne concerne pas la santé publique", "elle remplace tout suivi des effets indésirables"], "Vaccination"),
        ("pharmacie d'officine", "elle peut jouer un rôle d'accès, conseil, triage et prévention", ["elle est uniquement un entrepôt sans conseil", "elle n'a aucun contact avec les patients", "elle remplace tous les services hospitaliers"], "Officine"),
        ("littératie en santé", "elle influence la capacité du patient à comprendre et utiliser l'information", ["elle n'a aucun lien avec l'adhésion", "elle se mesure uniquement par l'âge", "elle interdit les supports écrits"], "Communication santé"),
        ("surveillance épidémiologique", "elle aide à suivre la fréquence et la distribution des maladies", ["elle consiste à mesurer le poids des comprimés", "elle remplace une prescription", "elle ne sert jamais aux décisions publiques"], "Épidémiologie"),
        ("équité d'accès aux soins", "elle vise à réduire les barrières évitables", ["elle impose le même traitement sans contexte", "elle exclut les populations vulnérables", "elle ne concerne pas la santé publique"], "Système de santé"),
        ("usage rationnel des médicaments", "il cherche à optimiser efficacité, sécurité et coûts", ["il signifie utiliser toujours plus de médicaments", "il ignore les préférences du patient", "il exclut toute évaluation du bénéfice-risque"], "Bon usage"),
    ],
    "Communication, triage et conseil officinal": [
        ("question ouverte", "elle permet au patient d'exprimer sa situation avec ses mots", ["elle ferme immédiatement l'entretien", "elle impose une réponse oui/non", "elle remplace toute écoute"], "Communication"),
        ("signes d'alarme", "ils justifient une orientation médicale rapide selon le contexte", ["ils doivent être minimisés systématiquement", "ils autorisent toujours l'automédication", "ils ne concernent jamais la pharmacie"], "Triage"),
        ("douleur thoracique avec dyspnée", "elle doit être considérée comme potentiellement urgente", ["elle se traite toujours par bonbon à sucer", "elle ne nécessite aucune question", "elle exclut un problème cardiovasculaire"], "Urgences"),
        ("conseil d'automédication", "il doit inclure indication, posologie, durée et critères de consultation", ["il se limite au nom commercial", "il interdit de demander l'âge", "il ignore les traitements en cours"], "Conseil"),
        ("reformulation", "elle vérifie la compréhension et montre l'écoute", ["elle consiste à contredire le patient", "elle remplace l'explication", "elle doit être évitée dans tous les cas"], "Communication"),
        ("confidentialité au comptoir", "elle protège les informations sensibles du patient", ["elle impose de parler plus fort", "elle n'existe pas en officine", "elle concerne seulement les ordonnances papier"], "Éthique"),
        ("triage pédiatrique", "il doit tenir compte de l'âge, du poids et des signes de gravité", ["il utilise toujours la dose adulte", "il ne nécessite jamais l'avis des parents", "il interdit toute orientation médicale"], "Pédiatrie"),
        ("demande de contraception d'urgence", "elle nécessite un entretien structuré et respectueux", ["elle doit être discutée publiquement", "elle ne nécessite aucune confidentialité", "elle se décide selon la marque préférée uniquement"], "Santé sexuelle"),
        ("technique teach-back", "elle demande au patient de reformuler ce qu'il a compris", ["elle teste la mémoire pour sanctionner", "elle évite toute explication", "elle remplace la posologie écrite"], "Éducation thérapeutique"),
        ("barrière linguistique", "elle peut nécessiter supports adaptés ou aide à la compréhension", ["elle doit être ignorée", "elle rend impossible tout conseil", "elle dispense de vérifier la compréhension"], "Accessibilité"),
    ],
}


def build_choices(correct: str, distractors: list[str], seed: int) -> tuple[dict[str, str], str]:
    answers = [correct, *distractors[:3]]
    rotation = seed % 4
    answers = answers[rotation:] + answers[:rotation]
    keys = ["A", "B", "C", "D"]
    choices = dict(zip(keys, answers))
    correct_key = next(key for key, value in choices.items() if value == correct)
    return choices, correct_key


def generate_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    counter = 1
    for category in CATEGORIES:
        topics = TOPICS[category]
        for topic_index, (concept, correct, distractors, sub_category) in enumerate(topics):
            for variant_index, template in enumerate(VARIANTS):
                choices, correct_key = build_choices(correct, distractors, counter)
                difficulty = DIFFICULTIES[(topic_index + variant_index) % len(DIFFICULTIES)]
                rows.append(
                    {
                        "id": f"DRAFT-{counter:04d}",
                        "categorie": category,
                        "sous_categorie": sub_category,
                        "difficulte": difficulty,
                        "question": template.format(concept=concept),
                        "choix_a": choices["A"],
                        "choix_b": choices["B"],
                        "choix_c": choices["C"],
                        "choix_d": choices["D"],
                        "bonne_reponse": correct_key,
                        "explication": f"{correct}. Cette question est générée comme brouillon et doit être vérifiée avant un usage sérieux.",
                        "reference": REFERENCES[category],
                        "statut_revision": "a_verifier",
                        "tags": f"généré,{sub_category.lower()},{concept.lower()}",
                    }
                )
                counter += 1
    return rows


def main() -> int:
    rows = generate_rows()
    OUTPUT.parent.mkdir(exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} questions générées dans {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
