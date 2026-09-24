# P4-U.2 — Cadrage de l'implémentation minimale (2026-09-24)

Exécute l'étape explicitement demandée par le porteur du projet, celle
que le protocole lui-même (Sec. 17) place immédiatement après la
calibration : « implémentation du module minimal (signature, Gate I,
Gate H, `STRUCTURAL_CLASS_HYPOTHESIS`) ». **Ce document cadre cette
implémentation — il n'écrit aucun code de production.** Même
discipline que pour P4-U.1 et P4-T : cadrage avant code.

```text
Protocole v0.1 (gelé, f6a96b2)
        ↓
Calibration C1-C7 -> Gate H v1.0 GELÉE (1211bab)
        ↓
CE CADRAGE (v0.1, commit 28ece87)       <- révisé ci-dessous
        ↓
implémentation (pas commencée)
        ↓
construction du benchmark verrouillé V1-V4 (pas commencée)
```

**Révision (2026-09-24), après relecture du porteur du projet sur
`28ece87`** — deux corrections apportées avant tout code, aucune
réouverture du fond du cadrage :
1. **Réserve de circularité ajoutée** à la Sec. 2.2 : la génération de
   candidats par égalité exacte de signature, suivie d'une mesure de
   cohésion sur cette MÊME signature, impose mécaniquement une cohésion
   interne élevée au groupe ainsi construit — qualification explicite en
   *candidate-generation heuristic*, jamais une preuve d'identifiabilité
   en soi, à charge du futur benchmark V1-V4 de le démontrer.
2. **`evaluate_gate_h` corrigé** (Sec. 3) : `N_null` n'a jamais été gelé
   comme valeur normative par Gate H v1.0 (seulement « confirmé stable »
   en calibration) — retiré tout défaut implicite (`n_null=300`),
   devenu un paramètre obligatoire, même discipline que
   `percentile_threshold` de Gate I.

## 1. Ce que la calibration a réellement figé — prêt pour l'implémentation

```text
Signature structurelle (Sec. 7)        RETENUE comme hypothèse de
                                        travail -- (d1,d2,d3, multiset
                                        de directions), D=3, via
                                        kernel2.discover_paths()
                                        INCHANGÉ

Statistique de cohésion (Sec. 8.1)     Cohesion_B (distance intra-
                                        groupe moyenne -> cohésion)
                                        -- seule statistique testée de
                                        bout en bout sur C1-C7

Modèle nul de Gate I (Sec. 9)          group-resample-only, CORRIGÉ
                                        (reproduit la procédure de
                                        sélection complète, campagne 5)
                                        -- piste 1 (topology-only)
                                        INVALIDÉE comme mécanisme
                                        principal (faux positif net
                                        démontré, campagne 5 Sec. TWIN)

Correction multi-comparaisons          max-statistique (comme P4-U.1),
(Sec. 8, point 3)                      nécessité démontrée (campagne 4
                                        Partie 3) et robustesse
                                        confirmée (20 graines)

Règle de partition Gate H (R1)         vote majoritaire sur le vecteur
                                        de traits (a_profondeur_2,
                                        a_profondeur_3), déterministe,
                                        jamais recherché

Gate H v1.0 (Sec. 10.2)                GELÉE : percentile>=95%,
                                        enveloppe k>=8 / group_size
                                        dans [20,40], sinon
                                        CALIBRATION_INSUFFICIENT
```

## 2. Ce qui reste ouvert — à décider maintenant, explicitement, pas silencieusement pendant le codage

### 2.1 Seuil de percentile de Gate I lui-même — jamais gelé

**Contrairement à Gate H, Gate I n'a jamais eu son propre seuil de
percentile formellement figé** — la checklist du protocole (Sec. 13,
point 5) ne l'indique que comme « N_null=200-300 confirmé stable »,
jamais comme un seuil de décision gelé. Décision de cadrage proposée
ici : la fonction d'évaluation de Gate I n'aura **aucune valeur par
défaut silencieuse** — `percentile_threshold` sera un paramètre
obligatoire, jamais un défaut caché, pour empêcher toute case
d'implémentation ou de futur benchmark verrouillé de figer ce nombre
sans décision explicite. Un appelant pourra choisir 95 % (par cohérence
avec Gate H) mais devra l'écrire, pas en hériter silencieusement.

### 2.2 Génération des candidats de regroupement — jamais spécifiée avant Gate I

**Lacune trouvée en préparant ce cadrage, pas résolue par les
campagnes de calibration** : le protocole (Sec. 4) fait démarrer le
pipeline à « candidat de regroupement C » directement à l'entrée de
Gate I — mais aucun document gelé ne spécifie COMMENT un candidat C est
proposé à partir du pool d'observations masquées. La cadrage v0.3
(Sec. 3) impose la chaîne en trois étapes `similarité -> structure
commune -> hypothèse`, mais ne fixe pas non plus l'algorithme de la
première étape.

**Proposition minimale pour ce cadrage, à valider explicitement** :
regrouper par ÉGALITÉ EXACTE de signature complète — c'est-à-dire la
même mécanique que `group_by_skeleton()` de P4-U.1
(`p4u1_unsupervised_pattern_discovery_v0_1.py`), appliquée ici à la
signature de Sec. 7 plutôt qu'au squelette de chemin. C'est
l'opérationnalisation la plus littérale possible de « structure
commune » : aucun seuil de similarité à inventer, aucun algorithme de
clustering à calibrer. Un faux candidat (deux relations réellement
différentes partageant par coïncidence la même signature grossière,
comme le cas TWIN) serait correctement rejeté par Gate I lui-même
(`INSUFFICIENT_STRUCTURAL_INFORMATION`), exactement le rôle que
l'architecture lui assigne — la génération de candidats n'a donc pas
besoin d'être infaillible, seulement de proposer, Gate I/Gate H faisant
le tri. **Ceci est une décision de conception NOUVELLE, jamais testée
par C1-C7 (qui ont toujours évalué Gate I/Gate H sur des groupes déjà
construits avec vérité terrain connue)** — à documenter comme telle
dans le code, pas présentée comme déjà validée.

**Réserve méthodologique supplémentaire, à ne jamais perdre de vue** :
si le candidat est construit par égalité exacte de la MÊME signature
que celle ensuite mesurée par `Cohesion_B`, la chaîne

```text
signature -> égalité exacte -> groupe candidat -> Cohesion_B
```

impose nécessairement une cohésion interne très élevée au groupe ainsi
construit — une partie de ce que Gate I « mesure » est en réalité déjà
imposée par la procédure de génération du candidat, pas découverte par
elle. Ceci ne rend pas la proposition inutilisable (Gate I compare
toujours cette cohésion à un modèle nul, pas à elle-même en isolation),
mais elle doit être qualifiée explicitement, dans le code et sa
documentation, de **candidate-generation heuristic** — jamais présentée
comme une preuve d'identifiabilité en soi. Le futur benchmark verrouillé
V1-V4 devra démontrer que cette mécanique ne transforme pas simplement
sa propre définition de candidat en une « découverte » circulaire — un
critère de conception du futur benchmark, pas encore résolu ici.

### 2.3 Ce qui est délibérément exclu du module minimal

```text
Cohesion_A / Cohesion_C            EXCLUES du module minimal -- seule
                                    Cohesion_B a été validée de bout en
                                    bout ; A/C restent des candidats
                                    documentés pour un futur incrément,
                                    jamais implémentées « au cas où »
                                    dans cette passe

Modèle nul topology-only           EXCLU explicitement -- prouvé
(piste 1, Sec. 9)                  générateur de faux positifs net
                                    utilisé seul (campagne 5) ; ne pas
                                    l'implémenter du tout évite le
                                    risque qu'un futur appelant le
                                    réactive par erreur

sélection intelligente du pool     EXCLUE -- différée à P4-U.2.2,
(P4-U.2.2)                         non cadrée ici (protocole Sec. 6)

réactivation de e20d_*             EXCLUE, sans exception (protocole
                                    Sec. 3)
```

## 3. Structure de module proposée

Un seul nouveau fichier, `p4u2_autonomous_relation_discovery_v0_1.py`
(même convention de nommage que `p4u1_unsupervised_pattern_discovery_v0_1.py`),
réutilisant `kernel2.py` sans aucune modification :

```text
--- Signature (Sec. 7) ---
Signature                          = NamedTuple(d1, d2, d3, directions)
edge_signature(graph, edge)        -> Signature
                                       (identique à la version jetable
                                       des campagnes 1-7, promue en
                                       code de production)

--- Génération de candidats (Sec. 2.2 ci-dessus, NOUVEAU) ---
group_by_signature(observations)   -> Dict[Signature, Tuple[edge_id,...]]

--- Cohésion (Sec. 8.1) ---
cohesion_b_mean_distance(sigs)     -> float   (seule statistique retenue)

--- Modèle nul de Gate I (Sec. 9, piste 2 corrigée) ---
null_resample_group(pool_sigs,
    group_size, seed)              -> Tuple[Signature,...]
null_distribution(pool_sigs,
    group_size, n_null, seed_base,
    stat_fn)                       -> Tuple[float,...]

--- Gate I (Sec. 8) ---
GateIResult                        = dataclass(status, observed,
                                       percentile, z, n_null)
evaluate_gate_i(candidate_sigs,
    pool_sigs, *, percentile_threshold,     # OBLIGATOIRE, Sec. 2.1
    n_null, seed_base)              -> GateIResult
gate_i_family_threshold(pool_sigs,
    group_size, n_candidates,
    n_null, percentile, seed_base)  -> float   (max-statistique)

--- Règle R1 + STRUCTURAL_CLASS_HYPOTHESIS (Sec. 10.1) ---
StructuralClassHypothesis          = dataclass(hypothesis_id,
                                       member_observation_ids,
                                       structural_signature, support,
                                       contradiction_support,
                                       status=UNKNOWN, provenance)
partition_by_majority_trait(sigs)  -> (dominant_trait, dissenting_idx)
contradiction_support_v2(sigs)     -> float

--- Gate H v1.0, GELÉE (Sec. 10.2) ---
GateHResult                        = dataclass(status, dissenting_count,
                                       minority_cohesion, percentile,
                                       envelope_ok)
evaluate_gate_h(candidate_sigs,
    pool_sigs, *, n_null,           # OBLIGATOIRE, pas de défaut --
    seed_base)                      -> GateHResult
    -- Gate H v1.0 gèle percentile>=95%/k>=8/group_size dans [20,40],
       JAMAIS N_null lui-même (seulement "confirmé stable" à 200-300 en
       calibration, jamais gelé comme valeur normative) -- même
       discipline que percentile_threshold de Gate I (Sec. 2.1) : un
       appelant doit écrire N_null explicitement, jamais en hériter
       d'un défaut caché
    -- applique R1, vérifie l'enveloppe (group_size dans [20,40] ET
       k>=8) AVANT tout calcul de percentile ; hors enveloppe ->
       CALIBRATION_INSUFFICIENT immédiat, jamais un calcul silencieux
```

**Aucune fonction d'orchestration de bout en bout** (« lancer la
découverte sur un graphe complet ») n'est incluse dans ce module —
cette responsabilité revient au futur runner de benchmark verrouillé
(mirroir de la séparation déjà existante entre
`p4u1_unsupervised_pattern_discovery_v0_1.py` et
`p4u1_locked_benchmark_runner_v0_1.py`), pas à ce module minimal.

## 4. Plan de tests déterministes

Chaque test ci-dessous correspond à un résultat déjà établi par les
campagnes C1-C7 — **transformé en test de régression permanent**, même
discipline que les gardes-fous déjà en place ailleurs dans ce dépôt
(exclusion des wedges de P4-U.1, correctifs de fuite P4-T.1/P4-T.1bis) :

```text
1. test_signature_matches_disposable_calibration_reference
   -- une signature calculée sur un petit graphe fixe doit correspondre
      exactement aux valeurs rapportées dans les campagnes 1-7

2. test_gate_i_null_gives_zero_z_on_homogeneous_corpus
   -- reproduction du corpus TWIN (campagne 5) : Gate I ne doit jamais
      déclarer PASS sur un corpus rigoureusement homogène

3. test_gate_i_naive_equality_would_be_wrong_but_group_statistic_is_right
   -- reproduction du cas de chevauchement partiel (identifiabilité,
      z=3,79) : garde contre toute régression vers une vérification par
      égalité de signature

4. test_multi_comparisons_correction_rejects_null_candidates
   -- reproduction de la campagne 4 Partie 3 : sur 1 vrai groupe + 9
      candidats nuls, la correction par maximum doit donner 0 faux
      positif sur le jeu de données fixé du test

5. test_gate_h_below_envelope_returns_calibration_insufficient
   -- k<8 ou group_size hors [20,40] -> CALIBRATION_INSUFFICIENT,
      JAMAIS PASS ni FAIL

6. test_gate_h_distinguishes_noise_from_manifest_heterogeneity
   -- reproduction de la campagne 4 Partie A / campagne 6 : un cas de
      bruit naturel et un cas d'hétérogénéité manifeste au même niveau
      de contradiction_support doivent donner des verdicts Gate H
      différents une fois dans l'enveloppe calibrée

7. test_group_by_signature_never_uses_ground_truth
   -- vérification statique (comme P4-T/P4-U.1) : aucune fonction de ce
      module n'importe ni n'accepte de vérité terrain avant le commit
```

## 5. Ce que ce cadrage ne fait PAS

Aucun code n'est écrit. La liste de fonctions ci-dessus est une
spécification, pas une implémentation. Aucune valeur numérique du futur
benchmark verrouillé (taille de groupe, N_null final, D final) n'est
fixée ici — ces décisions restent celles du protocole Sec. 13 point 7,
« à fixer par calibration sur des corpus jetables, jamais sur le
benchmark verrouillé lui-même ». La génération de candidats par égalité
exacte de signature (Sec. 2.2) est une proposition à valider
explicitement, pas une décision déjà prise. Aucun cas V1-V4 n'est
construit.

## 6. Prochaine étape

Sur validation explicite de ce cadrage par le porteur du projet :
écriture du module `p4u2_autonomous_relation_discovery_v0_1.py` et de
sa suite de tests (Sec. 4), puis, seulement ensuite, construction du
benchmark verrouillé V1-V4 (protocole Sec. 14) — jamais les deux en même
temps.
