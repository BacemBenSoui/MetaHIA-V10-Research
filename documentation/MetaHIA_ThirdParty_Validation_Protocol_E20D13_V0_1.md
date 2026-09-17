# MetaHIA — Protocole de validation tierce E20-D.13 v0.1

## Objet

Valider indépendamment la capacité `Path -> PathProperties -> PropertyObjects` et la discipline `Reference != Structure != Value` du kernel fourni.

## Précondition

Le tiers doit exécuter le kernel exactement tel que livré et vérifier son hash SHA-256 contre `tests/E20D13_KERNEL_HASH.txt`.

## Cas à exécuter

### TP1 — Propriétés identiques, identités différentes
Construire deux chemins indépendants avec les mêmes propriétés structurelles. Vérifier :
- `reference_equal` des objets réifiés = False ;
- `structural_equal` des `PathPropertyObject` = True ;
- les provenance/path_id diffèrent ;
- la structure comparable n'inclut pas la provenance.

### TP2 — Valeurs externes identiques, références différentes
Créer deux NodeRef distincts supposés porter la même valeur externe. Vérifier qu'ils ne sont jamais fusionnés par le mécanisme de propriétés.

### TP3 — Incohérence de référence
Créer deux `RefObject` ayant le même ref_id mais des structures différentes. Vérifier que le kernel lève une incohérence `R-V-1` au lieu de déclarer une égalité.

### TP4 — Direction
Construire un chemin inverse et vérifier que `direction_sequence` et `reversed_traversal` sont des propriétés structurales.

### TP5 — Chemin sémantiquement absurde
Utiliser des labels arbitraires tels que `MOTO`, `18`, `FRERE`, `POSSEDE`. Vérifier que la couche D13 extrait les propriétés sans juger leur cohérence humaine.

### TP6 — Provenance
Modifier uniquement les identifiants/provenances des chemins. Vérifier que l'identité/provenance change, mais pas la structure de la propriété.

### TP7 — Bundle
Réifier un `PathProperties` complet deux fois. Vérifier que les deux `RefObject` ont des identités différentes mais des structures désignées identiques.

### TP8 — Régression
Exécuter l'ensemble des `test_*.py` fournis avec le paquet et consigner exactement le nombre de tests passés/échoués.

## Interdictions

Le tiers ne doit :
- ajouter aucun dictionnaire sémantique ;
- modifier le kernel avant l'exécution complète ;
- convertir les labels en concepts humains ;
- considérer une similarité comme une preuve sémantique.

## Livrables attendus

- log d'exécution ;
- résultats TP1–TP8 ;
- hash du kernel exécuté ;
- éventuels contre-exemples minimaux ;
- conclusion limitée à la portée E20-D.13.

## Critère de consolidation

D13 peut être consolidé seulement si les résultats indépendants reproduisent les invariants structuraux et n'identifient aucun nouveau contre-exemple bloquant.
