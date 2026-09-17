# MetaHIA — E20-D.3 — Operator Space / Operation Discovery v0.1

## Objectif

Tester la transition :

`R(S1,S2) -> R'(O1,O2) -> O=f(O1,O2)`

sans ajouter de primitive au noyau K3 et sans injecter de détecteur sémantique.

## Principe

Chaque structure OBSERVATION porte déjà un opérateur en première position. Cette identité est représentée par `NodeRef`.

Le niveau supérieur construit alors un objet opératoire référencé :

`*O = f(*O1,*O2, common_properties, relation_facts)`

L'objet produit peut ensuite être comparé structurellement à un opérateur déjà existant :

- match structurel -> `IDENTIFIED_EXISTING`
- aucun match -> `CREATED_NEW`

## Séparation des trois niveaux

1. identité : `reference_equal`
2. structure : `structural_equal`
3. valeur/payload externe : hors noyau

Cette séparation est obligatoire également pour les opérateurs.

## Propriétés

Les propriétés et les relations inter-opérateurs sont actuellement des **faits structuraux opaques** fournis par le corpus d'évidence. Le module ne déduit pas encore, à partir des seuls calculs numériques, que `*` est une itération de `+`.

Le cas `+ , + -> +` est donc un test d'identité/reconnaissance, pas encore une preuve d'identification mathématique générale.

## Résultats v0.1

Les tests doivent confirmer :

- réification d'une composition d'opérateurs ;
- comparaison à un opérateur existant ;
- création d'un nouvel opérateur si aucun équivalent n'existe ;
- transport structural des propriétés communes ;
- transport des relations inter-opérateurs ;
- réutilisation récursive de l'opérateur produit ;
- respect de R-V-1.

## Statut

`E20-D.3 = PASS_MICROSTRUCTURAL` lorsque la suite associée est rejouée intégralement.

`E20-D global` reste `OPEN` tant que la découverte d'une opération à partir de comportements observés, et non de faits de propriété fournis comme évidence, n'est pas démontrée.
