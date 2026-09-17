# MetaHIA — Protocole de validation tierce E20-D.18 v0.1

## But
Vérifier indépendamment la fermeture récursive structurelle et la séparation identité/structure/valeur.

## Préconditions
Utiliser le `kernel2.py` livré avec le SHA-256 indiqué dans le rapport de développement. Ne pas modifier le code source ni ajouter de règle sémantique.

## Cas obligatoires
1. Construire `R(A,B)` + `S(B,C)` ; découvrir `A -> C` ; réifier le lien.
2. Réinjecter le lien ; vérifier qu'il devient une arête supplémentaire.
3. Ajouter `T(C,D)` ; vérifier que le lien généré permet `A -> C -> D`.
4. Générer un second lien `A -> D`, le réinjecter, puis vérifier une nouvelle exploration avec `U(D,E)`.
5. Vérifier que le graphe original n'est pas modifié.
6. Vérifier qu'un lien sémantiquement inconnu n'est pas filtré.
7. Vérifier deux liens de références différentes mais de structure équivalente.
8. Vérifier qu'un lien invalide est refusé.

## Critères
- Aucune fusion de références sur seule égalité de valeur.
- Aucun nom relationnel ajouté par le moteur.
- Provenance observable à chaque itération.
- Aucun résultat forcé en cas d'invalidité/ambiguïté.
- Reproductibilité de la trace.

## Verdict tiers
Classer séparément chaque cas : PASS, FAIL, ou INCONCLUSIVE. Aucun PASS global ne doit être déclaré si un invariant R-V-1 est violé.
