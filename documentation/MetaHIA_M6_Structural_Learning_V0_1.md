# MetaHIA — M6 — Structural Learning v0.1

## 1. Statut

- M1 : FROZEN
- M2 : STABLE / NON-PROMOTED
- M3 : PASS_INDEPENDENT_SCOPE
- M4 : PASS_INDEPENDENT_SCOPE
- M5 : PASS_INDEPENDENT_SCOPE
- M6 : **IMPLEMENTATION** (local uniquement — pas de validation tierce à ce stade)
- Kernel `kernel2.py` : inchangé par ce module (M6 ne fait qu'importer `structural_signature` et le vocabulaire de M4)

## 2. Objectif

M6 apprend `Rule × Context × Depth × Provenance → distribution d'issues épistémiques`, jamais `Rule = TRUE`. C'est une couche de calibration au-dessus de ce que M4/M5 produisent déjà — pas une nouvelle source de vérité.

```text
M4 (évidence résolue) + M5 (contexte structurel)
        ↓
StructuralOutcomeRecord (rule, context, depth, provenance, outcome)
        ↓
   split_by_rule() -- train / validation / holdout
        ↓
StructuralLearningPolicy.fit(train)  -- versionnée, immuable
        ↓
   predict() -- distribution + base honnête (exact/rule/global/uniforme)
        ↓
brier_score_multiclass() / expected_calibration_error_top_label()
   décomposés par règle, contexte, profondeur, provenance
        ↓
   evaluate_promotion() -- ferme par défaut
```

## 3. Décisions de conception (figées avant l'implémentation, 2026-09-17)

1. **Identité de règle** : `structural_signature(pattern)` pour un PATTERN/SHAPE_PATTERN (Node), ou `path_pattern_structural_form(pattern)` pour un `PathPattern` E20-D.12 — jamais l'identité de référence de l'objet, jamais un nom sémantique. *Élargi le 2026-09-17* : l'alimentation par corpus réel (section 5) a révélé que `generalize_path_pattern()` produit un `PathPattern`, pas un `Node`, et que l'égalité par défaut de `PathPattern` inclut `pattern_id`/`source_path_ids` (qui identifient l'événement de découverte, pas ce que le motif EST structurellement) — corrigé avant de construire le corpus réel dessus, avec 3 nouveaux tests d'invariant dédiés.
2. **Contexte** : grossier par construction — 3 bandes (LOW/MED/HIGH) sur novelty et redundancy = 9 buckets. La `provenance` de l'apprentissage est le vocabulaire fermé de M4 (`GROUNDED_DIRECT`/`GROUNDED_ANALOGY`/`UNGROUNDED_HUMAN`), jamais le tuple `path.provenance` de M5 (unique par chaîne de faits, donc inutilisable comme clé de bucket).
3. **Classes d'issue apprises** : exactement les 3 états stabilisés de M2/M4 — `SUPPORTED`, `CONTRADICTED`, `UNKNOWN`. `DERIVED` est explicitement exclu (état pré-évaluation, pas une issue).
4. **Source du label** : doit venir de la résolution indépendante de M4, jamais de la simple existence d'un pattern dérivé — traduction directe de l'invariant M2 « une dérivation ne peut pas être sa propre preuve ».
5. **Split train/validation/holdout par RÈGLE**, jamais par enregistrement individuel — sinon le holdout ne mesurerait que la mémorisation, pas la généralisation à une règle jamais vue (même philosophie que le holdout E20-D/M3 « opérandes renommés »).
6. **Calibration** : réutilise le vocabulaire déjà établi du projet (Brier, ECE) plutôt que d'en inventer un nouveau. Brier multi-classe est la métrique bloquante de promotion ; ECE top-label est un diagnostic secondaire. Les deux sont décomposés par règle, contexte, profondeur et provenance séparément.
7. **Promotion fermée par défaut** (`evaluate_promotion`) : bloque si le holdout est vide, si le Brier holdout dépasse un seuil absolu, si régression par rapport à la version précédente, ou si un bucket suffisamment peuplé est catastrophiquement mal calibré. Un bucket trop épars (`support < min_bucket_support`) est signalé mais n'entre jamais dans la décision, dans un sens comme dans l'autre.

## 4. Invariants permanents testés

`tests/test_m6_structural_learning_invariants_v0_1.py` (24 tests) :
- vocabulaires fermés (outcome/provenance), `DERIVED` toujours rejeté ;
- identité de règle structurelle (deux instances différentes du même pattern → même bucket ; deux patterns différents → buckets différents) ;
- `split_by_rule` ne scinde jamais une règle entre deux partitions, et est déterministe à seed fixée ;
- `version` de la politique n'avance que via `fit()`, jamais via `predict()` ;
- `predict()` ne fabrique jamais de confiance : repli honnête bucket exact → règle seule → prior global → uniforme (0 support), jamais l'inverse ;
- Brier borné [0,2], nul pour une politique parfaitement correcte ;
- `calibration_report` signale explicitement les buckets à données insuffisantes ;
- `evaluate_promotion` ferme sur holdout vide, seuil absolu dépassé, régression, bucket catastrophique suffisamment peuplé — et ne bloque jamais sur un bucket trop épars pour être fiable.

## 5. Alimentation par corpus réel M4/M5 (addendum 2026-09-17)

`m6_corpus_from_m4_m5_v0_1.py` fait tourner le pipeline complet pour de vrai, plutôt que
de construire des `StructuralOutcomeRecord` à la main par invariant :

```text
corpus/family_tree_facts_v0_1.json (22 faits réels, déjà tracés indépendamment
                                     plus tôt dans le projet)
        ↓
kernel2.build_structural_graph / discover_paths          (réel)
        ↓
kernel2.generalize_path_pattern                          (réel, E20-D.12)
        ↓
e20d_cognitive_control_v0_1.build_candidate / score_candidate  (réel, E20-D.19)
        ↓
m4_cold_start_evidence_v0_1.acquire_cold_start           (réel, M4)
        ↓
StructuralOutcomeRecord
```

**Indépendance de la preuve** : `discovery_facts` (16 faits) sont les seuls utilisés pour
découvrir/généraliser un pattern. `evidence_facts` (6 faits, disjoints) sont la seule
source que `acquire_cold_start()` a le droit de consulter — la même discipline de holdout
que E20-D/M3 (« généralisation sur opérandes jamais vus »), réutilisée ici comme véritable
source de preuve M4, pas comme simple assertion de test.

**Résultat réel** (vérifié par exécution, pas supposé) : sur 28 patterns candidats (1 et 2
sauts) découverts dans les faits d'entraînement, **seuls 2 trouvent une preuve** dans les
faits de preuve — `MERE_DE` et `FILLE_DE`, les deux seuls types de relation dont
`evidence_facts` contient effectivement une arête sortante correspondante. Les 26 autres
sont explicitement exclus (« no admissible evidence from holdout replay »), jamais
fabriqués. Les 2 enregistrements obtenus sont `SUPPORTED` / `GROUNDED_DIRECT`, profondeur 1.

**Limite honnête découverte, pas contournée** : le mécanisme de preuve par rejeu
(`replay_path_pattern_holdout`) ne peut, par construction, produire que `REPLAYED`
(toujours une confirmation directe, puisque le graphe de rejeu est bâti uniquement à partir
des faits de preuve réels) ou `NOT_FOUND`/`AMBIGUOUS` (aucune preuve) — jamais une
prédiction rejouée mais fausse. Sur ce corpus familial interne cohérent, aucun `CONTRADICTED`
réel n'est donc atteignable. `demo_contradicted_case()` vérifie séparément, avec un fait
délibérément conflictuel, que le même mécanisme réel atteint bien `CONTRADICTED` quand un
conflit existe réellement — **résultat explicitement écarté des statistiques du corpus réel**.

**Avec seulement 2 règles réelles, `split_by_rule` ne peut produire aucun holdout** aux
fractions par défaut (0,2/0,2) — `evaluate_promotion` refuse alors correctement la
promotion (`EMPTY_HOLDOUT`), plutôt que de promouvoir sur un holdout vide. C'est le même
garde-fou que `test_promotion_blocked_on_empty_holdout` teste synthétiquement, confirmé ici
sur des données réelles authentiquement insuffisantes — pas un bug, une limite de taille de
corpus à lever en alimentant M6 avec un corpus réel plus grand (travail futur, non fait ici
pour ne pas fabriquer un résultat de calibration que les données ne permettent pas
d'établir).

## 6. Validation tierce et étape INDEPENDENT HOLDOUT (addendum 2026-09-17)

Le protocole `MetaHIA_ThirdParty_Validation_Protocol_M6_V0_1.md` (9 cas critiques C01–C09,
gelé sur le corpus v0.1) a été exécuté en jouant le rôle du tiers indépendant, dans un
**clone Git frais**, pas la copie de travail de développement. **PASS_INDEPENDENT_SCOPE** :
13/13 cas critiques, 319/319 tests complets, reproductible sur deux exécutions. Une
divergence a été trouvée puis corrigée : les hashes gelés ne correspondaient pas à ceux
d'un `git clone` standard sous Windows (`core.autocrlf=true` convertit en CRLF au
checkout) — contenu identique, seule la matérialisation différait. Corrigé par
`.gitattributes` (`* text=auto eol=lf`), reconfirmé sur un troisième clone frais.

**Rappel de gouvernance** : cette exécution, bien que rigoureuse, reste auto-exécutée —
elle ne clôt pas la « independent gate » au sens strict (un tiers réellement externe reste
requis pour cela), exactement comme documenté dans le protocole lui-même.

### Étape suivante de la trajectoire : INDEPENDENT HOLDOUT

Le corpus v0.1 (22 faits, gelé, ne pas modifier — il est référencé par le protocole ci-dessus)
ne permet aucun holdout non vide (2 règles réelles seulement). `corpus/family_tree_facts_v0_2.json`
l'étend avec deux branches familiales indépendantes supplémentaires (même nature de données
qu'en v0.1, pas une nouvelle source) :

| Mesure | v0.1 | v0.2 |
|---|---|---|
| Patterns candidats | 28 | 69 |
| Règles avec preuve réelle | 2 | 23 |
| Exclus (aucune preuve) | 26 | 46 |
| Split train/val/holdout | impossible (holdout vide) | 13/5/5, non vide |
| Brier holdout | — | 0,0 |

**Honnêteté sur ce résultat** : un holdout non vide est nécessaire mais pas suffisant pour
une mesure de calibration significative. Le Brier de 0,0 ici est un **cas dégénéré**, pas
une preuve de compétence de calibration — parce que la totalité des 23 enregistrements ont
la même issue (`SUPPORTED`) et la même provenance (`GROUNDED_DIRECT`). C'est une propriété
structurelle du mécanisme de preuve par rejeu (déjà identifiée section 5) : sur un corpus
familial interne cohérent, il ne peut produire que `SUPPORTED` ou aucune preuve — jamais un
`CONTRADICTED` ni un `UNKNOWN` avec preuve réelle, quelle que soit la taille du corpus. Une
démonstration de calibration réellement discriminante nécessite un **mécanisme de preuve
plus riche** (par exemple relié à un vérificateur sémantique réel ou à une annotation
humaine indépendante), pas un corpus plus grand du même type — question ouverte documentée,
pas laissée implicite. Testé et rendu explicite par
`tests/test_m6_real_corpus_v0_2_holdout_v0_1.py`.

## 7. Résultat local

324 tests passés (277 hérités + 24 invariants M6 + 5 intégration corpus réel v0.1 + 13
validation critique C01–C09 + 5 holdout corpus v0.2), 0 échec, 0 régression.

## 8. Hors périmètre de cette version

- Validation par un tiers réellement externe (l'auto-exécution du protocole ne clôt pas la
  independent gate — voir section 6) ;
- un mécanisme de preuve capable de produire un `CONTRADICTED`/`UNKNOWN` réel et non
  dégénéré — nécessaire pour une mesure de calibration discriminante, voir section 6 ;
- choix définitif des seuils de promotion (`brier_threshold`, `per_bucket_brier_threshold`) — laissés comme paramètres explicites de l'appelant, pas de valeur par défaut imposée silencieusement ;
- réévaluation du gate M2/Phase 2 — M6 est un chantier de recherche K3 isolé, sans lien avec le gate empirique de la Phase 2 du dépôt de production.
