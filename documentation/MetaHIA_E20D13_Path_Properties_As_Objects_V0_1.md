# MetaHIA — E20-D.13 : Path Properties as Structural Objects v0.1

Date: 2026-09-17
Baseline: K3-DEV-BASELINE-V0.5

## Objectif

Transformer les propriétés descriptives extraites d'un `PathRecord` en objets
structurels référençables, comparables et réutilisables par les mêmes
mécanismes génériques, sans créer une ontologie rigide `PROPERTY`.

## Principe

Une propriété de chemin est un objet calculé :

`*P = f(path)`

Elle possède :

- une identité (`property_id` / `RefObject.ref`),
- une structure (`key`, `value`),
- une provenance (`path_id`, `provenance`).

La structure est indépendante de l'identité et de la provenance.

Deux propriétés issues de chemins différents peuvent donc être
`structural_equal=True` si leur couple `(key, value)` est identique, sans
fusionner leurs identités.

## Propriétés actuellement extraites

- `length`
- `operator_sequence`
- `direction_sequence`
- `node_sequence`
- `distinct_node_count`
- `distinct_operator_count`
- `repeated_operator`
- `reversed_traversal`
- `branching_at_start`
- `branching_at_end`

Ces clés sont des marqueurs structurels de la couche d'exécution. Elles ne
constituent pas un vocabulaire sémantique du core.

## Nouvelles capacités

`PathProperties.as_objects()` produit dix `PathPropertyObject`.

`path_property_objects(path, graph)` extrait directement ces objets.

`reify_path_property()` réifie une propriété comme `RefObject`.

`reify_path_properties()` réifie le bundle complet.

`structural_equal()` et `structural_signature()` reconnaissent désormais
`PathPropertyObject` et ignorent son identité/provenance lorsqu'une comparaison
structurelle est demandée.

## R-V-1

L'identité d'un `RefObject` reste visible dans `structural_signature()` de
l'enveloppe : deux objets `RefObject` distincts ont des signatures différentes.
Pour comparer le contenu désigné, on compare `x.structure` et `y.structure`.

Ainsi :

`reference_equal(x, y) = False`

peut coexister avec :

`structural_equal(x.structure, y.structure) = True`.

Aucun payload externe n'est utilisé pour l'identité.

## Résultat de validation

Tests ciblés : 8/8 PASS.

Régression complète du répertoire : 84/84 PASS.
Les tests ciblés Path/Pattern/Graph : 30/30 PASS.

Compilation : PASS.

## Portée scientifique

E20-D.13 démontre le passage :

`Path -> PathProperties -> PropertyObjects`

Il ne démontre pas encore que ces propriétés sont découvertes comme des
concepts sémantiques nommés, ni qu'elles permettent automatiquement de
construire une opération. Ces étapes restent ouvertes.

## Prochaine étape

Le chantier suivant doit comparer/composer ces objets de propriété pour faire
émerger des relations structurelles entre propriétés, puis alimenter la
construction d'opérateurs/règles sans injection sémantique.

## Validation tierce recommandée

Une validation indépendante est recommandée avant toute consolidation de D13. Le tiers devra notamment tester :

1. deux propriétés de chemins indépendants ayant même `(key,value)` mais des identités/provenances différentes ;
2. même référence avec contenu structurel incohérent ;
3. propriétés contenant des références distinctes portant éventuellement des valeurs externes identiques ;
4. chemins inverses et mélanges FORWARD/REVERSE ;
5. chemins structurellement plausibles mais sémantiquement absurdes ;
6. absence de fuite de provenance dans la structure comparable ;
7. re-jouabilité sur corpus indépendant et vérification du hash du kernel.

Le tiers doit fournir les entrées, sorties observées, verdicts et écarts, sans modifier le kernel avant comparaison.
