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

1. **Identité de règle** : `structural_signature(pattern)` — jamais l'identité de référence de l'objet, jamais un nom sémantique.
2. **Contexte** : grossier par construction — 3 bandes (LOW/MED/HIGH) sur novelty et redundancy = 9 buckets. La `provenance` de l'apprentissage est le vocabulaire fermé de M4 (`GROUNDED_DIRECT`/`GROUNDED_ANALOGY`/`UNGROUNDED_HUMAN`), jamais le tuple `path.provenance` de M5 (unique par chaîne de faits, donc inutilisable comme clé de bucket).
3. **Classes d'issue apprises** : exactement les 3 états stabilisés de M2/M4 — `SUPPORTED`, `CONTRADICTED`, `UNKNOWN`. `DERIVED` est explicitement exclu (état pré-évaluation, pas une issue).
4. **Source du label** : doit venir de la résolution indépendante de M4, jamais de la simple existence d'un pattern dérivé — traduction directe de l'invariant M2 « une dérivation ne peut pas être sa propre preuve ».
5. **Split train/validation/holdout par RÈGLE**, jamais par enregistrement individuel — sinon le holdout ne mesurerait que la mémorisation, pas la généralisation à une règle jamais vue (même philosophie que le holdout E20-D/M3 « opérandes renommés »).
6. **Calibration** : réutilise le vocabulaire déjà établi du projet (Brier, ECE) plutôt que d'en inventer un nouveau. Brier multi-classe est la métrique bloquante de promotion ; ECE top-label est un diagnostic secondaire. Les deux sont décomposés par règle, contexte, profondeur et provenance séparément.
7. **Promotion fermée par défaut** (`evaluate_promotion`) : bloque si le holdout est vide, si le Brier holdout dépasse un seuil absolu, si régression par rapport à la version précédente, ou si un bucket suffisamment peuplé est catastrophiquement mal calibré. Un bucket trop épars (`support < min_bucket_support`) est signalé mais n'entre jamais dans la décision, dans un sens comme dans l'autre.

## 4. Invariants permanents testés

`tests/test_m6_structural_learning_invariants_v0_1.py` (21 tests) :
- vocabulaires fermés (outcome/provenance), `DERIVED` toujours rejeté ;
- identité de règle structurelle (deux instances différentes du même pattern → même bucket ; deux patterns différents → buckets différents) ;
- `split_by_rule` ne scinde jamais une règle entre deux partitions, et est déterministe à seed fixée ;
- `version` de la politique n'avance que via `fit()`, jamais via `predict()` ;
- `predict()` ne fabrique jamais de confiance : repli honnête bucket exact → règle seule → prior global → uniforme (0 support), jamais l'inverse ;
- Brier borné [0,2], nul pour une politique parfaitement correcte ;
- `calibration_report` signale explicitement les buckets à données insuffisantes ;
- `evaluate_promotion` ferme sur holdout vide, seuil absolu dépassé, régression, bucket catastrophique suffisamment peuplé — et ne bloque jamais sur un bucket trop épars pour être fiable.

## 5. Résultat local

298 tests passés (277 hérités + 21 nouveaux), 0 échec, 0 régression.

## 6. Hors périmètre de cette version

- Validation tierce indépendante (étape suivante de la trajectoire, comme pour M3/M4/M5) ;
- corpus réel M4/M5 → M6 (ce v0.1 est testé sur des enregistrements synthétiques construits pour chaque invariant, pas encore sur une trace de production) ;
- choix définitif des seuils de promotion (`brier_threshold`, `per_bucket_brier_threshold`) — laissés comme paramètres explicites de l'appelant, pas de valeur par défaut imposée silencieusement ;
- réévaluation du gate M2/Phase 2 — M6 est un chantier de recherche K3 isolé, sans lien avec le gate empirique de la Phase 2 du dépôt de production.
