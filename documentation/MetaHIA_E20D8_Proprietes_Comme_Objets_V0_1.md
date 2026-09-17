# MetaHIA — E20-D.8 : propriétés et méta-structures comme objets

**Date : 17 septembre 2026**
**Socle : K3-DEV-BASELINE-V0.5**
**Statut : PASS_MICROSTRUCTURAL**

## 1. Directives stabilisées

Le core ne doit pas transformer `Property`, `Relation` ou `MetaStructure` en classes ontologiques rigides. Une entité calculée est un objet structurel référencé :

`*P = f(*A, *B, ...)`

La distinction demeure :

`Reference identity != Structural equivalence != External value`

Une structure nouvellement produite est admissible dans l’espace structurel sans devoir appartenir à un vocabulaire fermé. Son statut épistémique est géré en dehors de la constructibilité structurelle.

## 2. Extension du mécanisme Apply

Le kernel conserve les deux usages historiques de `Apply` pour `PATTERN` et `SHAPE_PATTERN`. Il ajoute un **usage constructeur générique** :

`apply_operator(*O, *P1, *P2, ...) -> Structure`

et l’entrée publique `apply()` accepte la même forme. L’opérateur est manipulé uniquement par référence opaque. Aucun sens externe n’est inspecté.

Ainsi :

`*M = f(*P1, *P2)`

produit une structure qui peut ensuite être réifiée :

`*M12 = M`

puis réutilisée :

`*M123 = g(*M12, *P3)`

Il s’agit d’une composition récursive de structures, pas d’une nouvelle primitive sémantique.

## 3. Propriétés comme objets

Une propriété découverte n’a pas besoin d’un `PROPERTY` fondamental du kernel. Elle peut être portée par un `RefObject` dont le corps est lui-même une structure ordinaire. Elle peut donc :

1. être comparée structurellement ;
2. être réifiée sous une nouvelle référence ;
3. devenir opérande d’une nouvelle structure ;
4. participer à une méta-structure ;
5. être comparée à nouveau à un niveau supérieur.

C’est la base de la fermeture récursive recherchée.

## 4. Correction R-V-1 intégrée à D8

Un contrôle de régression a révélé qu’un chemin interne de `pattern_is_applicable()` utilisait encore l’égalité brute pour une `literal_constraint` portant un `RefObject`. Le kernel utilise désormais `_kernel_values_equal()` dans les chemins décisionnels concernés.

Le contrat est :

- même référence + même structure -> `EQUAL` ;
- références différentes + structure équivalente -> `EQUAL` pour une comparaison structurelle ;
- même référence + structures différentes -> `ValueError` d’incohérence ;
- références différentes + structures différentes -> `DIFFERENT`.

## 5. Transparence ciblée des RefObject dans E18

La réserve précédente sur `RefObject(O(A,B))` a été rejouée. Le kernel peut maintenant voir à travers l’enveloppe lorsque le corps référencé est précisément une application récurrente du même opérateur étudié.

Cette transparence n’est **pas** généralisée à tout `RefObject`. Le wrapper reste une identité structurelle propre dès qu’aucune règle de traversée structurelle n’est applicable. Cela évite de confondre réification et expansion automatique.

## 6. Tests

- E20-D.8 ciblé : **12/12 PASS**.
- Régression R-V-1 : **7/7 PASS**.
- Fichiers `test_*.py` du répertoire : **12/12 PASS**.
- Compilation Python : **PASS**.

## 7. Ce qui n’est pas démontré

D8 ne démontre pas encore que MetaHIA sait découvrir automatiquement la sémantique d’une propriété. Il démontre l’infrastructure nécessaire pour que la propriété découverte reste un objet du même espace structurel et puisse être composée récursivement.

La distinction reste :

`observed -> structurally derived -> historical/statistical rapprochement -> epistemic interpretation`

Le core ne doit pas remplacer l’objet original par une interprétation statistique ultérieure.

## 8. Statut de gouvernance

`R-V-1 : CLOSED sur les chemins internes audités`

`E20-D.8 : PASS_MICROSTRUCTURAL`

`E20-D global : OPEN`

La prochaine validation doit porter sur la comparaison/composition de plusieurs propriétés dérivées et sur la possibilité de construire une nouvelle structure opératoire sans réintroduire de dictionnaire sémantique.
