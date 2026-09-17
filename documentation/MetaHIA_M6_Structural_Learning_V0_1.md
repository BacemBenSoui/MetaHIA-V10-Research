# MetaHIA — M6 — Structural Learning v0.1

## 1. Statut

- M1 : FROZEN
- M2 : STABLE / NON-PROMOTED
- M3 : PASS_INDEPENDENT_SCOPE
- M4 : PASS_INDEPENDENT_SCOPE
- M5 : PASS_INDEPENDENT_SCOPE
- M6 : **VALIDATED** (2026-09-17, clôturé explicitement par le porteur du projet sur preuves
  d'exécution externes — voir Sec. 6 et `JOURNAL_DE_BORD.md`)
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

**Divergence de hash trouvée par un vrai tiers externe, corrigée (addendum 2026-09-17,
postérieur à l'auto-exécution ci-dessus)** : un premier retour d'exécution par un tiers
réellement externe sur le paquet zip envoyé (commit `613c4cd`) a signalé que le hash gelé de
`m6_corpus_from_m4_m5_v0_1.py` (`f075f730...`) ne correspondait pas au fichier réellement
présent (`d78ebf1b...`). Cause identifiée par diff Git direct : le commit `634126a`
(« M6 INDEPENDENT HOLDOUT step ») avait par erreur ajouté une constante de confort
(`CORPUS_PATH_V0_2`) à ce fichier déjà gelé par le protocole, au lieu de la placer ailleurs —
une violation réelle de la discipline « un fichier gelé référencé par un protocole ne se
touche plus », commise après l'auto-exécution PASS_INDEPENDENT_SCOPE ci-dessus (donc sans
invalider ce PASS-là, obtenu avant la dérive), mais bien présente dans le paquet remis au
tiers. Aucun test n'était affecté (changement purement additif : une constante + `__all__`
mis à jour, aucune logique modifiée) — mais l'intégrité du gel, elle, était réellement rompue,
et le tiers a eu raison de refuser de qualifier son exécution de validation indépendante tant
que ce n'était pas réconcilié. Corrigé par retrait exact de l'ajout (`git show` du commit
d'origine du protocole, diff vérifié à deux lignes près, hash restauré et confirmé
`f075f730...`) ; le test qui utilisait cette constante l'importe désormais localement au lieu
de la lire dans le fichier gelé. Les 13 hashes des deux protocoles M6 (v0.1 et v0.2) ont été
revérifiés un par un après correctif — tous conformes. Un paquet zip corrigé a été renvoyé,
revérifié en conditions isolées puis depuis le zip final avant envoi.

Un second retour indépendant (environnement `Python 3.11.2` / `pytest 7.2.1`, distinct des
deux précédents) a ensuite confirmé **338/338** sur ce paquet.

**Clôture (2026-09-17)** : sur la base de ces deux exécutions externes réelles — 13/13, 7/7,
10/10, 24/24, 338/338 répété deux fois, 0 fichier modifié, une divergence d'intégrité trouvée
puis corrigée et revérifiée, et une confirmation dans un second environnement indépendant —
**Bacem Ben Soui (porteur du projet) a explicitement validé la clôture de cette étape.**
Détail complet dans `JOURNAL_DE_BORD.md`. **Statut M6 : `VALIDATED`** (base v0.1 + mécanisme
non dégénéré v0.2). Cette clôture est une décision de gouvernance du porteur de projet, pas
une auto-déclaration de l'assistant.

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

## 7. Mécanisme de preuve non dégénéré (addendum 2026-09-17)

Option retenue (discutée et choisie explicitement avant implémentation, parmi trois : corpus
de vérification adversarial / vérificateur de production / annotation humaine) : **corpus de
vérification adversarial**, seule option réalisable dans le périmètre isolé du dépôt sans
rouvrir la décision de zéro-couplage avec `MetaHIA-Consolidated-Repo`.

`m6_corpus_from_m4_m5_v0_2.py` sépare explicitement **prédiction structurelle** et
**vérification indépendante** :

```text
kernel2 : rejeu contre evidence_facts (disjoints de discovery_facts, inchangé)
        -> une prédiction structurelle (start, opérateur, direction) -> predicted_end
                ↓
corpus/family_tree_verification_claims_v0_1.json
        -> une claim de témoin indépendant sur ce même (sujet, opérateur, direction),
           délibérément parfois fausse (objet remplacé par un nom-placeholder sans
           ambiguïté, jamais un vrai nom du corpus)
                ↓
claimed_object == predicted_end  -> preuve SUPPORT
claimed_object != predicted_end  -> preuve CHALLENGE
aucune claim correspondante      -> aucune preuve (exclu, comme en v0.1/v0.2)
```

Le champ `verdict` du fichier de claims est une annotation pour le lecteur humain — **jamais
lu par le code**, qui ne fait que comparer `claimed_object` à `predicted_end` ; l'accord ou le
désaccord est donc découvert mécaniquement, pas injecté.

**Résultat réel, vérifié par exécution** : sur 69 patterns candidats, 49 sont exclus (aucune
claim de vérification correspondante), et **26 obtiennent une preuve indépendante réelle — 16
`SUPPORTED`, 10 `CONTRADICTED`.**

Sur ce jeu (seed=0, split 16/5/5) : **Brier de holdout = 0,48125, ECE = 0,025** — ni 0 (parfait
trivial) ni 2 (maximalement faux) : un résultat réellement informatif. `evaluate_promotion`
répond correctement au seuil : bloque à `brier_threshold=0.4`, autorise à `0.6` — démontré,
pas seulement affirmé, par `tests/test_m6_non_degenerate_evidence_v0_2.py`.

**Extension aux patterns de longueur > 1 (addendum 2026-09-17)** : la limite initiale (claims
limitées aux relations directes à un saut) a été levée. Les claims sont maintenant indexées
par **squelette complet** (`skeleton`, une séquence opérateur/direction de longueur
quelconque), pas seulement `(sujet, opérateur, direction)` — un témoin énonce naturellement
« je confirme/dément que le [squelette dérivé] de X est Y » sans avoir besoin de connaître les
sauts intermédiaires, exactement ce que prédit `replay_path_pattern_holdout`. Les deux
profondeurs (1 et 2) montrent chacune une diversité d'issues réelle et non triviale, testé par
`test_v2_covers_both_length_1_and_length_2_patterns`. Aucun pattern de longueur supérieure à 2
n'a encore de claim (le corpus de découverte ne produit pas de chemin plus long) — signalé, pas
fabriqué.

## 8. Résultat local

331 tests passés (330 précédents ; `test_m6_non_degenerate_evidence_v0_2.py` étendu de 6 à 7
tests pour couvrir les deux profondeurs), 0
échec, 0 régression.

## 9. Hors périmètre de cette version

- Validation par un tiers réellement externe (l'auto-exécution du protocole ne clôt pas la
  independent gate — voir section 6 ; paquet préparé pour un tiers externe, section 10) ;
- patterns de longueur > 2 dans le mécanisme non dégénéré — non testés faute de chemin plus
  long dans le corpus de découverte actuel, pas une limite du mécanisme lui-même ;
- choix définitif des seuils de promotion (`brier_threshold`, `per_bucket_brier_threshold`) — laissés comme paramètres explicites de l'appelant, pas de valeur par défaut imposée silencieusement ;
- réévaluation du gate M2/Phase 2 — M6 est un chantier de recherche K3 isolé, sans lien avec le gate empirique de la Phase 2 du dépôt de production.

## 10. Paquet de validation tierce externe (addendum 2026-09-17)

Deux protocoles couvrent désormais M6, chacun gelé sur son propre périmètre de fichiers :

- `documentation/MetaHIA_ThirdParty_Validation_Protocol_M6_V0_1.md` — mécanisme de base +
  corpus réel v0.1 (9 cas C01–C09), déjà auto-exécuté (section 6) ;
- `documentation/MetaHIA_ThirdParty_Validation_Protocol_M6_NonDegenerate_V0_2.md` — mécanisme
  de preuve non dégénéré (7 cas C01–C07, numérotation propre à ce protocole).

Comme ce dépôt GitHub est privé, un paquet zip autonome a été préparé pour être remis à un
tiers réellement externe par le canal de votre choix (le dépôt Git lui-même n'a pas été rendu
public ni de collaborateur ajouté — décision qui reste la vôtre). Contenu : les deux
protocoles, tous les fichiers gelés qu'ils couvrent, les suites de tests critiques
correspondantes, et un `README.md` de paquet expliquant comment les exécuter — sans fichier de
résultats attendus, sur le même modèle que les paquets M3/M5 déjà livrés plus tôt dans ce
projet.
