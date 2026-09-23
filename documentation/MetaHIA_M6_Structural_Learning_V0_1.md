# MetaHIA — M6 — Structural Learning v0.1

## 1. Statut

- M1 : FROZEN
- M2 : STABLE / NON-PROMOTED
- M3 : PASS_INDEPENDENT_SCOPE
- M4 : PASS_INDEPENDENT_SCOPE
- M5 : PASS_INDEPENDENT_SCOPE
- M6 : **MECHANISM_STATUS = VALIDATED** (2026-09-17, clôturé explicitement par le porteur du
  projet sur preuves d'exécution externes — voir Sec. 6 et `JOURNAL_DE_BORD.md`). Depuis
  2026-09-23, une dimension distincte **LEARNING_PERFORMANCE** est suivie séparément (M6-TRANSFER
  / M6-INTERNAL, non `VALIDATED`, caractérisation honnête en cours puis gelée — voir Sec. 14) :
  le mécanisme est validé, sa capacité d'apprentissage utile ne l'est pas encore.
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

## 11. Découverte structurelle : le holdout n'a jamais exercé `EXACT_BUCKET`/`RULE_ONLY` (2026-09-18)

En investiguant honnêtement pourquoi l'ajout d'évidence M7 (témoin multi-sauts) améliorait le
Brier de holdout (voir `documentation/MetaHIA_M7_TextClaimParser_V0_1.md` Sec. 14), une
vérification directe — pas une supposition — a révélé un fait structurel qui concerne **tous**
les résultats de calibration M6/M7 de ce projet, y compris le tout premier baseline déjà
`VALIDATED` (Brier de holdout = 0,48125, clôturé le 2026-09-17) :

**`StructuralLearningPolicy.predict()` n'a jamais utilisé la base `EXACT_BUCKET` ni
`RULE_ONLY` sur un seul enregistrement de holdout, depuis le tout premier calcul de ce Brier
jusqu'à aujourd'hui.** Vérifié directement (`tests/test_m6_holdout_basis_diagnosis_v0_1.py`) :
100 % des prédictions de holdout, pour chaque configuration testée ce projet, utilisent
`BASIS_GLOBAL_PRIOR`.

**Cause, structurelle et intentionnelle, pas un bug** : `split_by_rule()` garantit que chaque
règle atterrit entièrement dans une seule partition (jamais partagée entre train et holdout —
c'est précisément l'objectif de conception documenté au point 5 de la Sec. 3 : « holdout
mesure la généralisation à une règle non vue, pas la mémorisation d'une règle déjà
partiellement vue en entraînement »). Conséquence directe et jusqu'ici non remarquée : la
signature de règle d'un enregistrement de holdout n'apparaît **jamais** dans
`_bucket_counts`/`_rule_counts` de la politique entraînée — `predict()` ne peut donc **que**
retomber sur `BASIS_GLOBAL_PRIOR` (la distribution de classes globale, calculée sur tout
l'entraînement, indépendamment de la règle) ou `BASIS_UNIFORM_NO_DATA`.

**Conséquence pratique, à ne jamais perdre de vue en lisant un chiffre de Brier/ECE de ce
projet** : chaque nombre de calibration rapporté ici mesure si la distribution de classe
**globale** de l'entraînement généralise à la distribution de classe globale du holdout —
jamais si la politique a appris quoi que ce soit de **spécifique à une règle**, contrairement
à ce que le nom du module (`Rule × Context × Depth × Provenance → distribution`) et son
objectif documenté (Sec. 2) pourraient laisser croire. Ajouter des enregistrements
d'entraînement, quelle qu'en soit la source, ne peut faire bouger ce chiffre qu'en déplaçant
cette distribution globale — jamais en enseignant à la politique quoi que ce soit sur une
règle précise qu'elle sera amenée à prédire en holdout.

**Ce que cela ne remet pas en cause** : la validation tierce de M6 (Sec. 6/10) portait
explicitement sur le mécanisme (honnêteté, non-circularité, reproductibilité, séparation
train/holdout correcte) — jamais sur une démonstration de généralisation par-règle, que
chaque protocole a toujours explicitement exclue de son périmètre de preuve (« scientific
non-closure »). La clôture `VALIDATED` de M6 et M7 reste donc valide au sens où elle a été
formulée. **Ce que cela corrige** : la lecture informelle, jamais démentie jusqu'ici dans ce
document, du Brier de 0,48125 comme un résultat « réellement informatif de M6 » (Sec. 5) —
il est réel et non dégénéré (ni 0,0 ni 2,0), mais il ne démontre et n'a jamais démontré de
compétence de généralisation par-règle.

**Ce que cela signifie pour le témoin multi-sauts (M7)** : l'amélioration du Brier observée en
ajoutant 20 preuves `CONTRADICTED` (Sec. 14 du document M7) s'explique entièrement par ce
mécanisme de déplacement du prior global — confirmé, pas seulement supposé — et non par une
quelconque compétence relationnelle du LLM. Voir la mise à jour correspondante dans
`documentation/MetaHIA_M7_TextClaimParser_V0_1.md` Sec. 14.

**Non traité comme une régression à corriger dans ce document** : ce n'est pas un défaut de
code (`split_by_rule` fait exactement ce que sa propre documentation promet), c'est une limite
d'échelle du corpus actuel (trop peu de règles distinctes pour qu'un holdout par-règle puisse
un jour coexister avec une règle partiellement vue en entraînement). Un corpus futur
significativement plus riche pourrait un jour permettre un design d'évaluation différent qui
exercerait réellement `EXACT_BUCKET`/`RULE_ONLY` — non entrepris ici.

**Corroboration indépendante (2026-09-18)** : un relecteur travaillant séparément sur une
archive zip de ce dépôt a mené, sans connaître ce résultat, une expérience contrefactuelle
convergente — ajouter un lot d'observations longueur ≥2 artificiellement toutes
`CONTRADICTED` à une configuration adversarial+témoin fait passer le Brier de holdout de
0,47000 à 0,37535, sans aucune amélioration réelle du LLM. Son verdict prudent
(`SUSPECTED_MECHANICAL_ARTIFACT`, faute d'avoir inspecté directement le code de décision) est
ici confirmé plus fortement : l'inspection directe du champ `basis` retourné par
`predict()` (pas une simple comparaison de scores) prouve que le mécanisme n'est pas une
possibilité parmi d'autres mais **la seule chose qui se soit jamais produite**, sur chaque
holdout de ce projet. Reclassé en conséquence : **`CONFIRMED_MECHANICAL_ARTIFACT`** — la seule
réserve restante, légitime, est que les 20 sorties LLM brutes du run ayant produit le Brier
0,42649 du témoin multi-sauts n'ont pas été archivées comme un corpus figé, donc ce run précis
n'est pas rejouable à l'identique bit-à-bit ; cela ne remet pas en cause l'existence du
mécanisme, seulement la traçabilité exacte de cette exécution particulière.

## 12. Diagnostic de transfert contextuel (2026-09-22) — la piste « corpus plus riche » de la Sec. 11 était mal posée, un signal réel mais fragile existe sur un domaine

Demandé explicitement en suite du rééquilibrage d'effort P8→E20-D/M6
(voir `documentation/P8_Jev_Kev_Local_Decision_Model_V0_1.md` Sec.
6octies) : la Sec. 11 laissait ouverte l'idée qu'« un corpus futur
significativement plus riche pourrait un jour permettre... d'exercer
réellement `EXACT_BUCKET`/`RULE_ONLY` ». **Cette piste est
mécaniquement fausse, pas seulement optimiste** : `split_by_rule()`
garantit qu'une règle de holdout n'apparaît **jamais** dans
`_bucket_counts`/`_rule_counts` de la politique entraînée, quel que
soit le volume de données ajouté sous la MÊME politique de split —
ajouter des règles supplémentaires ne fait qu'ajouter des règles qui,
elles aussi, seront entièrement en train ou entièrement en holdout,
jamais partagées. Aucun volume de corpus ne peut changer cette
propriété logique.

La question qui reste réellement ouverte, formulée précisément pour la
première fois ici : **en ignorant délibérément l'identité de la règle
(la seule dimension garantie inatteignable), le CONTEXTE seul
(bandes de nouveauté/redondance, profondeur, provenance) porte-t-il un
signal prédictif qui transfère à une règle jamais vue ?** Si oui,
c'est une forme de généralisation structurelle jamais mesurée par ce
projet jusqu'ici. Si non, cela confirme — par la donnée réelle, pas
seulement par construction — que les corpus actuels ne portent aucune
régularité exploitable au-delà de la fréquence de classe brute, une
fois l'identité de règle retirée.

**Protocole** (`m6_context_transfer_diagnosis_v0_1.py`, adaptateur
parallèle, `StructuralLearningPolicy` non modifié) : `ContextOnlyPolicy`,
compatible en signature avec `StructuralLearningPolicy` (même
`predict(rule, novelty, redundancy, depth, provenance)`), construit
ses buckets sur `(bande_nouveauté, bande_redondance, profondeur,
provenance)` **sans** la signature de règle, réutilisant directement
`_band()` (jamais réimplémentée) pour éviter tout risque de dérive
entre les deux bandings. Les DEUX politiques (globale et contextuelle)
sont entraînées sur le MÊME split `split_by_rule()` et évaluées sur le
MÊME holdout — seule la présence ou l'absence de la signature de règle
dans la clé diffère. Réutilise sans modification
`brier_score_multiclass()`/`expected_calibration_error_top_label()`
(compatibilité de signature, pas de réimplémentation parallèle des
métriques, contrairement à certains modules P8 où c'était nécessaire
pour une incompatibilité de modèle de données réelle). 7 tests
déterministes (`tests/test_m6_context_transfer_diagnosis_v0_1.py`) :
**un vrai bug trouvé avant tout run réel** — le premier essai de
construction d'un `Node` synthétique de test utilisait le kind
`PATTERN`, que `structural_signature()` dirige vers
`_pattern_unified_signature()` (qui attend une vraie structure à base
de `PatternSlot` et renvoie silencieusement `None` pour un nœud de
test simplifié) — toutes les règles synthétiques s'effondraient sur la
même signature `None`, rendant le test inutile ; corrigé en utilisant
le kind générique `OBSERVATION`, qui emprunte la branche générique de
`structural_signature()` et donne bien une signature distincte par
règle.

**Résultat réel** (`validation/m6_context_transfer_diagnosis_v0_1_results_2026-09-22.json`,
10 seeds × 5 configurations = 50 comparaisons réelles, sur les 4
corpus de domaine déjà validés + leur union) :

| Domaine | N | Δ Brier moyen (contexte − global) | σ | Contexte gagne | Contexte perd | Égalité |
|---|---:|---:|---:|---:|---:|---:|
| family | 26 | +0,032 | 0,062 | 2/10 | 7/10 | 1/10 |
| **organization** | 24 | **−0,096** | 0,085 | **9/10** | 1/10 | 0/10 |
| supply_chain | 24 | +0,006 | 0,068 | 4/10 | 5/10 | 1/10 |
| library | 20 | **+0,205** | 0,324 | 1/10 | 6/10 | 3/10 |
| combined (4 domaines) | 94 | +0,002 | 0,006 | 5/10 | 5/10 | 0/10 |

(Δ négatif = le contexte seul bat le prior global ; positif = il fait
pire. `holdout` fait toujours 4 enregistrements par seed pour
organization/supply_chain/library, 4-7 pour family, ~19 pour la
combinaison — cf. le fichier JSON pour le détail par seed.)

**Lecture honnête, non lissée, en quatre points :**

1. **Aucun signal universel** : la moyenne combinée (4 domaines) est
   quasi nulle (+0,002, σ=0,006) et exactement partagée 5 gagnant/5
   perdant — le contexte seul n'apporte, en moyenne sur l'ensemble des
   corpus actuels, rien de mesurable au-delà du prior global. Ceci
   confirme, par la donnée et pas seulement par construction, que
   `BASIS_GLOBAL_PRIOR` n'occultait pas un signal structurel fort et
   universel qu'une base plus fine aurait facilement capturé.
2. **Mais le résultat n'est PAS uniformément négatif — un signal réel,
   quoique fragile, existe sur le domaine `organization`** : 9 seeds
   sur 10 où le contexte bat le prior global, avec une amélioration
   moyenne substantielle (Δ=−0,096) et cohérente en direction (une
   seule exception, seed 6). Ce n'est pas un artefact à sens unique
   trouvé une fois par hasard.
3. **Mais ce signal repose sur un échantillon minuscule** : seulement
   4 enregistrements de holdout et 1 à 2 clés de contexte partagées
   entre train et holdout à chaque seed pour ce domaine — assez pour
   qu'une coïncidence de petit échantillon (ex. « la plupart des
   preuves à provenance directe et faible nouveauté sont `SUPPORTED`
   dans ce corpus précis ») explique tout aussi bien le résultat qu'une
   véritable régularité structurelle transférable. **Ni confirmé ni
   réfuté par ce seul test** — nécessite un corpus `organization`
   sensiblement plus grand pour trancher, pas un changement de
   mécanisme.
4. **Le domaine `library` montre l'inverse : le contexte peut activement
   nuire**, parfois fortement (Δ jusqu'à +1,035 sur un seed isolé,
   σ=0,324 la plus grande variance des cinq configurations) — regrouper
   des enregistrements de règles différentes sous la même bande de
   contexte grossière peut mélanger des situations dissemblables et
   dégrader la calibration, pas seulement échouer à l'améliorer.

**Conséquence pour la piste « corpus plus riche » de la Sec. 11** :
reformulée correctement, un corpus plus riche n'aidera jamais à
atteindre `EXACT_BUCKET`/`RULE_ONLY` en holdout (impossible par
construction, confirmé Sec. 11 et ici) — mais **pourrait** aider à
déterminer si le signal `organization` (point 2) est réel ou un
artefact de petit échantillon, en donnant plus de règles et plus
d'enregistrements par bande de contexte à ce domaine spécifiquement.
Ce n'est pas une piste vague : c'est maintenant une question testable,
avec un protocole prêt à être rejoué dès qu'un corpus `organization`
plus grand existera.

**Ce que cela ne remet pas en cause** : la clôture `VALIDATED` de M6
(Sec. 6/10) et la reclassification `CONFIRMED_MECHANICAL_ARTIFACT` de
la Sec. 11 restent valides — ce diagnostic est un adaptateur parallèle
qui n'a jamais modifié `StructuralLearningPolicy`, et ne prétend
fermer aucun gate.

667 tests collectés (0 régression). Voir
`scripts/run_m6_context_transfer_diagnosis_v0_1.py` pour reproduire
l'expérience complète.

## 13. Reformulation M6-INTERNAL / M6-TRANSFER (2026-09-23) — deux capacités différentes, pas deux niveaux d'un même test

Clarification conceptuelle demandée explicitement par le porteur du
projet en réponse à la Sec. 12 : les Sec. 11/12 mesurent en réalité une
seule capacité, jamais nommée comme telle jusqu'ici. On la nomme
désormais rétroactivement **M6-TRANSFER** : *une règle jamais vue
bénéficie-t-elle de quelque chose appris sur d'autres règles ?*
`split_by_rule()` (Sec. 3) est conçu spécifiquement pour tester
M6-TRANSFER, et seulement cela — c'est pourquoi `BASIS_EXACT_BUCKET`/
`BASIS_RULE_ONLY` n'y sont jamais atteignables (Sec. 11), et pourquoi le
diagnostic de transfert contextuel (Sec. 12) était la bonne question à
poser dans ce cadre.

Mais le nom même du module (`Rule × Context × Depth × Provenance ->
distribution`, Sec. 2) promet une seconde capacité, jamais mesurée
jusqu'ici parce que `split_by_rule()` l'empêche structurellement : **M6-
INTERNAL** — *quand plusieurs observations d'une même règle existent,
`StructuralLearningPolicy` exploite-t-elle réellement `Rule × Context ×
Depth × Provenance` sur une observation retenue d'une règle
partiellement vue ?* Ce ne sont pas deux niveaux de performance d'un
même test : ce sont deux capacités différentes, avec des protocoles
d'évaluation structurellement incompatibles (l'un exige qu'une règle de
holdout soit absente de l'entraînement, l'autre exige le contraire).

**Protocole** (`m6_internal_learning_diagnosis_v0_1.py`, adaptateur
parallèle, `StructuralLearningPolicy` non modifié) : `split_within_rule()`,
l'inverse structurel exact de `split_by_rule()` — pour toute règle ayant
au moins `min_records_per_rule` observations (2 par défaut), une
fraction de SES PROPRES enregistrements part en holdout tout en
garantissant qu'au moins un enregistrement de cette même règle reste en
entraînement ; une règle avec moins d'observations part entièrement en
entraînement (rien à retenir qui testerait « déjà partiellement vue »
plutôt que de reproduire le cas de `split_by_rule()`). La politique
réelle est comparée à `GlobalOnlyPolicy`, une base compatible en
signature qui prédit toujours la fréquence de classe globale
d'entraînement, ignorant règle et contexte — exactement ce que
M6-TRANSFER a toujours mesuré. 10 tests déterministes
(`tests/test_m6_internal_learning_diagnosis_v0_1.py`) : aucun bug trouvé
cette fois.

**Découverte préalable, avant tout run réel** : sur les 4 corpus de
domaine, **aucune règle n'a jamais plus de 2 observations** — vérifié
directement. Avec la fraction de holdout par défaut (0,2) déjà utilisée
ailleurs dans ce projet, `round(2 × 0,2) = 0` : le holdout M6-INTERNAL
serait toujours vide, pas parce qu'aucune règle n'est éligible, mais
parce qu'aucune fraction raisonnable ne retient jamais ne serait-ce
qu'un seul enregistrement d'une règle à 2 observations. Une fraction de
0,5 (nécessaire, pas une préférence) a été utilisée pour rendre ce test
possible du tout.

**Résultat réel** (`validation/m6_internal_learning_diagnosis_v0_1_results_2026-09-23.json`,
10 seeds × 5 configurations) :

| Domaine | Règles éligibles | Taux EXACT/RULE_ONLY | Δ Brier moyen (réel − base globale) | σ | Réel gagne |
|---|---:|---:|---:|---:|---:|
| family | 6 | 100 % | **+1,449** | 0,095 | 0/10 |
| organization | 12 | 100 % | **+0,554** | 0,146 | 0/10 |
| supply_chain | 12 | 100 % | +0,086 | 0,031 | 0/10 |
| library | 10 | 100 % | +0,196 | 0,047 | 0/10 |
| combiné (4 domaines) | 40 | 100 % | +0,461 | 0,053 | 0/10 |

**Lecture honnête, sans lissage : un résultat négatif net, plus décisif
que celui de la Sec. 12, et entièrement expliqué mécaniquement.**

1. **`EXACT_BUCKET`/`RULE_ONLY` sont désormais atteignables à 100 %**,
   confirmant que le protocole teste bien ce qu'il prétend tester — la
   première fois que ces deux bases sont exercées sur un holdout dans
   toute l'histoire de ce projet.
2. **Mais la politique réelle fait PIRE que la base globale plate, dans
   les 5 configurations, sur les 10 seeds, sans une seule exception**
   (0/50 victoires). Ce n'est pas un signal faible ou mitigé comme en
   Sec. 12 — c'est un résultat négatif net et reproductible.
3. **Mécanisme identifié et vérifié directement, pas supposé** :
   `StructuralLearningPolicy._to_prediction()` ne fait aucun lissage —
   avec un support de 1 (une seule observation d'entraînement pour la
   règle), la prédiction est un one-hot à 100 % de confiance sur la
   classe observée. Quand la seconde observation de cette même règle
   (celle retenue en holdout) a une issue **différente** — chose qui
   arrive réellement, `Rule × Context × Depth × Provenance` n'étant pas
   parfaitement déterministe même pour un enregistrement de « même
   règle » — la pénalité de Brier est maximale (2,0, contre au plus
   ~0,67 pour une base globale prudente qui répartit sa masse). Un seul
   enregistrement suffit à produire une confiance totale, jamais
   justifiée par une taille d'échantillon de 1.
4. **La magnitude du dommage suit exactement le taux d'incohérence
   intra-règle, mesuré indépendamment** : proportion des règles à 2
   observations dont les deux issues diffèrent — family 100 %
   (Δ le plus élevé, +1,449), organization 50 % (Δ +0,554), library
   30 % (Δ +0,196), supply_chain 25 % (Δ le plus faible, +0,086, mais
   toujours positif). Plus une règle produit des issues incohérentes
   entre ses observations, plus la surconfiance sans lissage coûte
   cher — une explication causale complète, pas une corrélation
   laissée inexpliquée.

**Conséquence** : ce diagnostic répond à la question M6-INTERNAL posée
en introduction de cette section, et la réponse est claire et négative
sur les corpus actuels — **quand M6 peut exploiter `Rule × Context ×
Depth × Provenance` (ce qui n'arrive jamais en évaluation M6-TRANSFER,
Sec. 11), le faire sans lissage dégrade la calibration plutôt que de
l'améliorer**, à cause d'un estimateur ponctuel non régularisé combiné
à une véritable variabilité d'issue intra-règle. **Ce n'est pas une
critique du principe `Rule × Context × Depth × Provenance` lui-même**
(la Sec. 12 montre qu'un signal de contexte peut exister, notamment sur
`organization`) — c'est une critique précise et vérifiée de l'absence
de lissage/régularisation dans `StructuralLearningPolicy._to_prediction()`
face à un support de 1. Piste ouverte, non entreprise ici (parallel
adapter, pas de modification de la politique validée) : un lissage de
type Laplace ou une pondération par la confiance liée au support
pourrait corriger ce problème spécifique — à tester séparément, sans
toucher à la politique déjà `VALIDATED`.

**Ce que cela ne remet pas en cause** : la clôture `VALIDATED` de M6
reste inchangée — ce diagnostic, comme celui de la Sec. 12, est un
adaptateur parallèle qui ne modifie jamais `StructuralLearningPolicy` et
ne prétend fermer aucun gate.

687 tests collectés (0 régression). Voir
`scripts/run_m6_internal_learning_diagnosis_v0_1.py` pour reproduire
l'expérience complète.

## 14. Diagnostic de régularisation M6-INTERNAL (2026-09-23) — la régularisation aide beaucoup, ne suffit pas partout, M6-INTERNAL est désormais gelé

Suite directe à la Sec. 13, avec une nuance importante ajoutée par le
porteur du projet et retenue explicitement : le défaut identifié n'est
pas seulement « absence de lissage », c'est la **conjonction** de (A) un
support statistique aussi faible que 1 et (B) une réelle incohérence
d'issue intra-règle (mesurée, pas supposée) — même un excellent lissage
ne peut pas fabriquer une confiance qu'une seule observation ne
justifie pas. La vraie question devient : combien d'observations
faut-il pour estimer correctement la distribution d'une règle non
déterministe ?

**Protocole** (`m6_internal_regularized_diagnosis_v0_1.py`, adaptateur
parallèle, `StructuralLearningPolicy` non modifié) — deux mesures
séparées, comme demandé explicitement, jamais confondues :

- **Mesure A** : cinq politiques comparées sur le même split
  `split_within_rule()` (Sec. 13) que le diagnostic précédent —
  `GLOBAL_ONLY` (référence déjà utilisée), `M6_RAW` (reproduction
  vérifiée bit à bit de la vraie `StructuralLearningPolicy` — test
  dédié comparant les deux sur un vrai corpus, exact), `M6_LAPLACE_A1`,
  `M6_LAPLACE_A0.5` (lissage de Laplace), `M6_SUPPORT_WEIGHTED_K1`
  (repli additif vers le prior global, pondéré par
  `poids = support/(support + 1)`, la formule demandée : confiance
  modérée à support=1, dominée par l'estimation locale à support
  élevé).
- **Mesure B** : un banc de convergence synthétique contrôlé — 3
  distributions vraies connues (90/10, 50/50, 70/30) × 5 niveaux de
  support (1, 2, 5, 10, 20), 500 tirages indépendants par cellule,
  scorés contre la **distribution vraie directement** (jamais contre un
  seul tirage de holdout bruité) — isole le comportement de
  l'estimateur de tout artefact d'un corpus réel à petite échelle.

**17 tests déterministes**
(`tests/test_m6_internal_regularized_diagnosis_v0_1.py`) : **trois vrais
bugs trouvés avant tout run réel** — (1) `raw_smoothing` provoquait une
division par zéro sur le cas `UNIFORM_NO_DATA` (aucune donnée du tout),
corrigé en traitant ce cas séparément, exactement comme le fait la
vraie `StructuralLearningPolicy` elle-même ; (2) le premier banc
synthétique n'utilisait qu'une seule règle testée sans aucune autre
règle en arrière-plan, rendant `_rule_counts` et `_global_counts`
**identiques** par construction — `M6_SUPPORT_WEIGHTED` se repliait
alors sur lui-même (aucun lissage réel), corrigé en ajoutant un
arrière-plan fixe de 10 règles équilibrées 50/50, jamais réglé en
fonction de la distribution testée ; (3) import manquant
(`SUPPORTED`/`CONTRADICTED`).

### Résultat réel, Mesure A (`validation/m6_internal_regularized_diagnosis_v0_1_results_2026-09-23.json`, 10 seeds × 5 configurations × 5 politiques)

| Domaine | Incohérence intra-règle (Sec. 13) | Δ M6_RAW | Δ Laplace α=1 | Δ Laplace α=0,5 | Δ support-pondéré | Victoires (support-pondéré) |
|---|---:|---:|---:|---:|---:|---:|
| family | 100 % | +1,449 | +0,324 | +0,489 | +0,590 | 0/10 |
| organization | 50 % | +0,554 | +0,179 | +0,194 | +0,191 | 0/10 |
| supply_chain | 25 % | +0,086 | +0,086 | +0,026 | **−0,066** | **10/10** |
| library | 30 % | +0,196 | +0,121 | +0,076 | **+0,005** | 8/10 |
| combiné | — | +0,461 | +0,161 | +0,161 | +0,128 | 0/10 |

**Lecture honnête, sans lissage du résultat lui-même :**

1. **La régularisation réduit massivement le dommage partout** — le
   lissage de Laplace divise le Δ par 2 à 5 selon le domaine par
   rapport à `M6_RAW`. Ce n'est pas un effet marginal.
2. **Mais elle ne renverse le signe (bat `GLOBAL_ONLY`) que là où
   l'incohérence intra-règle est la plus faible** : `supply_chain`
   (25 %) — le seul domaine où le lissage pondéré par le support
   gagne, et gagne **systématiquement** (10/10 seeds) ; `library`
   (30 %) s'en approche fortement (8/10 victoires, Δ quasi nul,
   +0,005). Sur `family` (100 % d'incohérence) et `organization`
   (50 %), **aucune régularisation testée ne renverse jamais le
   résultat** — confirmation directe de la nuance du porteur du
   projet : le lissage ne peut pas compenser une règle authentiquement
   non déterministe.
3. **Le lissage pondéré par le support (la formule demandée
   explicitement) est la meilleure ou la meilleure ex-æquo des trois
   régularisations testées dans 3 domaines sur 4** (tous sauf
   `family`, où Laplace α=1 fait mieux) — cohérent avec l'intuition
   qu'une pondération qui croît avec le support réel est mieux motivée
   qu'une constante de Laplace fixe.

### Résultat réel, Mesure B (500 tirages par cellule)

| Distribution vraie | support=1 | support=2 | support=5 | support=10 | support=20 |
|---|---|---|---|---|---|
| 90/10 (loin de l'arrière-plan 50/50) | support-pondéré meilleur (0,132) | support-pondéré meilleur (0,079) | support-pondéré meilleur (0,035) | support-pondéré meilleur (0,018) | support-pondéré meilleur (0,009) |
| 50/50 (identique à l'arrière-plan) | `GLOBAL_ONLY` meilleur (0,004) | `GLOBAL_ONLY` meilleur | `GLOBAL_ONLY` meilleur | `GLOBAL_ONLY` meilleur | `GLOBAL_ONLY` meilleur |
| 70/30 (proche de l'arrière-plan) | `GLOBAL_ONLY` meilleur à tous les niveaux testés (jusqu'à support=20) | | | | |

**Deux lectures, aucune arrondie :**

1. **Pour une règle fortement asymétrique (90/10, loin du prior neutre),
   le lissage pondéré par le support est le meilleur estimateur à
   presque tous les niveaux de support testés** — une preuve directe,
   sur données synthétiques à vérité connue, que l'approche est bien
   fondée et convergente.
2. **Limite méthodologique du banc lui-même, disclosed honnêtement, pas
   cachée** : l'arrière-plan fixe (10 enregistrements, 50/50) est
   regroupé dans le dénominateur de `GLOBAL_ONLY`, qui inclut aussi les
   tirages de la règle testée elle-même — cela donne à `GLOBAL_ONLY`
   des échantillons supplémentaires « gratuits » et non biaisés dès que
   la distribution vraie n'est pas trop éloignée de 50/50, ce qui
   explique pourquoi `GLOBAL_ONLY` reste compétitif ou gagnant pour
   70/30 et 50/50 même à support=20. **Ce n'est pas un résultat
   invalide, c'est une limite de conception de ce banc précis** — la
   question de convergence reste tranchée uniquement pour le cas
   fortement asymétrique testé ici, pas de façon universelle.

### Décision de gouvernance M6 (demandée explicitement, adoptée)

`VALIDATED` reste inchangé, mais concerne désormais explicitement le
**mécanisme**, pas la performance d'apprentissage :

```text
M6
├── MECHANISM_STATUS : VALIDATED (2026-09-17, inchangé, Sec. 6/10)
│
└── LEARNING_PERFORMANCE (nouveau, 2026-09-23)
    ├── M6-TRANSFER  : signal contextuel réel mais non universel,
    │                   dépendant du domaine (Sec. 12)
    └── M6-INTERNAL  : négatif sans régularisation (Sec. 13) ;
                        avec régularisation, aide fortement partout,
                        ne bat la base globale que sur les domaines à
                        faible incohérence intra-règle (cette section) —
                        **gelé, caractérisé, pas un chantier actif**
```

**`M6-INTERNAL` est désormais considéré suffisamment caractérisé et
gelé, quel que soit le résultat mitigé** — décision explicite du
porteur du projet, pour éviter que M6 ne devienne à son tour une boucle
d'ablations sans fin. Aucune nouvelle variante de lissage
supplémentaire n'est prévue. Piste ouverte mais non entreprise :
appliquer la même mesure B à un arrière-plan plus large et plus neutre
pour lever la limite méthodologique du point 2 ci-dessus — pas urgent,
à décider explicitement avant de reprendre.

**Ce que cela ne remet pas en cause** : `MECHANISM_STATUS = VALIDATED`
reste inchangé — ce diagnostic, comme les Sec. 12/13, est un adaptateur
parallèle qui ne modifie jamais `StructuralLearningPolicy` et ne
prétend fermer aucun gate.

704 tests collectés (0 régression). Voir
`scripts/run_m6_internal_regularized_diagnosis_v0_1.py` pour reproduire
l'expérience complète (Mesure A + Mesure B).
