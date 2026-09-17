# MetaHIA — E20-D.4 — Operator Relation Discovery v0.1

## Objectif

Passer de la relation structurelle observée entre deux structures `R(S1,S2)` à la relation entre les opérateurs déjà présents dans ces structures, sans fournir cette relation comme connaissance préalable.

## Chaîne démontrée

```text
S1, S2 (paires observées)
        ↓
extraction de O1, O2 depuis la position opérateur
        ↓
agrégation des paires O1 → O2
        ↓
relation opératoire observée R'(O1,O2)
        ↓
fact structural OPERATOR_MAPPING
        ↓
réutilisation du mécanisme Operator Space
        ↓
O = f(O1,O2) sous forme d'objet référencé
```

## Règles

1. L'opérateur est déjà un constituant structurel de l'`OBSERVATION`.
2. L'identité des opérateurs est portée par `NodeRef`.
3. Une même source opératoire doit conduire vers une cible cohérente sur les observations fournies.
4. Une contradiction est enregistrée et ne doit pas être résolue par devinette.
5. Aucune interprétation sémantique de `+`, `*`, etc. n'est effectuée.
6. La découverte de la relation n'implique pas encore la découverte de ses propriétés mathématiques.

## Exemple minimal

Observations appariées :

`+(A1,B1) → +(A1,B1)`
`+(A2,B2) → +(A2,B2)`
`+(A3,B3) → +(A3,B3)`

Le moteur découvre :

`R'(+,+)`

puis peut transmettre ce fait à la couche Operator Space.

Exemple non trivial :

`+(A1,B1) → *(A1,B1)`
`+(A2,B2) → *(A2,B2)`
`+(A3,B3) → *(A3,B3)`

Le moteur découvre :

`R'(+ , *)`

sans conclure que `*` signifie multiplication ni que la relation est une itération. Ces interprétations nécessitent une étape ultérieure fondée sur les comportements/propriétés observés.

## Limites

- Le mécanisme actuel apprend une relation observée de type mapping déterministe `O1 → O2`.
- Avec des opérateurs opaques et un nombre fini d'exemples, il ne peut pas identifier à lui seul une loi mathématique générale.
- `O=f(O1,O2)` est actuellement réifié comme structure relationnelle; la dérivation autonome de `f` à partir du comportement reste ouverte.
- Le prochain test doit relier les propriétés/comportements observés des opérateurs à une composition identifiée ou à la création d'un nouvel opérateur.

## Statut

**E20-D.4 = PASS_MICROSTRUCTURAL**

Ce résultat ne ferme pas E20-D globalement.
