# C9-1 — null conditionnel aux degrés, statistique T inchangée — pré-enregistrement

Rédigé AVANT tout run, 2026-09-24. Base : MetaHIA-V10-Research `2631252`, production inchangée.
Portée : C9-A et C9-B. C9-C (signal relationnel à degrés contrôlés) sera conçu et
pré-enregistré APRÈS lecture de C9-B. C9-2 (T_nontrivial) n'est pas lancé. Le défaut
MAX_PATHS (P4-U.2-R1) est hors périmètre : les configurations critères sont choisies
sans troncature (mesuré), et toute troncature est comptée et rapportée.

## Statistique (inchangée)
T = max_s |G_s| via `group_by_signature()` de production ; percentile mid-rank de
production ; rejet si ≥ 95.

## Null C9 (nouveau)
Réplicat = sources de l'observé conservées dans l'ordre, liste des cibles permutée
uniformément, rejet de toute la permutation si une boucle apparaît (s == t), nouvel essai
(plafond 10^6 essais, dépassement consigné). Donc : séquences de degrés entrants et
sortants préservées exactement, multi-arêtes autorisées (comme le générateur observé),
aucune boucle. Tirage exact et indépendant (pas de chaîne de Markov, pas de mélange à
diagnostiquer).
Propriété connue avant le run : pour tout générateur produit P(s,t) ∝ w_s·w_t
(uniforme, Zipf), la loi conditionnelle aux degrés est uniforme, donc le null est exact
et la calibration de C9-A est garantie par construction (test d'implémentation). T est
invariant à l'ordre des arêtes en l'absence de troncature.

## C9-A — calibration (100 graines, N_null = 200)
Critères, 100 nœuds / 100 arêtes, poids Zipf ∝ 1/(rang+1)^s :
- C9-A0 : s = 0 (uniforme)
- C9-A1 : s = 0,5
- C9-A2 : s = 0,75
Supplémentaires (hors critère) :
- C9-Abis : exactement A-bis (60 / 100, s = 1,0) — troncature présente, CONFONDU avec
  R1, rapporté pour comparaison directe avec 88 % / 58 %.
- C9-SBM : 100 nœuds, 2 blocs de 50, 100 arêtes, P(intra) : P(inter) = 9 : 1 (par paire),
  sans régularité relationnelle injectée — structure mésoscopique non produit, donc NON
  exacte sous le null : c'est le bras non tautologique.
Critères (Bonferroni 0,05/3 = 0,0167 sur A0–A2) :
 N1. binomial exact bilatéral taux de rejet vs α_eff : p ≥ 0,0167 ;
 N2. KS et χ² (10 classes) sur PIT randomisé : p ≥ 0,0167 ;
 N3. absence d'inflation avec l'hétérogénéité : test de tendance de Cochran-Armitage
     sur les rejets (A0, A1, A2 ; scores s = 0 ; 0,5 ; 0,75), unilatéral « croissant » :
     p ≥ 0,05 ;
 N4. troncature : zéro graphe tronqué (observés + nuls) dans A0–A2, sinon compté et
     signalé ; la config n'est alors pas jugée sur N1–N3.

## C9-B — falsification du signal C8.1 (100 graines, N_null = 200)
B1/B2/B3 rejoués tels quels (mêmes graines, mêmes graphes observés que
C8.1-confirmation), seul le null change. Aucun critère PASS/FAIL : mesure.
Rapporté : TPR, Wilson, α_eff, comparaison appariée avec le null uniforme (table 2×2 +
McNemar exact), taille du bucket d'impasses (1,0,0,{F}) observée vs moyenne nulle,
signature arg-max observée.
Prédiction (écrite avant) : la signature (1,0,0,{F}) ⇔ cible de degré total 1 (aux
multi-arêtes près) ; ce nombre est fixé par la séquence de degrés, donc le bucket
d'impasses est quasi constant sous le null C9 ; la puissance de B1–B3 devrait tomber
vers α_eff sauf si un autre bucket (ex. (1,1,0,{F,FF}) des premières arêtes) excède le
null.
