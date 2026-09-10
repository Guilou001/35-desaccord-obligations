# Refaire les calculs

La configuration est dans `config/protocol.json`. Les versions résolues sont dans `uv.lock` et l’environnement de réalisation est dans `config/environment.json`.

## Contrôle sans données brutes

```bash
uv sync --locked
uv run pytest
uv run desaccord verify
```

Ce contrôle utilise les sorties mensuelles publiées. Il retrouve les indicateurs, les frais et les résultats SQL. Il ne réestime pas les modèles depuis les données originales.

## Réestimation complète

```bash
uv sync --all-groups --locked
uv run desaccord fetch
uv run desaccord run
uv run desaccord verify
uv run --group report desaccord report
```

Les fichiers de marché évoluent chez leurs fournisseurs. Le manifeste décrit l’édition qui a produit les résultats publiés. Une édition différente demande une expérience documentée comme telle.

La reconstruction des graphiques et du PDF utilise les tables publiées et n’exige pas les fichiers bruts. Une conclusion qui change de signe bloque la publication automatique et demande une relecture du texte.

Le classeur Excel est un document de contrôle supplémentaire, avec ses données dans `results/tables/workbook_source.json`. Sa génération emploie `@oai/artifact-tool`, séparément du pipeline scientifique Python. Les formules restent consultables et modifiables dans le fichier livré.

Le générateur du classeur est conservé dans `tools/build_workbook.mjs`. Il se lance depuis la racine du dépôt avec Node et `@oai/artifact-tool` disponible. Il vérifie les équivalents certains et une modification de l’aversion au risque avant export.
