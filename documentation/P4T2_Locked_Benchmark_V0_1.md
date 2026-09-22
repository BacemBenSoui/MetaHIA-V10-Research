# MetaHIA V10 — P4-T.2 : benchmark train/holdout/témoin verrouillé v0.1

Date : 2026-09-21
Statut : **implémenté et vérifié — protocole auto-administré, structurellement
verrouillé, PAS une clôture de gate par un tiers externe**

## 1. Le problème que ce chantier résout

`documentation/P4T_Structural_Transformation_Induction_V0_1.md` Sec. 8
déclarait explicitement cette limite : *« les tests de ce fichier
construisent leurs propres données synthétiques dans le même fichier que
l'assertion — c'est une preuve de mécanisme unitaire, pas un protocole avec
un corpus gelé et remis par un tiers avant exécution »*. La revue externe a
demandé : `TRAIN ≠ HOLDOUT ≠ WITNESS`, idéalement « un paquet remis avant
exécution ».

Ce chantier construit ce protocole — **auto-administré** (aucun tiers
externe disponible dans cette session), mais **verrouillé
mécaniquement**, pas seulement par convention.

## 2. Séparation en trois fichiers

- `p4t_locked_benchmark_cases_v0_1.py` — lignes d'entraînement (source ET
  cible) et observations de holdout **source seule** (aucune information
  de cible n'existe dans ce fichier, ni même masquée — l'absence est
  totale, exactement la discipline déjà utilisée par tous les tests P4-T
  existants).
- `p4t_locked_benchmark_witness_v0_1.py` — **seul** fichier contenant les
  bonnes réponses. Calculées une fois par exécution directe du mécanisme
  déjà validé (`discover()`/`freeze()`/`blind_replay()`), pas par
  supposition : un protocole verrouillé avec un mécanisme déterministe ne
  peut pas avoir un témoin calculé autrement — le contenu scientifique est
  la **séparation structurelle et l'ordre d'exécution imposé**, pas le
  secret de la réponse elle-même.
- `p4t_locked_benchmark_runner_v0_1.py` — orchestre les trois étapes dans
  un ordre strict, **vérifié mécaniquement, pas seulement promis**.

## 3. Verrouillage vérifié, pas seulement promis

Trois vérifications indépendantes, toutes exécutées réellement :

1. **Statique (texte)** : `test_discovery_and_commit_functions_never_mention_the_witness_module_by_name`
   inspecte le code source de `run_discovery_and_replay`/`_discover_and_freeze`/
   `commit_predictions` via `inspect.getsource()` et confirme que le nom du
   module témoin n'y apparaît **jamais** — seule `reveal_and_compare` le
   mentionne.
2. **Statique (AST)** : `test_witness_module_is_not_imported_at_module_scope`
   parse l'arbre syntaxique du fichier et confirme l'absence de tout
   `import`/`from...import` du module témoin au niveau du module (mirroring
   `_m7_dependency_scan`, déjà utilisé dans ce projet pour la même
   discipline sur M7).
3. **Dynamique (exécution réelle)** : `test_witness_module_is_absent_from_sys_modules_at_the_moment_predictions_are_committed`
   exécute réellement `run_discovery_and_replay()` puis `commit_predictions()`,
   et vérifie — via le mécanisme de cache d'import de Python lui-même, pas
   sur la foi du code — que `"p4t_locked_benchmark_witness_v0_1" not in
   sys.modules` à ce point précis. Ce n'est qu'ensuite que
   `reveal_and_compare()` importe le témoin.

**Limite trouvée et documentée pendant l'écriture des tests** : le cache
d'import de Python est global au processus. Une fois qu'un test a
légitimement révélé le témoin, le module reste en cache pour le reste de
la session — un second appel à `run_locked_benchmark()` dans le même
processus ne peut plus redémontrer « témoin absent avant commit » sans
purger explicitement `sys.modules` au préalable. Ce n'est pas un bug du
runner (son ordre interne reste correct à chaque appel) ; c'est une
limite du test lui-même, trouvée par échec réel d'un test
(`test_run_locked_benchmark_reports_witness_not_imported_before_commit`
a échoué à la première écriture, pas en théorie) et corrigée en purgeant
`sys.modules` avant l'assertion.

**Conséquence pratique, pas un défaut** : `validation/p4t_locked_benchmark_predictions_v0_1.json`
lui-même engagé dans ce dépôt reflète l'état réel du processus qui l'a
généré — son champ `witness_module_imported_yet` peut légitimement valoir
`true` quand ce fichier est régénéré au sein d'une suite complète (où
d'autres tests ont déjà importé le témoin avant celui-ci), et `false` lors
d'une exécution isolée de `python p4t_locked_benchmark_runner_v0_1.py`
sur un processus frais. Les deux sont des enregistrements honnêtes de
l'exécution réelle qui les a produits — seule la vérification dédiée
(`test_witness_module_is_absent_from_sys_modules_at_the_moment_predictions_are_committed`,
qui purge explicitement le cache d'abord) fait foi de la propriété
structurelle elle-même, pas ce fichier ponctuel.

## 4. Sept cas, toutes les familles P4-T + les deux issues fermées

| Cas | Famille attendue | Résultat réel |
|---|---|---|
| C01 | `COMPARE_PERMUTATION` | prédiction exacte (vérifiée `structural_equal`) |
| C02 | `COMPARE_RECURSIVE` | prédiction exacte |
| C03 | `SELECTION_MAPPING` (projection) | prédiction exacte |
| C04 | `SELECTION_MAPPING` (duplication) | prédiction exacte |
| C05 | `COMPOSED` (deux transformations gelées indépendamment, `compose_frozen`) | prédiction exacte |
| C06 | `AMBIGUOUS` (construit délibérément) | issue correctement `AMBIGUOUS` |
| C07 | `REJECTED` (cible constante) | issue correctement `REJECTED` |

**7/7 cas correspondent au témoin**, vérifié par exécution réelle, pas
supposé — voir `validation/local_regression_2026-09-21_p4t2.txt` et
`validation/p4t_locked_benchmark_predictions_v0_1.json` (fichier
horodaté, déterministe entre exécutions, engagé sur disque avant toute
lecture du témoin).

**Bug réel trouvé et corrigé pendant la construction** : la première
version de `reveal_and_compare()` comparait les prédictions via
`repr()` — qui embarque le `node_id` arbitraire de chaque `Node` généré
par `blind_replay()`, jamais identique entre deux exécutions même quand
le contenu structurel est correct. Confirmé par exécution : 4 des 5 cas à
prédiction échouaient à tort. Corrigé en comparant via
`kernel2.structural_equal()` (qui ignore `node_id`, compare `kind`/`children`
canoniquement) — exactement le même outil déjà utilisé par `verify()`
(Porte D). Un second bug (identifiant `frozen_id` basé sur `id(rows)`,
une adresse mémoire non déterministe) a aussi été trouvé et corrigé pour
que le fichier de prédictions engagées soit reproductible entre
exécutions.

## 5. Ce que ce protocole établit — et ce qu'il n'établit PAS

**Établit** : la découverte, le gel et le replay sont **mécaniquement**
incapables d'avoir lu la réponse — pas seulement par absence de tricherie
constatée après coup, mais par une structure de code qui ne permet même
pas la lecture accidentelle (aucune information de cible dans le fichier
de cas ; aucune mention du module témoin dans le code de découverte/gel/
engagement, vérifié statiquement et dynamiquement).

**N'établit PAS** :
- Une clôture de gate par un tiers externe — personne d'autre que cette
  session n'a détenu le fichier témoin. C'est la même distinction déjà
  posée pour M4-M7 dans ce projet : l'auto-exécution ne ferme jamais un
  gate de validation à elle seule.
- Une généralisation à des données non contrôlées par l'auteur du
  benchmark — les 7 cas ont été conçus et leur témoin calculé par la même
  session qui a écrit le mécanisme. Le protocole prouve la **séparation et
  l'ordre**, pas l'absence de biais de sélection des cas eux-mêmes.
- Une clôture d'E20-D — la matrice de clôture (voir
  `P4T_Structural_Transformation_Induction_V0_1.md` Sec. 9.1) passe de
  « mécanisme, pas de benchmark séparé » à « mécanisme + verrouillage
  structurel auto-administré », toujours pas à « verrouillé par un
  tiers ».

## 5bis. Correctif C02 : entité constante du holdout rendue réellement fraîche (2026-09-22)

Une revue externe a relevé que `_C02_HOLDOUT` réutilisait
`NodeRef("c02_z")` — la même identité que `_C02_TRAIN` — pour le 4ᵉ
créneau constant, en contradiction avec le commentaire du fichier
revendiquant des « entités totalement fraîches côté holdout ». Confirmé
par lecture du code (`c02_z` apparaît identiquement dans les deux
tuples), contrairement aux positions `p`/`q` qui étaient déjà
correctement disjointes (`c02_{i}p`/`c02_{i}q` vs `c02_h{i}p`/`c02_h{i}q`).

Ce même relecteur affirmait que ce partage causait un échec du replay
avec une entité vraiment fraîche — **affirmation testée et réfutée** par
exécution directe (voir
`documentation/P4T_Structural_Transformation_Induction_V0_1.md` Sec. 6.2) :
`blind_replay()` ne renvoie jamais `None` pour une différence de valeur
littérale, seulement pour une différence d'arité/forme. Le partage
n'était donc pas une fuite opérationnelle, mais restait un vrai écart
documentation/code.

**Correction** : `_C02_HOLDOUT` utilise désormais `NodeRef("c02_hz")`.
Le témoin correspondant (`WITNESS_PREDICTIONS["C02_RECURSIVE_PERMUTATION"]`
dans `p4t_locked_benchmark_witness_v0_1.py`) a été **recalculé par
exécution directe** de `discover()`/`freeze()`/`blind_replay()` sur le
cas corrigé (pas supposé par édition manuelle) — méthodologie identique
à celle qui a produit le témoin initial (Sec. 3 ci-dessus). Résultat
confirmé : le 4ᵉ enfant de chaque prédiction reflète correctement
`*c02_hz`, jamais `*c02_z`. Les 8 tests de
`tests/test_p4t_locked_benchmark_v0_1.py`, y compris
`test_run_locked_benchmark_matches_witness_on_every_case`, passent
après cette double mise à jour (cas + témoin).

## 6. Tests

`tests/test_p4t_locked_benchmark_v0_1.py` (8 tests) : couverture des
sept familles, absence d'identifiants témoins dans le fichier de cas,
vérification statique (texte + AST) de l'ordre d'import, vérification
dynamique via `sys.modules`, correspondance complète au témoin,
déterminisme du fichier de prédictions engagées entre deux exécutions.

## 7. Décision

**P4-T.2 = `SELF_ADMINISTERED_LOCKED_BENCHMARK, PASS`.** Améliore
concrètement la matrice de clôture E20-D sur l'axe « holdout aveugle »
(Sec. 9.1) sans revendiquer une clôture de gate par un tiers. E20-D reste
`OPEN`.
