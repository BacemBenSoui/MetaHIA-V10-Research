# P4-U.2 — C9-2 : statistique T′ non triviale — pré-enregistrement

Rédigé avant toute exécution de C9-2, 2026-09-24. Gelé en même temps que
`PREREGISTRATION_C9_C.md`, avant tout run de C9-2 ou C9-C.
Base : MetaHIA-V10-Research `2631252`, production inchangée.

## Statut méthodologique
C9-2 est une expérience **prospective issue d'une hypothèse générée par C9-1**
(attribution descriptive, rapport C9-1 Sec. 5 : famille non triviale muette sur A0/SBM,
excédentaire sur B1). Elle est pré-enregistrée et exécutée sur des graines neuves, mais
**ses résultats ne seront pas présentés comme une validation indépendante de C9-1**.
Aucune modification du moteur de production pendant C9-2.

## Hypothèse
T = max_s |G_s| est dominé par des signatures triviales d'impasse quand les degrés
sont préservés. Statistique testée :
    T′ = max_{s : d2(s) > 0 ∨ d3(s) > 0} |G_s|     (T′ = 0 si aucune signature éligible)
Les signatures sans composante d2 ni d3 sont exclues : `(1,0,0,{F})`, et aussi
l'artefact de troncature `(0,0,0,∅)`. Cette exclusion NE corrige PAS les autres
signatures tronquées, partiellement fausses.

## Null (inchangé, identique à C9-1)
Sources observées conservées, cibles permutées uniformément, rejet des boucles ; même
univers, même nombre d'arêtes, mêmes degrés entrants/sortants, même procédure de
signature, même correction de sélection globale (null construit sur T′ lui-même).
Aucun changement de null introduit simultanément avec T′. T est recalculé sur les MÊMES
graphes et les MÊMES réplicats, pour une comparaison appariée T contre T′.

## Configurations (100 graines neuves chacune, N_null = 200)
Spécificité (critères) : C92-A0 / A1 / A2 = 100 nœuds / 100 arêtes, Zipf s = 0 ; 0,5 ;
0,75 ; C92-SBM = 100 nœuds, 2 blocs, 9:1, 100 arêtes.
Spécificité (descriptif, contaminé) : C92-Abis = 60 / 100, s = 1,0 — troncature
présente, **ne peut servir à aucune conclusion positive de spécificité**.
Détection : C92-B2 / B1 / B3 = 8 / 15 / 25 chaînes (même générateur que C8.1/C9-1).

## Critères
Spécificité (A0, A1, A2, SBM ; Bonferroni 0,05/4 = 0,0125), pour T′ :
 P1. binomial exact bilatéral taux de rejet vs α_eff(T′) : p ≥ 0,0125 ;
 P2. KS et χ² (10 classes) sur PIT randomisé : p ≥ 0,0125 ;
 P3. troncature : 0 graphe tronqué (observés + nuls), sinon config non jugée.
Détection (B1–B3), pour T′ — mesures sans seuil de puissance :
 taux de détection, Wilson, binomial unilatéral > α_eff, tendance Cochran-Armitage sur
 (8, 15, 25), signature et famille arg-max, taille du bucket observé contre null.
Règle d'interprétation : une amélioration de T′ par rapport à T = preuve DESCRIPTIVE de
meilleure focalisation, jamais preuve définitive de spécificité relationnelle. Aucun
seuil de performance choisi après observation.

## Sorties obligatoires par configuration
T′ obs / null, percentile, α_eff, FPR ou TPR, PIT, signature arg-max, famille (impasse /
non triviale / tronquée), taille du bucket arg-max obs / null, et les mêmes grandeurs
pour T (apparié), McNemar T contre T′, comptes de troncature. Aucune modification
architecturale ne découle automatiquement de C9-2.
