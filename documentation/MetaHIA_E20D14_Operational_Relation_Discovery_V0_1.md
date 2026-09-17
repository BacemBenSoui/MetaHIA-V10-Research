# MetaHIA — E20-D.14 : Découverte de relations opérationnelles V0.1

Date : 17 septembre 2026
Socle : K3-DEV-BASELINE-V0.5 + maintenance R-V-1 E20-D.14

## 1. Objectif

E20-D.14 teste le passage de propriétés/path structures déjà produites par le core à une relation opérationnelle explicite, sans dictionnaire sémantique de domaine.

Entrée générique :

    X1, X2

Sortie :

    OperationalRelationRecord(X1, X2)

La relation enregistrée décrit les propriétés structurelles communes et leurs différences. Elle est ensuite réifiable comme un objet RefObject.

## 2. Principe

Le mécanisme n'invente pas le sens d'une relation. Il exploite uniquement les propriétés structurelles déjà calculées : longueur, séquence d'opérateurs, directions, bindings, position groups, etc.

Un résultat `STRUCTURAL_EQUIVALENCE` signifie que les propriétés communes comparées sont toutes structurellement équivalentes.

Un résultat `STRUCTURAL_RELATION` signifie qu'au moins une propriété commune est différente.

Aucune fusion d'identité n'est effectuée.

## 3. Discipline R-V-1

- l'identité d'un objet reste portée par sa référence ;
- la structure désignée est comparée indépendamment de cette identité ;
- la provenance reste hors de la forme structurelle afin de permettre la comparaison entre dérivations indépendantes ;
- une incohérence "même référence + structure différente" reste une erreur interne, non une égalité.

## 4. Impact kernel

Deux corrections de maintenance ont été incluses dans `kernel2.py` :

1. `compare()` retourne `None` pour deux structures identiques, au lieu de fabriquer un faux SHAPE_PATTERN d'identité.
2. `_compare_observations()` utilise `_kernel_values_equal()` au lieu de `!=` brut, afin de respecter R-V-1 dans la détection des positions variables.

Aucune nouvelle primitive ontologique n'est ajoutée à K3.

## 5. Limite scientifique volontaire

E20-D.14 ne réalise pas encore :

    relation entre propriétés -> opération génératrice

et ne réalise pas non plus :

    opération génératrice -> nouvel opérateur validé

Le résultat est une réification structurelle d'une relation observée entre objets structuraux.

## 6. Exemple

Pour deux chemins ayant :

    operator_sequence = (MERE_DE, ENFANT_DE)
    direction_sequence = (FORWARD, REVERSE)
    length = 2

le moteur peut établir une équivalence structurelle avec un autre chemin de même squelette, même si les références de nœuds et les identifiants de chemin diffèrent.

Pour deux chemins de même longueur mais dont les directions diffèrent, le résultat devient une relation structurelle décrivant cette différence.

## 7. Résultats

Tests ciblés E20-D.14 : 8/8 PASS.
Régression complète des tests du répertoire : 91/91 PASS.
Compilation : PASS.

## 8. Statut

E20-D.14 = PASS_MICROSTRUCTURAL.

E20-D global reste OPEN.

La consolidation indépendante par un tiers est recommandée avant toute promotion de cette capacité en statut plus élevé.
