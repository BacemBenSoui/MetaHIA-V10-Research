# MetaHIA V10 — P4-U.1 v0.2 : découverte non supervisée de compositions structurelles (protocole verrouillé, avant tout code)

## 0. Statut et rapport à la v0.1

```text
P4-U.1 = OPEN_RESEARCH
scope  = UNSUPERVISED COMPOSITIONAL PATTERN DISCOVERY
         (jamais raccourci en « unsupervised discovery » — Sec. 11)
exclu  = NOT_AUTONOMOUS_RELATION_DISCOVERY
```

Remplace intégralement
`documentation/P4U1_Unsupervised_Compositional_Pattern_Discovery_V0_1.md`
(conservé pour l'historique de la revue, non implémentable tel quel).
La v0.1 posait la bonne architecture générale et refusait déjà le
critère naïf « le motif injecté est retrouvé », mais une revue
méthodologique du porteur du projet (2026-09-23) a identifié trois
points réellement bloquants avant tout code :

1. le modèle nul (« même topologie ») n'était pas défini précisément ;
2. aucune correction pour comparaisons multiples n'était prévue —
   avec des milliers de squelettes candidats, un faux positif devient
   presque garanti sans elle ;
3. Gate B et Gate C restaient qualitatives (« seuil pré-enregistré »,
   « doit rester observable ») plutôt que des scores et seuils
   explicites.

Ce document corrige les trois, plus sept renforcements demandés dans la
même revue (compétition entre candidats dans U1, clarification U1/U2/U3
vs le rôle transversal du modèle nul, règle de choix des points
d'ancrage du rejeu, `structural_digest`, déterminisme de `max_paths`,
discipline de nommage, format du témoin). **Toujours aucun code écrit**
— ce document reste un protocole, pas une implémentation.

**Toujours aucun code écrit.** La discipline « protocole avant
implémentation » (déjà appliquée à P4-T) s'applique avec d'autant plus
de rigueur ici que P4-U.1 est un axe entièrement nouveau, créé par ces
deux documents, pas un jalon déjà défini par une roadmap antérieure.

## 1. Origine et cadrage — inchangé depuis la v0.1

`P4-U` n'existe nulle part dans l'historique du projet avant ces deux
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

## 2. Objectif exact — renforcé

> Découvrir, sans cible désignée, une composition structurelle
> récurrente dans un graphe à relations déjà nommées, **et démontrer
> statistiquement** que cette découverte est distinguée du bruit ET de
> l'effet des comparaisons multiples — pas seulement fréquente, pas
> seulement plus fréquente qu'un seuil arbitraire.

La v0.1 posait déjà que « le squelette est retrouvé » est un critère
insuffisant. Cette v0.2 ajoute la raison statistique précise pourquoi :
`discover_paths()` peut énumérer des milliers de squelettes candidats
(Sec. 6) — sous cette échelle, il est **normal** qu'au moins un
candidat paraisse exceptionnel par pur hasard, même si chacun,
individuellement, est peu probable sous le bruit. Ignorer cet effet
transformerait ce protocole en générateur de faux positifs garantis.

## 3. Entrée et interdits — inchangé depuis la v0.1

**Entrée, uniquement** : un graphe (nœuds + arêtes déjà étiquetées).

**Interdit** : relation cible, couple source→cible, squelette cible,
hypothèse de transformation, dictionnaire sémantique.

## 4. Architecture cible

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
         Gate B quantitative (Sec. 9)
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
    replay_path_pattern_holdout() sur TOUS
       les starts admissibles
                     │
        G_holdout_negative[1..N]
        (même null model, dérivé de G_holdout)
                     │
         Gate C quantitative (Sec. 10)
```

Réutilise strictement `kernel2.discover_paths()`,
`kernel2.generalize_path_pattern()`, `kernel2.replay_path_pattern_holdout()`
(aucune modification). Un module minimal nouveau porte
`group_by_skeleton()`, le modèle nul, les scores de Gates B/C, et
`freeze()`. **Toujours pas de réactivation** des 5 fichiers `e20d_*`
morts (confirmé sans appelant hors tests, 2026-09-23).

## 5. `min_depth` imposé explicitement

```text
min_depth = 2   (obligatoire — sans cette borne, un chemin de longueur 1,
                 ex. A --MERE_DE--> B, serait accepté et le protocole
                 mesurerait de la fréquence d'arête simple, pas de la
                 composition)
max_depth = 3   (pour le premier benchmark verrouillé — raisonnable :
                 A→R1→B ou A→R1→C→R2→B)
```

Tout candidat de profondeur `< min_depth` est rejeté avant même le
calcul de support — pas seulement découragé par le score. Le témoin
(Sec. 15) doit inclure explicitement un ou plusieurs candidats attendus
rejetés **uniquement** pour cette raison, pour vérifier que le filtre
fonctionne (voir le decoy de profondeur, Sec. 8).

## 6. Modèle nul — défini précisément, pas juste « même topologie »

La v0.1 disait « conserver les marges pertinentes (fréquences
d'étiquettes, topologie choisie) » — trop ambigu : conserver exactement
la topologie risquerait de conserver précisément les chemins que le
modèle nul doit détruire.

**Modèle nul retenu : configuration model stratifié par étiquette**
(randomisation de graphe à degré préservé, une technique standard de
science des réseaux — pas inventée ad hoc pour ce protocole) :

```text
Préservé exactement par null_generator(G, seed) :
  - |V| (nombre de nœuds)
  - |E| (nombre d'arêtes)
  - distribution des étiquettes (compte par relation, ex. MERE_DE: 12,
    TRAVAILLE_DANS: 8, ...)
  - degré entrant/sortant par nœud, PAR ÉTIQUETTE quand le modèle
    d'observation le permet (objectif ; si structurellement
    inatteignable pour une configuration donnée, documenté
    explicitement comme telle, jamais approximé silencieusement)

Procédure : pour chaque étiquette séparément, un double-edge-swap
(permutation d'extrémités d'arêtes par paires, répétée, préservant le
degré de chaque nœud pour cette étiquette) — déterministe par seed.
```

**Nombre de réplications** : `N_null = 200` par défaut (même ordre de
grandeur que les 200-500 tirages Monte-Carlo déjà utilisés dans ce
projet pour le banc de convergence M6-INTERNAL,
`m6_internal_regularized_diagnosis_v0_1.py`) — assez pour qu'un
percentile 99 soit interprétable, pas arbitrairement plus. Seeds
`0..N_null-1`, déterministes et reproductibles, **fixés dans le
protocole avant toute construction de graphe réel**, jamais ajustés
après avoir vu un résultat.

**Le modèle nul est un mécanisme transversal de contrôle statistique,
pas un troisième type de jeu de données** (correction de la v0.1,
Sec. 13 de la revue) : chaque cas (U1, U2, U3 — Sec. 14) génère ses
propres `G_negative[1..N_null]` à partir de son propre `G_train`, et
`G_holdout` génère séparément ses propres `G_holdout_negative[1..N_null]`
pour Gate C (Sec. 10) — jamais de réutilisation croisée des réplicats
d'un côté pour l'autre.

## 7. Correction pour comparaisons multiples — statistique du maximum

Point le plus important ajouté par cette v0.2. Comparer
`support(candidat) > percentile_null(candidat)` candidat par candidat
ignore l'effet : « parmi des milliers de squelettes essayés, il est
normal qu'au moins un paraisse extraordinaire par hasard ». Ce
protocole utilise donc une correction de type contrôle du taux d'erreur
familial par statistique du maximum (« max-statistic » / méthode de
type Westfall-Young — une méthode standard, pas inventée ici) :

```text
Pour chaque réplicat G_negative_i (i = 1..N_null) :
    candidats_i = group_by_skeleton(discover_paths(G_negative_i, min_depth=2, max_depth=3))
    max_support_null_i = max(support(c) pour c dans candidats_i)

Distribution null du maximum : {max_support_null_1, ..., max_support_null_N_null}

Pour un candidat observé de support support_obs (dans G_train réel) :
    p_valeur_empirique = (1 + compte(max_support_null_i >= support_obs)) / (N_null + 1)
    seuil équivalent : support_obs > percentile_99(distribution du maximum sous null)
```

Le candidat est comparé à la distribution du **maximum par tirage nul**,
jamais à sa propre distribution nulle candidat-par-candidat — c'est ce
qui rend la comparaison robuste au nombre de squelettes essayés.

## 8. Compétition entre candidats — U1 n'est plus un cas trivial

Dans la v0.1, U1 injectait un seul motif fortement supporté — la
découverte y devenait presque triviale et ne testait pas réellement la
**sélection**. U1 doit désormais contenir, en plus du vrai motif :

```text
U1 = { motif réel,
       decoy_train_only  -- fréquent dans G_train, non reproductible
                             dans G_holdout (le même mécanisme que U2,
                             intégré ici comme concurrent)
       decoy_sub_seuil    -- modérément fréquent, en dessous du seuil
                             Gate B (teste que le rejet fonctionne,
                             pas seulement que la sélection accepte)
       decoy_depth1       -- une régularité réelle mais de profondeur 1
                             (teste que le filtre min_depth, Sec. 5,
                             la rejette même si son support serait
                             par ailleurs suffisant) }
```

Le pipeline doit démontrer `DISCOVER + SELECT`, jamais seulement
`SEARCH + MATCH` : retenir le motif réel et rejeter les trois decoys,
chacun pour une raison distincte et vérifiable séparément par le
témoin (Sec. 15).

## 9. Gate B — quantitative

```text
Score_discovery(candidat) = support_train(candidat)
   (le même score utilisé pour la comparaison au maximum sous null, Sec. 7
    — pas un score différent inventé séparément)

Gate B = RETAINED si, simultanément :
  (a) support_train(candidat) >= S_min
      (support absolu minimal — valeur numérique fixée au moment de la
       construction du benchmark verrouillé, Sec. 16, jamais après avoir
       vu le holdout)
  (b) support_train(candidat) > percentile_99(distribution du maximum
      sous null, Sec. 7)
  (c) depth(candidat) >= min_depth (Sec. 5)
  (d) generalize_path_pattern(candidat) ne renvoie pas None (compatibilité
      structurelle stricte déjà vérifiée par kernel2, aucune modification)

sinon REJECTED.
```

Si plusieurs squelettes distincts satisfont (a)-(d) simultanément, le
résultat est rapporté explicitement comme `MULTIPLE_RETAINED` — jamais
fusionné arbitrairement ni réduit silencieusement à un seul (contraste
volontaire avec P4-T.3's `select_hypothesis()`, qui choisit UN
hypothèse par rang de complexité minimal ; ici, rien n'impose qu'un
seul squelette structurellement valide et statistiquement significatif
existe, donc rien n'impose de n'en retenir qu'un).

## 10. Gate C — quantitative, symétrique à Gate B

```text
Réplication (Gate C) = REPLICATED si, simultanément :
  (a) support_holdout(pattern) >= K_min
      (seuil absolu, fixé au moment du benchmark verrouillé)
  (b) support_holdout(pattern) > percentile_99(distribution du maximum
      sous null CALCULÉE SUR G_holdout_negative[1..N_null], Sec. 6 --
      jamais réutilisation des réplicats nuls de G_train)
  (c) couverture des points d'ancrage (Sec. 11) >= X %
      (valeur fixée au moment du benchmark verrouillé)

sinon FAILED.
```

Structure délibérément symétrique à Gate B (même statistique,
appliquée côté holdout) — un candidat REJECTED à Gate B n'est jamais
soumis à Gate C (`NOT_APPLICABLE`).

## 11. Points d'ancrage du rejeu — règle pré-enregistrée, jamais choisie après coup

```text
starts_admissibles(G_holdout) = { tout nœud n de G_holdout tel que
    degré_sortant(n) >= 1 }
    -- une condition purement dimensionnelle et structurelle,
       indépendante du squelette recherché ; jamais une condition liée
       au label ou à la position du motif ciblé.

Rejoué systématiquement sur TOUS les starts admissibles (jamais un
sous-ensemble choisi à la main -- choisir manuellement les starts qui
font réussir le motif serait une sélection a posteriori déguisée).

couverture = (nombre de starts produisant le pattern via
              replay_path_pattern_holdout) / (nombre total de starts
              admissibles)
```

## 12. `FrozenPattern` — contrat renforcé

```text
FrozenPattern
├── skeleton              -- operator_sequence + direction_sequence
│                            (kernel2.PathPattern porte ces deux champs)
├── depth
├── structure              -- position_groups (intersection déjà
│                             calculée par generalize_path_pattern())
├── support_train
├── structural_digest      -- NOUVEAU : sha256(repr((skeleton, depth,
│                             structure))) -- MÊME construction que
│                             p4t_structural_transformation_induction_v0_1.freeze()'s
│                             propre `structural_digest`
│                             (`sha256(repr((family, sigma)))`), qui
│                             fingerprints la transformation elle-même,
│                             jamais les lignes d'entraînement -- réutilisation
│                             directe de cette discipline déjà validée,
│                             pas une nouvelle notion.
│                             Invariant à : (a) l'identité des nœuds
│                             d'entraînement, (b) l'identité des chemins
│                             d'entraînement (`source_path_ids`), (c)
│                             l'ordre des observations d'entraînement
│                             équivalentes.
└── discovery_metadata     -- N_null, seeds utilisés, S_min, seuil
                              percentile, min_depth/max_depth, max_paths,
                              horodatage
```

**Explicitement exclu** (inchangé depuis la v0.1, confirmé nécessaire
par lecture directe de `kernel2.PathPattern`, qui porte bien un champ
`source_path_ids`) :

- `source_path_ids`
- toute identité de nœud d'entraînement (`NodeRef`, `node_id`)
- toute information de holdout, sous quelque forme, avant Gate C

## 13. `max_paths` — déterminisme, jamais de limite asymétrique

```text
Premier benchmark verrouillé : max_paths = None si le graphe reste
   assez petit pour une énumération exhaustive (recommandé).
Sinon : une limite fixe, IDENTIQUE sur G_train ET tous les
   G_negative[1..N_null] du même cas (et sur G_holdout et tous les
   G_holdout_negative[1..N_null]) -- jamais une limite différente selon
   le graphe, ce qui biaiserait la comparaison au null en faveur ou en
   défaveur d'un côté selon l'ordre d'énumération.
Ordre d'énumération : celui, déjà déterministe, de
   kernel2.discover_paths() -- non modifié.
```

## 14. Les trois cas verrouillés — U1 / U2 / U3, redéfinis

```text
U1 = cas positif compositionnel + compétition (Sec. 8)
     Attendu : DISCOVER (motif réel + 3 decoys tous découverts comme
               candidats) -> SELECT (motif réel RETAINED, les 3 decoys
               REJECTED chacun pour sa raison propre) -> REPLICATE
               (motif réel Gate C = REPLICATED)

U2 = cas dédié « régularité de train uniquement », standalone
     (distinct des decoys intégrés à U1, pour isoler ce mode d'échec
     sans la compétition d'U1)
     Attendu : DISCOVER possible, SELECT possible (Gate B peut passer
               légitimement -- le motif est réellement fréquent et
               significatif DANS le train), Gate C = FAILED. **FAILED
               est le résultat attendu, pas un échec du protocole** --
               un runner qui « corrigerait » ce résultat serait
               disqualifié par construction (même principe que P4-T
               Gate E).

U3 = cas de contrôle nul pur
     G_train lui-même est un graphe nul (aucune régularité injectée
     nulle part -- généré par la même procédure que null_generator(),
     Sec. 6, mais traité comme le "vrai" G_train de ce cas).
     Attendu : aucun candidat ne satisfait Gate B -- formulation précise
               retenue : le meilleur candidat de ce graphe ne dépasse
               jamais percentile_99(distribution du maximum sous null)
               calculée sur SES PROPRES réplicats G_negative[1..N_null]
               -- pas de comparaison à U1/U2, chaque cas est évalué
               contre son propre null.
```

Pour chaque cas (U1, U2, U3), son propre `G_train` génère ses propres
`G_negative[1..N_null]`, et son propre `G_holdout` (quand applicable)
génère ses propres `G_holdout_negative[1..N_null]` — jamais de
réplicats partagés entre cas.

## 15. Format du témoin — verrouillage formel

Même discipline que `p4t_locked_benchmark_witness_v0_1.py`/`_v0_2.py` :
jamais importé avant le commit des prédictions ; vérifié statiquement
(absence de mention dans le code de découverte) et dynamiquement
(absence de `sys.modules` au moment du commit).

Pour chaque cas, le témoin enregistre, **avant toute exécution du
runner** :

```text
WITNESS[case_id] = {
    candidates: {
        candidate_label: {
            expected_gate_a: DISCOVERED | NOT_DISCOVERED,
            expected_gate_b: RETAINED | REJECTED,
            expected_rejection_reason: (si REJECTED) --
                MIN_DEPTH | SUB_THRESHOLD | NOT_NULL_SIGNIFICANT | None,
            expected_gate_c: REPLICATED | FAILED_AS_EXPECTED | NOT_APPLICABLE,
        }
        pour chaque candidat nommé du cas (motif réel + chaque decoy)
    },
    expected_coverage_range: (min, max) si applicable,
}
```

## 16. Checklist de pré-enregistrement — à figer avant le benchmark verrouillé, jamais après

Cette v0.2 fixe la FORME de chaque score/seuil ; les valeurs numériques
elles-mêmes doivent être choisies au moment de la construction du
benchmark verrouillé réel (`p4u1_locked_benchmark_*_v0_1.py`, non
encore écrit), **avant** toute exécution du runner sur ce benchmark,
jamais ajustées après avoir vu un résultat de holdout — exactement la
même discipline de pré-enregistrement déjà appliquée aux seuils de
`evaluate_promotion()` (M6) et aux constantes de décision d'E20-D.19
(P4-T.6) :

```text
1.  modèle nul exact                         (Sec. 6 -- forme fixée, N_null=200 par défaut)
2.  nombre de randomisations null              (N_null, valeur numérique à fixer)
3.  correction comparaisons multiples          (Sec. 7 -- forme fixée)
4.  min_depth / max_depth                      (Sec. 5 -- valeurs déjà fixées : 2 / 3)
5.  max_paths                                  (Sec. 13 -- None recommandé, sinon valeur fixe)
6.  définition exacte du score                 (Sec. 9/10 -- forme fixée)
7.  seuil Gate B (S_min, percentile)           (Sec. 9 -- valeurs à fixer)
8.  seuil Gate C (K_min, percentile, couverture)(Sec. 10 -- valeurs à fixer)
9.  règle de sélection (MULTIPLE_RETAINED)     (Sec. 9 -- forme fixée)
10. règle de choix des starts                  (Sec. 11 -- forme fixée)
11. métrique de réplication (couverture)        (Sec. 11 -- forme fixée)
12. format exact du témoin                     (Sec. 15 -- forme fixée)
```

**Séquence obligatoire** :

```text
protocole v0.2 (ce document) — gelé
        ↓
benchmark verrouillé : valeurs numériques 2/7/8 fixées (checklist ci-dessus)
        ↓
implémentation (module minimal + cas U1/U2/U3)
        ↓
tests déterministes (données synthétiques, avant tout run réel)
        ↓
run réel contre le benchmark verrouillé
        ↓
documentation du résultat réel, sans lissage, quel qu'il soit
```

## 17. Discipline de nommage — confirmée, non renégociable

Toujours **« Unsupervised COMPOSITIONAL PATTERN Discovery »**, jamais
raccourci en « unsupervised discovery » dans un futur document — un
raccourci gonflerait artificiellement le statut scientifique après un
résultat positif, exactement le risque que ce protocole existe pour
éviter.

## 18. Ce que ce protocole ne prétend PAS démontrer — inchangé depuis la v0.1

- Pas la découverte autonome d'une relation totalement inconnue
  (`P4-U.2`, non défini).
- Pas la fermeture d'`E20-D` (4 conditions globales, voir
  `documentation/P4T_Structural_Transformation_Induction_V0_1.md` Sec. 9.1).
- Pas un substitut à un futur `P4-U.2`, à cadrer seulement après les
  résultats réels de P4-U.1.

## 19. Prochaine étape — non commencée par ce document

Une fois cette v0.2 validée explicitement par le porteur du projet :
fixer les valeurs numériques de la checklist (Sec. 16, points 2/7/8),
puis implémenter dans l'ordre déjà annoncé (module minimal → cas
verrouillés U1/U2/U3 → tests déterministes → run réel). **Ce document
ne code toujours rien.**
