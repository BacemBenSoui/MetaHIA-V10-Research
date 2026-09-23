# MetaHIA V10 — P4-U.1 v0.3 : découverte non supervisée de compositions structurelles (résolution Gate B / Gate C, avant toute implémentation nouvelle)

## 0. Statut et rapport à la v0.2

```text
P4-U.1 = OPEN_RESEARCH
scope  = UNSUPERVISED COMPOSITIONAL PATTERN DISCOVERY
         (jamais raccourci en « unsupervised discovery » — Sec. 17)
exclu  = NOT_AUTONOMOUS_RELATION_DISCOVERY
```

Remplace intégralement
`documentation/P4U1_Unsupervised_Compositional_Pattern_Discovery_V0_2.md`
(conservé pour l'historique de la revue et du diagnostic, non
implémentable tel quel : sa Sec. 20 documente la tension bloquante que
cette v0.3 résout).

**Origine de cette révision.** L'implémentation minimale de la v0.2
(`p4u1_unsupervised_pattern_discovery_v0_1.py`, 22 tests, commit
`510b36b`) a révélé, en calibrant les seuils numériques sur des corpus
d'essai, une contradiction directe entre Gate B et Gate C :

```text
Gate B a besoin d'une structure concentrée (« hub ») pour être
statistiquement significative face au modèle nul.

Gate C, via kernel2.replay_path_pattern_holdout() (max_candidates_per_step=1
par défaut), échoue systématiquement en AMBIGUOUS dès qu'un nœud a plus
d'une continuation valide — exactement la structure que Gate B exige.

=> aucune structure de corpus ne peut satisfaire les deux portes
   simultanément avec les définitions de la v0.2.
```

Détail complet du diagnostic, des trois bugs corrigés avant même
d'atteindre cette tension, et des quatre options envisagées :
`documentation/P4U1_Unsupervised_Compositional_Pattern_Discovery_V0_2.md`
Sec. 20 et `JOURNAL_DE_BORD.md` (entrée du 2026-09-23).

**Décision explicite du porteur du projet** (revue méthodologique
détaillée, 2026-09-23), reprise ici sans l'affaiblir : le décalage
n'est pas dans Gate B, ni dans le modèle nul, ni dans `kernel2` — il
est dans la **sémantique de Gate C**. Le rejeu actuel de `kernel2`
répond à la question *« existe-t-il une continuation UNIQUE compatible
avec le pattern ? »*, alors que P4-U.1 doit répondre à *« existe-t-il
AU MOINS UNE continuation structurellement compatible permettant de
réaliser le motif ? »*. Un nœud-hub avec plusieurs continuations
valides n'est pas nécessairement une ambiguïté épistémique — cela peut
être une relation un-à-plusieurs réelle du graphe.

```text
Gate B                                    : INCHANGÉ
kernel2 (discover_paths/generalize_path_pattern/replay_path_pattern_holdout) : INCHANGÉ
Gate C                                    : REDÉFINI (rejeu à valeur d'ensemble)
Nouveau module (protocole seulement, pas encore codé) : p4u1_set_valued_replay_v0_1.py
```

**Toujours aucun code nouveau écrit par ce document.** La discipline
« protocole avant implémentation » s'applique de nouveau intégralement
avant de toucher au module de rejeu : ce document fige la sémantique
de la v0.3, l'implémentation de l'adaptateur `p4u1_set_valued_replay_v0_1.py`
et la construction du benchmark verrouillé U1/U2/U3 viennent seulement
après.

## 1. Origine et cadrage — inchangé depuis la v0.1/v0.2

`P4-U` n'existe nulle part dans l'historique du projet avant ces trois
documents (vérifié par recherche directe, 2026-09-23). Distinction
essentielle, non renégociée :

```text
P4-U.1 = découverte non supervisée de COMPOSITIONS structurelles
         sur un graphe à relations DÉJÀ ÉTIQUETÉES
         (MERE_DE, TRAVAILLE_DANS, ENFANT_DE...)

P4-U.2 (futur, non défini ici) = découverte autonome de relations
         INCONNUES — à définir seulement après avoir vu les résultats
         réels de P4-U.1
```

P4-T reçoit un couple `(source, cible)` explicitement pendant
l'entraînement. P4-U.1 ne reçoit que le graphe : aucune paire, aucune
cible, aucun squelette cible, aucune hypothèse de transformation.

## 2. Objectif exact — inchangé depuis la v0.2

> Découvrir, sans cible désignée, une composition structurelle
> récurrente dans un graphe à relations déjà nommées, **et démontrer
> statistiquement** que cette découverte est distinguée du bruit ET de
> l'effet des comparaisons multiples — pas seulement fréquente, pas
> seulement plus fréquente qu'un seuil arbitraire.

## 3. Entrée et interdits — inchangé depuis la v0.1

**Entrée, uniquement** : un graphe (nœuds + arêtes déjà étiquetées).

**Interdit** : relation cible, couple source→cible, squelette cible,
hypothèse de transformation, dictionnaire sémantique.

## 4. Architecture cible — mise à jour côté Gate C uniquement

```text
                 G_train
                    │
             discover_paths()
                    │
            filtrage min_depth (Sec. 5)
                    │
             group_by_skeleton()
                    │
              tous les candidats
              (support_train par candidat)
                    │
        ┌───────────┴───────────┐
        │                       │
   G_negative[1..N]        support_train(candidat)
   (Sec. 6, le même            │
    G_train, N tirages)        │
        │                       │
   distribution du            comparaison
   MAXIMUM sous null    (Sec. 7, correction
   (Sec. 7)              multi-comparaisons)
        │                       │
        └───────────┬───────────┘
                     │
         sélection pré-enregistrée
         Gate B quantitative (Sec. 9) -- INCHANGÉ
                     │
                   freeze()
              -> FrozenPattern (Sec. 12)
                     │
             ╔═══════════════════╗
             ║   AUCUN ACCÈS AU  ║
             ║      HOLDOUT      ║
             ╚═══════════════════╝
                     │
                     ↓
                G_holdout
                     │
        starts admissibles (Sec. 11)
                     │
      p4u1_set_valued_replay_v0_1.py  -- NOUVEAU (Sec. 10)
      (utilise les primitives kernel2 existantes, ne les modifie pas ;
       kernel2.replay_path_pattern_holdout() enregistré en diagnostic
       secondaire, jamais comme critère principal — Sec. 10.3)
                     │
        G_holdout_negative[1..N]
        (même null model, dérivé de G_holdout)
                     │
         Gate C quantitative -- REDÉFINIE (Sec. 10)
```

Réutilise strictement `kernel2.discover_paths()`,
`kernel2.generalize_path_pattern()`, `kernel2.replay_path_pattern_holdout()`
(aucune modification, y compris dans cette v0.3 — c'est le point que
la revue du porteur du projet a explicitement voulu préserver). Un
module minimal nouveau (`p4u1_unsupervised_pattern_discovery_v0_1.py`,
déjà écrit) porte `group_by_skeleton()`, le modèle nul, le score de
Gate B, et `freeze()`. Un second module nouveau, encore à écrire
(`p4u1_set_valued_replay_v0_1.py`), porte exclusivement la sémantique
de rejeu à valeur d'ensemble de Gate C — jamais mélangé au premier
module ni à `kernel2`. **Toujours pas de réactivation** des 5 fichiers
`e20d_*` morts.

## 5. `min_depth` imposé explicitement — inchangé depuis la v0.2

```text
min_depth = 2   (obligatoire)
max_depth = 3   (pour le premier benchmark verrouillé)
```

## 6. Modèle nul — inchangé depuis la v0.2

Configuration model stratifié par étiquette. **Précision ajoutée par
l'implémentation** (déjà documentée dans
`documentation/P4U1_Unsupervised_Compositional_Pattern_Discovery_V0_2.md`
Sec. 20, reprise ici car elle reste la spécification exacte du modèle
nul verrouillé) : le double-edge-swap strict et la permutation complète
des cibles préservent tous deux le degré exact par nœud et par
étiquette — donc **exactement** ce que le protocole voulait garantir —
mais laissent alors le support d'une composition à 2 sauts
algébriquement invariant (`support = Σ_n in_degree_A(n) × out_degree_B(n)`,
invariant sous toute permutation à degré exact préservé). Le modèle nul
retenu échantillonne donc, pour chaque étiquette séparément, de
nouvelles paires (source, cible) par tirage uniforme indépendant à
partir de deux pools **séparés par rôle** (pool des sources
originales de cette étiquette, pool des cibles originales de cette
étiquette — jamais fusionnés), en rejetant boucles et doublons. Ceci
préserve le nombre d'arêtes et les pools d'entités par rôle et par
étiquette, mais pas le degré exact de chaque nœud individuel — un
compromis plus faible que l'objectif initial, disclosed explicitement
ici, conformément à la clause d'échappement déjà prévue par la v0.2
elle-même (« si structurellement inatteignable... documenté
explicitement, jamais approximé silencieusement »).

`N_null = 200` par défaut, seeds déterministes `0..N_null-1`. Le modèle
nul reste un mécanisme transversal de contrôle statistique, jamais un
troisième type de jeu de données (inchangé depuis la v0.2, Sec. 6).

## 7. Correction pour comparaisons multiples — inchangé depuis la v0.2

Statistique du maximum (méthode de type Westfall-Young) sur la
distribution `{max_support_null_1, ..., max_support_null_N_null}` —
voir v0.2 Sec. 7 pour le détail complet, non repris ici car non
modifié par cette révision.

Un ajout de l'implémentation, non prévu par la v0.2 mais nécessaire :
les squelettes « aller-retour » sur une même relation (ex.
`X <-REL- Y -REL-> Z`) sont exclus de toute candidature (Gate A
elle-même), pour tous les corpus uniformément — sous l'échantillonnage
du modèle nul (Sec. 6), un nœud recevant par hasard plusieurs arêtes
de la même étiquette produit une explosion combinatoire (`k×(k-1)`) de
tels chemins qui dominerait sinon systématiquement la statistique du
maximum, écrasant tout signal de composition à deux relations
distinctes.

## 8. Compétition entre candidats — inchangé depuis la v0.2

U1 contient le motif réel plus trois decoys (`decoy_train_only`,
`decoy_sub_seuil`, `decoy_depth1`) — voir v0.2 Sec. 8, non modifié.

## 9. Gate B — quantitative, INCHANGÉE

```text
Score_discovery(candidat) = support_train(candidat)

Gate B = RETAINED si, simultanément :
  (a) support_train(candidat) >= S_min
  (b) support_train(candidat) > percentile_99(distribution du maximum sous null, Sec. 7)
  (c) depth(candidat) >= min_depth (Sec. 5)
  (d) generalize_path_pattern(candidat) ne renvoie pas None

sinon REJECTED.
```

Décision explicite de cette v0.3 (revue du porteur du projet, Sec. 0) :
**Gate B n'est pas modifiée.** Elle est lisible, elle répond à une
question précise (« ce motif est-il exceptionnellement concentré dans
TRAIN, au-delà de l'effet des comparaisons multiples ? »), et le
problème diagnostiqué dans la v0.2 vient du rejeu, pas de la
statistique de découverte. Jeter cette statistique aurait sacrifié un
travail déjà validé pour un problème localisé ailleurs.

Si plusieurs squelettes distincts satisfont (a)-(d) simultanément,
rapporté comme `MULTIPLE_RETAINED` — inchangé depuis la v0.2.

## 10. Gate C — REDÉFINIE : rejeu structurel à valeur d'ensemble (« set-valued replay »)

### 10.1 Le décalage conceptuel identifié

`kernel2.replay_path_pattern_holdout()` répond implicitement à une
question forte : *« existe-t-il une continuation UNIQUE compatible
avec le pattern à chaque étape ? »* — toute étape avec plus d'un
successeur valide renvoie `AMBIGUOUS`, traité par la v0.2 comme un
échec de Gate C. P4-U.1 doit en réalité répondre à une question plus
faible et plus correcte structurellement : *« existe-t-il AU MOINS UNE
continuation structurellement compatible permettant de réaliser le
motif ? »* — un nœud-hub avec plusieurs continuations valides n'est pas
une ambiguïté épistémique, c'est potentiellement une relation
un-à-plusieurs réelle du graphe.

### 10.2 Nouvelle sémantique — existence, pas unicité

```text
REPLICATED(start) =
    ∃ un chemin admissible depuis `start`, dans G_holdout,
    dont le squelette structurel (operator_sequence + direction_sequence)
    est compatible avec FrozenPattern.skeleton et FrozenPattern.structure
    (même critère de compatibilité structurelle que
     generalize_path_pattern()/kernel2 utilisent déjà pour Gate B —
     pas un critère nouveau inventé pour Gate C)

support_holdout(pattern) =
    nombre de starts admissibles pour lesquels REPLICATED(start) est vrai

Gate C = RETAINED si, simultanément :
  (a) support_holdout(pattern) >= K_min
      (seuil absolu, fixé au moment du benchmark verrouillé — Sec. 16)
  (b) support_holdout(pattern) > percentile_99(distribution du maximum
      sous null CALCULÉE SUR G_holdout_negative[1..N_null], Sec. 6 --
      jamais réutilisation des réplicats nuls de G_train -- INCHANGÉ
      depuis la v0.2)
  (c) couverture (Sec. 11, redéfinie) >= X %
      (valeur fixée au moment du benchmark verrouillé)

sinon FAILED.
```

Un candidat `REJECTED` à Gate B n'est jamais soumis à Gate C
(`NOT_APPLICABLE`) — inchangé depuis la v0.2.

Le contrôle négatif (condition (b)) reste obligatoire et n'est **pas**
affaibli par ce changement : le fait qu'« une continuation existe »
serait, seul, potentiellement trop facile dans un graphe dense — c'est
précisément ce que la comparaison au maximum sous `G_holdout_negative`
empêche. La nouvelle Gate C reste donc :

```text
Gate C = K_min AND dépassement du null AND couverture >= X
avec : réplication = EXISTENCE, pas UNICITÉ.
```

### 10.3 Ce qui ne change pas : `kernel2` reste intouché, conservé comme diagnostic

`kernel2.replay_path_pattern_holdout()` n'est **pas modifié** et
continue d'exister, appelé exactement comme avant. Son résultat
(`REPLAYED` / `AMBIGUOUS` / `FAILED`) est désormais enregistré comme un
**diagnostic secondaire**, `unique_replay_status`, jamais comme le
critère principal de Gate C :

```text
Gate C principal        -> set-valued replication (Sec. 10.2)
diagnostic secondaire   -> unique_replay_status (legacy, kernel2 non modifié)
```

Ceci a une valeur scientifique propre : comparer `support_holdout`
(existence) au taux de `REPLAYED` (unicité) sur les mêmes starts
mesurera directement à quel point la structure découverte dépend de la
multiplicité des continuations — une information que la v0.2 n'aurait
jamais pu produire.

### 10.4 Nouveau module, pas de modification du noyau

La sémantique de rejeu à valeur d'ensemble est portée par un
**adaptateur séparé**, encore à écrire :

```text
p4u1_set_valued_replay_v0_1.py
```

qui réutilise les primitives existantes de `kernel2`
(`discover_paths()` sur `G_holdout` pour énumérer les continuations
admissibles depuis un `start` donné, `generalize_path_pattern()` /
la même logique de compatibilité structurelle que Gate B) mais définit
sa propre fonction de décision `REPLICATED(start)` au lieu de dépendre
de `replay_path_pattern_holdout()`. Discipline déjà appliquée ailleurs
dans ce projet (mécanisme validé + adaptateur expérimental ≠
modification silencieuse du noyau) :

```text
FrozenPattern
     ↓
set-valued replay adapter (p4u1_set_valued_replay_v0_1.py)
     ↓
toutes les continuations admissibles depuis `start`
     ↓
existence d'une trajectoire compatible avec FrozenPattern
     ↓
REPLICATED(start) : bool
```

**Ce module n'est pas encore écrit.** Ce document en fige la
spécification ; l'implémentation vient après le gel de cette v0.3.

### 10.5 Règle anti-circularité — jamais choisir la branche avec le témoin

Point critique explicitement soulevé par le porteur du projet, à ne
jamais violer :

```text
INTERDIT :
    continuations = [A, B, C]
    witness dit que B est la bonne
    → choisir B

OBLIGATOIRE :
    continuations = [A, B, C]
    → déterminer STRUCTURELLEMENT lesquelles satisfont FrozenPattern
    → REPLICATED(start) = (au moins une le satisfait)
    → le témoin n'intervient qu'APRÈS le commit de la décision,
      pour scorer le résultat -- jamais pour le produire.
```

Exactement la même discipline d'aveuglement que P4-T (le témoin ne
sert jamais à sélectionner une branche pendant l'exécution du
mécanisme, seulement à vérifier après coup).

### 10.6 Vocabulaire — niveau rejeu vs niveau décision Gate C, séparés explicitement

Le mot « ambiguïté » portait, dans la v0.2, une connotation d'échec
épistémique (« le moteur ne sait pas choisir ») qui ne correspond plus
à la sémantique retenue (un nœud à plusieurs continuations n'est pas un
échec, c'est une propriété structurelle du graphe). Deux niveaux de
vocabulaire, désormais distincts :

```text
Niveau rejeu (p4u1_set_valued_replay_v0_1.py, par start) :
    NO_PATH     -- aucune continuation admissible ne mène nulle part de compatible
    ONE_PATH    -- exactement une continuation admissible, compatible ou non
    MULTI_PATH  -- plusieurs continuations admissibles (remplace l'usage de
                   « AMBIGUOUS » comme s'il s'agissait d'un échec)

Niveau décision Gate C (par pattern, agrégé sur tous les starts) :
    REPLICATED  -- Sec. 10.2, existence + contrôle négatif + couverture
    FAILED      -- sinon

Niveau diagnostic legacy (kernel2.replay_path_pattern_holdout(), par start,
inchangé, Sec. 10.3) :
    REPLAYED / AMBIGUOUS / FAILED
    (`AMBIGUOUS` garde ici son sens original de kernel2 -- un artefact du
     rejeu à candidat unique, jamais renommé dans kernel2 lui-même)
```

### 10.7 Constat réel trouvé en écrivant les tests de l'adaptateur (2026-09-23) — la contrainte de co-référence est aujourd'hui un no-op

`kernel2.discover_paths()` interdit structurellement de revisiter un
nœud déjà présent dans le chemin en cours de construction (sa propre
fonction `walk()`, vérifiée par lecture directe) — **toute**
`PathRecord` qu'elle retourne a donc des positions deux à deux
DISTINCTES dans son `node_sequence`. Conséquence directe, trouvée en
écrivant les tests de `p4u1_set_valued_replay_v0_1.py`, pas anticipée
par la Sec. 10.2 telle que rédigée ci-dessus : `generalize_path_pattern()`
ne peut donc **jamais** produire un `position_groups` non trivial (une
contrainte de co-référence réelle, taille >= 2) pour un candidat issu
du pipeline de découverte standard — `_position_groups_satisfied` reste
appliqué uniformément à chaque candidat (jamais ignoré silencieusement,
puisque `position_groups` est un champ générique de `PathPattern`),
mais sa branche de rejet est aujourd'hui inatteignable en pratique.
`REPLICATED(start)` se réduit donc, avec les données que ce pipeline
peut produire aujourd'hui, à une pure question d'existence d'AU MOINS
UN chemin de bon squelette — ce qui reste exactement la propriété
recherchée par cette révision (Sec. 10.1) et résout bien la tension de
la v0.2, seulement sans le raffinement de co-référence que le champ
`structure` du `FrozenPattern` pourrait un jour apporter si une future
source de chemins (ou une évolution de `kernel2`) autorisait des
positions répétées. Testé directement sur des `PathRecord` construits
à la main (seule façon de l'exercer aujourd'hui) dans
`tests/test_p4u1_set_valued_replay_v0_1.py`.

## 11. Points d'ancrage du rejeu et couverture — redéfinis

```text
starts_admissibles(G_holdout) = { tout nœud n de G_holdout tel que
    degré_sortant(n) >= 1 }
    -- inchangé depuis la v0.2 : condition purement dimensionnelle et
       structurelle, indépendante du squelette recherché.

Rejoué systématiquement sur TOUS les starts admissibles -- inchangé.
```

**Couverture, redéfinie** pour correspondre à la sémantique
d'existence de Gate C :

```text
coverage =
    ( nombre de starts pour lesquels au moins une trajectoire
      admissible complète correspond au FrozenPattern -- i.e.
      REPLICATED(start) est vrai, Sec. 10.2 )
    /
    ( nombre total de starts admissibles )
```

**Diagnostic supplémentaire, conservé en parallèle** (nouveau par
rapport à la v0.2, demandé explicitement) :

```text
mean_valid_continuations_per_replicating_start =
    moyenne, sur les seuls starts REPLICATED, du nombre de
    continuations admissibles compatibles avec FrozenPattern à chaque
    étape du chemin
```

Une lecture typique attendue pour une structure concentrée (« hub »)
serait `coverage` élevée avec `mean_valid_continuations_per_replicating_start`
également élevée (ex. coverage=80%, avg continuations=4,2) — signature
exactement inverse de celle d'une structure plate (coverage variable,
avg continuations proche de 1).

## 12. `FrozenPattern` — inchangé depuis la v0.2

Voir v0.2 Sec. 12 pour le détail complet (`skeleton`, `depth`,
`structure`, `support_train`, `structural_digest`,
`discovery_metadata`) — non modifié par cette révision, qui ne touche
que le côté holdout/rejeu (Sec. 10-11), jamais la construction ou le
contenu du `FrozenPattern` lui-même.

## 13. `max_paths` — inchangé depuis la v0.2

Voir v0.2 Sec. 13 — non modifié.

## 14. Les trois cas verrouillés — U1 / U2 / U3, attendus mis à jour pour la nouvelle Gate C

```text
U1 = cas positif compositionnel + compétition (Sec. 8)
     Attendu : DISCOVER (motif réel + 3 decoys tous découverts) ->
               SELECT (motif réel RETAINED à Gate B, les 3 decoys
               REJECTED chacun pour sa raison propre) ->
               REPLICATE (motif réel : Gate C = REPLICATED au sens de
               la Sec. 10.2 -- existence d'au moins une continuation
               compatible sur suffisamment de starts, au-delà du null)

U2 = cas dédié « régularité de train uniquement », standalone
     Attendu : DISCOVER possible, SELECT possible (Gate B peut passer
               légitimement), Gate C = FAILED -- FAILED reste le
               résultat attendu même avec la sémantique d'existence :
               le motif n'existe simplement plus, sous aucune
               continuation, dans G_holdout.

U3 = cas de contrôle nul pur
     Attendu : aucun candidat ne satisfait Gate B (inchangé depuis la
               v0.2 -- Gate B n'est pas modifiée par cette révision).
```

Cette séparation reste exactement celle recherchée depuis le début :

```text
U1 : structure concentrée réelle -> B PASS, C REPLICATED
U2 : motif TRAIN-only            -> B peut PASS, C FAILED
U3 : null pur                    -> B FAILED
```

Pour chaque cas, son propre `G_train`/`G_holdout` génère ses propres
réplicats nuls — inchangé depuis la v0.2 (Sec. 14).

## 15. Format du témoin — mis à jour pour la nouvelle Gate C

Même discipline que `p4t_locked_benchmark_witness_v0_1.py`/`_v0_2.py` :
jamais importé avant le commit des prédictions ; vérifié statiquement
et dynamiquement (Sec. 10.5 — le témoin ne doit strictement jamais
influencer la sélection d'une branche de rejeu).

```text
WITNESS[case_id] = {
    candidates: {
        candidate_label: {
            expected_gate_a: DISCOVERED | NOT_DISCOVERED,
            expected_gate_b: RETAINED | REJECTED,
            expected_rejection_reason: (si REJECTED) --
                MIN_DEPTH | SUB_THRESHOLD | NOT_NULL_SIGNIFICANT | None,
            expected_gate_c: REPLICATED | FAILED_AS_EXPECTED | NOT_APPLICABLE,
            expected_coverage_range: (min, max) si applicable,
            expected_unique_replay_diagnostic: (optionnel) --
                distribution attendue de REPLAYED/AMBIGUOUS/FAILED
                (kernel2 legacy, Sec. 10.3), à titre de diagnostic
                seulement, jamais un critère de PASS/FAIL du witness.
        }
        pour chaque candidat nommé du cas (motif réel + chaque decoy)
    },
}
```

## 16. Checklist de pré-enregistrement — mise à jour

```text
1.  modèle nul exact                          (Sec. 6 -- forme fixée, N_null=200 par défaut)
2.  nombre de randomisations null              (N_null, valeur numérique à fixer)
3.  correction comparaisons multiples          (Sec. 7 -- forme fixée)
4.  min_depth / max_depth                      (Sec. 5 -- valeurs déjà fixées : 2 / 3)
5.  max_paths                                  (Sec. 13 -- None recommandé, sinon valeur fixe)
6.  définition exacte du score Gate B          (Sec. 9 -- forme fixée, INCHANGÉE)
7.  seuil Gate B (S_min, percentile)           (Sec. 9 -- valeurs à fixer)
8.  seuil Gate C (K_min, percentile, couverture)(Sec. 10.2/11 -- valeurs à fixer, sémantique REDÉFINIE)
9.  règle de sélection (MULTIPLE_RETAINED)     (Sec. 9 -- forme fixée)
10. règle de choix des starts                  (Sec. 11 -- forme fixée)
11. métrique de réplication (couverture)        (Sec. 11 -- REDÉFINIE : existence, pas unicité ;
                                                  + diagnostic mean_valid_continuations_per_replicating_start)
12. format exact du témoin                     (Sec. 15 -- mis à jour)
13. spécification de l'adaptateur set-valued   (Sec. 10.4 -- forme fixée par ce document,
    replay                                      implémentation p4u1_set_valued_replay_v0_1.py
                                                  encore à écrire)
```

**Séquence obligatoire, mise à jour** :

```text
protocole v0.3 (ce document) — gelé
        ↓
implémentation de l'adaptateur p4u1_set_valued_replay_v0_1.py
   (réutilise kernel2 sans le modifier -- Sec. 10.4)
        ↓
tests déterministes de l'adaptateur (données synthétiques,
   avant tout run réel -- y compris un test qui vérifie
   explicitement la non-circularité, Sec. 10.5)
        ↓
benchmark verrouillé U1/U2/U3 : valeurs numériques 2/7/8/11 fixées
   (checklist ci-dessus) -- AVANT de voir un résultat de holdout
        ↓
run réel contre le benchmark verrouillé
        ↓
documentation du résultat réel, sans lissage, quel qu'il soit
```

## 17. Discipline de nommage — inchangé depuis la v0.2

Toujours **« Unsupervised COMPOSITIONAL PATTERN Discovery »**, jamais
raccourci en « unsupervised discovery ».

## 18. Ce que ce protocole ne prétend PAS démontrer — inchangé depuis la v0.1/v0.2

- Pas la découverte autonome d'une relation totalement inconnue
  (`P4-U.2`, non défini).
- Pas la fermeture d'`E20-D` (4 conditions globales, voir
  `documentation/P4T_Structural_Transformation_Induction_V0_1.md` Sec. 9.1).
- Pas un substitut à un futur `P4-U.2`, à cadrer seulement après les
  résultats réels de P4-U.1.
- **Ajout de cette v0.3** : le passage à une sémantique de réplication
  par existence (Sec. 10.2) ne prétend pas que « plus de continuations
  valides » est en soi une preuve de qualité structurelle — c'est
  justement pour cela que le contrôle négatif (Gate C condition (b))
  et le diagnostic `mean_valid_continuations_per_replicating_start`
  (Sec. 11) restent obligatoires : une couverture élevée obtenue dans
  un graphe simplement dense, sans dépasser le null, resterait `FAILED`.

## 19. Prochaine étape — non commencée par ce document

Une fois cette v0.3 validée explicitement par le porteur du projet :
écrire `p4u1_set_valued_replay_v0_1.py` (Sec. 10.4) avec ses tests
déterministes, PUIS fixer les valeurs numériques de la checklist
(Sec. 16, points 2/7/8/11) et construire le benchmark verrouillé
U1/U2/U3, PUIS lancer le run réel. **Ce document ne code toujours
rien.**

## 20. Séquence complétée (2026-09-23) — valeurs numériques figées, benchmark verrouillé construit et exécuté

La séquence de la Sec. 19 est maintenant intégralement exécutée :

1. **`p4u1_set_valued_replay_v0_1.py` écrit et testé** (13 tests, voir
   `JOURNAL_DE_BORD.md` et `release_manifest.json` pour le détail).
2. **Valeurs numériques figées AVANT toute comparaison contre un
   résultat de holdout verrouillé**, par calibration directe sur des
   corpus jetables (jamais sur le benchmark verrouillé lui-même) :
   voir `documentation/P4U1_Locked_Benchmark_Numeric_Calibration_2026-09-23.md`
   pour l'enregistrement complet, y compris un renoncement corrigé
   (une première structure « hub multi-branches » s'est révélée être
   la même structure « plate » déjà prouvée invariante en Sec. 6/10.7,
   remplacée par une structure « pont unique » où la concentration
   porte sur le produit `in_degree × out_degree` d'UN nœud) et un
   changement de `max_paths` (de `None`, prohibitivement lent en
   pratique par mesure directe, à une limite fixe de 1000, appliquée
   uniformément partout par la Sec. 13). Valeurs retenues :
   `N_null=200`, `S_min=15`, `K_min=15`, `coverage_min=0.10`,
   `max_paths=1000`, `null_percentile=99.0`.
3. **Benchmark verrouillé U1/U2/U3 construit** :
   `p4u1_locked_benchmark_cases_v0_1.py` (train + holdout, aucune
   vérité), `p4u1_locked_benchmark_witness_v0_1.py` (vérité seule,
   jamais importé avant le commit des prédictions),
   `p4u1_locked_benchmark_runner_v0_1.py` (même discipline mécanique
   d'ordre d'import que `p4t_locked_benchmark_runner_v0_1.py` :
   preuve dynamique via `sys.modules`, pas seulement une promesse).
4. **Tests déterministes écrits et passants**
   (`tests/test_p4u1_locked_benchmark_v0_1.py`), y compris la
   vérification statique/dynamique de non-circularité et un test de
   déterminisme (deux exécutions complètes produisent des prédictions
   identiques, horodatage excepté).
5. **Run réel exécuté** : les 7 candidats déclarés (4 pour U1, 1 pour
   U2, 2 pour U3) correspondent TOUS aux 3 gates (A/B/C) attendus par
   le témoin :

```text
U1 REAL_MOTIF       : DISCOVERED, RETAINED, REPLICATED
U1 DECOY_SUB_SEUIL  : DISCOVERED, REJECTED (SUB_THRESHOLD), NOT_APPLICABLE
U1 DECOY_DEPTH1     : NOT_DISCOVERED
U1 DECOY_TRAIN_ONLY : DISCOVERED, RETAINED, FAILED
U2 REAL_MOTIF       : DISCOVERED, RETAINED, FAILED
U3 NULL_CANDIDATE_FORWARD/REVERSE : DISCOVERED, REJECTED (NOT_NULL_SIGNIFICANT), NOT_APPLICABLE
```

C'est la démonstration empirique complète, sur un benchmark verrouillé
(aveugle, aux seuils pré-enregistrés), de la séparation que ce
protocole a été conçu pour produire : Gate B (inchangée) distingue les
structures concentrées (REAL_MOTIF, DECOY_TRAIN_ONLY) des structures
trop petites (DECOY_SUB_SEUIL) ou de mauvaise profondeur (DECOY_DEPTH1)
; Gate C (redéfinie, Sec. 10) distingue ensuite, parmi les structures
concentrées, celle qui existe réellement dans le holdout (REAL_MOTIF)
de celle qui n'existe que dans le train (DECOY_TRAIN_ONLY et U2) ; et
U3 confirme qu'un graphe sans régularité injectée ne dépasse jamais son
propre seuil de significativité statistique.

**Portée exacte de cette démonstration — ce qui n'est PAS établi** :
comme pour P4-T.7 avant sa clôture tierce, ceci est une exécution
auto-administrée (par cet assistant), pas une validation par un tiers
indépendant. Elle établit que le mécanisme (Gates A-C, modèle nul,
correction multi-comparaisons, rejeu à valeur d'ensemble) fonctionne de
façon honnête et non circulaire sur CE benchmark précis, avec CES
seuils précis — pas que ces seuils généralisent à un graphe réel de
provenance inconnue, ni que P4-U.1 est prêt pour une quelconque
utilisation en production. Décision de clôture (validation tierce,
extension à `P4-U.2`, ou autre) : réservée au porteur du projet.
