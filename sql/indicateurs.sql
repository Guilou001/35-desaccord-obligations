-- Depuis la racine du dépôt, lire avec DuckDB.
-- Rendements décimaux mensuels. Aversion au risque fixée à cinq.
SELECT model, cost_bps, count(*) AS months,
       12 * avg(excess) - 30 * var_samp(excess) AS ce
FROM read_parquet('results/tables/paths.parquet')
GROUP BY model, cost_bps
ORDER BY model, cost_bps;
