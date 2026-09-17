# MetaHIA — M5 — Metacognitive Dynamic Controller v0.1

## 1. Statut

- Baseline : K3-DEV-BASELINE-V0.5
- M1 : FROZEN / STABLE
- M2 : STABLE / NON-PROMOTED
- M3 : PASS_INDEPENDENT_SCOPE
- M4 : VALIDATION TIERCE POSITIVE (entrée M5)
- M5 : `PASS_MICROSTRUCTURAL_LOCAL / READY_FOR_THIRD_PARTY`
- Kernel `kernel2.py` : **inchangé**

## 2. Objectif

M5 transforme le contrôleur ROI statique E20-D.19 en une politique qui observe les conséquences de ses propres décisions et adapte sa stratégie à partir de résultats mesurés.

Chaîne :

```text
Context + Static ROI
        ↓
   M5 Decision
        ↓
 Structural action / evidence request
        ↓
   Observed outcome
        ↓
 M5 policy update
        ↓
 next decision
```

M2 reste la seule couche autorisée à attribuer un statut épistémique. M5 peut enregistrer une transition fournie par l'appelant, mais ne la juge pas.

## 3. Décisions

```text
CONTINUE
DEFER
STOP
REQUEST_EVIDENCE
CHANGE_STRATEGY
```

`CONTINUE` est l'équivalent dynamique de `EXPLORE` du contrôleur E20-D.19.

## 4. Variables observées

```text
depth
uncertainty
provenance
conflict
novelty
redundancy
cost
expected_gain
historical_outcome
```

Aucune signification sémantique de relation, nœud ou opérateur n'est inspectée.

## 5. Politique

Le contexte est canonisé en clé structurale/control. La politique maintient, par contexte :

- nombre d'observations ;
- gain réalisé ;
- coût réalisé ;
- ROI réalisé ;
- taux d'issues utiles.

Une adaptation n'est autorisée qu'après `min_observations_for_adaptation` observations et lorsqu'un drift mesuré dépasse `drift_threshold`.

Une dérive négative entraîne un ajustement conservateur. Une dérive positive permet d'actualiser le gain attendu. Un faible taux d'utilité historique peut produire `CHANGE_STRATEGY`.

## 6. Provenance / épistémique

M5 ne transforme jamais une dérivation en preuve. Les transitions épistémiques sont de simples observations externes :

```text
DERIVATION ≠ EVIDENCE ≠ EPISTEMIC STATUS
```

## 7. Déterminisme

À historique de politique identique et contexte identique, la décision est déterministe. Chaque observation incrémente la version de politique ; une simple consultation ne la modifie pas.

## 8. Benchmark critique

`dynamic_vs_exhaustive()` compare une trajectoire dynamique à une baseline exhaustive externe.

KPI :

- coût dynamique ;
- coût de la baseline exhaustive ;
- réduction de coût ;
- gain réalisé ;
- rétention de gain ;
- couverture utile ;
- séquence des décisions.

La baseline exhaustive et la définition de « utile » sont fournies par le banc expérimental et ne sont pas inventées par M5.

## 9. Résultats locaux

- Tests M5 unitaires : **14/14 PASS**
- Tests critiques M5 : **10/10 PASS**
- Tests benchmark dynamique : **2/2 PASS**
- Tests ciblés cumulés : **26/26 PASS**
- Régression globale : **157/157 PASS**
- Compilation : **PASS**
- Kernel modifié : **NON**

## 10. Limites

Ce résultat ne démontre pas encore un avantage cognitif général. Il démontre une adaptation de politique mesurée sur un espace de contrôle structurel et un benchmark contrôlé.

Restent ouverts :

1. validation tierce aveugle ;
2. inférence relationnelle réelle de plus grande taille ;
3. comparaison exhaustive vs dynamique sur plusieurs corpus ;
4. preuve de gain computationnel sans perte de couverture utile ;
5. apprentissage plus riche de M6.

## 11. Gate M5

Promotion tierce requise après :

```text
LOCAL PASS
 +
BLIND THIRD-PARTY PASS
 +
NO SEMANTIC LEAK
 +
REPEATABILITY
 +
DYNAMIC VS EXHAUSTIVE MEASUREMENT
```

M6 n'est pas promu tant que M5 n'est pas démontré sur un protocole indépendant.
