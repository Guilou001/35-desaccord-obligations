-- Une ligne porte le signal de t et le rendement de t+1.
-- La fenêtre s'arrête au signal de t-1, dont le rendement est connu en t.
-- Le moteur crée la vue scores après avoir contrôlé les six modèles.
SELECT signal_date, cusip,
       count(realized) OVER history AS n_history,
       stddev_samp(realized) OVER history AS lag_volatility,
       avg(abs_error) OVER history AS lag_error
FROM scores
WINDOW history AS (
    PARTITION BY cusip ORDER BY signal_date
    RANGE BETWEEN INTERVAL '12' MONTH PRECEDING AND INTERVAL '1' MONTH PRECEDING
);
