# MetaHIA — Road Map complète consolidée v0.5.5
## État au 17 septembre 2026 — après validation tierce M5

## 1. Règle de gouvernance
Une capacité suit : `CONCEPT → FORMALIZED → IMPLEMENTED → UNIT TESTED → INTEGRATED → BENCHMARKED → EMPIRICALLY VALIDATED → PROMOTED`.

`PASS_INDEPENDENT_SCOPE` signifie que le périmètre critique testé par un tiers indépendant est reproductible et intègre. Il ne vaut pas preuve générale hors périmètre.

## 2. Architecture scientifique cible
```text
OBSERVATION
  ↓
STRUCTURE / NORMALISATION
  ↓
M1 — ALGEBRA KERNEL
  ↓
DERIVED RELATION SPACE
  ↓
M2 — EPISTEMIC EVALUATION
  ↓
M3 — RECURSIVE STRUCTURAL CLOSURE
  ↓
M4 — COLD-START / EVIDENCE
  ↓
M5 — DYNAMIC METACOGNITIVE CONTROL
  ↓
M6 — STRUCTURAL LEARNING
  ↓
INDEPENDENT HOLDOUT
  ↓
M7 — EMPIRICAL LLM LOOP
  ↓
V6 / PRODUCTION
  ↓
CONTROLLED COGNITIVE EVOLUTION
```

Le LLM reste une branche d’observation/production; il n’est pas le fondement du raisonnement structurel.

## 3. État global
| Élément | Statut | Porte de sortie |
|---|---|---|
| M1 Algebra Kernel v0.4 | FROZEN | maintien du hash + non-régression |
| M2 Epistemic Evaluation v0.4 | STABLE / NON-PROMOTED | evidence indépendante et calibration empirique |
| E20-D Structural Discovery | OPEN | autonomie + généralisation + composition + contrôle |
| M3 Recursive Closure v0.1 | PASS_INDEPENDENT_SCOPE | intégration M2+M3 plus large |
| M4 Cold-start v0.1 | PASS_INDEPENDENT_SCOPE | mesure N_min et couverture sur corpus réels |
| M5 Dynamic Controller v0.1 | PASS_INDEPENDENT_SCOPE | benchmark sur inférence relationnelle réelle |
| M6 Structural Learning | VALIDATED (2026-09-17, clôturé par le porteur du projet sur preuves externes — `JOURNAL_DE_BORD.md`) | — |
| M7 LLM loop | VALIDATED (2026-09-18, clôturé par le porteur du projet sur preuves externes — `JOURNAL_DE_BORD.md`, portée "témoin LLM" — voir `documentation/MetaHIA_M7_LLM_Fact_Proposer_V0_1.md`) | extension longueur > 1 |
| M7 parseur texte→preuve | VALIDATED (2026-09-18, clôturé par le porteur du projet sur preuves externes — `JOURNAL_DE_BORD.md`, portée "texte → preuve sur prédiction existante" — voir `documentation/MetaHIA_M7_TextClaimParser_V0_1.md`) | amélioration fidélité de parsing |
| M7 corpus mixte v0.2 (3 sources) | **RETENU** (2026-09-18, décision explicite du porteur du projet — `+both` : union adversarial+témoin+parseur, 32 appels, Brier 0,489, PROMOTE — voir `documentation/MetaHIA_M7_TextClaimParser_V0_1.md` Sec. 10/12) | pas de validation tierce dédiée (réutilise des mécanismes déjà validés séparément) |
| V6 production | DEFERRED | stabilité scientifique + hardening |
| Cognitive Evolution | DEFERRED | shadow + holdout + rollback |

## 4. M1 — Algebra Kernel v0.4
Noyau gelé. K3 (`Node, Apply, Compare`) reste l’hypothèse minimale expérimentale. R-V-1 sépare identité de référence, équivalence structurelle et égalité de valeur. Aucune nouvelle primitive fondamentale ne doit être ajoutée sans expérience falsifiable dédiée.

Hash gelé : `987839172357c4b0e43e5d3d03dcda32825f4da817dbb02390a5bc4c3f9ea3d9`.

## 5. E20-D — programme de découverte structurelle
Sous-capacités D1–D19 : toutes testées microstructurellement. D10–D12 démontrent le graphe/chemin et la généralisation de formes; D15–D16 réification/replay; D17–D18 émergence et fermeture récursive locale; D19 contrôle ROI.

E20-D reste `OPEN` car quatre conditions de clôture générale ne sont pas simultanément démontrées :
1. découverte autonome d’une relation non fournie ;
2. généralisation sur holdout aveugle ;
3. composition relation → opération → nouvelle structure ;
4. contrôle coût/ROI sans perte systématique.

## 6. M2 — Epistemic Evaluation
États : `DERIVED`, `SUPPORTED`, `CONTRADICTED`, `UNKNOWN`.

Invariant : `DERIVATION ≠ EVIDENCE ≠ EPISTEMIC STATUS`. Une dérivation ne peut pas devenir sa propre preuve. Les preuves portent une source, une polarité, une indépendance et un identifiant.

## 7. M3 — Recursive Structural Closure
Périmètre indépendamment validé : réinjection multi-passes, bornage profondeur/cycles, immutabilité du graphe source, provenance, ambiguïté, répétabilité.

Résultat tiers : 18/18 PASS.

## 8. M4 — Cold-start / Evidence Acquisition
Niveaux : A backoff structurel; B UNKNOWN + humain; C provenance explicite (`GROUNDED_DIRECT`, `GROUNDED_ANALOGY`, `UNGROUNDED_HUMAN`).

Le verrou vise notamment à empêcher la conversion d’une absence d’information en fausse preuve.

## 9. M5 — Dynamic Metacognitive Controller
M5 remplace progressivement un ROI statique par une politique qui observe les résultats de ses décisions et adapte sa stratégie selon gain, coût, utilité et dérive.

Entrées : profondeur, incertitude, provenance, conflit, nouveauté, redondance, coût, gain attendu, historique.
Décisions : `CONTINUE`, `DEFER`, `STOP`, `REQUEST_EVIDENCE`, `CHANGE_STRATEGY`.

Validation tierce : 26/26 sur 3 exécutions; 10/10 exigences critiques; paquet intact; absence de fuite sémantique détectée.

Benchmark du scénario critique : coût dynamique −62,5 %, 70 % du gain conservé, 100 % de couverture utile. Ces valeurs restent spécifiques au scénario.

## 10. M6 — Structural Learning
**Addendum 2026-09-17** : v0.1 implémentée localement (`m6_structural_learning_v0_1.py`),
alimentée par un corpus réel M4/M5, protocole de validation tierce préparé et **auto-exécuté
avec PASS_INDEPENDENT_SCOPE** (13/13 cas critiques C01–C09, clone Git frais ; ne clôt pas la
independent gate au sens strict). Étape INDEPENDENT HOLDOUT franchie structurellement, puis
**mécanisme de preuve non dégénéré conçu et implémenté** (`m6_corpus_from_m4_m5_v0_2.py`,
corpus de vérification adversarial `family_tree_verification_claims_v0_1.json`), **étendu le
même jour aux patterns de longueur > 1** (claims indexées par squelette complet, pas
seulement une relation directe) : 26 enregistrements réels avec diversité d'issue authentique
aux deux profondeurs (16 `SUPPORTED`, 10 `CONTRADICTED`), **Brier de holdout = 0,48125, ECE =
0,025** — résultat de calibration réellement informatif de M6, non dégénéré. Voir
`documentation/MetaHIA_M6_Structural_Learning_V0_1.md` Sec. 6–8. Paquet remis à un tiers
externe (section 10 de la même doc) : deux exécutions externes indépendantes obtenues (13/13,
7/7, 10/10, 24/24, 338/338 répété deux fois dans deux environnements différents), une
divergence de hash trouvée et corrigée, revérifiée. **M6 = VALIDATED**, clôturé explicitement
par le porteur du projet le 2026-09-17 — détail complet dans `JOURNAL_DE_BORD.md`. Reste hors
périmètre : choix définitif des seuils de promotion (non bloquant pour la clôture de cette
étape).

**M7 — Empirical LLM Loop** implémenté le 2026-09-17 (portée "témoin LLM"/fact-proposer,
Ollama local avec repli LAN sandbox), puis étendu le 2026-09-18 par une intégration au
pipeline de promotion M6 avec un corpus mixte (`m7_corpus_mixed_v0_1.py`) : résultat réel
honnêtement neutre pour la calibration (Brier holdout 0,48125 → 0,47, ECE inchangé à 0,025 —
mouvement non significatif sur un holdout de 5 à 8 enregistrements, non attribuable à une
compétence analogique réelle du LLM, dont l'évidence reste systématiquement `CONTRADICTED`
16/16). Protocole de validation tierce préparé le même jour (9 cas critiques C01–C09,
délibérément sans dépendance réseau), puis remis à un tiers externe : deux exécutions
externes indépendantes obtenues (9/9, 9/9 hashes conformes, 371/371 hors démonstrations live,
0 modification, dans deux environnements distincts), même réserve méthodologique honnête
soulevée indépendamment par les deux relecteurs (archive sans `.git`, hash de commit non
vérifiable cryptographiquement — non bloquant, hashes de fichiers gelés concluants). **M7 =
VALIDATED**, clôturé explicitement par le porteur du projet le 2026-09-18 — détail complet
dans `JOURNAL_DE_BORD.md` et `documentation/MetaHIA_M7_LLM_Fact_Proposer_V0_1.md` Sec. 10.
Reste hors périmètre à ce stade : extension aux patterns de longueur > 1 (priorité incertaine
tant que le résultat mixte reste neutre), amélioration de la justesse du LLM lui-même.

**Parseur texte → preuve** choisi explicitement le 2026-09-18 comme prochain jalon, parmi
trois options présentées (extension longueur > 1, addendum de récupération de motifs M6, ou
ce parseur) — retenu pour sa valeur de nouveauté architecturale réelle (le seul élément de
périmètre M7 nommé par le roadmap qui restait). Rôle architectural lui-même choisi
explicitement avant code, parmi deux options (texte → preuve sur prédiction existante /
texte → nouveaux faits du graphe) : la première retenue, pour rester dans les paliers de
provenance déjà établis sans ouvrir de nouvelle question de confiance sur des faits non
vérifiés entrant directement dans le graphe. `m7_text_claim_parser_v0_1.py` +
`m7_corpus_from_text_claims_v0_1.py`, réutilisant 100 % de la machinerie M4/M6/M7 déjà
validée. Résultat réel (`llama3.2:latest`, 2026-09-18) : fidélité de parsing 8/16 (50 %),
7 enregistrements de preuve produits avec une diversité d'issue réelle (5 `SUPPORTED`,
2 `CONTRADICTED`) — contrairement au résultat dégénéré du mécanisme témoin à question fermée.
Protocole de validation tierce préparé le même jour (9 cas critiques C01–C09, délibérément
sans dépendance réseau), puis remis à un tiers externe : deux exécutions externes
indépendantes obtenues (9/9, 8/8 hashes conformes, 391/391 hors démonstrations live, 0
modification, dans deux environnements distincts), encodage UTF-8 du corpus français
vérifié explicitement et confirmé sans corruption par les deux relecteurs indépendamment.
**M7 parseur texte→preuve = VALIDATED**, clôturé explicitement par le porteur du projet le
2026-09-18 — détail complet (y compris deux observations honnêtement signalées : instabilité
d'un appel à l'autre du petit modèle local à température par défaut, et un artefact
d'encodage console écarté après vérification directe des octets) dans
`documentation/MetaHIA_M7_TextClaimParser_V0_1.md` Sec. 9 et `JOURNAL_DE_BORD.md`.
Reste hors périmètre : amélioration de la fidélité de parsing, option architecturale
« texte → nouveaux faits du graphe », intégration au corpus mixte de promotion.

Apprendre :
```text
Rule × Context × Depth × Provenance
            ↓
distribution of epistemic outcomes
```

Jamais `Rule = TRUE`.

### Garde-fous
- séparation train / validation / holdout ;
- aucune gold provenant de la dérivation ;
- métriques par règle, contexte, profondeur, provenance ;
- calibration ;
- robustesse au changement de corpus ;
- policy versionnée ;
- promotion impossible sans survie au holdout.

## 11. Trajectoire critique mise à jour
E20-D reste une piste scientifique parallèle : son ouverture n’interdit plus l’implémentation de M6, car les gates M3, M4 et M5 sont franchies sur leurs périmètres critiques. La fermeture générale E20-D reste requise pour les claims de découverte autonome générale et les objectifs cognitifs forts.

```text
M3 VALIDATED
   ↓
M4 VALIDATED
   ↓
M5 VALIDATED
   ↓
M6 IMPLEMENTATION            [FAIT]
   ↓
M6 THIRD-PARTY VALIDATION    [FAIT — clôturé par le porteur du projet 2026-09-17, JOURNAL_DE_BORD.md]
   ↓
INDEPENDENT HOLDOUT          [FAIT]
   ↓
M7 EMPIRICAL LLM LOOP        [FAIT -- portée "témoin LLM", 2026-09-17]
   ↓
M7 MIXED-CORPUS PROMOTION    [FAIT -- résultat neutre pour la calibration, 2026-09-18]
   ↓
M7 THIRD-PARTY VALIDATION    [FAIT -- clôturé par le porteur du projet 2026-09-18, JOURNAL_DE_BORD.md]
   ↓
M7 TEXT CLAIM PARSER         [FAIT -- fidélité de parsing 50 %, 2026-09-18]
   ↓
M7 TEXT CLAIM PARSER VALIDATION [FAIT -- clôturé par le porteur du projet 2026-09-18, JOURNAL_DE_BORD.md]
   ↓
M7 MIXED-CORPUS v0.2 (3 sources)  [FAIT -- +text claims seul ne promeut pas, +both promeut, 2026-09-18]
   ↓
M7 TEXT CLAIM CONSENSUS       [FAIT -- hypothèse infirmée, consensus aggrave la calibration, 2026-09-18]
   ↓
M7 CROSS-MECHANISM CONSENSUS  [FAIT -- dominé (32 appels, 0 preuve), piste fermée, 2026-09-18]
   ↓
M7 CONFIGURATION RETENUE      [FAIT -- "les deux" (union) choisi par le porteur du projet, 2026-09-18]
   ↓
M7 TÉMOIN LONGUEUR > 1        [FAIT -- 20/20 CONTRADICTED (limite déjà connue confirmée), Brier améliore mais prudence méthodologique, 2026-09-18]
   ↓
DÉCOUVERTE : HOLDOUT = GLOBAL_PRIOR SEUL  [FAIT -- vérifié pour tout M6/M7, mécanisme du gain multi-sauts confirmé (pas causal), 2026-09-18]
```

Parallèlement : `E20-D GLOBAL DISCOVERY = OPEN`.

## 12. Éléments différés explicitement
- ~~parseur texte → structure~~ — **partiellement FAIT (2026-09-18)**, portée restreinte à
  « texte → preuve sur prédiction existante » (pas « texte → nouveaux faits du graphe »),
  voir `documentation/MetaHIA_M7_TextClaimParser_V0_1.md`, fidélité de parsing 50 %,
  amélioration et validation tierce restent différées ;
- normalisation complète / MNF opérationnelle de bout en bout ;
- ~~communication LLM live multi-provider~~ — **partiellement FAIT (2026-09-17)** : un seul
  fournisseur (Ollama local) implémenté, portée "témoin LLM" seulement, voir
  `documentation/MetaHIA_M7_LLM_Fact_Proposer_V0_1.md`. Multi-provider reste différé ;
- ~~apprentissage structurel~~ — **FAIT (2026-09-17)**, voir M6, `VALIDATED` ;
- véritable vérificateur sémantique pour la gate empirique historique ;
- production V6 ;
- évolution cognitive avec rollback.

## 13. Indicateurs directeurs
K1 Structural Coverage; K2 Structural Generalization; K3 Provenance Completeness; K4 Epistemic Integrity; K5 Independent Validation Rate; K6 Recursive Closure Stability; K7 Useful Gain/Cost; K8 Holdout Generalization; K9 Calibration; K10 Promotion Safety.

## 14. Prochaine étape
~~M6 — Structural Learning v0.1 : implémentation + protocole de validation indépendante dès la conception.~~
**FAIT** — voir `documentation/MetaHIA_M6_Structural_Learning_V0_1.md`, `VALIDATED` (2026-09-17).

~~Protocole de validation tierce M6, sur le même modèle que M3/M4/M5.~~ **FAIT** — deux
exécutions externes indépendantes, `JOURNAL_DE_BORD.md`.

~~M7 — Empirical LLM Loop : fact-proposer, repli LAN, intégration corpus mixte, validation
tierce.~~ **FAIT** — `VALIDATED` (2026-09-18), voir
`documentation/MetaHIA_M7_LLM_Fact_Proposer_V0_1.md` Sec. 10.

~~Parseur texte → preuve, portée « texte → preuve sur prédiction existante ».~~ **FAIT** —
`VALIDATED` (2026-09-18), deux exécutions externes indépendantes, voir
`documentation/MetaHIA_M7_TextClaimParser_V0_1.md` Sec. 9 et `JOURNAL_DE_BORD.md`. Reste hors
périmètre : amélioration de la fidélité de parsing, intégration au corpus mixte de promotion.

~~Intégration au corpus mixte de promotion du parseur texte (comparaison à quatre
conditions : baseline / +témoin / +texte / +les deux).~~ **FAIT (2026-09-18)** — résultat
réel honnête et contraire à l'hypothèse de départ : `+texte` seul dégrade la calibration au
point de bloquer la promotion (`HOLDOUT_BRIER_ABOVE_THRESHOLD`), `+both` restaure une
promotion. Voir `documentation/MetaHIA_M7_TextClaimParser_V0_1.md` Sec. 10.

~~Consensus multi-modèles sur le parseur texte (llama3.2 local + qwen2.5-coder LAN, votants
indépendants, accord exact requis).~~ **FAIT (2026-09-18)** — hypothèse de départ **infirmée** :
le filtrage par consensus aggrave la calibration (Brier 0,58527 contre 0,50794 non filtré et
0,48125 baseline), au lieu de la corriger. Voir
`documentation/MetaHIA_M7_TextClaimParser_V0_1.md` Sec. 11.

~~Consensus inter-mécanismes (témoin + parseur doivent s'accorder).~~ **FAIT (2026-09-18)** —
piste **fermée** : coût mesuré identique ou supérieur à l'union simple (32 appels réels,
184,5 s), mais **zéro évidence produite** (le témoin et le parseur ne convergent jamais vers
la même réponse brute sur ce corpus). Mesure de surcharge ressource réelle disponible pour les
quatre configurations testées (témoin seul, parseur seul, union, consensus inter-mécanismes)
dans `documentation/MetaHIA_M7_TextClaimParser_V0_1.md` Sec. 12.

~~Décision de configuration retenue pour le pipeline d'évidence M7.~~ **FAIT (2026-09-18)** —
**« Les deux » (union simple)** retenu explicitement par le porteur du projet, malgré un Brier
légèrement moins bon que le témoin seul (0,489 contre 0,47), pour préserver la diversité
d'issue réelle du parseur en vue d'une amélioration future. Voir
`documentation/MetaHIA_M7_TextClaimParser_V0_1.md` Sec. 12 et `JOURNAL_DE_BORD.md`.

~~Extension longueur > 1 du témoin ou du parseur.~~ **FAIT (2026-09-18, témoin uniquement,
sur trois options présentées)** — mécanisme fonctionnel, 20/20 `CONTRADICTED` (même limite
empirique déjà documentée pour la longueur 1, confirmée une seconde fois sur une tâche plus
dure). Effet sur la calibration positif mais **non crédité comme compétence réelle du LLM**
(explication mécanique probable : biais systématique constant entre train et holdout, même
prudence que pour l'effet déjà observé en Sec. 10) — voir
`documentation/MetaHIA_M7_TextClaimParser_V0_1.md` Sec. 14.

~~Vérifier indépendamment l'hypothèse du biais mécanique (Priorité 1, point 1).~~ **FAIT
(2026-09-18)** — découverte plus large que prévu : **100 % des prédictions de holdout, pour
tout chiffre de calibration M6/M7 de ce projet depuis le tout premier baseline `VALIDATED`
(Brier 0,48125), utilisent `BASIS_GLOBAL_PRIOR`** — jamais `EXACT_BUCKET` ni `RULE_ONLY`.
Cause structurelle et intentionnelle (`split_by_rule` ne laisse jamais une règle apparaître à
la fois en entraînement et en holdout), pas un bug. Conséquence : aucun chiffre de calibration
de ce projet n'a jamais démontré d'apprentissage spécifique à une règle — seulement une
généralisation de la distribution de classe globale. L'hypothèse initialement avancée pour le
témoin multi-sauts (« même biais reproduit entre train et holdout d'une même règle ») était
**structurellement impossible et donc fausse** ; corrigée avec le mécanisme réel, vérifié.
Robustesse testée sur 10 graines : l'ajout de l'évidence multi-sauts améliore le Brier 8 fois
sur 10, le dégrade 2 fois sur 10 — pas une amélioration garantie. Voir
`documentation/MetaHIA_M6_Structural_Learning_V0_1.md` Sec. 11 et
`documentation/MetaHIA_M7_TextClaimParser_V0_1.md` Sec. 14 (mis à jour).

Reclassé le même jour, corroboré par un second relecteur indépendant (contrôle contrefactuel
convergent, Brier 0,47000 → 0,37535 sur une configuration adversarial+témoin en ajoutant un
lot artificiel tout-`CONTRADICTED`) : **`CONFIRMED_MECHANICAL_ARTIFACT`** (pas seulement
suspecté — l'inspection directe du code de décision, pas seulement une comparaison de scores,
prouve que le mécanisme est la seule chose qui se soit jamais produite sur ce holdout).

~~Priorité 1, points 2-3 : décision sur le témoin longueur > 1 et sur l'extension du
parseur.~~ **FAIT (2026-09-18)** — **témoin longueur > 1 non promu** dans la configuration
retenue (gain non causal, non garanti, 8/10 graines seulement) mais conservé comme témoin
expérimental isolé ; **extension du parseur à la longueur > 1 différée** par anticipation du
même raisonnement, coût par appel déjà plus élevé. Voir
`documentation/MetaHIA_M7_TextClaimParser_V0_1.md` Sec. 14.

**Prochaine étape : non encore décidée explicitement** — Priorité 1 (boucles scientifiques
ouvertes) est close ; passer à la Priorité 2 (hygiène documentaire M7) ou à la Priorité 3
(diversification du corpus, interface minimale M1-M6), ou autre chantier.
