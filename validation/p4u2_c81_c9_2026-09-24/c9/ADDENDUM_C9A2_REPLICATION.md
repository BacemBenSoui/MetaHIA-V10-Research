# Addendum C9-1 — réplication de C9-A2 (rédigé après lecture de C9-A0/A1/A2/B1, avant tout run de réplication)

Constat déclencheur : C9-A2 (100 nœuds / 100 arêtes, s = 0,75) donne 10/100 rejets contre
α_eff = 4,18 % (binomial p = 0,0093 < 0,0167) → N1 FAIL ; N3 (tendance) p = 0,025 → FAIL.
Ces verdicts pré-enregistrés RESTENT ENREGISTRÉS tels quels ; cette réplication ne les
annule pas, elle sert à les interpréter.

Raison : pour ce générateur (produit w_s·w_t), le null par permutation des cibles est
exact (argument en PREREGISTRATION_C9_1.md). Une inflation réelle impliquerait un bug
d'implémentation ; sinon le 10/100 est une fluctuation (p ≈ 0,009 sur ≥ 5 tests).

Protocole : C9-A2rep = même configuration que C9-A2, 300 graines neuves (base 1130000),
N_null = 200. Lecture pré-déclarée :
- taux de rejet compatible avec α_eff (binomial bilatéral p ≥ 0,05) → FAIL initial
  interprété comme fluctuation ; le verdict initial reste noté, avec cette interprétation ;
- sinon → défaut d'implémentation ou d'argument d'exactitude à trouver avant toute
  suite de C9 ; aucune campagne suivante lancée.
