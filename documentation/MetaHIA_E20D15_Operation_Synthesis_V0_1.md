# MetaHIA — E20-D.15 — Synthèse / réification d'opération V0.1

## Objectif

Transformer une `OperationalRelationRecord` déjà découverte en un objet opérationnel référençable :

`OperationalRelation -> DerivedOperationRef`

Le résultat n'exécute aucune sémantique externe. Il devient simplement un objet structurel utilisable par `Apply`.

## Contrat

- `IDENTIFIED_EXISTING` : exactement une opération existante est structurellement équivalente.
- `CREATED_NEW` : aucune opération existante équivalente ; une nouvelle référence est créée.
- `AMBIGUOUS` : plusieurs références distinctes possèdent la même structure ; le moteur refuse de sélectionner.

## Invariants

1. Référence, structure et valeur restent séparées.
2. La provenance est conservée dans le `DerivedOperationRecord`, mais n'entre pas dans l'équivalence structurelle de l'opération.
3. Le nouvel objet n'est pas déclaré sémantiquement vrai.
4. `Apply` construit une application structurelle ; il n'évalue pas le sens du nouvel opérateur.

## Chaîne

`S1,S2 -> OperationalRelation -> DerivedOperation -> Apply(DerivedOperation, operands)`

## Limite volontaire

Cette étape ne démontre pas encore qu'une opération calculée reproduit une transformation cible inconnue. Elle démontre seulement la réification fidèle et la réutilisabilité de l'opération comme objet K3. La vérification d'une transformation sur holdout reste une étape ultérieure.
