# MetaHIA V10 — Revue et rejet des expériences P4.1–P4.5 (2026-09-19)

Statut : **P4.1–P4.5 non adoptés**. P5 (stabilisation de l'interface M1–M6 et régression
multi-domaines) reste adopté séparément — voir
`documentation/P5_M1_M6_Stabilization_Multidomain_Regression_v0_1.md`.

## 1. Contexte

Un paquet externe (`MetaHIA-V10-P5-M1-M6-Stabilization-Multidomain-v0.1.zip`) a été reçu,
prétendant établir une chaîne expérimentale P4.1 → P4.5 : baseline de transfert
inter-domaines, invariance structurelle imposée, découverte autonome d'invariant, réification
d'opération + rejeu, puis « opération exécutable → nouvelle structure » avec confirmation par
témoin indépendant. Ces affirmations touchent directement les critères de clôture d'E20-D
(découverte autonome, composition relation → opération → nouvelle structure) — un enjeu
scientifique majeur pour ce projet, qui exige donc la même rigueur que pour toute autre preuve
de ce projet : **vérification par exécution directe, jamais par lecture du récit seul.**

Chaque fichier a été lu intégralement, puis exécuté réellement (pas seulement inspecté) dans
un bac à sable isolé. Deux défauts méthodologiques réels et distincts ont été trouvés et
confirmés par instrumentation du code, pas par supposition.

## 2. Défaut n°1 (P4.1, P4.2) — mécanisme de corpus dégénéré

`p4_transfer_baseline_v0_1.py` et `p4_structural_transfer_v0_1.py` importent :

```python
from m6_corpus_from_m4_m5_v0_1 import build_real_corpus
```

`m6_corpus_from_m4_m5_v0_1.py` est le mécanisme **v0.1**, déjà documenté dans ce projet comme
structurellement incapable de produire autre chose que `SUPPORTED` sur un corpus interne
cohérent (voir son propre docstring, et
`tests/test_m6_real_corpus_v0_2_holdout_v0_1.py::test_v0_2_zero_brier_is_a_known_degenerate_single_class_case_not_calibration_skill`).
C'est précisément la raison pour laquelle ce projet a conçu et adopté
`m6_corpus_from_m4_m5_v0_2.py` (`build_real_corpus_v2`, corpus de vérification adversarial)
comme mécanisme de référence pour **tout** le reste du travail M6/M7 de ce projet.

**Vérifié par exécution réelle** :

```json
"family": {"records": 23, "rules": 23, "outcomes": ["SUPPORTED"]}
```

23 enregistrements, **100 % `SUPPORTED`**, Brier holdout = 0,0000 — le résultat dégénéré déjà
connu, pas un signal de calibration. Toute expérience de « transfert » utilisant ce côté
comme source (P4.1 et P4.2) apprend donc d'une source **sans aucun exemple négatif** — le
« transfert » mesuré ne peut, par construction, jamais révéler si une évidence
`CONTRADICTED` traverse les domaines.

## 3. Défaut n°2 (P4.4, P4.5) — généralisation de motif circulaire

C'est le défaut le plus important, et il a été confirmé par instrumentation directe du code,
pas par lecture seule.

`p4_operation_execution_v0_1.py::_target_pattern_from_candidates` groupe les chemins cibles
par squelette exact (couple opérateur/direction), puis appelle
`generalize_path_pattern(items, ...)` avec `min_support=2` — le strict minimum. Le motif
retenu par le test de démonstration (`Module_D → Direction_H`) est généralisé à partir
d'**exactement 2 exemples** :

```text
groups[('PROJET_DE', 'PORTE_PAR')] = [
    Module_D → Direction_H,   # <- c'est justement le cas "prédit" par l'expérience
    Module_E → Direction_I,
]
```

Le rejeu (`replay_path_pattern`) est ensuite exécuté en partant de `Module_D` — **une des deux
instances mêmes qui ont servi à généraliser le motif** — sur le même graphe. Le chemin
`Module_D -PROJET_DE-> Projet_Q -PORTE_PAR-> Direction_H` est un fait brut déjà présent dans
le graphe (`O-E07` + `O-E03`, `corpus/organization_facts_v0_1.json`). Le rejeu ne peut
structurellement pas aboutir ailleurs qu'à `Direction_H` : ce n'est pas une prédiction sur une
donnée masquée, c'est la relecture d'un fait qui a servi à construire le motif lui-même.

**Conséquence pour le témoin** : `ORG-WITNESS-11` (« Module_D → Direction_H ») confirme un
fait déjà entièrement déterminé par le graphe cible seul — l'invariant découvert côté Famille
ne sert qu'à **sélectionner quel chemin déjà réel regarder**, jamais à **calculer** sa valeur.
Aucune information ne transite réellement du domaine source vers la valeur prédite.

C'est exactement le risque que le document `P4_Structural_Transfer_v0_1.md` (P4.2) mettait
lui-même en garde d'éviter (« nous risquons de fabriquer une abstraction spécialement adaptée
au test ») — et l'implémentation de P4.4/P4.5 y est tombée, sans que la documentation associée
ne le remarque.

Preuve reproductible (sans appel réseau, sans modification de M1/M6) :

```python
from e20d_p4_autonomous_transfer_v0_1 import make_paths, discover_source_invariants, _shape
# ... voir cette section pour la reproduction complète ...
# groupe candidat de taille exactement 2, incluant le cas testé -- confirmé par exécution.
```

## 4. Ce qui est néanmoins verdict-neutre

Le docstring de `p4_operation_replay_v0_1.py` (P4.4) reconnaît déjà partiellement le problème
qu'il pose lui-même (« v0.1 does not claim that this object itself computes the endpoint »),
et `p4_operation_execution_v0_1.py` (P4.5) a été explicitement écrit pour corriger *cette
même* faiblesse — un signe de rigueur honnête de l'auteur externe. Le défaut trouvé ici (le
motif généralisé à partir d'un ensemble qui inclut l'instance testée) est un défaut plus
subtil, non couvert par cette correction, et n'a pas été identifié dans les rapports reçus.

## 5. Décision

- **P4.1, P4.2, P4.3, P4.4, P4.5 : non adoptés.** Ni le code ni les documents associés
  (`P4_Transfer_Baseline_v0_1.md`, `P4_Structural_Transfer_v0_1.md`,
  `P4_3_Autonomous_Structural_Transfer_v0_1.md`, `P4_4_Operation_Reification_Replay_v0_1.md`,
  `P4_5_Executable_Operation_Masked_Endpoint_v0_1.md`) ne sont intégrés à ce dépôt.
- **La mécanique structurelle sous-jacente** (découverte de forme opérateur-agnostique,
  réification via E20-D.14/E20-D.15) pourrait avoir une valeur d'ingénierie réutilisable pour
  un futur protocole correctement conçu — mais seulement avec une vraie séparation
  entraînement/test (à l'image de `discovery_facts`/`evidence_facts` déjà utilisée partout
  ailleurs dans ce projet), et sur un ensemble de candidats assez large pour qu'aucune instance
  testée ne fasse partie des exemples ayant servi à généraliser le motif.
- **P5 reste adopté séparément** (`m1_m6_interface_v0_2.py`,
  `p5_m1_m6_multidomain_regression_v0_1.py`, `p5_multiseed_regression_v0_1.py`) : ces fichiers
  utilisent correctement `build_real_corpus_v2` et ont été vérifiés par exécution réelle,
  chiffre par chiffre.
- **E20-D reste `OPEN`** — rien dans cette revue ne change son statut ; ce paquet ne
  satisfaisait de toute façon pas ses critères de clôture même sur la base de son propre récit.

Cette décision n'est pas une clôture de gate de validation tierce (aucun protocole n'a été
préparé pour P4) — c'est un rejet motivé, avant intégration, sur la base d'un défaut de
conception expérimentale trouvé par exécution directe.
