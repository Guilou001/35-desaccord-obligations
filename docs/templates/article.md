# Désaccord des modèles et choix d'obligations

Guillaume Vaudescal

Document de recherche, version 1.1 du 10 septembre 2026. Le protocole de l’étude initiale est conservé dans son premier commit local. L’extension et ses limites sont décrites séparément.

## Résumé

Cette étude demande si le désaccord entre prévisions améliore une sélection d'obligations. Elle utilise six modèles publiés par Dickerson, Nozawa et Robotti, sans les réentraîner.

Le désaccord est associé aux erreurs futures, même après contrôle des erreurs passées et de la volatilité. La pente conditionnelle vaut {{slope}}, sur des variables exprimées en rangs.

Ce résultat descriptif ne se traduit pas en avantage économique pour la règle étudiée. La règle pénalisant le désaccord présente un écart de rendement certain équivalent net de {{delta_ce}} point de pourcentage annuel.

L'intervalle apparié à 95 % est [{{ci_low}}, {{ci_high}}]. La règle pénalisée tourne davantage et perd déjà une partie de l'équivalent certain avant frais.

Un placebo suggère que le désaccord propre au titre contient une information. Le résultat demeure conditionnel au panneau publié, dont nous ne pouvons pas reconstruire les exclusions initiales.

## Abstract

This study uses six published bond return forecasts to distinguish model disagreement, historical forecast errors and return volatility. The models are not retrained.

Disagreement predicts future absolute forecast errors after historical controls. However, the prespecified disagreement-penalized portfolio underperforms the mean-forecast ranking in net certainty equivalent.

Conditional permutations preserve coarse forecast and volatility groups. Observed disagreement performs better than these permutations, while remaining below the mean-forecast benchmark. Findings are conditional on the released panel and hypothetical execution assumptions.

## 1. Une information sur l'erreur n'est pas nécessairement un signal de vente

Deux modèles peuvent prévoir des rendements proches et se tromper ensemble. Ils peuvent aussi prévoir des rendements différents, dont la moyenne reste utile. Leur dispersion et leur exactitude sont donc deux propriétés distinctes.

Les travaux de Bali, Kelly, Mörke et Rahman replacent le désaccord des prévisions parmi les variables étudiées en valorisation des actifs [1]. Notre expérience transpose cette question au marché obligataire.

La transposition reste limitée. Nous mesurons une dispersion entre familles d'algorithmes publiées par une autre équipe. Nous ne reproduisons pas la construction exacte de Bali et ses coauteurs.

Les obligations ajoutent une difficulté économique. Une sélection qui change souvent peut sembler intéressante avant frais et devenir coûteuse à réaliser. Dickerson, Nozawa et Robotti étudient notamment les délais de négociation [2].

Nous séparons donc deux questions. Le désaccord renseigne-t-il sur l'erreur à venir ? Et une règle qui le pénalise produit-elle un meilleur portefeuille, après les coûts retenus ?

Le protocole fixe les deux objets avant les résultats. Une association statistique favorable ne sera pas utilisée pour redéfinir ensuite le classement de portefeuille.

La contribution est cette séparation, accompagnée de contrôles comparables. Elle ne suppose ni nouveauté mondiale de l'idée, ni accès à des prix exécutables.

## 2. Les prévisions publiques rendent l'expérience possible

La source est l'archive d'Open Source Bond Asset Pricing publiée en avril 2026 [3]. Elle contient {{n_rows}} lignes et {{n_dates}} mois de signal, de juillet 2002 à novembre 2022.

Chaque ligne correspond à une obligation, une date de signal, une cible et un modèle. La date du rendement réalisé est celle de la fin du mois suivant.

La documentation associe déjà la prévision à sa cible future. Décaler encore le rendement créerait une erreur d'horizon. Le chargeur conserve donc cet appariement.

Les six modèles sont lasso, ridge, elastic net, réseau neuronal, arbres extrêmement aléatoires et forêt aléatoire. Trois ensembles supplémentaires sont fournis. Ils sont des moyennes et ne comptent pas comme trois opinions indépendantes.

Trois cibles sont disponibles. La cible principale, retxrf, est le rendement total de l'obligation au-delà du taux sans risque mensuel. Elle sert à la simulation des portefeuilles.

La cible retx est un rendement de crédit. La cible retd normalise ce rendement par une mesure combinant duration et écart de crédit. Ces deux cibles servent uniquement aux sensibilités descriptives.

La duration mesure la sensibilité du prix obligataire aux taux. L'écart de crédit mesure un supplément de rendement relativement à des titres du Trésor comparables. Leurs transformations ne constituent pas automatiquement le rendement d'un placement détenu.

## 3. L'audit vérifie le fichier, sans certifier l'univers initial

Le contrôle lit toutes les lignes. Les clés sont uniques, les dates du rendement suivent les dates de signal d'un mois et les valeurs sont finies.

Pour une même obligation et une même cible, tous les modèles doivent avoir le même rendement réalisé. Le programme vérifie cette identité. Il confronte aussi l'ensemble fourni à la moyenne arithmétique des six prévisions.

Le fichier ne contient aucune valeur manquante sur ces prévisions et rendements appariés. Cette propriété ne signifie pas que l'univers initial était complet. Elle peut résulter de filtres appliqués avant publication.

Nous ne disposons pas des observations exclues, des obligations dépourvues de rendement apparié ou du journal complet de préparation des caractéristiques. La portée de l'étude reste conditionnelle à ce panneau.

La chronologie des entraînements appartient également aux auteurs. Nos contrôles peuvent vérifier les dates du fichier et nos propres transformations. Ils ne peuvent pas reconstituer chaque décision de leur apprentissage.

Cette distinction empêche de présenter le résultat comme une preuve de performance négociable. Elle n'empêche pas d'étudier les relations entre prévisions, erreurs et classements dans les observations publiées.

L'archive reste hors de Git. Le dépôt conserve son adresse, sa taille et son empreinte SHA-256. Les droits de redistribution du panneau ne sont pas supposés à partir de son seul accès public.

## 4. Trois informations sont mesurées séparément

La prévision centrale est la moyenne des six modèles. Le désaccord est leur écart type, avec cinq degrés de liberté.

$$
\bar\mu_{i,t}=\frac{1}{6}\sum_{m=1}^{6}\hat\mu_{i,t}^{(m)},\qquad d_{i,t}=\sqrt{\frac{1}{5}\sum_{m=1}^{6}(\hat\mu_{i,t}^{(m)}-\bar\mu_{i,t})^2}
$$

Cette dispersion n'est pas un intervalle de confiance calibré. Les modèles partagent des données et ne sont pas indépendants. Un accord entre eux peut coexister avec un biais commun.

L'erreur passée est la moyenne des erreurs absolues de la prévision centrale pendant les douze mois précédents. La volatilité passée est l'écart type des rendements de ces mêmes mois.

Les fenêtres sont calendaires. Une obligation absente pendant plusieurs mois ne reçoit pas artificiellement les douze dernières lignes comme si elles représentaient une année continue.

Au moins six observations historiques sont nécessaires. Les méthodes partagent ensuite le même univers admissible. Sur la période testée, il comprend entre {{eligible_min}} et {{eligible_max}} obligations par mois.

Le calcul SQL s'arrête à la ligne dont le signal date du mois précédent. Le rendement associé à cette ligne est déjà connu à la date courante. La cible de la ligne actuelle reste exclue.

Le contrôle indépendant reconstruit une fenêtre à la main. Modifier les rendements futurs doit laisser les fenêtres précédentes inchangées. Ces propriétés sont vérifiées dans les tests.

## 5. Les règles gardent le même nombre de titres

La référence classe les obligations selon leur prévision moyenne. Elle retient les 20 % les mieux classées, avec des poids égaux.

La règle principale pénalise le désaccord à partir de rangs dans le mois. Le coefficient de pénalité vaut un demi et n'est pas optimisé.

$$
s_{i,t}=\operatorname{rang}_t(\bar\mu_{i,t})-\frac{1}{2}\operatorname{rang}_t(d_{i,t})
$$

Les rangs sont compris entre zéro et un. Les égalités reçoivent un rang moyen. La sélection finale conserve un ordre déterministe lorsque plusieurs scores sont égaux.

Deux contrôles remplacent le rang du désaccord par le rang de l'erreur passée ou de la volatilité passée. Tous utilisent la même pénalité et retiennent le même nombre d'obligations.

Un portefeuille supplémentaire conserve toutes les obligations admissibles. Il mesure ce que coûte la sélection relativement à cet univers de référence, sans prétendre représenter un indice obligataire officiel.

Le test principal porte sur les signaux de juillet 2005 à novembre 2022. Les rendements encaissés vont d'août 2005 à décembre 2022, soit {{months}} mois.

Cette fenêtre laisse une histoire avant le test pour construire les erreurs, la volatilité et le budget de risque. Elle n'est pas déplacée selon les performances obtenues.

## 6. Le risque et les frais sont comptés avant la comparaison

Chaque portefeuille sélectionné est combiné avec des liquidités. Sa part risquée dépend de sa volatilité historique sur vingt-quatre mois, avec au moins douze observations.

Le budget annuel vaut 6 %. La part risquée est plafonnée à un. Ce budget commun ne garantit pas que tous les portefeuilles auront la même volatilité réalisée.

La volatilité utilisée appartient au portefeuille théorique avant frais. Elle est calculée avant d'ajouter son rendement courant à l'histoire. La position ne connaît donc pas la variation qu'elle va encaisser.

Les rendements excédentaires sont reconvertis en rendements totaux avec le taux mensuel de French [4]. Ce taux sert également au placement en liquidités. Il constitue notre convention de financement.

Les coûts portent sur les achats et ventes d'obligations. Les poids dérivent avec les rendements totaux. Les frais sont financés avant l'encaissement du rendement suivant.

$$
k_t=1-c\sum_i|k_t w_{i,t}-b_{i,t}|
$$

Le poids avant échange est noté b, la cible après frais w et la richesse restante k. Seules les obligations sont facturées. La liquidité ferme le bilan.

Une obligation sortante est supposée vendue au dernier prix implicite connu. Sa vente est facturée. Nous ne supposons pas qu'un rendement manquant vaut zéro, mais la possibilité de cette liquidation reste hypothétique.

Les coûts sont fixés à zéro, dix, vingt-cinq, cinquante et cent points de base. Le scénario principal est vingt-cinq points de base par montant acheté ou vendu. Il n'est pas estimé depuis des transactions observées.

Les frais et les délais sont deux objets différents. Un coût proportionnel ne décrit pas l'impossibilité de trouver une contrepartie. Les données mensuelles fournies ne suffisent pas à reconstruire une exécution retardée de quelques jours.

## 7. Le désaccord prédit une partie de l'erreur

Les obligations sont réparties en cinq groupes de désaccord chaque mois. On calcule d'abord les moyennes de chaque groupe, puis leur moyenne temporelle. Les mois ne sont pas pondérés par leur nombre d'obligations.

L'erreur absolue moyenne passe de {{mae_low}} % à {{mae_high}} % par mois entre les groupes extrêmes. L'augmentation relative est de {{mae_increase}} %. La volatilité passée augmente également.

![Chaque barre est une moyenne temporelle des moyennes mensuelles du groupe. Les erreurs et rendements sont ceux du mois suivant, tandis que la volatilité est historique.](results/figures/desaccord_erreur.png)

La comparaison brute ne sépare donc pas le désaccord de la volatilité. Une régression est estimée chaque mois pour examiner leur information conditionnelle.

La variable expliquée est le rang de l'erreur absolue future. Les variables explicatives sont les rangs du désaccord, de la volatilité passée, de l'erreur passée et de la prévision en valeur absolue.

$$
\operatorname{rang}_t(|r_{i,t+1}-\bar\mu_{i,t}|)=a_t+b_t\operatorname{rang}_t(d_{i,t})+\theta_t^{\top}C_{i,t}+u_{i,t+1}
$$

Le vecteur C rassemble les trois contrôles. La moyenne temporelle de b vaut {{slope}}. Son intervalle par blocs de douze mois est [{{slope_low}}, {{slope_high}}].

Une pente positive indique une association supplémentaire entre désaccord et erreur. Elle ne mesure pas une causalité, et son échelle reste celle des rangs. Une hausse de rang de 0,1 est associée à une variation estimée dix fois plus petite que la pente affichée.

![Chaque point est la moyenne d'un coefficient mensuel. Les intervalles rééchantillonnent des blocs de douze mois. Les variables partagent l'échelle des rangs, entre zéro et un.](results/figures/information_conditionnelle.png)

Les deux autres cibles sont présentées ci-dessous. Leur pente concerne une association d'erreur, sans création d'un portefeuille de richesse à partir de rendements transformés.

{{target_table}}

## 8. Pénaliser cette information ne produit pas un meilleur portefeuille

À coût principal, la référence rapporte {{mean_return}} % par an. La règle pénalisant le désaccord rapporte {{disagreement_return}} %. Les deux chiffres décrivent la croissance composée des placements simulés.

Le rendement certain équivalent retranche une pénalité de risque au rendement excédentaire moyen. Il vaut {{mean_ce}} % par an pour la référence, contre {{disagreement_ce}} % pour la règle pénalisée.

$$
CE_\gamma=12\bar r-6\gamma s_r^2,\qquad \gamma=5
$$

La différence principale vaut {{delta_ce}} point de pourcentage annuel. L'intervalle à 95 % est [{{ci_low}}, {{ci_high}}], avec une valeur p centrée de {{p_value}}.

{{performance_table}}

La rotation annuelle atteint {{disagreement_turnover}} fois le capital pour la règle de désaccord. Elle vaut {{mean_turnover}} pour la référence. Les achats et ventes sont tous deux comptés.

La détérioration ne vient pas seulement des frais. Avant coûts, l'écart d'équivalent certain vaut déjà {{gross_delta}} point de pourcentage annuel. Les frais amplifient ensuite cet écart.

![Les écarts sont calculés relativement au classement par prévision moyenne, au même coût. Les lignes relient uniquement les scénarios fixés avant le test.](results/figures/couts_classement.png)

Éviter une erreur importante peut retirer une obligation dont le rendement attendu rémunère justement davantage de risque. Le portefeuille peut aussi changer plus souvent de composition. Cette expérience ne permet pas d'attribuer une part causale exacte à ces deux mécanismes.

## 9. Le placebo distingue une information réelle d'une règle utile

Le placebo conserve la prévision centrale et la volatilité passée. Il croise leurs quintiles pour former des groupes de titres comparables dans chaque mois.

Le désaccord est ensuite redistribué au hasard à l'intérieur de ces groupes. La règle de classement, le nombre de titres et le traitement des frais restent identiques.

Les {{placebo_count}} permutations sont déterminées par des graines fixées. Leur équivalent certain médian vaut {{placebo_median}} % par an. {{placebo_below}} sont inférieures à la règle utilisant le désaccord effectivement observé.

La règle réelle reste pourtant inférieure à la référence sans pénalité. Le désaccord contient donc une information propre au titre qui ne justifie pas, à elle seule, le coefficient de pénalité étudié.

![La distribution représente les redistributions conditionnelles. Le trait bleu utilise le vrai désaccord. Le trait orange utilise seulement la prévision moyenne.](results/figures/placebo.png)

L'échangeabilité des obligations à l'intérieur des groupes demeure une hypothèse. Le placebo est donc un diagnostic descriptif. Il n'identifie ni croyances humaines ni mécanisme causal de prix.

## 10. La conclusion résiste aux blocs, pas à toutes les limites de données

Les intervalles de la comparaison principale restent négatifs pour les trois longueurs de blocs prévues. Leur largeur varie avec l'hypothèse de dépendance temporelle.

{{bootstrap_table}}

Ces intervalles déplacent les mêmes mois pour les deux stratégies. Un rééchantillonnage indépendant des obligations aurait ignoré une partie des chocs communs de marché.

Un diagnostic supplémentaire de sélection emploie huit blocs disjoints. La proportion de classements sous la médiane hors de la moitié choisie vaut {{pbo}} %. Les fichiers conservent aussi une sensibilité du Sharpe dégonflé [5, 6].

Ces diagnostics sont postérieurs au calcul des chemins et restent descriptifs. Ils ne remplacent ni le test principal fixé, ni une vérification des données initiales non fournies.

L'objection la plus forte porte sur l'univers publié. Si la présence dans le fichier dépend d'un rendement futur observable, les portefeuilles héritent de cette sélection. Nos tests ne peuvent pas éliminer une sélection dont les observations exclues manquent.

Une autre pénalité pourrait produire un classement différent. Elle ne serait pas une confirmation de ce protocole si elle était choisie après lecture du test. Elle demanderait une nouvelle comparaison et de nouvelles données.

## Conclusion

Le désaccord entre modèles renseigne sur une partie de leurs erreurs futures. Dans la règle fixée ici, le pénaliser réduit néanmoins la performance économique nette.

La distinction entre information et décision est le résultat utile. Le placebo suggère une information propre au titre, tandis que la référence montre son insuffisance pour améliorer cette sélection.

Une extension crédible demanderait les observations avant filtrage et des données de transaction permettant de mesurer la réalisation des positions. Le fichier mensuel actuel ne fournit pas ces deux éléments.

## Reproductibilité et statut des affirmations

L'archive et les calculs propres au dépôt sont mesurés. Les frais, les liquidations et le placement en liquidités suivent des conventions modélisées. Les travaux de la littérature sont rapportés avec leurs références.

Le SQL, les tests, toutes les variantes prévues et les résultats mensuels des portefeuilles sont disponibles. Les données individuelles brutes restent locales. Le PDF est produit depuis cet article.

L'assistance d'IA a servi au code et à la rédaction. Les contrôles indépendants sont documentés. Le document n'a pas été évalué par les pairs.

## Extension de septembre 2026 — Les intervalles restent-ils valables après sélection ?

L'étude principale montre qu'une information sur les erreurs ne garantit pas une meilleure sélection. L'extension examine une autre utilisation du désaccord. Peut-il servir à construire des intervalles prédictifs fiables pour les titres effectivement achetés ? Une couverture globale correcte pourrait cacher une couverture différente dans le groupe choisi.

Le protocole est fixé avant les calculs de cette extension, mais la période avait déjà été examinée dans l'étude principale. Il s'agit donc d'une analyse exploratoire, sans nouvelle période indépendante. Le rendement cible, les six prévisions publiées et les conditions d'admissibilité restent les mêmes.

### Construire les fourchettes avec le passé disponible

Chaque intervalle est centré sur la moyenne des six prévisions. Sa demi-largeur est le produit d'un quantile historique d'erreur normalisée et d'une échelle courante. Nous comparons une échelle constante, le désaccord, l'erreur absolue passée et la volatilité passée. Les échelles variables ont un plancher de 0,0001 en rendement décimal.

La calibration utilise les 24 mois précédents, avec au moins douze mois disponibles. Chaque mois reçoit le même poids. À l'intérieur d'un mois, les obligations se partagent ce poids. Les niveaux annoncés sont 50, 80, 90 et 95 %. Le quantile pondéré est une statistique d'ordre empirique, pas une garantie conforme de couverture finie.

Deux ensembles de calibration sont comparés. Le premier emploie tous les titres admissibles. Le second utilise les titres qui avaient été sélectionnés à leur propre date historique, dans le quintile supérieur des prévisions moyennes. Aucun classement n'est refait avec une prévision future. Les deux calibrations sont ensuite évaluées sur l'univers et sur les titres actuellement sélectionnés.

Ces fourchettes concernent le rendement qui sera réalisé. Elles ne sont pas des intervalles de confiance sur le rendement moyen attendu. La dépendance des obligations et les changements de distribution empêchent d'invoquer automatiquement une garantie d'échangeabilité.

### Le résultat contredit l'hypothèse de sous-couverture après sélection

Avec une largeur liée au désaccord et une calibration générale, la couverture annoncée à 90 % est réalisée à {{coverage_all}} % sur tous les titres. Elle atteint {{coverage_selected}} % dans le quintile sélectionné. L'écart sélection moins univers vaut {{coverage_gap}} points de pourcentage, avec un intervalle à 95 % de {{coverage_low}} à {{coverage_high}}.

![Couverture des intervalles](results/figures/calibration_selection.png)

La calibration spécifique au groupe sélectionné réduit les largeurs, mais sa couverture sur ce groupe tombe à {{coverage_recalibrated}} %. La proposition de recalibrer après sélection ne suffit donc pas à améliorer cette mesure dans notre expérience.

Ce résultat dépend de l'échelle. Une largeur constante se comporte différemment, ce que montrent les 64 lignes du tableau de calibration. Le désaccord tend déjà à élargir les intervalles sur les titres sélectionnés. Il serait incorrect de conclure que la sélection améliore toujours la couverture.

L'inférence porte sur les écarts mensuels moyens, par blocs circulaires appariés de 6, 12 et 24 mois et 4 999 répétitions. Elle ne considère pas les centaines d'obligations d'un même mois comme des observations indépendantes. La comparaison de couverture principale de l'extension est fixée dans `selection_protocol.json`. Les autres niveaux et échelles restent descriptifs.

### Réduire les positions quand l'incertitude augmente

Les trois filtres conservent les mêmes titres que le classement par prévision moyenne. Ils modifient seulement la part du capital qui leur est consacrée, selon la volatilité, l'erreur passée ou la largeur moyenne de l'intervalle calibré sur les titres sélectionnés.

Le multiplicateur est la médiane de l'indicateur durant les 24 mois précédents divisée par sa valeur actuelle. Il reste entre 0,25 et un. Chaque flux filtré reçoit ensuite le même budget annuel de risque de 6 %, estimé sur ses propres 24 mois passés et plafonné à 100 % du capital. Les liquidités rapportent le taux sans risque et les frais suivent le registre exact de l'étude principale.

Le recalibrage du budget de risque peut compenser une partie du filtre. Il ne faut donc pas lire ces stratégies comme une réduction permanente de l'exposition par rapport au repère. Leurs risques et leurs expositions réellement obtenus sont publiés.

{{filters_table}}

Le tableau utilise 25 points de base de frais par montant acheté ou vendu. Dans cette configuration, chacun des trois filtres donne un équivalent certain inférieur à la sélection sans filtre. Cette dernière retrouve exactement le chemin du classement moyen de l'étude principale, ce qui vérifie la cohérence des deux expériences.

![Écarts des filtres après frais et incertitude](results/figures/filtres_selection.png)

### Un repère explicite issu d'Uncertainty-Aware Asset Pricing

Liu, Luo, Wang et Zhang proposent un classement qui utilise les bornes d'intervalles. Nous reprenons le signe de leur règle longue, la moyenne prévue **plus** un quantile des erreurs absolues propres au titre. Le quantile à 5 % n'est pas une fourchette à 95 % et n'est pas remplacé par celle-ci.

Notre adaptation calcule les quantiles à 1, 5 et 10 % sur les 36 mois passés, avec au moins douze observations. Elle utilise les prévisions obligataires déjà publiées, choisit le décile supérieur et conserve uniquement des positions acheteuses. Le repère moyen choisit le même décile dans le même univers. Les deux règles passent par le même budget de risque.

{{uas_table}}

Les colonnes utilisent 25 points de base de frais. Ces variantes reprennent le noyau du classement, mais pas l'échantillon d'actions, la validation longue ou le portefeuille long-court de l'article. Elles ne sont donc pas une réplication de ses performances. Leur présence empêche de présenter comme nouvelle une utilisation des bornes déjà proposée dans la littérature.

### Vérification et portée de l'extension

Les tests contrôlent les quantiles pondérés sur une distribution à réponse connue, les dates admises dans la calibration et le signe du classement de référence. La vérification recalcule la couverture à partir des moyennes mensuelles et les performances depuis les registres de rendements. Les calculs SQL et le classeur fournissent une autre lecture des mêmes observations.

Le résultat établi reste limité. Dans l'échelle principale fondée sur le désaccord, les titres sélectionnés sont mieux couverts que l'ensemble. Une calibration spécifique les couvre moins bien. Les filtres d'exposition testés ne montrent pas d'amélioration économique. Une nouvelle période serait nécessaire pour évaluer une règle modifiée à la lumière de ces résultats.

**Extension abstract.** We calibrate empirical return intervals using past out-of-time forecast errors and compare coverage before and after selecting the highest-forecast bonds. Under disagreement scaling, selected bonds are better covered than the full universe. Calibration restricted to historically selected bonds narrows the intervals but reduces their realized coverage. Exposure filters and an adapted uncertainty-aware upper-bound sort do not establish a new economic advantage. The extension is exploratory on the previously examined historical sample.

Référence complémentaire. Liu, Luo, Wang et Zhang (2026). *Uncertainty-Aware Asset Pricing*. Version du 2 janvier. [Texte intégral](https://arxiv.org/html/2601.00593v1).

## Références

[1] Bali, T. G., Kelly, B., Mörke, M. et Rahman, J. 2026. Machine Forecast Disagreement. Review of Financial Studies. [DOI](https://doi.org/10.1093/rfs/hhag042).

[2] Dickerson, A., Nozawa, Y. et Robotti, C. 2025. Factor Investing with Delays. Document de travail du 23 juillet. [Texte universitaire](https://www.ier.hit-u.ac.jp/Common/publication/DP/DPS-A771.pdf).

[3] Open Source Bond Asset Pricing. Archive des prévisions, avril 2026. [Fichiers et documentation](https://openbondassetpricing.com/machine-learning-data/).

[4] French, K. Research Data Factors. [Données et conventions](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html).

[5] Bailey, D., Borwein, J., López de Prado, M. et Zhu, Q. 2017. The Probability of Backtest Overfitting. Journal of Computational Finance 20. [DOI](https://doi.org/10.21314/JCF.2016.322).

[6] Bailey, D. et López de Prado, M. 2014. The Deflated Sharpe Ratio. Journal of Portfolio Management 40, 94 à 107. [DOI](https://doi.org/10.3905/jpm.2014.40.5.094).
