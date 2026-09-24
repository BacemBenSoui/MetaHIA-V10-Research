# P4-U.2 — Gate H v1.0, gelée (2026-09-24)

Formalise la décision de gel explicite du porteur du projet après la
campagne de calibration C4→C7 (`documentation/P4U2_Calibration_Campaign4_2026-09-24.md`
à `documentation/P4U2_Calibration_Campaign7_VoletC_RealCorpus_2026-09-24.md`),
complétant `documentation/P4U2_Protocol_V0_1.md` Sec. 10.2, où Gate H
était formulée mais laissée volontairement sans seuil numérique dans
l'attente de cette calibration. **La campagne de calibration C4→C7 est
close par ce document — aucune campagne C8 n'est prévue.**

## 1. Spécification gelée

```text
Gate H v1.0

statistique         = cohésion du sous-groupe dissident (Cohesion_B,
                       distance intra-groupe moyenne convertie en
                       cohésion), calculée sur le sous-groupe issu de
                       la Règle R1 (vote majoritaire sur le vecteur de
                       traits (a_profondeur_2, a_profondeur_3) déjà
                       fixé par la signature structurelle, protocole
                       Sec. 7 -- jamais recherché ni optimisé)

modèle nul           = CORRIGÉ (campagne 5) : reproduit la procédure
                       complète -- tirage d'un groupe nul de même
                       taille dans le pool de fond -> mêmes traits
                       gelés -> même Règle R1 -> cohésion du dissident
                       émergent -- jamais un raccourci qui ré-échantillonne
                       directement un sous-ensemble de taille k

percentile_threshold        = 95 %
multiple_comparison_control = MAX-STATISTIC (maximum de la statistique
                               sur l'ensemble des candidats testés
                               simultanément -- discipline reprise de
                               P4-U.1, testée et confirmée nécessaire
                               en campagne 4 Partie 3 et campagne 4/5)

calibration_envelope:
    group_size ∈ [20, 40]
    k >= 8                  (k = effectif du sous-groupe dissident émergent)

outside_envelope:
    verdict = CALIBRATION_INSUFFICIENT

never:
    un verdict hors enveloppe ne devient JAMAIS DISCOVERY
```

## 2. Ce que cette spécification établit, et ce qu'elle n'établit PAS

**C'est une enveloppe de calibration empirique opérationnelle, pas une
loi universelle sur tous les futurs corpus de MetaHIA.** Les valeurs
`k >= 8` et `group_size ∈ [20,40]` décrivent le domaine dans lequel les
campagnes C5-C7 ont vérifié un comportement acceptable — elles ne sont
pas dérivées d'une preuve mathématique générale et ne doivent pas être
extrapolées hors de ce domaine sans nouvelle calibration.

**Ce qui EST établi, par exécution directe, sur ce domaine** :
- Le modèle nul corrigé répond correctement (z=0,0 exact) sur un corpus
  rigoureusement homogène où aucune distinction ne peut exister
  (campagne 5, Sec. TWIN).
- La transition `k≤7 → k≥8` (taux de faux positifs élevé puis proche du
  niveau nominal) est reproduite sur QUATRE pools de fond indépendants :
  trois compositions synthétiques pré-enregistrées (150/80/40, 120/90/60,
  90/90/90, campagne 6 Volet B) et un pool dérivé de données structurelles
  réelles du dépôt (134 faits, quatre domaines M6/M7, campagne 7/Volet C).
- L'hétérogénéité manifeste (une vraie seconde classe structurelle) est
  systématiquement et nettement détectée (percentile 97,2 à 100,0 selon
  la configuration) dans tout le domaine testé, sans exception.

**Ce qui N'EST PAS établi, à ne jamais présenter comme démontré** :
- **Un taux de faux positifs précis de 5 %.** Toutes les mesures de FPR
  de ce document reposent sur 20 à 30 répétitions externes par cellule
  (200 pour le balayage k=3-7 de la campagne 6 Volet A, qui reste hors
  de l'enveloppe gelée). Une cellule à `1/30 ≈ 3,3 %` ou `2/30 ≈ 6,7 %`
  ne permet pas d'affirmer finement si le taux réel est supérieur ou
  inférieur à 5 % — seulement que le comportement est COHÉRENT avec un
  taux proche du niveau nominal, pas qu'il est PROUVÉ égal à 5 %.
- Le comportement à des tailles de groupe hors `[20,40]`, ou à des
  compositions de pool radicalement différentes des quatre testées.
- Que `k>=8` soit une propriété universelle de tout mécanisme de type
  Gate H sur tout futur corpus MetaHIA — c'est une propriété calibrée
  empiriquement sur les cas testés ici, à revalider si le contexte change
  significativement (nouvelle famille de signature, nouveau type de
  corruption structurelle, etc.).

## 3. Historique de la calibration — clôturé par ce document

```text
C4   INVALIDÉ    -- modèle nul mal spécifié (raccourci de sélection,
                    pool mélangeant arêtes membres et arêtes de
                    continuation structurelle) ; sa conclusion propre
                    (k_min≈9-10) n'a jamais été confirmée par la suite
C5   CONFIRMÉ    -- modèle nul corrigé, validé sur TWIN/SEP/PARTIAL
C6   CONFIRMÉ    -- trou petit-k résolu (200 graines), robustesse à
                    3 pools synthétiques pré-enregistrés
C7   CONFIRMÉ    -- même transition k≤7/k≥8 reproduite sur un pool réel
                    indépendant (4 corpus M6/M7, 134 faits)
     └──> Gate H v1.0 GELÉE (ce document)
```

Aucune campagne C8 n'est prévue. Une extension future de la calibration
(taille de pool réel plus grande, plus de graines, autres tailles de
groupe) resterait possible mais n'est plus jugée prioritaire par rapport
à la prochaine étape du projet.

## 4. Conséquence directe

`p4u2_status` (protocole, calibration) : la statistique de cohésion, le
modèle nul `group-resample-only` corrigé, la correction multi-comparaisons
par maximum, et maintenant Gate H v1.0 dans son enveloppe `k>=8`/`group_size
∈[20,40]` constituent l'ensemble des éléments mécaniques nécessaires
avant l'implémentation minimale de P4-U.2 (protocole Sec. 17). Le choix
final entre les trois statistiques de cohésion candidates (A/B/C) reste
ouvert mais non bloquant, `Cohesion_B` étant celle effectivement utilisée
et validée par toute la chaîne de calibration C5-C7.
