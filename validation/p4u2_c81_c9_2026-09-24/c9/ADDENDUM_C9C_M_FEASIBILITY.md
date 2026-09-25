# Addendum C9-C — faisabilité de m (rédigé AVANT tout run C9-C, aucune statistique calculée)

Constat : la procédure d'injection gelée (motifs à nœuds DISJOINTS) échoue sur 10/10
graines pour m = 25, à N = 100 comme à N = 150 (E = 150). Appliquée telle quelle, la règle
d'invalidation rendrait M25 et S25 vides, donc non interprétables. C'est un défaut de
conception du pré-enregistrement, pas un résultat.

Mesure de faisabilité (graines 9000..9019, disjointes de toutes les graines de campagne,
sans calcul de T, T′ ni signature) :
  N = 100 : m = 12 → 20/20 ; 15 → 19/20 ; 18 → 8/20 ; 20 → 0/20
  N = 150 : m = 12 → 20/20 ; 15 → 14/20 ; 18 → 0/20 ; 20 → 0/20

Amendement (seul changement) : m ∈ {10, 25} remplacé par m ∈ {5, 12}.
12 = plus grand m faisable à 20/20 dans les deux densités ; 5 garde un rapport ≈ 2,4,
proche du 2,5 initial. Configurations : C9C-M5, C9C-M12, C9C-S5, C9C-S12 (bases
3005000, 3012000, 3105000, 3112000) ; C9C-M0 inchangée. Le critère de détection
« au moins les configurations m = 25 » devient « au moins les configurations m = 12 ».
Contrainte de nœuds disjoints, null, contrôles, statistiques et seuils : INCHANGÉS.
