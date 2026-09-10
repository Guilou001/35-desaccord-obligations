# Faut-il éviter les obligations sur lesquelles les modèles hésitent ?

Dans les données étudiées, les modèles se trompent davantage sur les obligations dont les prévisions divergent. Pourtant, pénaliser systématiquement leur désaccord dégrade ici le portefeuille construit avec leur prévision moyenne.

Sur {{months}} mois, l'écart de rendement certain équivalent net atteint {{delta_ce}} point de pourcentage par an. Son intervalle à 95 % va de {{ci_low}} à {{ci_high}}.

[Lire l'article](ARTICLE.md) · [Télécharger le PDF](rapport/rapport.pdf) · [Lire le protocole](docs/PROTOCOLE.md) · [Examiner les résultats](results/tables)

![Les obligations sont réparties chaque mois en cinq groupes. Plus les modèles divergent, plus leurs erreurs sont grandes. Ces obligations sont aussi plus volatiles et rapportent davantage avant coûts.](results/figures/desaccord_erreur.png)

## La question en quelques mots

Une obligation est une dette que l’on peut acheter et revendre. Son rendement dépend notamment des intérêts reçus et des variations de son prix.

Six modèles donnent chacun une prévision pour la même obligation. Leur moyenne résume le rendement attendu. Leur désaccord indique à quel point leurs réponses diffèrent.

On pourrait préférer les obligations sur lesquelles les modèles s'accordent. Ce choix doit cependant être comparé à deux règles simples, éviter les erreurs passées ou éviter la volatilité.

L'étude fait cette comparaison sur les prévisions publiques de Dickerson, Nozawa et Robotti. Elle ne réentraîne pas les modèles et ne prétend pas mesurer directement les croyances des investisseurs.

## Ce que les résultats montrent

Dans le groupe de faible désaccord, l'erreur absolue moyenne vaut {{mae_low}} % par mois. Elle atteint {{mae_high}} % dans le groupe de fort désaccord.

Le désaccord apporte encore une petite information après contrôle de la volatilité et des erreurs passées. Cette information ne suffit pas à améliorer notre règle de portefeuille.

{{performance_table}}

L’équivalent certain retranche une pénalité de risque au rendement moyen au-delà du taux sans risque. Il sert à comparer ce qu’un rendement rapporte avec les fluctuations qu’il impose.

Les coûts valent vingt-cinq points de base par montant acheté ou vendu, soit 25 cents pour 100 dollars échangés. La rotation annuelle est la somme des achats et ventes, exprimée en multiples du capital.

Le classement pénalisant le désaccord échange davantage de titres. Il perd déjà une partie du rendement certain équivalent avant frais, puis subit davantage de coûts.

![Les règles pénalisant le désaccord, les erreurs passées ou la volatilité sont comparées à la prévision moyenne seule. Chaque point correspond à une hypothèse de coût fixée au protocole.](results/figures/couts_classement.png)

## L'apport de ce projet

| Notion | Ce qu'elle mesure | Traitement dans le dépôt |
|---|---|---|
| Désaccord | Dispersion des six prévisions actuelles | Écart type entre modèles |
| Erreur passée | Distance historique entre prévision et résultat | Moyenne sur les douze mois précédents |
| Volatilité | Fluctuations historiques du rendement | Écart type sur les douze mois précédents |

Un placebo redistribue le désaccord entre obligations comparables. La variable observée fait mieux que ses {{placebo_count}} redistributions, mais reste derrière la prévision moyenne seule. Elle contient donc une information qui n'améliore pas automatiquement la décision retenue.

## Les vérifications et la limite principale

L'audit porte sur {{n_rows}} lignes et {{n_dates}} mois de signal. Il vérifie les clés uniques, les dates, les rendements communs aux modèles et la moyenne des ensembles.

Le fichier associe déjà chaque prévision à son rendement du mois suivant. Aucun décalage supplémentaire n'est appliqué. Les variables historiques sont calculées en SQL avant la date du signal.

Nous n'avons pas l'univers des obligations avant les filtres des auteurs. Le résultat concerne donc le panneau publié. Il ne prouve pas que toutes ces positions auraient été négociables à ces prix.

Les frais sont hypothétiques. Les délais d'exécution et les fourchettes acheteur-vendeur ne sont pas observés dans ce fichier mensuel.

## Reproduire

```bash
uv sync --all-groups --locked
uv run desaccord fetch
uv run pytest
uv run desaccord run
uv run desaccord verify
uv run --group report desaccord report
```

Python 3.12 et [uv](https://docs.astral.sh/uv/) sont nécessaires. L'archive publique pèse environ 201 Mo. DuckDB traite le panneau sans charger toutes les prévisions empilées en mémoire.

Les empreintes du millésime sont enregistrées. Un fichier remplacé chez le fournisseur entraîne un arrêt explicite. Les données brutes ne sont pas redistribuées.

## Sources et droits

Bali, Kelly, Mörke et Rahman, [Machine Forecast Disagreement, RFS, 2026](https://doi.org/10.1093/rfs/hhag042). Dickerson, Nozawa et Robotti, [Factor Investing with Delays, 2025](https://www.ier.hit-u.ac.jp/Common/publication/DP/DPS-A771.pdf).

[Prévisions officielles et dictionnaire](https://openbondassetpricing.com/machine-learning-data/). [Taux sans risque de French](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html).

Code sous licence MIT. Article, figures et textes sous CC BY 4.0. Les données tierces conservent leurs droits. Guillaume Vaudescal, avec assistance d'IA pour le code et la rédaction. Document de recherche, sans évaluation par les pairs.

## Contrôler les résultats sans refaire l’apprentissage

Le [classeur à formules](reports/controle.xlsx) recalcule les indicateurs du test principal depuis les rendements mensuels. La [requête SQL](sql/indicateurs.sql) retrouve les équivalents certains de toutes les méthodes.

Le [journal de vérification](docs/VERIFICATION.md) précise les contrôles, les corrections et leurs limites. La commande `desaccord verify` vérifie les tables publiées sans télécharger les données brutes.
