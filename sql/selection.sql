-- Comparaisons à gamma identique, rendements décimaux.
SELECT "model", "cost_bps", count(*) AS months,
       12*avg(excess) - 6*5.0*var_samp(excess) AS ce
FROM read_parquet('results/selection/paths.parquet')
GROUP BY "model", "cost_bps"
ORDER BY "model", "cost_bps";
