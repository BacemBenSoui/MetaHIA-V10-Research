# Audit de couche du vérificateur P1 (2026-09-25)

Audit en lecture seule, mené dans le dépôt MetaHIA-V6 (branche
`feat/v6-wp23-verifier-safety`, à partir de `main` `eaf48ce`) et dans ce dépôt
(`kernel2.py` `c76adfd2…efc9aa9`). Il a été demandé par le porteur du projet après le
FAIL du test n°1 : avant de corriger le moteur, **comprendre par quel chemin exact un
SUPPORTED est produit**.

## 1. Chemin réel du P1

```text
SemanticVerifier.verify_text (verification/semantic_verifier.py)
  └─ PredicateEntailment.decide(claim, evidence) (verification/predicate_entailment.py)
       ├─ _tokens : minuscules, expressions régulières, liste STOP, table VERB_MAP, table SYN
       ├─ règles de contradiction : rôles, attributs, négation portée, cardinalité
       └─ _same_core : ratio de couverture des mots de la claim ≥ 0,78 (ou 0,90) → SUPPORTED
```

`ArgumentBindingWP05` et `ArgumentStructure` réutilisent les mêmes fonctions lexicales.

## 2. Absence de K3, M1 et M2 dans `verification/`

`verification/` n'importe que la bibliothèque standard et ses propres modules. Aucun
import de `kernel2` (K3), de `research/k3_spike_e13a2`, de `metahia_m1`, de
`metahia_m2` ni de `structural/`. Dans V6, M1 et M2 ne sont appelés que par
`runtime/v8_relational_bridge.py`, qui n'appelle pas le vérificateur. **Le vérificateur
P1 et le Core sont deux systèmes disjoints.**

## 3. Mécanisme lexical actuel

Le verdict est pris directement sur des ensembles de mots, sans aucune représentation
Node/Apply intermédiaire. Conséquences observées :
- **mots supprimés avant comparaison** : `before`, `after`, `under`, `over`, `alone`,
  `all`, `every`… sont dans `STOP` ;
- **tolérance de couverture** : un mot de contenu manquant ou substitué passe sous le
  seuil de 78 % ;
- **connaissance lexicale limitée** aux tables `VERB_MAP` et `SYN`, bâties sur le
  vocabulaire de développement. D'où l'UNKNOWN massif sur un vocabulaire nouveau.

## 4. Distinction structure, projection, épistémique

```text
K3 structural result  ≠  semantic interpretation  ≠  epistemic verdict
```

Le vérificateur actuel confond les trois : un recouvrement de mots (résultat pseudo-
structurel) devient directement un verdict (épistémique), sans interprétation
explicite ni couche de projection.

## 5. *Cairo / Oslo*

- Pour K3, `in(…, oslo)` et `in(…, cairo)` ont la même forme, avec une feuille
  différente. `compare()` renvoie `None` (aucune transformation ne les relie) et
  `structural_equal` est faux.
- Le bon verdict par défaut est UNKNOWN, faute de relation connue entre les deux
  villes.
- Le SUPPORTED observé venait du ratio de 78 % de `_same_core`, pas du Core.

Vérifié : `P1_CORE_CAPABILITY_RESULT_2026-09-25.md`, H-P1-STRUCT PASS.

## 6. *before / after*

- Dans le vérificateur, `before` et `after` étaient supprimés comme mots vides, donc les
  deux phrases devenaient identiques.
- Dans K3, `op:before` et `op:after` sont deux références d'opérateur distinctes :
  forme identique, opérateur différent, `compare()` = `None`.
- Le passage à CONTRADICTED exige une relation d'opposition. K3 ne l'exploite pas seul
  (B0), mais une projection le fait si la relation est fournie comme donnée
  (H-P1-NEG-B PASS).

## 7. Statut réel de la négation dans le Core

- **K3 (`kernel2.py`) n'a aucune primitive de négation.**
- `neg(P)` se représente comme une application ordinaire d'un opérateur `op:neg`, sans
  rien modifier au noyau. La portée est conservée et reste discriminante
  (H-P1-NEG-A PASS).
- Ailleurs dans V6 : M2 porte une polarité **de preuve** (`EvidencePolarity.SUPPORT` /
  `CHALLENGE`), et `structural/extended_logic.py` une négation **de valeur de vérité**,
  sous forme de table. Ni l'une ni l'autre n'est une négation structurelle de
  proposition dans K3.

## 8. Statut de la partie A de WP23 (V6)

La partie A, commit `b104251` dans MetaHIA-V6, est un **filet de sécurité fail-closed
temporaire** posé dans `PredicateEntailment`. Elle transforme un SUPPORTED risqué en
UNKNOWN : couverture complète, relations opposées, marqueurs d'exclusivité, polarité
portée.

**Ce n'est pas une implémentation de l'architecture MetaHIA.** Décision du porteur :
elle reste active, **sans extension lexicale** (la partie B lexicale est suspendue),
et ne doit pas devenir l'architecture par accumulation de règles.

## 9. Hypothèses H-P1-STRUCT et H-P1-NEG

Pré-enregistrées et testées dans `validation/p1_core_capability_2026-09-25/`.
Résultat : **PASS**, voir `P1_CORE_CAPABILITY_RESULT_2026-09-25.md`. Il s'agit d'une
expérience de capacité du Core, confirmatoire par construction, sans test de la
passerelle texte → structure.

## 10. Séparation V6 ↔ V10-Research

- Cette expérience et ses conclusions restent dans V10-Research.
- **Rien n'est intégré dans V6** : ni K3 dans le vérificateur, ni la couche de
  projection du harnais.
- Toute intégration exige le statut `EMPIRICALLY VALIDATED` et une décision explicite
  du porteur du projet (document de passation, §2.3).
- `research/k3_spike_e13a2/` dans V6 reste l'ancêtre figé.
