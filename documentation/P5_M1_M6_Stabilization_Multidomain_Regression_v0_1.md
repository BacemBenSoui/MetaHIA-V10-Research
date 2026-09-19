# MetaHIA V10 — P5.1 Stabilisation M1–M6 et régression multi-domaines v0.1

Date : 2026-09-18  
Statut : **expérimental — baseline stabilisé, clôture scientifique non revendiquée**

## 1. Objectif

P5.1 transforme l'interface M1–M6 expérimentale v0.1 en un **contrat de transport versionné v0.2**, tout en exécutant une régression réelle sur deux corpus indépendants :

- `FAMILY-TREE-V0.2` — arbre familial ;
- `ORGANIZATION-V0.1` — organisation/projets.

L'objectif est la stabilité du transport et la reproductibilité de la régression, pas la démonstration d'un transfert sémantique inter-domaines.

## 2. Contrat v0.2

Le contrat stable est :

```text
M1/M3 structure
      ↓
M2 outcome
      ↓
M4 evidence/provenance
      ↓
M5 control metadata
      ↓
M6LearningPacket
      ↓
M1M6StableEnvelope v0.2
```

Le nouveau `M1M6StableEnvelope` ajoute uniquement :

- `corpus_id` ;
- `domain_id` ;
- `contract_version`.

Ces champs sont **audit-only**. Ils ne sont pas transmis au calcul M6 : `as_record_kwargs()` restitue exactement les sept champs historiques de `StructuralOutcomeRecord`.

## 3. Invariants du gel v0.2

- M1/K3 n'est pas modifié.
- M6 n'est pas modifié.
- M7/LLM n'est pas une dépendance.
- aucun dictionnaire sémantique de domaine n'est ajouté.
- le split M6 reste par règle.
- les deux corpus restent séparés comme sources ; leur concaténation sert seulement à une régression combinée.
- les métadonnées de domaine ne deviennent pas une feature d'apprentissage.

## 4. Régression exécutée

### Famille

- 26 records ; 20 règles ;
- split seed 0 : 16 train / 5 validation / 5 holdout ;
- Brier holdout : **0,48125** ;
- ECE top-label : calculé comme diagnostic ;
- round-trip JSON de l'interface : PASS.

### Organisation

- 24 records ; 12 règles ;
- split seed 0 : 16 train / 4 validation / 4 holdout ;
- Brier holdout : **0,6953125** ;
- ECE top-label : calculé comme diagnostic ;
- round-trip JSON de l'interface : PASS.

### Combiné

- 50 records ; 32 règles ;
- split seed 0 : 31 train / 9 validation / 10 holdout ;
- aucune règle du holdout n'est présente dans le train ;
- Brier holdout : **0,49198751300728405** ;
- ECE top-label : **0,07741935483870965** ;
- round-trip JSON : PASS.

Ces chiffres ne sont pas comparés comme s'ils provenaient de la même population. Ils servent de **baselines de régression**.

## 5. Probe multi-seed de stabilité statistique

Une seconde exécution P5.2 répète exactement le split par règle sur les seeds `0..9`, sans changer M6. Les dispersions observées sont :

| Domaine | Brier moyen | écart-type population | min | max | ECE moyen |
|---|---:|---:|---:|---:|---:|
| Famille | 0,535278 | 0,103619 | 0,406250 | 0,764444 | 0,143365 |
| Organisation | 0,471875 | 0,215410 | 0,125000 | 0,695313 | 0,200000 |
| Combiné | 0,444565 | 0,107167 | 0,287774 | 0,680791 | 0,120950 |

Cette variance n'indique pas une instabilité de l'interface. Elle indique que les **estimations de calibration restent sensibles au split sur de petits corpus et peu de règles**. P5 ne fixe donc pas encore de chiffre de performance M6 « représentatif ». Le test multi-seed est conservé comme baseline avant tout agrandissement du corpus.

## 6. Limites / non-fermeture

P5.1 ne démontre pas :

- une généralisation inter-domaines sémantique ;
- une invariance opérateur indépendante découverte par M6 ;
- une amélioration de calibration due à M7 ;
- une fermeture E20-D ;
- une readiness préproduction.

Le transfert structurel reste couvert par les expériences P4.2–P4.5 et doit être distingué de cette régression d'intégration.

## 7. Tests

Nouveau test ciblé : `tests/test_p5_m1_m6_multidomain_regression_v0_1.py`.

Le test vérifie :

1. versionnement et exclusion de M7 ;
2. round-trip JSON ;
3. baselines Famille et Organisation ;
4. baseline combinée ;
5. absence de dépendance M7 ;
6. absence de fuite des métadonnées de domaine dans M6 ;
7. respect du split par règle.

## 8. Décision

**P5.1 = `PASS_INTERFACE_REGRESSION_BASELINE`.**

Le contrat v0.2 est suffisamment stable pour les régressions multi-domaines suivantes, sans imposer une refonte de M1 ou M6.

La prochaine étape ne doit pas être une extension fonctionnelle immédiate : il faut d'abord exécuter une **régression multi-seed** et vérifier la stabilité des métriques et des partitions avant de considérer l'interface comme définitivement gelée.

## 9. Revue et intégration (2026-09-19)

Ce module a été reçu avec les expériences P4.1–P4.5 dans le même paquet. Après vérification
par exécution réelle, **P5 est adopté séparément** : `m1_m6_interface_v0_2.py`,
`p5_m1_m6_multidomain_regression_v0_1.py` et `p5_multiseed_regression_v0_1.py` utilisent
correctement `build_real_corpus_v2` (le mécanisme non dégénéré déjà validé), et tous les
chiffres cités en Sec. 4–5 ont été confirmés exacts par exécution directe, pas acceptés sur
description. Un renforcement mineur a été ajouté à `m1_m6_interface_v0_1.py`
(`M6LearningPacket.validate()` vérifie maintenant aussi le type de `rule`, en défense en
profondeur de la même vérification déjà ajoutée sur `M1StructuralPacket`).

**Les expériences P4.1–P4.5 du même paquet ont en revanche été rejetées** — deux défauts
méthodologiques réels trouvés par exécution directe (mécanisme de corpus dégénéré pour la
source Famille ; généralisation de motif circulaire pour le rejeu Organisation). Détail
complet : `documentation/P4_Transfer_Review_and_Rejection_2026-09-19.md`. La ligne 102
ci-dessus (« le transfert structurel reste couvert par les expériences P4.2–P4.5 ») doit donc
être lue comme : ce transfert reste **non démontré**, pas seulement distinct de cette
régression.
