# Protocole tiers — MetaHIA E20-D.16

## But

Valider indépendamment le rejeu d'une opération structurelle sur holdout, sans accéder aux assertions internes du test auteur.

## Cas minimaux

1. Rejeu unique et succès.
2. Étape absente -> `NOT_FOUND`.
3. Deux continuations compatibles -> `AMBIGUOUS`.
4. Direction `REVERSE`.
5. Références distinctes avec payloads potentiellement égaux.
6. Vérification de provenance exacte des arêtes utilisées.
7. Vérification qu'aucune arête non présente dans le graphe n'est fabriquée.

## Critères

PASS seulement si :

- le endpoint attendu est retrouvé lorsque la continuation est structurellement unique ;
- aucune décision n'est forcée dans les cas `NOT_FOUND` ou `AMBIGUOUS` ;
- l'identité repose sur les références ;
- la provenance est complète ;
- aucun sens sémantique n'est injecté.

## Attention

Le tiers doit utiliser son propre harness de test et ne pas recopier les assertions du dépôt MetaHIA. Le résultat attendu est un rapport reproductible avec entrées, sorties et verdicts par cas.
