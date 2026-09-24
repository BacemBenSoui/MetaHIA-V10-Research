# P4-U.2 — Campagne 8 (candidate-generation / Gate-I identifiability) : rapport intermédiaire, calibration NON terminée (2026-09-24)

Répond à la campagne demandée par le porteur du projet après la
découverte de circularité (`documentation/P4U2_Candidate_Generation_Gate_I_Circularity_Finding_2026-09-24.md`,
commit `90bed8b`) : tester empiriquement l'Approche A (statistique de
support) combinée à l'Approche B (modèle nul procédural complet), avant
toute décision architecturale. **Ce document rapporte un état
intermédiaire honnête, pas une conclusion** — deux obstacles réels ont
été trouvés en cours de route (un problème de performance et un bug de
construction du pool nul), et le résultat obtenu avec la correction
appliquée reste lui-même préoccupant, pas encore exploitable pour geler
quoi que ce soit.

## 1. Confirmation préalable : `Cohesion_B` dégénérée aussi sous un null procédural complet

Avant de tester l'Approche A, vérification directe que le modèle nul
procédural complet (reconstruire le graphe, ré-exécuter
`group_by_signature()`, recalculer `Cohesion_B` sur les buckets nuls)
ne sauve pas non plus `Cohesion_B` : **chaque bucket, dans chaque
réplicat nul, a une cohésion exactement égale à 1,0** — confirmé
directement, pas supposé. `Cohesion_B` est donc dégénérée sous les DEUX
constructions de null (ré-échantillonnage naïf ET null procédural
complet), pas seulement l'une des deux. Ceci confirme que le problème
n'est pas la construction du null mais le choix de statistique lui-même
pour ce type de génération de candidat — exactement le diagnostic du
porteur du projet.

## 2. Premier obstacle trouvé : coût de calcul bien supérieur à l'estimation initiale

Un premier test de faisabilité (Approche A+B, `N_null=30`, seulement 3
configurations, 20 graines chacune) a mis **93 minutes** à s'exécuter —
très supérieur à l'estimation initiale. Cause trouvée par mesure
directe : `compute_signatures()` appelle `kernel2.discover_paths()` une
fois PAR ARÊTE, alors que toutes les arêtes partageant la même source
peuvent réutiliser le même appel. Une version optimisée
(`compute_signatures_fast`, réservée à cette campagne jetable, **le
module de production n'est pas modifié**) a été écrite et **vérifiée
identique bit à bit** à la version originale sur un cas de test, avec un
gain d'environ 2× — insuffisant à lui seul pour rendre la grille
complète demandée (plusieurs comptes de classes × tailles × pools ×
20+ graines × N_null=200) praticable en un temps raisonnable : à
l'échelle « grand pool » (600 arêtes, 250 nœuds), un seul calcul de
signatures prend encore 1,4 à 2 secondes, et une seule cellule de
calibration (10 graines × 30 réplicats nuls) a nécessité environ 13
minutes.

## 3. Second obstacle trouvé : un vrai bug de construction du pool nul

Le premier script de campagne tirait le pool nul (`sources`/`targets`
pour le ré-échantillonnage) depuis les seuls nœuds ayant EFFECTIVEMENT
apparu comme source/cible dans le corpus original — pas depuis
l'univers complet de nœuds utilisé pour construire ce corpus. Sur un
graphe aléatoire clairsemé, ces deux ensembles diffèrent
significativement. **Vérifié par comparaison directe sur le même
graphe** : le null construit sur le sous-ensemble donnait une
distribution de taille de bucket maximal `[8..14]` (observé=12, non
significatif) ; le null corrigé sur l'univers complet donnait
`[11..18]` (observé=12, encore moins significatif) — les deux
constructions donnent des verdicts DIFFÉRENTS sur le MÊME graphe
observé, confirmant que ce choix n'est pas un détail cosmétique.

## 4. Résultat obtenu avec la correction appliquée — toujours préoccupant

Avec le pool nul corrigé (univers complet) et le calcul de signature
optimisé, taux de faux positifs sur du bruit pur, `N_null=30`,
seulement 10 graines par configuration (résolution limitée, comme pour
les tout premiers balayages des campagnes précédentes) :

```text
petit pool  (100 arêtes, 60 nœuds)  : FPR = 20 % (2/10)
grand pool  (600 arêtes, 250 nœuds) : FPR = 10 % (1/10)
```

**Le taux reste au-dessus du niveau nominal de 5 % aux deux échelles
testées**, avec un renversement de direction par rapport au tout
premier essai (pool-nul bugué : 5 % petit -> 30 % grand ; pool-nul
corrigé : 20 % petit -> 10 % grand) — la correction du pool a
clairement changé le comportement, mais n'a PAS produit un taux proche
du niveau nominal. **Avec seulement 10 répétitions par cellule, ceci
reste un signal à surveiller, pas une caractérisation fine** (la même
réserve statistique déjà appliquée aux campagnes 4-7) — mais il est
cohérent aux deux échelles dans le sens « au-dessus du nominal », pas
un simple bruit d'échantillonnage isolé.

## 5. Ce que ce rapport intermédiaire établit, et ce qu'il n'établit pas

**Établi, par exécution directe** :
- `Cohesion_B` est dégénérée sous les deux constructions de null
  testées (naïve et procédurale complète) — confirmé, pas supposé.
- Le coût de calcul de la grille complète demandée par le porteur du
  projet est très supérieur à l'estimation initiale — une version
  optimisée existe (2×) mais reste insuffisante pour la grille complète
  dans un temps raisonnable sans une réduction de portée ou une
  approche plus rapide encore.
- La construction du pool nul (univers complet vs sous-ensemble observé)
  change matériellement le verdict sur un même graphe — un piège
  méthodologique réel, maintenant documenté, à ne pas répéter.
- Avec la correction appliquée, le taux de faux positifs de l'Approche
  A+B (statistique de support, null procédural complet, maximum sur
  tous les buckets) reste au-dessus du niveau nominal aux deux échelles
  testées (10-20 %, sur seulement 10 répétitions chacune).

**Non établi, délibérément** :
- Un taux de faux positifs précisément calibré (10 répétitions
  insuffisantes, comme toujours à ce stade d'une calibration).
- La grille complète demandée (plusieurs comptes de classes, tailles de
  classes, tailles de pool, comparaison A/B systématique, sensibilité
  au nombre de classes) — non exécutée, pour la raison de coût de
  calcul exposée en Sec. 2.
- Si l'Approche A (support) est finalement viable une fois correctement
  calibrée, ou si elle nécessite elle-même un raffinement (ex. un
  contrôle multi-comparaisons distinct, une statistique dérivée du
  support plutôt que le support brut) — question ouverte.
- Les Parties 2 et 3 du plan de campagne (vrai signal injecté,
  sensibilité au nombre de classes) — non exécutées.

## 6. Prochaine étape — décision requise avant de poursuivre

Deux obstacles pratiques bloquent la poursuite de la grille complète
telle que spécifiée : le coût de calcul et le besoin de recalibrer le
pool nul correctement caractérisé maintenant. Options, aucune choisie
ici :

```text
1. Réduire la portée de la grille (moins de configurations, tailles de
   pool plus petites, N_null réduit) pour rester dans un budget de temps
   raisonnable, au prix d'une résolution plus faible.
2. Optimiser davantage le calcul de signature avant de relancer à pleine
   échelle (ex. réduire max_paths, mettre en cache au niveau du graphe
   plutôt que par nœud, éviter de reconstruire le graphe complet à
   chaque réplicat nul).
3. Reconsidérer la statistique elle-même avant de recalibrer davantage
   l'Approche A telle quelle -- le taux de faux positifs élevé pourrait
   indiquer que le maximum sur TOUS les buckets (family-wise, comme
   P4-U.1) est trop sensible au nombre de classes qui émergent
   naturellement d'un graphe aléatoire, une question que la Partie 3 du
   plan original visait justement à explorer mais n'a pas encore pu
   être exécutée.
```

Décision explicite du porteur du projet requise avant de relancer tout
calcul supplémentaire à grande échelle.
