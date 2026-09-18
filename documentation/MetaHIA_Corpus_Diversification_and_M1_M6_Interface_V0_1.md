# MetaHIA — Diversification du corpus et interface minimale M1–M6 v0.1

Date : 2026-09-18  
Statut : **expérimental / non promotionné**

## 1. Objectif

Cette étape de Priorité 3 traite deux risques distincts :

1. la validation empirique M6/M7 était concentrée sur le seul domaine fictif de l'arbre généalogique ;
2. les contrats de transport entre M1–M6 n'étaient pas encore réduits à une interface minimale explicite.

M7 reste volontairement hors de cette interface. L'objectif est de pouvoir tester la chaîne structurelle M1–M6 sans faire de la sortie LLM une dépendance architecturale.

## 2. Second domaine : organisation/projets

Le corpus `corpus/organization_facts_v0_1.json` introduit un domaine indépendant : équipes, projets, directions et modules.

- 18 faits de découverte ;
- 10 faits d'évidence, disjoints des faits de découverte ;
- 24 témoins de vérification indépendants ;
- 6 témoins volontairement contradictoires ;
- 27 patterns candidats considérés ;
- 15 patterns sans témoin utilisable, explicitement exclus ;
- 24 `StructuralOutcomeRecord` réellement produits par la chaîne M4/M6 ;
- 12 règles structurelles distinctes ;
- profondeurs 1 et 2 représentées ;
- 18 `SUPPORTED` / 6 `CONTRADICTED`.

Le corpus familial n'est pas réutilisé comme source de faits. Les labels de relations du corpus organisationnel sont distincts de ceux du corpus familial.

## 3. Première mesure M6 sur le nouveau domaine

Avec `split_by_rule(val_fraction=0.2, holdout_fraction=0.2, seed=0)` :

- train : 16 enregistrements / 8 règles ;
- validation : 4 / 2 règles ;
- holdout : 4 / 2 règles ;
- Brier holdout : **0,6953125** ;
- ECE non utilisé comme critère de promotion dans ce test.

Cette valeur n'est **pas** présentée comme une amélioration ou une dégradation par rapport au corpus familial : les populations, règles et distributions diffèrent. Elle constitue un premier témoin de généralisation intra-domaine sur des règles non vues, et montre surtout que la diversification ne produit pas artificiellement un score parfait.

## 4. Limite importante : transfert inter-domaines non démontré

M1/M6 identifient actuellement une règle par sa forme structurelle qui conserve les opérateurs/références structurelles. Deux domaines ayant des labels d'opérateurs différents ne deviennent donc pas automatiquement une même règle.

Le second corpus démontre une validation **dans un domaine indépendant**, mais ne prouve pas encore un transfert de règle entre domaines. Un futur test de transfert devra définir expérimentalement une représentation d'abstraction commune, sans ajouter de dictionnaire sémantique caché.

## 5. Interface minimale M1–M6

Le module `m1_m6_interface_v0_1.py` introduit cinq contrats transport :

```text
M1StructuralPacket
        ↓
M2EpistemicPacket
        ↓
M4EvidencePacket
        ↓
M5ControlPacket
        ↓
M6LearningPacket
```

M3 fournit des structures/chemins et leur profondeur avant le transport, mais n'est pas transformé en nouveau type sémantique.

### Invariants

- dérivation structurelle ≠ preuve ;
- preuve ≠ statut épistémique ;
- provenance M4 conservée explicitement ;
- contexte de contrôle M5 séparé des résultats M6 ;
- les trois états M6 restent `SUPPORTED`, `CONTRADICTED`, `UNKNOWN` ;
- aucune dépendance à M7/LLM ;
- aucun dictionnaire sémantique de domaine ;
- interface additive : les modules existants ne sont pas remplacés.

## 6. Ce que cette étape ne démontre pas

Elle ne démontre pas :

- la généralisation inter-domaines ;
- une amélioration de calibration par rapport au corpus familial ;
- une autonomie de découverte E20-D ;
- la fiabilité du parseur M7 ;
- une intégration M7 ;
- la readiness préproduction.

## 7. Tests ajoutés

- `tests/test_corpus_diversification_v0_1.py`
- `tests/test_m1_m6_interface_v0_1.py`

Les tests vérifient notamment l'indépendance du second domaine, la production réelle des records M6, l'existence d'un holdout par règle et le caractère M7-free de l'interface.

## 8. Décision de gouvernance

La Priorité 3 est considérée comme **implémentée expérimentalement** mais pas comme une fermeture scientifique globale.

Prochaine étape logique : exécuter la suite critique puis la suite complète, puis examiner si l'interface minimale doit être ajustée à partir des deux corpus avant d'envisager une véritable expérience de transfert inter-domaines.

## 9. Revue et intégration (2026-09-18)

Ce paquet a été reçu en zip, inspecté fichier par fichier, exécuté réellement (pas seulement
lu), et intégré après correction. Vérifications effectuées :

- Diff complet contre le dépôt de travail : les seuls fichiers réellement nouveaux sont les 7
  listés en Sec. 7 plus ce document et les deux fichiers de corpus (Sec. 2) — aucune
  modification d'un fichier gelé, aucun fichier hors périmètre.
- Les 5 tests originaux exécutés réellement contre le dépôt : tous les chiffres cités
  (27 candidats, 24 enregistrements, 15 exclusions, 12 règles, split 16/4/4, Brier
  0,6953125) sont **confirmés exacts**, pas seulement plausibles.
- Aucun code réseau, `eval`/`exec`, ou appel système dans les fichiers proposés.

**Un bug réel trouvé et corrigé avant intégration** : `m6_corpus_from_organization_v0_1.py`
réutilisait le préfixe `record_id` `"realv2::"` déjà utilisé par
`m6_corpus_from_m4_m5_v0_2.py` (corpus familial). Sans correction, combiner un jour les deux
corpus (exactement le scénario de « transfert inter-domaines » que ce document anticipe en
Sec. 4/8) aurait rendu les enregistrements des deux domaines indistinguables par préfixe —
violation de la convention déjà établie dans ce projet (chaque mécanisme a un préfixe unique).
Corrigé en `"orgv1::"` ; test de non-régression dédié ajouté.

**Améliorations ajoutées** (le paquet original avait une couverture de tests fine, en dessous
de la rigueur déjà établie ailleurs dans ce projet) :
- `m1_m6_interface_v0_1.py` : `M1StructuralPacket.validate()` ne vérifiait pas le type de
  `structure` — un objet mal typé passait la validation silencieusement et n'échouait que plus
  tard, avec un message confus, à l'intérieur de `StructuralOutcomeRecord`. Ajout d'une
  vérification explicite (`Node`/`PathPattern`) à la frontière de l'interface, avec message
  clair.
- `tests/test_m1_m6_interface_v0_1.py` : passé de 2 à 13 tests — ajout de la couverture
  fail-closed manquante (identifiant de paquet vide, type de structure invalide, profondeur
  négative, novelty/redundancy hors intervalle, issue épistémique inconnue, provenance M4
  inconnue, gain/coût négatifs, construction bout en bout d'un vrai
  `StructuralOutcomeRecord`).
- `tests/test_corpus_diversification_v0_1.py` : passé de 3 à 7 tests — ajout de la
  répétabilité, de la comptabilité honnête (candidats = enregistrements + exclusions, jamais
  ni l'un ni l'autre ni les deux), de la vérification de provenance, et du test de
  non-régression sur le préfixe `record_id`.

**Résultat après intégration** : 461/461 tests passés (441 déjà présents + 20 nouveaux),
0 échec, 0 régression.

**Verdict** : **adopté**, avec les corrections ci-dessus. Le paquet correspond fidèlement à
la Priorité 3 telle que définie (diversification du corpus + interface minimale M1-M6, M7
explicitement exclu), respecte toutes les disciplines déjà établies du projet (fichiers gelés
non touchés, exclusions honnêtes jamais fabriquées, aucune nouvelle vocabulaire épistémique),
et ses affirmations chiffrées ont été vérifiées par exécution réelle, pas acceptées sur
description.
