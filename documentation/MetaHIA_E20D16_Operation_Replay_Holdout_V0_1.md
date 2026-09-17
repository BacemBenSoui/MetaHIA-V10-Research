# MetaHIA — E20-D.16 Operation Replay / Holdout Prediction v0.1

## Objectif

Vérifier qu'une opération structurelle déjà découverte et exécutable peut être réappliquée sur un graphe structurel de holdout afin de produire une structure prédite, avec provenance complète.

## Entrée réelle

- `PathPattern` : séquence d'opérateurs/directions et bindings structurels.
- `StructuralGraph` de holdout : observations `OBSERVATION(operator, source_ref, target_ref)` non utilisées pour construire le pattern.
- `start : NodeRef`.

## Opération testée

Le `PathPattern` est utilisé comme descripteur d'opération structurelle : à chaque étape, le moteur recherche dans le graphe de holdout une continuation compatible avec l'opérateur opaque et la direction demandée.

## Sorties

- `REPLAYED` : une continuation unique est trouvée à chaque étape ; un `PathRecord` est produit avec endpoint prédit et provenance.
- `NOT_FOUND` : une étape requise manque ; aucun endpoint n'est forcé.
- `AMBIGUOUS` : plusieurs continuations compatibles dépassent la limite autorisée ; aucune prédiction n'est forcée.
- `predicted_link` : objet `RefObject` optionnel dérivé du chemin rejoué.

## Exemple abstrait

Apprentissage :

`R(A,B)`, `S(B,C)`

et :

`R(X,Y)`, `S(Y,Z)`

produisent le pattern :

`R(FORWARD) -> S(FORWARD)`.

Holdout :

`R(M,N)`, `S(N,P)`

Rejeu depuis `M` :

`M --R--> N --S--> P`

Sortie : `predicted_end = P`.

## Invariants

1. Identité des noeuds par `NodeRef`, jamais par payload.
2. Direction inverse représentée par `PATH_REVERSE`, sans fabriquer un opérateur sémantique `inverse`.
3. Ambiguïté fail-closed.
4. Provenance complète du chemin rejoué.
5. Aucune interprétation sémantique des opérateurs.

## Limite scientifique explicite

D16 ne démontre pas qu'un opérateur sémantique est exécuté, ni qu'une arête absente du graphe peut être inventée correctement. Il démontre le passage :

`structure opératoire réutilisable -> replay sur holdout structurel -> structure prédite/tracée`.

Le prochain niveau devra tester la généralisation vers une opération qui crée ou transforme réellement une structure de sortie, plutôt que de simplement suivre une structure déjà présente dans le holdout.

## Vérification

- Tests ciblés : 7/7 PASS.
- Régression du dépôt : 106/106 PASS.
- Compilation du kernel : PASS.
