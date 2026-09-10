# Journal de réalisation et de vérification

La première édition a été réalisée le 10 septembre 2026. Ce journal décrit les contrôles effectivement exécutés et leur portée.

## Le protocole précède les résultats

Le premier commit `01a57cc` conserve le protocole et sa configuration avant le calcul des performances. La configuration actuelle lui est identique, octet pour octet. Il s’agit d’un historique Git local, sans enregistrement préalable auprès d’un tiers.

L’empreinte SHA-256 du protocole est `9ae86d0cfad7cf29047f1bca4fbba4d5151a28003ab098b6aa644a498c05325a`.

La comparaison principale, les périodes, les frais, les graines et les blocs de rééchantillonnage n’ont pas été modifiés après lecture du test. Les diagnostics de sélection ont été ajoutés après les performances et sont explicitement descriptifs.

## Les vérifications du calcul

Une histoire artificielle permet de retrouver manuellement la moyenne et la volatilité des douze mois précédents. Modifier les rendements futurs ne change ni les fenêtres antérieures ni le classement. L’audit intégral porte sur 29 787 291 lignes, 19 773 obligations et 245 mois de signal.

La suite contient 8 tests. Le calcul des frais est confronté à une résolution scalaire indépendante. Les partitions de sélection sont testées sur une construction dont le classement est connu.

Le vérificateur recalcule 525 valeurs dans les 75 lignes de performance. Il utilise des sommes compensées et un registre de richesse scalaire, sans appeler le moteur d’indicateurs.

L’écart absolu maximal est 5.33e-15, sur les unités décimales des fichiers. Les 25 équivalents certains SQL retrouvent aussi les résultats Python.

La conservation des frais est vérifiée sur les 5 225 lignes mensuelles de stratégies et de scénarios. Ces lignes ne représentent pas autant d’observations économiques indépendantes.

Le [rapport de contrôle lisible par machine](../results/tables/verification.json) conserve les résultats et les empreintes des entrées vérifiées. Le contrôle s’exécute avec `uv run desaccord verify`.

## Les choix et corrections documentés

L’archive comporte déjà la date du signal et celle du rendement suivant. Le programme conserve cet appariement. Les fenêtres SQL excluent la cible courante et utilisent des mois calendaires.

Les trois ensembles du panneau sont des moyennes. Ils sont exclus des six opinions utilisées pour calculer le désaccord. Le placebo conditionnel est un diagnostic descriptif sous une hypothèse d’échangeabilité, pas une preuve causale.

Le diagnostic de Sharpe dégonflé refuse une série de variance nulle. Son nombre effectif d’essais reste inconnu.

La lecture visuelle a repéré une ambiguïté Typst qui absorbait une parenthèse dans un indice. Les indices concernés sont désormais groupés explicitement. Les équations composées ont été relues après correction.

Les corrections de présentation ont conservé les conclusions mesurées. Elles ont clarifié les écarts signés, les prévisions combinées et la portée du protocole local. Les trois sensibilités de longueur de bloc sont présentées ensemble.

## Les articles et les fichiers de lecture

Le README et l’article sont produits depuis les modèles de texte et les tables. Le PDF reprend l’article. Chaque équation possède une traduction Typst explicite, relue avec son expression mathématique.

Les huit pages du PDF ont été rendues et inspectées. Les figures utilisent un fond blanc et sont disponibles en PNG, SVG et PDF. Les unités, les périodes et les repères sont indiqués.

Le classeur contient les rendements du test principal et des formules de performance. Ses équivalents certains ont été rapprochés des calculs Python. Mettre l’aversion au risque à zéro retrouve le rendement moyen annualisé.

Le recalcul et l’export ont été contrôlés avec `@oai/artifact-tool`. Le classeur n’a pas été ouvert dans l’application Microsoft Excel. Il ne contient aucune macro et les données sources sont également fournies en JSON.

## Ce que ces contrôles ne démontrent pas

Les exemples analytiques vérifient le code sur leurs propriétés propres. Ils ne certifient ni la disponibilité historique de toutes les données, ni l’exécution réelle des positions.

Le bootstrap rééchantillonne des blocs d’une histoire finie. Il ne crée pas de nouveaux épisodes économiques. Les coûts restent les scénarios annoncés, sans estimation de transactions individuelles.

L’article est un document de recherche avec assistance d’IA. Il n’a pas fait l’objet d’une évaluation par les pairs, ni d’une validation indépendante par une autre équipe.
