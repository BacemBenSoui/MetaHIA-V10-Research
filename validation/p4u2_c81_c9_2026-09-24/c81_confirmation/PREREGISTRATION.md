# C8.1-confirmation — pré-enregistrement (rédigé AVANT tout run)

Date : 2026-09-24. Base : MetaHIA-V10-Research `2631252` (production P4-U.2 inchangée).

## Harnais
Les scripts jetables C8/C8.1 n'ont pas été committés. Harnais reconstruit
(`c81_confirmation.py`) à partir du module de production et des rapports C8/C8.1 :
- signatures : `compute_signatures` de production, avec un cache par nœud source
  vérifié bit à bit identique sur 30 graphes (même appel `discover_paths(start=source)`,
  donc même troncature `max_paths`) ;
- statistique : `T = max_s |G_s|` sur `group_by_signature()` de production ;
- percentile : `percentile_rank` (mid-rank) de production, rejet si ≥ 95 ;
- générateur de bruit : E arêtes, chacune `rng.sample(univers, 2)` (source ≠ cible) ;
- null procédural : même générateur, univers COMPLET de nœuds, même nombre d'arêtes,
  graphe → signatures → group_by_signature → T ;
- signal : c chaînes à 2 sauts sur 3c nœuds dédiés + 80 arêtes de fond sur 60 nœuds ;
  null = générateur uniforme sur l'univers complet (60 + 3c nœuds, 80 + 2c arêtes).
  Choix vérifié par pré-test : il reproduit la plage T observée publiée par C8.1
  (T ∈ [17, 24] sur 25 graines contre [17, 27] publiés) ; la variante « chaînes posées
  sur les 60 nœuds de fond » donne T ∈ [3, 8] et est donc rejetée.
- graines : plages neuves, disjointes de C8.1 (inconnues), dérivées par configuration.

## Étage 0 — ancrage de fidélité (pas un test du moteur)
R0-bruit : 60 nœuds / 100 arêtes, 40 graines, N_null = 50.
R0-signal : 15 chaînes, 25 graines, N_null = 50.
Attendu : distributions compatibles avec C8.1 (FPR ≈ 5 %, TPR ≈ 80 %, percentiles signal ≥ ~80).
Si l'ancrage échoue, les étages A/B ne sont PAS interprétés comme une confirmation de C8.1.

## Étage A — calibration nulle (100 graines, N_null = 200)
A1 : 60 nœuds / 100 arêtes (config C8.1, K ≈ 69 classes)
A2 : 150 nœuds / 100 arêtes (K ≈ 44)
A3 : 250 nœuds / 100 arêtes (K ≈ 25)
Variation du nombre de classes K à nombre d'arêtes fixé (pas d'augmentation de corpus).

## Étage A-bis — sensibilité à la spécification du null (SUPPLÉMENTAIRE, hors critère)
A-bis : 60 nœuds / 100 arêtes, graphe observé à degrés hétérogènes (poids de nœud
∝ 1/(rang+1), Zipf s=1, pour source et cible) ; null uniforme inchangé.
Motif : sous A1–A3 le graphe observé est tiré par le générateur du null lui-même,
donc échangeable avec les réplicats → la calibration y est garantie par construction
et ne teste que l'implémentation. A-bis mesure ce qui arrive quand le H0 réel n'est
pas le générateur du null. Rapporté, jamais utilisé pour PASS/FAIL.

## Étage B — détection (100 graines, N_null = 200)
B1 : 15 chaînes (config C8.1) ; B2 : 8 chaînes ; B3 : 25 chaînes. Fond : 80 arêtes / 60 nœuds.

## Mesures par configuration
taux de rejet + IC de Wilson 95 % ; α_eff = taille exacte du test discret
(mid-rank ≥ 95 sur un T entier à ex-aequo), estimée par leave-one-out sur les
réplicats nuls ; test binomial exact vs α_eff ; PIT randomisé
u = (nb_inf + U·(nb_égal+1))/(N+1) — exactement U(0,1) sous échangeabilité ;
KS vs U(0,1) et χ² à 10 classes sur u ; K moyen ; quantiles de T observé et nul ;
pour B : attribution du bucket arg-max (part d'arêtes de chaîne).

## Critères de sortie (figés ici)
Null (A1, A2, A3), seuil Bonferroni 0,05/3 par famille de tests :
 N1. binomial exact bilatéral taux de rejet vs α_eff : p ≥ 0,0167 ;
 N2. KS et χ² sur le PIT randomisé : p ≥ 0,0167.
Signal (B1, B2, B3) :
 S1. taux de rejet > α_eff (binomial unilatéral, p < 0,0167) dans CHAQUE config ;
 S2. déplacement présent dans chaque config (médiane des percentiles > 50) — aucun
     seuil de puissance fixé a posteriori ; les TPR sont rapportés, pas jugés ;
 S3. (interprétation, non bloquant) part des détections dont le bucket arg-max
     contient ≥ 50 % d'arêtes de chaîne.
Architecture : aucune modification quel que soit le résultat.
