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

**M7 — Empirical LLM Loop** : neuf mécanismes/décisions testés entre le 2026-09-17 et le
2026-09-18 (témoin question fermée, corpus mixte v0.1/v0.2, deux consensus, extension
longueur > 1, découverte transversale du `BASIS_GLOBAL_PRIOR`) — **synthèse complète en une
page** : `documentation/MetaHIA_M7_State_Summary_V1.md`. Configuration active aujourd'hui :
corpus mixte v0.2 condition `+both` (adversarial + témoin + parseur, longueur 1). Détail
complet, citations verbatim des relecteurs externes, et raisonnement de conception dans
`documentation/MetaHIA_M7_LLM_Fact_Proposer_V0_1.md`, `documentation/MetaHIA_M7_TextClaimParser_V0_1.md`
et `JOURNAL_DE_BORD.md`.

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

**Historique condensé** (chronologie exhaustive avec citations verbatim :
`JOURNAL_DE_BORD.md` ; état M7 complet : `documentation/MetaHIA_M7_State_Summary_V1.md`) —
tous **FAIT**, dans l'ordre : M6 implémentation + validation tierce (`VALIDATED`, 2026-09-17) ;
M7 témoin question fermée + repli LAN + corpus mixte v0.1 + validation tierce (`VALIDATED`,
2026-09-18) ; M7 parseur texte + validation tierce (`VALIDATED`, 2026-09-18) ; corpus mixte
v0.2 à 4 conditions (parseur seul dégrade, union sauve la promotion) ; consensus même-
mécanisme (hypothèse infirmée) ; consensus inter-mécanismes (dominé, fermé) ; décision de
configuration retenue par le porteur du projet (« les deux ») ; extension longueur > 1 du
témoin (mécanisme fonctionnel, gain suspecté) ; vérification de l'hypothèse (Priorité 1) →
découverte transversale **`CONFIRMED_MECHANICAL_ARTIFACT`** (100 % des holdouts de ce projet,
y compris le premier baseline `VALIDATED`, n'utilisent que `BASIS_GLOBAL_PRIOR`, jamais
`EXACT_BUCKET`/`RULE_ONLY` — corroboré par un second relecteur indépendant) ; décisions P1.2/P1.3
(témoin longueur > 1 non promu, parseur longueur > 1 différé).

~~Priorité 2 : hygiène documentaire M7 (synthèse d'état unique + élagage de ce document).~~
**FAIT (2026-09-18)** — voir `documentation/MetaHIA_M7_State_Summary_V1.md` et cette section.

~~Priorité 3 : diversification du corpus (second domaine indépendant) + interface minimale
M1-M6 (M7 explicitement exclu).~~ **FAIT (2026-09-18)** — paquet reçu, inspecté fichier par
fichier, exécuté réellement, un bug réel trouvé et corrigé (collision de préfixe `record_id`
entre corpus organisationnel et corpus familial v0.2), couverture de tests renforcée (2→13 et
3→7 tests), **adopté**. Second domaine (organisation/projets, `corpus/organization_facts_v0_1.json`) :
27 candidats, 24 enregistrements réels, 12 règles distinctes, Brier holdout 0,6953125 —
diversité intra-domaine démontrée, **transfert inter-domaines non démontré** (limite
explicitement déclarée, pas cachée). Interface `m1_m6_interface_v0_1.py` : contrats de
transport M1→M2→M4→M5→M6 typés et validés, M7 explicitement exclu — pas encore une interface
utilisable par un humain (CLI/API), seulement un contrat de composition interne. 461/461 tests,
0 régression. Voir `documentation/MetaHIA_Corpus_Diversification_and_M1_M6_Interface_V0_1.md`
Sec. 9.

**Prochaine étape : non encore décidée explicitement.**
