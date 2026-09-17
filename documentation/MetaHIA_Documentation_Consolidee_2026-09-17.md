# MetaHIA — Documentation consolidée du projet
## De l’idée initiale à l’évaluation du 17 septembre 2026

### 0. Objet et portée
Cette documentation consolide les jalons, changements de paradigme, hypothèses et validations effectivement établis dans les artefacts de travail disponibles. Elle n’est pas une transcription verbatim de toutes les conversations. Les statuts distinguent toujours hypothèse, capacité locale, validation tierce et résultat empirique.

## 1. Point de départ
MetaHIA a été formulé comme un système qui ne doit pas seulement répondre : il doit décomposer l’information en représentation structurée reconstructible, puis laisser les relations, inférences et états d’incertitude être manipulés explicitement. Le premier principe de travail est donc : `représenter avant de conclure`.

Architecture initiale : extraction → représentation → normalisation → validation → raisonnement optionnel.

## 2. Premier changement de paradigme — de la réponse à la structure
Conséquence : le résultat central n’est plus une réponse textuelle mais une structure qui conserve entités, relations, contexte, provenance et incertitude. Cette orientation a conduit à formaliser MetaHIA Core v1.0 avec propositions, réification, portée, provenance, ambiguïtés et conflits.

## 3. Deuxième changement — du dictionnaire sémantique vers l’algèbre structurelle
Les limites rencontrées sur des cas tels que l’opposition de prédicats, le binding d’arguments ou les relations familiales ont conduit à abandonner l’idée d’ajouter des listes de règles sémantiques au noyau. La question devient : quelles primitives structurelles et quelles opérations suffisent à représenter ces phénomènes sans vocabulaire métier injecté ?

K3 est retenu comme hypothèse minimale expérimentale : `Node`, `Apply`, `Compare`. Ce n’est pas une preuve mathématique de minimalité.

## 4. Troisième changement — les rôles remplacent les classes ontologiques rigides
Une même structure peut jouer le rôle d’un nœud, opérateur, relation, propriété, pattern ou méta-structure selon son usage. La générativité structurelle est prioritaire sur l’interprétation : une structure étrange mais bien formée reste admissible.

## 5. Quatrième changement — identité, structure et valeur sont séparées
R-V-1 impose :
`reference identity ≠ structural equivalence ≠ external value equality`.

Une référence différente n’est jamais fusionnée parce que sa structure est équivalente. Une même référence associée à une structure incompatible doit rester une incohérence détectable.

## 6. Cinquième changement — de Compare pairwise vers le graphe et les chemins
Les essais familiaux ont montré qu’un pairwise Compare ne suffisait pas pour factoriser des relations multi-observations. La représentation graphe/path a donc été introduite.

Un premier corpus familial de 25 observations a produit 19 nœuds, 25 arêtes, 722 chemins, 469 squelettes opérateur/direction et 193 `PathPattern`. L’ajout de six faits a produit 22 nœuds, 31 arêtes, 1300 chemins et 348 `PathPattern`. Ces chiffres mesurent une capacité structurelle de génération et d’exploration, pas la vérité des relations produites.

## 7. Sixième changement — dérivation ≠ preuve
Après l’évaluation historique et les risques d’auto-validation, M2 formalise :
`DERIVATION ≠ EVIDENCE ≠ EPISTEMIC STATUS`.

Une dérivation reste un candidat. `SUPPORTED` et `CONTRADICTED` nécessitent une evidence indépendante; `UNKNOWN` n’est pas un échec. Les preuves support et challenge restent conservées.

## 8. Septième changement — fermeture récursive contrôlée
M3 transforme une capacité locale en processus : Graph → Path → Frontier → Link → Reinjection → Next Pass. La profondeur, les cycles, le nombre de chemins, la provenance et l’idempotence deviennent des objets de contrôle.

Validation tierce M3 : 18/18 PASS sur le périmètre critique.

## 9. Huitième changement — cold-start et valeur de l’évidence
M4 traite le cas où l’information est absente. Au lieu de transformer un manque d’évidence en pseudo-certitude, le système peut escalader : backoff structurel, UNKNOWN + humain, puis provenance explicite.

Statut de projet : `PASS_INDEPENDENT_SCOPE`.

## 10. Neuvième changement — du ROI statique à la politique dynamique
D19 évaluait la valeur d’exploration de façon statique. M5 ajoute une boucle : observation → mesure → décision → résultat → mise à jour de politique. Les décisions possibles sont CONTINUE, DEFER, STOP, REQUEST_EVIDENCE, CHANGE_STRATEGY.

Validation tierce du 17/09/2026 : 26/26, répétée trois fois; 10/10 exigences critiques; paquet intact; aucune fuite sémantique détectée. Le scénario critique montre 62,5 % de réduction de coût pour 70 % du gain et 100 % de couverture utile, sans prétendre généraliser ces chiffres.

## 11. Hypothèses fondamentales regroupées par type de vérification

### A — Vérification théorique / conceptuelle
1. **K3 minimalité expérimentale** : Node + Apply + Compare peuvent couvrir l’espace structurel ciblé sans primitive supplémentaire démontrée nécessaire.
2. **Générativité structurelle** : toute structure générable par les primitives admises est structurellement admissible, même si son interprétation sémantique n’est pas connue.
3. **R-V-1** : identité, équivalence structurelle et valeur doivent être des dimensions distinctes.
4. **Séparation épistémique** : la dérivation ne constitue pas une preuve.
5. **Récursivité contrôlée** : la fermeture doit être séparée de l’évaluation de vérité et bornée par des budgets.
6. **Métacognition fonctionnelle** : elle exige une boucle observée/mesurée/décidée/réévaluée, pas seulement un score ROI.
7. **Apprentissage structurel** : apprendre une distribution d’issues par contexte vaut mieux qu’encoder une règle comme vraie.

### B — Vérification par tests atomiques / locaux
- M1 : tests de primitives et invariants, kernel gelé.
- E20-D D1–D19 : validations microstructurelles de PatternRef, transformations, opérateurs, propriétés, graph/path, réification, replay, émergence, fermeture et ROI.
- M3 : 10/10 ciblés + 8/8 critiques + 140/140 régression.
- M4 : 25/25 ciblés + 131/131 régression.
- M5 : 26/26 ciblés + 157/157 régression.

Ces résultats établissent des invariants de code sur des scénarios déterminés; ils ne suffisent pas à eux seuls pour les claims scientifiques généraux.

### C — Vérification indépendante tierce
- M3 : 18/18, répétition reproductible.
- M4 : statut `PASS_INDEPENDENT_SCOPE` selon la décision de validation consignée dans l’historique; détails externes non intégralement présents dans le répertoire nettoyé.
- M5 : 26/26 sur trois exécutions indépendantes, commande exacte `python -m pytest -q`, Windows/Python 3.13.14/pytest 9.1.1, hashes conformes, aucun fichier modifié, fuite sémantique non détectée.

### D — Vérification empirique / holdout
1. Évaluation historique sur `source_test.json` + annotation humaine : 9842 cas; 3329 SUPPORTED, 3278 CONTRADICTED, 3235 UNKNOWN. MetaHIA historique : couverture décisionnelle 18,83 %, accuracy sur décisions 84,89 %, exact-match 47,10 %, ECE 0,0464. Ces résultats ont surtout servi à identifier les abstentions et leurs causes; ils ne constituent pas une validation finale de la nouvelle architecture.
2. Diagnostic historique : 7989 abstentions; 6589 sans prédicat partagé; 2940 cas `CONTRADICTED → UNKNOWN`. Conclusion : faiblesse principalement représentationnelle, pas un simple problème de seuil.
3. Gate empirique historique : resté fermé car la seconde annotation n’était pas jugée suffisamment indépendante et les 15 traces held-out n’étaient pas celles d’un véritable vérificateur sémantique.
4. Corpus familial : forte activité graphe/path, mais découverte autonome d’une relation générale non démontrée.
5. Boucle de surcharge : +6 observations a produit une croissance mesurable des espaces de chemins; les sorties dérivées n’ont pas été converties en preuve.

## 12. Dette scientifique actuelle
- fermeture générale E20-D ;
- découverte autonome de constantes / neighbourhood patterns ;
- généralisation inter-corpus blind ;
- composition pleinement autonome relation → opération → structure ;
- intégration M2+M3 sur corpus réel ;
- N_min sur corpus réels ;
- apprentissage M6 sans contamination ;
- parser texte→structure ;
- LLM live multi-provider ;
- holdout indépendant du moteur sémantique ;
- benchmark final coût/qualité.

## 13. Règle de développement
Le kernel M1 reste gelé. Une modification du kernel exige backup, nouveau hash, tests complets et nouvelle validation des gates affectées. Aucun dictionnaire sémantique métier ne doit être injecté pour masquer une faiblesse structurelle.

## 14. État final au 17 septembre 2026
```text
M1  FROZEN
M2  STABLE / NON-PROMOTED
E20-D  OPEN SCIENTIFICALLY
M3  PASS_INDEPENDENT_SCOPE
M4  PASS_INDEPENDENT_SCOPE
M5  PASS_INDEPENDENT_SCOPE
M6  IMPLEMENTATION (local, 2026-09-17)
M7  DEFERRED
V6  DEFERRED
```

**Addendum 2026-09-17** : M6 v0.1 implémentée localement, voir
`documentation/MetaHIA_M6_Structural_Learning_V0_1.md`. Prochaine étape : validation tierce
indépendante de M6, sur le même modèle que M3/M4/M5.
