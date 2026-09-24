# P4-U.2 — Cadrage du benchmark verrouillé V1-V4 (2026-09-24)

Exécute l'étape suivante de la séquence gelée du protocole (Sec. 13) :
« implémentation du module minimal [FAIT, `2174d00`] → construction du
benchmark verrouillé V1/V2/V3/V4 (Sec. 14) ». **Ce document cadre cette
construction — il n'écrit ni corpus, ni code, ni valeur numérique
verrouillée.** Même discipline que pour P4-T et P4-U.1.

```text
Protocole v0.1 (gelé, f6a96b2)
        ↓
Calibration C1-C7 -> Gate H v1.0 GELÉE (1211bab)
        ↓
Cadrage d'implémentation (28ece87, corrigé 98f4105)
        ↓
Module minimal + 7 tests (2174d00)
        ↓
CE CADRAGE                              <- ce document
        ↓
construction du benchmark verrouillé V1-V4 (pas commencée)
```

## 1. Ce qui est déjà acquis, réutilisé sans reprise de débat

```text
Signature (Sec. 7), Cohesion_B, modèle nul group-resample-only corrigé,
correction multi-comparaisons max-statistique, Règle R1, Gate H v1.0
(percentile>=95%, enveloppe k>=8/group_size dans [20,40]) -- tout est
déjà implémenté et testé dans p4u2_autonomous_relation_discovery_v0_1.py
(commit 2174d00). Ce cadrage ne rouvre rien de ceci.
```

## 2. Décisions numériques nouvelles requises pour CE benchmark — chacune reliée à une preuve déjà produite, aucune inventée ici

Le protocole (Sec. 13, point 7) exige que ces valeurs soient fixées
« par calibration sur des corpus jetables, jamais sur le benchmark
verrouillé lui-même ». Les campagnes C1-C7 ont déjà produit cette
calibration jetable — ce qui suit n'invente rien de nouveau, cela
**relie explicitement chaque choix à la preuve existante** plutôt que de
le laisser implicite au moment de construire les cas.

### 2.1 Seuil de percentile de Gate I pour ce benchmark — proposition, à valider

Gate I n'a jamais eu de seuil formellement gelé (cadrage
d'implémentation Sec. 2.1). **Proposition : 95 %**, pour deux raisons
directes, pas par défaut de commodité :
1. Toute l'analyse de puissance de Gate I (campagne 2, balayage de
   signal et de taille ; campagne 3, calibration de taille finale) a été
   conduite À ce seuil précis — en changer maintenant invaliderait
   cette analyse et exigerait de la refaire.
2. Cohérence directe avec Gate H v1.0, déjà gelée au même seuil.

### 2.2 Profondeur de signature D — retenue, PAS re-testée par ablation

`D=3` a été utilisé identiquement dans C1-C7 sans exception. **Aucune
campagne n'a testé `D=2` ou `D=4` par ablation directe** — ceci reste
une lacune honnête, pas une confirmation. Proposition : retenir `D=3`
pour ce benchmark (aucune preuve d'insuffisance rencontrée), en
consignant explicitement que ce choix n'a jamais été stress-testé
contre une alternative — à rouvrir si le run réel du benchmark échoue
de façon suggérant un déficit de profondeur.

### 2.3 Taille de groupe par cas — pas une taille unique pour les quatre cas

```text
V1 (signal net)        taille=40 -- campagne 3 : z>=3,79 avec large
                        marge à cette taille (et à des tailles
                        inférieures), aucune raison de descendre plus bas
V4 (chevauchement 80/20) taille=40 -- campagne 3 Partie C : plus petite
                        taille testée donnant une marge réelle
                        (z=2,18, pas seulement le seuil) sur le cas
                        difficile ; tailles 20/30 démontrées
                        insuffisantes (campagne 3)
V2 (TWIN)               taille=20 -- la campagne 5 a démontré le
                        comportement correct (z=0,0 exact) précisément
                        à cette taille ; V2 teste l'ABSENCE de signal,
                        pas la puissance de détection, donc la même
                        exigence de marge que V1/V4 ne s'applique pas
V3 (nul pur)            taille=20 -- même raisonnement que V2, contrôle
                        négatif, pas un test de puissance
```

### 2.4 N_null pour le run verrouillé — 300

Stabilité confirmée de 200 à 2000 (campagne 2 Partie 2C, campagne 7).
`N_null=300` retenu (déjà utilisé dans la majorité des runs de
calibration finaux C5-C7).

### 2.5 Correction multi-comparaisons dans le benchmark — nécessaire dès qu'un cas contient plus d'un candidat

Chaque corpus V1-V4 doit contenir, en plus du signal ciblé (s'il existe),
**des candidats-leurres réalistes** produits par `group_by_signature()`
lui-même sur le corpus complet — jamais seulement le groupe cible
isolé. C'est la seule façon de faire fonctionner réellement la
correction par maximum (Sec. 2.5, protocole Sec. 8 point 3) dans le
benchmark, plutôt que de la laisser être seulement vérifiée
unitairement (déjà fait, test 4 du module). Nombre exact de leurres par
cas : décision de construction, pas une valeur à calibrer statistiquement
— même approche que le design « pont unique + leurres » déjà retenu par
P4-U.1.

## 3. Architecture d'orchestration requise — absente du module minimal, à la charge de ce runner

`p4u2_autonomous_relation_discovery_v0_1.py` ne fournit délibérément
aucune fonction de bout en bout (cadrage d'implémentation Sec. 3). Le
futur `p4u2_locked_benchmark_runner_v0_1.py` doit l'assembler, en
miroir exact de `p4u1_locked_benchmark_runner_v0_1.py` :

```text
run_discovery_and_gates(G_masked) :
    1. group_by_signature(signatures)          -- TOUS les candidats,
                                                   jamais seulement la
                                                   cible attendue
    2. pour chaque bucket de taille >= 2 :
       evaluate_gate_i(..., percentile_threshold=95.0, ...)
       -- si plusieurs buckets testés simultanément : comparer contre
          gate_i_family_threshold(), jamais un seuil individuel par
          bucket (protocole Sec. 8 point 3)
    3. buckets PASS Gate I -> StructuralClassHypothesis (status=UNKNOWN)
    4. evaluate_gate_h() sur chaque hypothèse
    5. hypothèses PASS Gate I ET Gate H -> candidates à DISCOVERED,
       en attente de holdout

commit_predictions(predictions) :
    -- même discipline que P4-T/P4-U.1 : vérification statique (le
       témoin n'apparaît nulle part dans le code de découverte) ET
       dynamique (WITNESS_MODULE_NAME absent de sys.modules au moment
       du commit) AVANT toute écriture de prédiction

reveal_and_compare(predictions, G_holdout) :
    -- re-exécute intégralement l'étape 1-5 sur G_holdout (disjoint,
       jamais vu avant), PUIS seulement importe le témoin pour comparer
       (Sec. 15) -- jamais pour orienter la découverte elle-même

run_locked_benchmark() :
    -- assemble les trois étapes, vérifie witness_imported_before_commit
       == False comme condition de validité du run, exactement comme
       P4-U.1
```

## 4. Exigence anti-circularité — le pipeline complet doit tourner, pas seulement Gate I/Gate H sur un groupe déjà choisi

**Point trouvé en préparant ce cadrage, directement issu de la réserve
de circularité déjà posée (cadrage d'implémentation Sec. 2.2)** :
aucune campagne C1-C7 n'a jamais fait tourner `group_by_signature()`
sur un corpus complet et laissé le pipeline découvrir lui-même quel
bucket tester — chaque test a toujours reçu un groupe candidat DÉJÀ
choisi avec vérité terrain connue. **Le benchmark verrouillé est donc
le premier test réel de la chaîne complète `group_by_signature ->
Gate I -> Gate H`, pas une répétition de la calibration.** Ceci doit
être explicite dans la construction : chaque cas V1-V4 doit être
construit comme un corpus complet, jamais comme « le groupe cible plus
son étiquette », et le runner doit laisser `group_by_signature()`
proposer tous les buckets sans filtrage préalable.

## 5. Spécification des quatre cas — reprise du protocole Sec. 14, complétée des paramètres ci-dessus

```text
V1 -- signal net (taille=40, percentile Gate I/H=95%, N_null=300)
   Corpus : un groupe cible de 40 arêtes à rôle topologique net (ex.
   hub à fort éventail vs 1-à-1, comme l'investigation empirique du
   2026-09-23), noyé dans un fond produisant plusieurs buckets leurres
   via group_by_signature().
   Attendu : Gate I PASS -> STRUCTURAL_CLASS_HYPOTHESIS -> Gate H PASS
   -> re-test G_holdout PASS -> DISCOVERED
   Démonstration d'identifiabilité requise avant tout run (Sec. 14) :
   le rôle topologique du groupe cible doit être vérifié DIFFÉRENT de
   tous les buckets leurres, par construction, pas par supposition.

V2 -- TWIN, rôle topologique RIGOUREUSEMENT identique (taille=20)
   Corpus : reproduction du corpus TWIN (campagne 5) -- cycles
   disjoints, chaque arête structurellement identique.
   Attendu : Gate I FAIL sur tout bucket -> INSUFFICIENT_STRUCTURAL_
   INFORMATION (résultat correct, jamais un échec du mécanisme)

V3 -- contrôle nul pur (taille=20)
   Corpus : généré directement par le modèle nul lui-même (aucune
   régularité injectée) -- même rôle que U3 de P4-U.1.
   Attendu : aucun bucket ne dépasse Gate I -> INSUFFICIENT_STRUCTURAL_
   INFORMATION, ou REJECTED si un bucket est proposé puis rejeté par
   Gate H

V4 -- chevauchement partiel (taille=40, reproduction exacte du cas
   ayant révélé la faille méthodologique de l'expérience
   d'identifiabilité, 2026-09-23)
   Attendu : Gate I PASS via la statistique de groupe -- JAMAIS via une
   égalité de signature par observation (déjà gardé par le test 3 du
   module, mais ré-exercé ici en conditions de benchmark réel) -> Gate H
   PASS -> re-test G_holdout -> DISCOVERED. Existe SPÉCIFIQUEMENT pour
   garantir que l'implémentation ne régresse jamais vers la
   vérification naïve déjà prouvée fausse.
```

Chaque cas doit être accompagné, avant tout run, d'une démonstration
explicite de son identifiabilité (ou de sa non-identifiabilité
délibérée pour V2/V3) — jamais une assertion abstraite (protocole
Sec. 14, v0.3 Sec. 3).

## 6. Discipline anti-fuite — même exigence que P4-T/P4-U.1

```text
G_train / G_holdout / G_negative      identités de nœuds totalement
                                       disjointes (mirroir du split
                                       graphe complet de P4-U.1)
FrozenPatternU2 (à créer)             ne doit exposer aucune identité
                                       de nœud d'entraînement ni
                                       référence de chemin source --
                                       même catégorie de fuite que
                                       P4-T.1/P4-T.1bis, anticipée ici
                                       avant implémentation
Témoin                                jamais importé avant
                                       commit_predictions() -- vérifié
                                       statiquement ET dynamiquement
                                       (sys.modules)
```

## 7. Ce que ce cadrage ne fait PAS

Aucun corpus V1-V4 n'est construit. Aucune valeur numérique n'est
écrite dans un fichier verrouillé. Aucun `p4u2_locked_benchmark_runner_v0_1.py`
ni `p4u2_locked_benchmark_cases_v0_1.py` n'existe. Le nombre exact de
buckets-leurres par cas et la structure précise de `FrozenPatternU2`
restent des décisions de construction, pas encore prises. La réserve de
circularité sur `group_by_signature()` (cadrage d'implémentation
Sec. 2.2) n'est pas résolue par ce document — elle sera testée pour la
première fois par le run réel du benchmark lui-même (Sec. 4 ci-dessus).

## 8. Prochaine étape

Sur validation explicite de ce cadrage par le porteur du projet :
construction effective des corpus V1-V4 (données), écriture de
`FrozenPatternU2` (anti-fuite), écriture de `p4u2_locked_benchmark_runner_v0_1.py`
suivant l'architecture Sec. 3, tests déterministes, puis, seulement
ensuite, run réel contre le benchmark verrouillé et documentation
honnête du résultat, quel qu'il soit.
