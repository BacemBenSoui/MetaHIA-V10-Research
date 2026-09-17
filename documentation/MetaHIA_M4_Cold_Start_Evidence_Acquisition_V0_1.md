# MetaHIA — M4 Cold-start / Evidence Acquisition v0.1

Date: 17 septembre 2026  
Baseline: K3-DEV-BASELINE-V0.5  
Kernel: `kernel2.py` inchangé

## 1. Objectif

M4 transforme `UNKNOWN` en objet de pilotage expérimental sans confondre :

```text
DERIVED != EVIDENCE != EPISTEMIC STATUS
```

M4 encadre l'acquisition et la provenance. Il ne décide pas lui-même de la vérité d'une relation.

## 2. Niveaux

```text
A — STRUCTURAL_BACKOFF
B — UNKNOWN_HUMAN
C — EXPLICIT_PROVENANCE
```

Niveau A exploite un fournisseur de récupération/backoff déjà disponible.  
Niveau B conserve `UNKNOWN` et peut produire une demande humaine.  
Niveau C impose une provenance explicite.

## 3. Provenances

```text
GROUNDED_DIRECT
GROUNDED_ANALOGY
UNGROUNDED_HUMAN
```

Une entrée `HUMAN` est obligatoirement `UNGROUNDED_HUMAN`.  
Une entrée analogique reste `GROUNDED_ANALOGY`.  
Une origine de type système ne peut pas compter comme evidence indépendante.

## 4. Indépendance

L'identifiant d'indépendance est :

```text
independent_group || source_id
```

Deux extraits d'un même groupe ne comptent donc qu'une seule fois dans les mesures d'indépendance.

## 5. Protection contre l'auto-validation

M4 rejette :

- une evidence dont `source_id == candidate_id` ;
- une evidence issue d'une source bloquée ;
- une evidence dont `source_id` commence par `M1_ALGEBRA` ;
- toute evidence de type `SYSTEM` comme preuve indépendante ;
- toute evidence humaine déclarée comme grounding direct ou analogique.

## 6. N_min

`measure_n_min()` teste, pour les petits pools contrôlés, toutes les combinaisons d'éléments indépendants jusqu'à la taille maximale demandée. Le critère de succès est fourni par l'évaluateur appelant.

Le moteur ne fixe donc pas arbitrairement un nombre universel de preuves.

## 7. Ledger

Chaque tentative conserve :

```text
attempt_id
candidate_id
level
query_ref
source_ids
independent_groups
accepted_evidence_ids
rejected_evidence_ids
cost
result_state
transition_reason
```

Les transitions conservent l'état précédent, le nouvel état, la raison et les evidence IDs.

## 8. Règles de complétude

M4 est complet microstructurellement lorsque :

1. provenance explicite et validée ;
2. indépendance reproductible ;
3. auto-validation bloquée ;
4. `UNKNOWN` conservé tant qu'aucune évaluation externe ne le change ;
5. escalade A → B → C fonctionnelle ;
6. N_min mesurable ;
7. ledger append-only ;
8. comportement déterministe ;
9. tests critiques passants ;
10. régression globale passante.

## 9. Limites scientifiques

M4 ne prouve pas la qualité de l'information récupérée. Il ne remplace pas M2. Il ne mesure pas encore une véritable valeur de l'information (VOI) pendant une inférence complète. Ces points appartiennent aux étapes M5 et aux validations empiriques.

## 10. Résultat local

- tests M4 ciblés + critiques : **24/24 PASS**
- régression complète : **130/130 PASS**
- compilation : **PASS**
- `kernel2.py` : **inchangé**
- validation tierce : **à exécuter sur paquet gelé**

## 11. Décision

```text
M4 = PASS_MICROSTRUCTURAL_LOCAL
M4 = READY_FOR_THIRD_PARTY_BLIND_VALIDATION
```

Le passage à M5 reste conditionné au gate indépendant et à l'absence de violation des invariants d'évidence.
