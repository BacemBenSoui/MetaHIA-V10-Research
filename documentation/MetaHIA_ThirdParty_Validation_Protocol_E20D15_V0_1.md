# Validation tierce aveugle — E20-D.15

## But

Valider indépendamment que la synthèse d'opération :

`relation -> operation`

conserve l'identité, la structure et la provenance séparément, et qu'elle refuse les collisions ambiguës.

## Cas obligatoires

1. relation unique -> `CREATED_NEW`
2. une opération équivalente existante -> `IDENTIFIED_EXISTING`
3. deux opérations équivalentes avec références distinctes -> `AMBIGUOUS`
4. mêmes valeurs externes mais références distinctes -> aucune fusion
5. opération synthétisée réutilisée via `Apply`
6. provenance différente mais structure identique -> équivalence structurelle conservée
7. relation incomplète -> refus explicite

## Critère

Aucun nom sémantique (`grandfather`, `commutative`, etc.) ne doit être nécessaire dans le code du test.

Le rapport tiers doit inclure : commandes, versions, stdout/stderr, nombre d'assertions, et traces des trois statuts.
