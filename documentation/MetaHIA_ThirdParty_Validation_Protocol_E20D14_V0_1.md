# MetaHIA — Protocole de validation tierce E20-D.14 V0.1

## Objectif
Valider que la découverte de relations opérationnelles est réellement structurelle, référençable, traçable et non sémantique.

## Conditions
Le tiers exécute le code fourni sans modification du kernel et sans ajouter de dictionnaire de domaine.

## Jeux minimaux

### A. Équivalence structurelle
Deux PathPropertyObject distincts, même clé et même valeur.
Attendu : `STRUCTURAL_EQUIVALENCE`, identités distinctes, formes structurelles égales.

### B. Différence structurelle
Même clé, valeurs différentes.
Attendu : `STRUCTURAL_RELATION`, champ `DIFFERENT`.

### C. Clés sans intersection
Clés disjointes.
Attendu : `None` (fail-closed).

### D. Deux chemins isomorphes
Même longueur, même séquence opérateur/direction, nœuds différents.
Attendu : relation structurale exploitable sans dépendre des noms/valeurs.

### E. Deux PathPattern équivalents
Patterns issus de deux corpus indépendants.
Attendu : relation structurelle équivalente sans fusion des références.

### F. Test R-V-1
Deux relations réifiées avec références différentes et structure identique.
Attendu : `reference_equal=False`, `structural_equal=True`.

### G. Test provenance
Même structure, provenance différente.
Attendu : relation structurelle identique ; provenance conservée uniquement dans les records.

### H. Cas généalogique réel
Utiliser les chemins :
- Amanda -> David -> Lucas
- Amanda -> David -> Emma
- Sonia <- David -> Moto

Attendu : relations structurelles décrivables, sans introduction de `GrandParent`, `Oncle`, etc.

## Critères de réussite
- aucun résultat obtenu par dictionnaire sémantique ;
- aucune fusion de NodeRef/RefObject sur égalité de payload ;
- relation reifiable et rejouable ;
- provenance présente ;
- aucun choix arbitraire lorsqu'aucun axe structurel commun n'existe ;
- les cas structurellement équivalents donnent des formes équivalentes indépendamment des identifiants.

## Sortie attendue du tiers
Fournir :
1. commandes exactes exécutées ;
2. résultats par cas ;
3. traces JSON ;
4. hash SHA-256 du kernel utilisé ;
5. tout écart ou résultat inattendu.
