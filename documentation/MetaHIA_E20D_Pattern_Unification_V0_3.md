# MetaHIA — E20-D.1 Unification structurelle PATTERN / SHAPE_PATTERN v0.3

Date: 2026-09-16

## Hypothèse testée

L’unification peut être obtenue par extension du constructeur objet, sans fusionner les représentations internes. Un `PatternRef` porte une référence d’identité et encapsule indifféremment un `PATTERN` ou un `SHAPE_PATTERN`.

Forme générale :

`*P = f(*A, *B, ...)`

L’identité référentielle reste distincte de la structure désignée et de toute valeur externe.

## Implémentation

- `PatternRef` : enveloppe commune pour les deux représentations.
- `ref_object()` : constructeur étendu par dispatch sur le type structurel.
- `pattern_ref()` : constructeur explicite.
- `pattern_structural_equal()` : égalité structurelle inter-représentations.
- `compare_pattern_references()` : comparaison à trois états : `True`, `False`, `None` lorsque la conversion commune perdrait de l’information.
- `structural_signature()` : signature canonique sans dereferencement de payload externe.

Une PATTERN de mapping positionnel pur est levée dans le même espace de réécriture que `ShapeRewrite`. L’opérateur reste un marqueur opaque commun; aucune connaissance sémantique n’est introduite.

## Résultats

### E20-D v0.2 — régression
7/7 PASS.

### Invariant Reference/Value
19/19 PASS.

### E20-D.1 constructeur + unification
7/7 PASS.

### E20-D cross-representation integration
3/3 PASS.

Compilation Python des modules et tests concernés : PASS.

## Ce qui est démontré

1. Deux `PatternRef` distincts peuvent désigner des structures équivalentes sans être la même identité.
2. Un `PATTERN` et un `SHAPE_PATTERN` représentant le même mapping positionnel peuvent être reconnus comme structurellement équivalents.
3. Des transformations différentes ne sont pas fusionnées.
4. Les patterns contenant une contrainte littérale ne sont pas artificiellement convertis en mapping générique.
5. Des références distinctes portant éventuellement des payloads égaux restent distinctes.
6. Le mécanisme est utilisable directement dans la comparaison de transformations E20-D.

## Limites restantes

E20-D n’est pas encore globalement fermé. L’unification démontrée couvre les mappings positionnels purs et les réécritures d’arbre canoniques correspondantes. Elle ne prouve pas l’identification de fonctions arbitraires ni l’unification sans perte de toutes les formes possibles de `PATTERN` et `SHAPE_PATTERN`.

Statut : **E20-D = OPEN** ; **E20-D.1 = PASS_MICROSTRUCTURAL**.

## Principe architectural ajouté

> Toute structure calculée pouvant être manipulée récursivement doit disposer d’une identité référentielle indépendante de sa structure et de sa valeur.

Corollaire : `NodeRef` et `PatternRef` appartiennent au même mécanisme de séparation identité/structure/valeur.
