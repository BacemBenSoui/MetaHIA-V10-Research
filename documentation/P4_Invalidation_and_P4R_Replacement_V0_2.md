# MetaHIA — Invalidation P4.1–P4.5 et remplacement P4-R v0.2

## Statut

Les résultats expérimentaux précédemment publiés sous P4.1 à P4.5 sont
**invalidés comme preuves scientifiques** pour deux raisons documentées :

1. P4.1/P4.2 reposaient sur un mécanisme/corpus dégénéré avec distribution
   d'issues ne permettant pas un vrai test contradictoire.
2. P4.4/P4.5 permettaient de sélectionner un motif cible déjà présent dans les
   données servant ensuite au replay. Le fait de retarder la lecture du witness
   n'éliminait pas cette fuite structurelle.

Aucun chiffre de ces expériences n'est retenu comme preuve d'E20-D.

## Remplacement

P4-R v0.2 impose une séparation de flux :

`SOURCE DISCOVERY -> FREEZE -> TARGET EXECUTION`

L'opération transférable ne contient ni identités d'opérateurs source, ni
identités de nœuds source, ni chemin cible, ni endpoint cible.

Deux sous-gates sont séparés :

### A. Micro-gate structurel

Une relation découverte uniquement sur le domaine Famille est réduite à une
spécification structurale générique, puis appliquée à deux nouveaux opérandes
du domaine Organisation. Le résultat doit être un nouvel objet K3.

Ce résultat valide uniquement la génération d'un **objet structurel nouveau**.
Il ne prouve pas une prédiction sémantique.

### B. Strong endpoint gate

Le cas cible `Module_D -> Projet_Q -> Direction_H` est utilisé uniquement avec
son antécédent `O-E07: PROJET_DE(Module_D, Projet_Q)`. Le fait
`O-E03: PORTE_PAR(Projet_Q, Direction_H)` est absent de l'entrée d'exécution.

Le résultat obligatoire du kernel actuel est `NOT_DERIVABLE` : aucune invention
d'endpoint n'est autorisée.

## Résultat P4-R v0.2

- micro-gate : PASS technique ;
- endpoint gate : `OPEN_EXPECTED` ;
- E20-D : OPEN.

Cette formulation est volontairement plus faible que les conclusions P4.3 à
P4.5 invalidées.

## Invariants anti-circularité

- les claims de vérification ne sont jamais utilisés avant la production du
  candidat structurel ;
- l'endpoint masqué n'est jamais fourni à l'exécution ;
- le pattern cible n'est pas découvert ni sélectionné dans le flux source ;
- les identités de domaine ne sont pas ajoutées comme règles sémantiques ;
- M1/K3 et M6 sont inchangés ;
- M7 est exclu.
