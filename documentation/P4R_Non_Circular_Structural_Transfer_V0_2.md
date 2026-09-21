# MetaHIA — P4-R Non-Circular Structural Transfer v0.2

## Objet

Ce protocole remplace les conclusions P4.1–P4.5 invalidées. Il sépare
explicitement une preuve micro-structurelle positive d'une tentative plus forte
de prédiction d'endpoint.

## 1. SOURCE DISCOVERY

Seul `corpus/family_tree_facts_v0_2.json.discovery_facts` est utilisé pour :

- découvrir les `AbstractPathInvariant` ;
- sélectionner deux chemins source ;
- découvrir la `OperationalRelationRecord` ;
- construire et figer une `TransferableOperationSpec`.

Aucune donnée Organisation n'entre dans cette phase.

## 2. OPÉRATION FIGÉE

La spécification transférable conserve uniquement :

- longueur ;
- séquence de directions ;
- pattern de binding des nœuds ;
- arité ;
- catégorie structurelle de relation ;
- catégories EQUAL/DIFFERENT des champs structurels.

Les identités des opérateurs, nœuds et chemins source ne sont pas conservées
dans le corps transférable. Aucun dictionnaire sémantique n'est introduit.

## 3. TARGET STRUCTURAL GENERATION

Deux références d'opérandes appartenant au corpus Organisation découverte
sont fournies au runtime : `Module_A` et `Projet_X`.

L'opération figée construit un nouvel objet K3 à partir de ces deux opérandes.
Cet objet doit être structurellement nouveau par rapport aux observations
Organisation fournies.

Cette réussite ne constitue pas une preuve de prédiction sémantique.

## 4. STRONG ENDPOINT GATE

Un cas cible séparé est préparé avec :

`O-E07: PROJET_DE(Module_D, Projet_Q)`

Le fait d'endpoint :

`O-E03: PORTE_PAR(Projet_Q, Direction_H)`

est masqué et n'est jamais donné à l'exécution.

Le protocole exige un échec fermé (`NOT_DERIVABLE`) avec aucun endpoint
prédit. Une prédiction positive dans cette situation ne serait acceptable que
si le kernel possédait une règle exécutable indépendante, découverte et figée
avant l'évaluation.

## 5. Résultat attendu / portée

La partie micro-structurelle peut PASSER :

`relation source -> opération abstraite figée -> nouvel objet structurel cible`.

La partie endpoint reste OPEN avec les primitives actuelles :

`opération abstraite -> endpoint sémantique absent du graphe`.

Ce protocole ne ferme donc pas E20-D. Il élimine principalement les deux
modes d'invalidité identifiés dans P4.1–P4.5 : corpus dégénéré et circularité
par lecture/choix du pattern cible.

## Gouvernance

- M1/M6 inchangés.
- M7 exclu.
- aucune consultation du witness avant prédiction.
- aucun endpoint caché présent dans l'entrée d'exécution.
- aucun commit/push effectué par l'outil.

## 6. Revue et adoption (2026-09-21)

Reçu dans le même paquet que les fichiers déjà rejetés `p4_transfer_baseline_v0_1.py`,
`p4_structural_transfer_v0_1.py`, `p4_operation_replay_v0_1.py`,
`p4_operation_execution_v0_1.py` et leurs documents/tests associés (voir
`documentation/P4_Transfer_Review_and_Rejection_2026-09-19.md`) — **ces fichiers restent
non adoptés**, seul le nouveau module `p4r_non_circular_transfer_v0_2.py` et sa dépendance
`e20d_p4_autonomous_transfer_v0_1.py` (P4.3, jamais elle-même mise en cause — seule sa
consommation en aval par P4.4/P4.5 l'était) sont intégrés ici.

Vérification par exécution réelle, dans une copie locale isolée du dépôt (aucun accès
réseau, aucun serveur LAN) :

- `run_p4r(...)` exécuté directement : chaque champ du JSON produit correspond exactement
  à `validation/P4R_non_circular_transfer_2026-09-21.json` — `micro_structural_transfer =
  PASS`, `strong_endpoint_transfer = OPEN_EXPECTED`, `e20d_closure = OPEN`,
  `leakage_audit` confirmant l'absence de fuite d'identité source/cible.
- Les deux modes d'invalidité précédemment prouvés par instrumentation ne se reproduisent
  pas ici : la source (`choose_source_case`) ne lit que `family_tree_facts_v0_2.json`, la
  cible (`Module_A`, `Projet_X`) appartient à un domaine disjoint qui ne peut structurellement
  pas être l'un des deux exemples d'entraînement source ; et `masked_endpoint_gate` ne
  consulte jamais le fait masqué (vérifié : `hidden_endpoint_visible_in_execution_input =
  False`).
- Limite non cachée par le code lui-même : `masked_endpoint_gate` ne fait qu'un contrôle de
  fuite textuelle et renvoie toujours `NOT_DERIVABLE` sans réellement invoquer une tentative
  de dérivation du noyau — c'est honnête (le noyau K3 actuel n'a pas d'évaluateur sémantique
  transitif au-delà de l'égalité structurelle), mais cela signifie que cette moitié du gate
  est une affirmation de portée, pas une expérience falsifiable en l'état.
- Un import mort (`build_derived_operation`, jamais utilisé dans le fichier) trouvé et
  retiré avant intégration.
- 3/3 tests ciblés (`test_p4r_non_circular_transfer_v0_2.py`) + 3/3 tests de la dépendance
  P4.3 (`test_p4_autonomous_transfer_v0_1.py`) passent. Suite complète rejouée dans la copie
  isolée : 473 passed / 1 skipped (le skip live-Ollama déjà documenté), zéro régression.

**Verdict : P4-R v0.2 adopté.** E20-D reste `OPEN` — ce protocole ne le prétend pas fermer,
il ferme seulement les deux défauts méthodologiques de P4.1-P4.5. Le gate d'endpoint fort
reste à concevoir avec une vraie règle de dérivation indépendante avant de pouvoir produire
autre chose que `NOT_DERIVABLE`.
