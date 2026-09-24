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

~~Interface M1-M6 v0.2 (contrat versionné, stable) + régression multi-domaines + probe
multi-seed.~~ **FAIT (2026-09-19)**, reçu dans le même paquet qu'une chaîne d'expériences
« P4.1-P4.5 » de transfert structurel inter-domaines — **adopté séparément après vérification
par exécution réelle** : `m1_m6_interface_v0_2.py` (enveloppe versionnée, métadonnées d'audit
qui n'atteignent jamais M6), `p5_m1_m6_multidomain_regression_v0_1.py` +
`p5_multiseed_regression_v0_1.py` (utilisent correctement `build_real_corpus_v2`, tous les
chiffres confirmés exacts : Famille 0,48125, Organisation 0,6953125, combiné 0,4919875).
Probe multi-seed (10 graines) : la variance de calibration reste sensible au split sur ces
petits corpus — aucun chiffre de performance M6 n'est encore considéré représentatif. Voir
`documentation/P5_M1_M6_Stabilization_Multidomain_Regression_v0_1.md`.

~~Chaîne d'expériences P4.1-P4.5 (transfert structurel inter-domaines, invariant autonome,
opération exécutable).~~ **REJETÉE (2026-09-19)**, non adoptée — deux défauts méthodologiques
réels trouvés par exécution directe, pas par simple lecture : (1) P4.1/P4.2 utilisent
`m6_corpus_from_m4_m5_v0_1.py` (mécanisme dégénéré déjà documenté, remplacé par v0.2 partout
ailleurs dans ce projet) comme source « Famille », donnant 23 enregistrements 100 %
`SUPPORTED` — aucun signal négatif possible ; (2) P4.4/P4.5, l'affirmation la plus forte
(« opération exécutable → nouvelle structure », touchant directement les critères de clôture
E20-D), est **circulaire** : le motif « prédisant » `Module_D → Direction_H` est généralisé à
partir d'exactement 2 exemples qui incluent le cas lui-même testé — confirmé par
instrumentation directe du code, pas par supposition. E20-D reste `OPEN`, sans changement.
Détail complet : `documentation/P4_Transfer_Review_and_Rejection_2026-09-19.md`.

~~P4-R v0.2 — remplacement non-circulaire de la chaîne P4.1-P4.5.~~ **FAIT/ADOPTÉ
(2026-09-21)**, reçu en paquet externe séparé, exécuté réellement dans une copie locale
isolée (aucun accès réseau, aucun serveur LAN) avant intégration. Corrige les deux modes
d'invalidité identifiés le 2026-09-19 : flux `SOURCE DISCOVERY -> FREEZE -> TARGET
EXECUTION` strict (audité — aucune identité source/cible ne fuit dans l'opération figée,
vérifié), et gate d'endpoint fort qui renvoie honnêtement `NOT_DERIVABLE` au lieu de
revendiquer une prédiction. Deux sous-résultats distincts, tous deux confirmés par
exécution directe : micro-gate structurel `PASS` (génération d'un nouvel objet K3 à partir
de deux opérandes cibles — ne prouve aucune sémantique) ; gate d'endpoint `OPEN_EXPECTED`
(aucune invention d'endpoint, comme attendu de l'absence d'évaluateur sémantique
transitif dans le noyau K3 actuel). **E20-D reste `OPEN`** — ce protocole ne le ferme pas,
il ferme seulement les défauts méthodologiques P4.1-P4.5. Un import mort supprimé avant
intégration. 473/474 tests passing (1 skip Ollama déjà documenté) dans la copie isolée,
confirmé de nouveau dans le dépôt live avant commit. Aucun paquet de validation tierce
préparé pour ce protocole : contrairement à M4-M7, P4-R ne revendique aucune clôture
(`OPEN_EXPECTED`/`OPEN`), donc rien à faire valider par un tiers pour l'instant — un
paquet sera préparé si/quand une vraie règle de dérivation indépendante est conçue pour le
gate d'endpoint fort. Détail complet : `documentation/P4R_Non_Circular_Structural_Transfer_V0_2.md`
Sec. 6.

~~Interface minimale CLI/API préproduction pour test humain sur le cœur M1-M6.~~ **FAIT
(2026-09-21)** — `cli_preprod_v0_1.py`, quatre commandes (`manifest`, `list-records`,
`regression`, `predict`), n'ajoute aucune capacité nouvelle : expose seulement l'API déjà
validée (`build_real_corpus_v2`, `build_organization_corpus`, `StructuralLearningPolicy`,
`split_by_rule`) derrière une surface qu'un humain peut lancer sans lire le code Python.
Discipline de transparence non négociable : `predict` renvoie toujours le champ `basis` de
chaque prédiction (jamais masqué), et `regression` renvoie `basis_distribution_over_holdout`
— un testeur voit dès la première commande que 100 % des prédictions holdout de ce projet
reposent sur `BASIS_GLOBAL_PRIOR` (la découverte du 2026-09-18), pas seulement dans un
document séparé. `manifest.m7_excluded=true` vérifié par exécution, pas seulement par
lecture. 7 tests (sous-processus réels, pas de mock) : reproduisent exactement les deux
baselines déjà validés (Famille Brier 0,48125 ; Organisation Brier 0,6953125), vérifient
l'échec fermé sur un `record_id` inconnu, et vérifient qu'un enregistrement réellement en
holdout reçoit bien `basis=GLOBAL_PRIOR` en itérant sur tous les enregistrements, pas en le
supposant. Répond directement à la question initiale de ce chantier (« le core algébrique
peut-il être mis en préprod pour test humain ? ») pour le périmètre M1-M6 — M7 reste hors
périmètre (déjà exclu par construction de `m1_m6_interface_v0_2.py`), aucune capacité
nouvelle, aucune clôture de gate scientifique revendiquée. Détail complet :
`documentation/MetaHIA_CLI_Preprod_M1_M6_V0_1.md`.

~~Troisième domaine indépendant pour re-tester si le transfert inter-domaines reste non
démontré à plus grande échelle.~~ **FAIT (2026-09-21) — P6.** Nouveau domaine
« chaîne d'approvisionnement » (`corpus/supply_chain_facts_v0_1.json`,
`m6_corpus_from_supply_chain_v0_1.py`, réutilise exactement le mécanisme déjà validé
d'Organisation), topologie délibérément non isomorphe (asymétrie 3/1 ouvriers-usines,
toutes les pièces sur une seule branche) pour éviter un simple renommage. Résultat réel :
24 enregistrements, 12 règles, diversité réelle (17 `SUPPORTED`/7 `CONTRADICTED`), Brier
holdout 0,375. **Conclusion inchangée, vérifiée par exécution** : le transfert
inter-domaines reste structurellement impossible à observer (signatures de règle
disjointes par vocabulaire de domaine) — confirmé par 100 % `BASIS_GLOBAL_PRIOR` sur le
holdout combiné à trois domaines, pas seulement supposé. Ce qui CHANGE réellement :
`p6_three_domain_multiseed_v0_1.py` (10 graines) montre que l'écart-type du Brier combiné
passe de 0,107167 (deux domaines, P5) à 0,056129 (trois domaines) — la mise en commun
stabilise l'estimation du prior global, sans transfert sémantique. CLI étendue
(`--domain supply_chain`). 19 nouveaux tests (9 corpus + 6 régression + 4 multiseed),
1 ajouté à la CLI. Détail complet : `documentation/P6_Third_Domain_Supply_Chain_V0_1.md`.

~~Étendre la CLI à une commande `regression --domain combined`.~~ **FAIT (2026-09-21)** —
`cli_preprod_v0_1.py` accepte désormais `--domain combined` sur les trois commandes
(`list-records`, `regression`, `predict`), qui pool les trois domaines réels et reproduit
exactement le baseline `combined_three` de P6 (74 enregistrements, 44 règles, Brier
holdout 0,35556). `manifest` liste `combined` et porte un nouveau champ
`combined_domain_caveat` qui rappelle explicitement que ce n'est pas une revendication de
transfert inter-domaines — le même disclaimer que P6 Sec. 3-4, jamais laissé implicite. 3
tests ajoutés (11 au total sur la CLI). Détail complet :
`documentation/MetaHIA_CLI_Preprod_M1_M6_V0_1.md` Sec. 2 et 5.

~~Quatrième domaine si le motif de stabilisation de la Sec. 4 de P6 doit être confirmé
au-delà de trois points.~~ **FAIT (2026-09-21) — P7.** Nouveau domaine « bibliothèque »
(`corpus/library_facts_v0_1.json`, `m6_corpus_from_library_v0_1.py`, mécanisme déjà validé
réutilisé à l'identique), topologie encore différente (auteurs 2/1/3 livres, éditeurs 2/1
auteurs) pour éviter tout renommage. Résultat réel : 20 enregistrements, 10 règles,
diversité réelle (15 `SUPPORTED`/5 `CONTRADICTED`), Brier holdout 0,375. **Conclusion
« transfert non démontré » toujours inchangée** — reconfirmée une troisième fois (100 %
`BASIS_GLOBAL_PRIOR` sur le holdout combiné à quatre domaines). **Résultat le plus
important, et il infirme l'hypothèse implicite de la question posée** :
`p7_four_domain_multiseed_v0_1.py` (10 graines) montre que l'écart-type du Brier combiné
NE continue PAS à baisser — il **remonte légèrement** de 0,056129 (trois domaines, P6) à
0,066963 (quatre domaines), tout en restant bien inférieur au chiffre à deux domaines
(0,107167, P5). La stabilisation observée P5→P6 n'était donc pas le début d'une tendance
monotone — trois domaines constituaient un minimum local sur cette plage, pas une loi
générale. CLI étendue (`--domain library`) ; `--domain combined` évolue pour pool
désormais quatre domaines (94 enregistrements, 54 règles) — comportement d'outil qui
évolue avec le nombre de domaines connus, documenté explicitement comme tel (le test CLI
correspondant a été mis à jour vers les nouveaux chiffres, avec la raison expliquée dans
le test lui-même). 19 nouveaux tests (9 corpus + 6 régression + 4 multiseed, dont un test
qui gèle explicitement la non-monotonie comme régression permanente), 2 mis à jour sur la
CLI. Détail complet : `documentation/P7_Fourth_Domain_Library_V0_1.md`.

~~Reconsidérer la voie principale vers E20-D à la lumière d'une revue externe de
`e20d_protocol.py` (déjà présent dans ce dépôt, commit `92d396d`).~~ **FAIT (2026-09-21) —
P4-T, Induction de transformation structurelle, Gates A-G.** Remplace P4-R comme voie
principale vers E20-D. Revue externe vérifiée par exécution directe avant adoption (pas
acceptée sur récit) : 99 tests E20-D existants rejoués (0 échec, périmètre plus large que
les « 69 » cités, sans contradiction) ; `test_recursive_transformation_replays_on_unseen_rows`
inspecté ligne à ligne et confirmé non circulaire (entités de holdout totalement fraîches,
à la différence du bug P4.4/P4.5) ; sondes adversariales indépendantes confirmant cible
constante rejetée et many-to-one rejeté.

Limite réelle trouvée dans `kernel2.compare()`/`compare_candidates()` : ces fonctions
exigent une arité égale entre les deux côtés comparés, donc ne peuvent structurellement
pas exprimer une transformation qui change l'arité (projection `f(x,y)=x`, duplication
`f(x)=(x,x)`) — exactement la limite que la revue avait identifiée. Nouveau fichier
`p4t_structural_transformation_induction_v0_1.py` (ne modifie ni `e20d_protocol.py` ni
`kernel2.py`) : réutilise le mécanisme déjà validé pour RÉFÉRENCE-ÉGALITÉ/PERMUTATION/
RÉCURSIF, et ajoute un mécanisme unique et général (`discover_selection_mapping`) qui
couvre projection et duplication sans code dupliqué — vérifié par exécution avec replay
aveugle sur entités fraîches pour les deux familles, plus une composition littérale de
deux transformations indépendamment gelées (`compose_frozen`). Pipeline complet Gates
A→D (discovery → freeze opaque → replay aveugle → vérification) vérifié pour quatre
familles. Porte E (anti-triche) vérifiée par 4 sondes adversariales : ambiguïté exposée,
contradiction rejetée, cible constante rejetée, cible non structurelle rejetée. Porte B
(gel) vérifiée sans fuite de provenance d'entraînement (un faux positif de test dû à une
coïncidence de sous-chaîne dans un hash SHA-256 a été trouvé et corrigé pendant la
rédaction, pas dans le mécanisme lui-même). Porte G (coût) mesure réellement temps et
comptes d'opérations, mais n'est explicitement PAS encore branchée sur le modèle ROI
d'E20-D.19 (`e20d_cognitive_control_v0_1.py`, couplé à `PathCandidate`/`PathRecord`, pas à
un candidat de transformation) — déclaré ouvert, pas revendiqué fait. 13 nouveaux tests,
tous exécutés réellement. **Verdict : `P4-T = STRONG_MICROSTRUCTURAL_CANDIDATE`. E20-D
reste `OPEN`** — ce chantier ferme seulement la question du mécanisme (réel, non
circulaire, maintenant pour quatre familles + leur composition), pas la clôture
scientifique d'E20-D elle-même (pas de découverte non supervisée générale, pas de corpus
de holdout verrouillé séparément par un tiers, pas de sélection automatique entre
hypothèses candidates). Détail complet :
`documentation/P4T_Structural_Transformation_Induction_V0_1.md`.

~~Revue externe de durcissement de P4-T avant d'en faire un véritable gate E20-D.~~
**FAIT (2026-09-21) — P4-T.1.** Revue externe recentrant explicitement la trajectoire
E20-D sur P4-T (pas le transfert inter-domaines), et proposant une séquence P4-T.1→P4-T.7.
Deux affirmations techniques concrètes vérifiées par exécution directe avant correction
(pas acceptées sur récit) : (1) `freeze()` laissait fuiter les identifiants de lignes
d'entraînement pour la branche PERMUTATION/RECURSIVE (`CrossSlotCandidate.evidence_rows`
et même le `node_id`/`provenance` du `Node` PATTERN lui-même) — confirmé `"row1" in
repr(frozen)` avant correction ; (2) le `structural_digest` de cette même branche ne
dépendait que de `(family, relation_kind)`, constant pour toute une famille — deux
permutations différentes produisaient le même digest, confirmé par construction directe.
Corrigé : `freeze()` reconstruit une copie anonymisée du PATTERN (`_anonymize_pattern`) et
calcule le digest via `kernel2.structural_signature()` (déjà utilisé ailleurs dans ce
projet pour la même fonction). 2 tests de régression permanents ajoutés (15 au total sur
P4-T). **P4-T.1 clôt le premier point de la séquence proposée** ; voir
`documentation/P4T_Structural_Transformation_Induction_V0_1.md` Sec. 6.1 et 9.1-9.2 pour
la matrice de clôture E20-D mise à jour et la séquence complète P4-T.2→P4-T.7.

~~Explorer JEV (TypeSafe System One) et ses alternatives locales comme mécanisme
d'évidence M7.~~ **FAIT (2026-09-21) — planification P8, explicitement séparée de la
trajectoire E20-D/P4-T** (la revue externe le confirme : JEV ne doit jamais servir à
« fermer » E20-D, seulement à proposer une évidence analogique M7, comme tout LLM déjà
utilisé dans ce projet). Benchmark réel exécuté contre l'API Jev officielle (22/22 cas,
`jev-1.13.0`) : 100 % sujet/relation sur cas positifs, 81 % objet (bug de bouclage
auto-référentiel réel, 3/16 cas), coercition d'un quasi-synonyme hors-vocabulaire
(« conjoint » → `EPOUX_DE`, confiance 0,98 — échec net sur le critère le plus important
pour ce projet). Trois alternatives locales proposées par l'utilisateur vérifiées réelles
(pas hallucinées) par requête directe à l'API GitHub : `jaredpalmer/kev` (recommandé —
compatible fil-à-fil avec `jev_client_v0_1.py`, probabilités réellement calibrées par
lecture de logits) ; `razorback16/openjev` et `githubnext/localjev` (probabilités
auto-rapportées par le modèle, pas des logits — le README de LocalJev le déclare
lui-même). **P8 = PRIORISÉ, EN ATTENTE D'INFRASTRUCTURE** : bloqué sur la configuration
Ollama/LAN (`192.168.1.11`) que l'utilisateur fournira. Aucun code d'intégration écrit
avant cette information — seul le plan technique complet (fichiers
`m7_jev_relation_choice_v0_1.py`/`m7_corpus_from_jev_v0_1.py`, garde-fous
sujet≠objet/GROUNDED_ANALOGY) est documenté. Détail complet :
`documentation/P8_Jev_Kev_Local_Decision_Model_V0_1.md`.

~~P4-T.3 — étape « hypothèses → sélection/rationalisation » manquante.~~ **FAIT
(2026-09-21).** `discover_all_hypotheses()`/`select_hypothesis()` : classement des
hypothèses candidates par complexité structurelle uniquement (rasoir d'Occam,
`REFERENCE_EQUALITY` < `COMPARE_PERMUTATION` < `SELECTION_MAPPING` < `COMPARE_RECURSIVE`),
égalité de rang exposée comme `AMBIGUOUS_SELECTION`, jamais choisie arbitrairement.
Constat vérifié par exécution, pas supposé : `REFERENCE_EQUALITY`/`COMPARE_PERMUTATION`
sont intrinsèquement non orientées (une relation d'égalité de référence vaut dans les deux
sens) — documenté comme propriété réelle, pas caché. Corroboration optionnelle via
`e20d_rationalization_v0_1.rationalize()` **réutilisé sans aucune modification** : deux
transformations récursives découvertes indépendamment à partir de données totalement
disjointes et structurellement identiques donnent `similarity=1.0`/`SUPPORTED_HISTORICAL`,
vérifié par exécution. Frontière de portée explicite : ne s'applique pas à
`SELECTION_MAPPING` (`sigma` est un tuple d'entiers, pas un `RefObject` comparable par
E20-D.6) — renvoie `None`, pas une comparaison forcée. 8 nouveaux tests (23 au total sur
P4-T). Détail complet : `documentation/P4T_Structural_Transformation_Induction_V0_1.md`
Sec. 8.1 et 9.1-9.2 (matrice de clôture E20-D mise à jour : sélection d'hypothèses passe de
🔴 absente à 🟢 fait).

~~P4-T.2 — vrai benchmark séparé (train/holdout aveugle/témoin indépendant, verrouillé
avant exécution).~~ **FAIT (2026-09-21).** Trois fichiers distincts :
`p4t_locked_benchmark_cases_v0_1.py` (train + holdout SOURCE seule, aucune information de
cible même masquée), `p4t_locked_benchmark_witness_v0_1.py` (seul fichier avec les bonnes
réponses), `p4t_locked_benchmark_runner_v0_1.py` (ordonne découverte → gel → replay aveugle
→ **engagement sur disque** → seulement ensuite lecture du témoin). Verrouillage vérifié
mécaniquement, pas seulement promis : contrôle statique par texte (`inspect.getsource`),
contrôle statique par AST (mirroring `_m7_dependency_scan` déjà utilisé pour M7), et
contrôle **dynamique** confirmant via `sys.modules` lui-même que le module témoin est
absent au moment de l'engagement. 7 cas couvrant les 5 familles P4-T (permutation,
récursif, projection, duplication, composition) plus les deux issues fermées
(`AMBIGUOUS`, `REJECTED`) — **7/7 correspondent au témoin**, vérifié par exécution réelle.
Deux bugs réels trouvés et corrigés pendant la construction : comparaison par `repr()`
(qui embarque un `node_id` arbitraire, jamais identique entre exécutions) au lieu de
`kernel2.structural_equal()` — confirmé 4/5 cas à prédiction échouaient à tort avant
correction ; `frozen_id` basé sur une adresse mémoire non déterministe, corrigé pour un
fichier de prédictions engagées reproductible. 8 nouveaux tests. **Portée déclarée
explicitement** : protocole auto-administré (structurellement verrouillé), PAS une
clôture de gate par un tiers externe — même distinction déjà posée pour M4-M7 dans ce
projet. Détail complet : `documentation/P4T2_Locked_Benchmark_V0_1.md`.

~~P4-T.4 — nouvelles familles de transformation au-delà de
permutation/récursif/projection/duplication/composition.~~ **FAIT (2026-09-21).**
Sélection multi-source (`discover_multi_source()`/`discover_multi_source_selection_mapping()`) :
assemble une cible à partir de **plusieurs** structures source nommées indépendamment
(combinaison qu'aucune famille précédente — mono-source ou récursive — ne pouvait
exprimer), même discipline de non-devinette (`sigma[j]` devient `(indice_source,
indice_enfant)`, ambiguïté/rejet jamais devinés). Vérifié par exécution réelle : cible
assemblée depuis deux sources indépendantes correctement découverte et rejouée sur des
entités totalement fraîches, aucune fuite de provenance d'entraînement dans l'objet gelé.
Classée rang 4 (la plus complexe) dans `FAMILY_COMPLEXITY_RANK` de P4-T.3 — le rasoir
d'Occam continue de préférer une famille mono-source quand elle suffit. 5 nouveaux tests.

~~P4-T.6 — brancher la Porte G sur le modèle ROI d'E20-D.19.~~ **FAIT (2026-09-21).**
`score_hypothesis_roi()` : adaptateur **parallèle**, pas un appel direct à
`score_candidate()` (qui exige un véritable `kernel2.PathRecord` — un chemin de graphe,
pas une hypothèse de transformation ; fabriquer un faux `PathRecord` aurait été la même
comparaison forcée déjà refusée ailleurs dans ce projet). Réutilise la formule ROI et les
constantes de décision d'E20-D.19 (`DECISION_EXPLORE`/`DEFER`/`STOP`, importées telles
quelles, jamais redéfinies) ; `e20d_cognitive_control_v0_1.py` non modifié. `nouveauté`
réutilise le crochet de rationalisation de P4-T.3 (0,0 si correspondance historique
`SUPPORTED_HISTORICAL`, 1,0 sinon) ; `coût` est réel et mesuré (Porte G), jamais estimé ;
`gain_attendu` reste fourni par l'appelant, comme dans E20-D.19 lui-même. Vérifié par
exécution : une correspondance historique fait chuter le ROI à exactement 0,0. 5 nouveaux
tests. Matrice de clôture E20-D mise à jour : le coût/ROI passe de 🟠 mesure seule à 🟢
mesure + adaptateur.

~~P4-T.1 bis — durcissement résiduel de l'opacité de `freeze()` (fuite via
`literal_constraint`, digest non invariant à l'identité des entités).~~ **FAIT
(2026-09-22).** Une seconde revue externe a montré que le durcissement P4-T.1
(2026-09-21) était incomplet : `_anonymize_pattern()` remplaçait `node_id`/`provenance`
mais copiait `PatternSlot.literal_constraint` sans modification. Deux bugs réels
confirmés par exécution directe avant correction : (1) une position découverte comme
« toujours exactement cette entité d'entraînement » (créneau constant d'un motif
récursif, cas C02 du benchmark verrouillé) gardait le vrai `NodeRef` d'entraînement
verbatim dans le motif gelé ; (2) le digest, calculé sur la structure **brute**
pré-anonymisation, n'était donc pas invariant à l'identité des entités — deux
transformations de forme identique mais entraînées sur des entités différentes
produisaient deux digests différents. Une affirmation précise du relecteur (« avec un
holdout réellement frais, le replay récursif échoue ») a été **testée et réfutée**, pas
acceptée sur récit : `blind_replay()` ne renvoie jamais `None` pour une différence de
valeur littérale (confirmé par exécution directe, et par la docstring déjà figée de
`kernel2.apply_pattern()`, qui documente ce comportement comme délibéré). Corrigé :
nouvelle fonction `_anonymize_literal()` appelée uniformément sur chaque
`literal_constraint` ; le digest de `freeze()` est désormais calculé sur l'objet **déjà
anonymisé**, jamais sur la structure brute. Corollaire : le cas C02 du benchmark
verrouillé, qui réutilisait `NodeRef("c02_z")` identique entre train et holdout (en
contradiction avec son propre commentaire), a été corrigé (`c02_hz`) et son témoin
recalculé par exécution directe. 2 nouveaux tests de régression permanents (35 total sur
P4-T). Détail complet : `documentation/P4T_Structural_Transformation_Induction_V0_1.md`
Sec.6.2, `documentation/P4T2_Locked_Benchmark_V0_1.md` Sec.5bis.

~~P4-T.2 v0.2 + intégration réelle de P4-T.3 dans le benchmark verrouillé.~~ **FAIT
(2026-09-22).** Trois nouveaux fichiers (`p4t_locked_benchmark_cases_v0_2.py`,
`_witness_v0_2.py`, `_runner_v0_2.py`), v0.1 laissé strictement inchangé. Le runner
appelle désormais `discover_all_hypotheses()` → `select_hypothesis()` → `freeze()` de
l'hypothèse réellement retenue, au lieu de recevoir une paire de positions du cas de
test — `LockedCaseV2` ne porte d'ailleurs plus aucun champ de position, vérifié par un
test dédié. 6 cas, dont les deux demandés explicitement par la revue : un à ≥2
hypothèses valides avec sélection unique (`V2C03_TWO_HYPOTHESES_UNIQUE_WINNER`, 3
hypothèses au total : 2 `COMPARE_RECURSIVE` à égalité + 1 `SELECTION_MAPPING` gagnante)
et un à ≥2 hypothèses de même complexité (`V2C04_AMBIGUOUS_SELECTION`, 4 hypothèses
`REFERENCE_EQUALITY` à égalité). **Résultat honnête trouvé par exécution directe avant
toute conception de cas** : une ligne à seulement deux positions porteuses de `Node`
(source et cible, rien d'autre) est directionnellement ambiguë sous sélection réelle
pour une famille auto-inverse (`COMPARE_PERMUTATION`, `COMPARE_RECURSIVE`) — vérifié
concrètement, pas supposé. 6/6 cas correspondent au témoin, même triple verrouillage
mécanique que v0.1 (texte, AST, `sys.modules`) réappliqué. Un nouveau test permanent
garde explicitement contre la réintroduction du défaut corrigé par P4-T.1 bis (fuite
d'identité holdout↔train), via une comparaison de `ref_id` réellement extraits, pas de
chaîne complète. 12 nouveaux tests (582 total dans la suite, 575 passés + 7 démos
réseau optionnelles non exécutables dans ce bac à sable). **Portée non couverte, à
signaler honnêtement** : la demande précise de la revue de porter le cas C02 lui-même
avec un *troisième* `NodeRef` frais (distinct de `c02_z` et `c02_hz`) n'a pas de sens
littéral ici — le nouveau schéma de cas v0.2 ne fixe plus aucune position, donc il n'y a
plus de case nommé « C02 » à porter ; l'inquiétude sous-jacente (aucune identité
partagée entre train et holdout) est néanmoins couverte, de façon plus générale, par le
nouveau test de non-réutilisation ci-dessus, appliqué à tous les cas v0.2. Détail
complet : `documentation/P4T2_Locked_Benchmark_V0_1.md` Sec.6bis,
`documentation/P4T_Structural_Transformation_Induction_V0_1.md` Sec.8.1/9.1/9.2.

~~P4-T.5 — structure émergente (opération figée appliquée à de nouveaux opérandes,
recouvre partiellement E20-D.17).~~ **FAIT (2026-09-22).** Nouveau fichier
`p4t_emergent_structure_v0_1.py`, adaptateur parallèle vers
`e20d_emergent_structure_v0_1.py` (même discipline que P4-T.6 : pas d'appel forcé à
`generate_emergent_structure()`, qui exige un opérateur `RefObject` incompatible avec
une `FrozenTransformation`) — ajoute une vérification de nouveauté (`structural_equal`)
au-dessus d'un `blind_replay()` non modifié. Démontré pour `SELECTION_MAPPING`
(projection, duplication) : opérande jamais vu dans l'entraînement → structure neuve
vérifiée contre un ensemble `observed` ; doublon exact déjà présent → `NOT_NEW` ; forme
incompatible → `NO_PREDICTION` fail-closed. **Frontière de portée réelle, trouvée par
exécution directe avant d'écrire un seul test, pas supposée** : les familles à base de
motif (`COMPARE_PERMUTATION`, `COMPARE_RECURSIVE`) exigent un lot de fraîches
observations de la même taille que l'entraînement pour rejouer (le `PATTERN` gelé a
lui-même une arité de premier niveau égale au nombre de lignes d'entraînement) — un seul
opérande renvoie donc correctement `NO_PREDICTION`, jamais une structure fabriquée à
tort ; gardé par un test de régression permanent, pas traité comme un bug à corriger.
8 nouveaux tests (590 total dans la suite, 583 passés + 7 démos réseau optionnelles non
exécutables dans ce bac à sable). Le sens sémantique de la structure produite reste
Inconnu, exactement le contrat déjà déclaré par E20-D.17 lui-même — ce chantier prouve la
nouveauté et la traçabilité, jamais la signification. Détail complet :
`documentation/P4T5_Emergent_Structure_V0_1.md`.

**Prochaine étape : non encore décidée explicitement** — options restantes : (a) P8 —
dès que l'infrastructure Ollama/LAN promise par l'utilisateur est disponible ;
(b) cinquième domaine M6 ; (c) P4-T.7 — validation indépendante (suppose un tiers
réellement disponible, non le cas dans cette session). Aucune de ces trois n'est
urgente ; à décider explicitement avant de commencer, comme pour chaque étape précédente
de ce chantier.

---

## 15. Mise à jour — état au 24 septembre 2026 (synchronisation demandée par le porteur du projet)

Ce document était en retard sur l'état réel du dépôt depuis le 17/09. Mise à
jour de synchronisation uniquement — aucun des constats des sections 1-14
n'est modifié ou réévalué ici ; **E20-D reste `OPEN`**, sans changement de
statut (section 5).

### 15.1 État vérifié des chantiers ouverts depuis le 17/09

```text
P4-T.7 (validation tierce de P4-T)      ✅ CLOSED   (2026-09-23)
P4-U.1 (découverte compositionnelle
        supervisée, relations déjà
        étiquetées)                     ✅ THIRD-PARTY GATE CLOSED (2026-09-23)
P4-U.2 (découverte autonome de
        relations inconnues)             🟠 OPEN_RESEARCH, protocole gelé,
                                             calibration close (voir 15.2)
E20-D                                    🔴 OPEN, sans changement
```

**P4-T.7** — clos par le porteur du projet sur la base de deux
exécutions convergentes (auto-administrée + un ingénieur systèmes
réellement externe, Linux Ubuntu Server 24 LTS), résultats identiques
au commit `98bb4477`. Voir `release_manifest.json` clé `p4t_status` et
`documentation/P4T_Structural_Transformation_Induction_V0_1.md` Sec. 9.

**P4-U.1** — gate de validation tierce clos par le porteur du projet
sur la base d'une seule exécution humaine véritablement externe
(départ explicite et assumé du précédent M6/M7/P4-T.7 qui exigeait deux
exécutions convergentes). **Le pipeline complet, y compris le
« set-valued replay » (`p4u1_set_valued_replay_v0_1.py`, Gate C
redéfinie comme propriété d'EXISTENCE plutôt que d'UNICITÉ pour gérer
les nœuds-hub à plusieurs continuations légitimes), est déjà implémenté,
testé (13 tests dédiés, `tests/test_p4u1_set_valued_replay_v0_1.py`) et
intégré dans `p4u1_locked_benchmark_runner_v0_1.py`, le runner exact du
benchmark verrouillé validé par le tiers externe.** Ce point corrige
explicitement une caractérisation erronée reçue du porteur du projet
lors de cette synchronisation (« set-valued replay reste un chantier
expérimental/documentaire, à implémenter ») — vérifié directement par
lecture du code et par ré-exécution de la suite dédiée (13/13 PASS)
avant d'écrire cette section, pas accepté sur récit. **P4-U.1 n'a donc
aucune implémentation en attente** ; ce qui reste ouvert pour P4-U.1
est uniquement la question de généralisation déjà actée
(`GENERALIZATION OPEN`, non rouverte ici) et la clôture non-bloquante de
la non-discriminance de `position_groups` (v0.3 Sec. 10.7). Voir
`release_manifest.json` clé `p4u1_status`.

### 15.2 P4-U.2 — protocole et calibration

```text
Cadrage v0.1 → v0.2 → v0.3                         ✅ FAIT
Protocole v0.1 (Gate I/Gate H formalisées)          ✅ GELÉ (f6a96b2)
Calibration C1 (statistique × modèle nul × Gate H)  ✅ ARCHIVÉE (854b32e)
Calibration C2 (puissance Gate I)                   ✅ ARCHIVÉE (97981f0)
Calibration C3 (Gate H mini-campagne)               ✅ ARCHIVÉE (38b1f74)
Calibration C4 (partition R1, null raccourci)       ❌ INVALIDÉ PAR C5
Calibration C5 (null CORRIGÉ, baseline)             ✅ ARCHIVÉE (56803a8)
Calibration C6 (petits k, robustesse pool)          ✅ ARCHIVÉE (177e64e)
Calibration C7 / Volet C (validation corpus réel)   ✅ ARCHIVÉE (8dcf415)
Gate H v1.0                                          ✅ GELÉE (2026-09-24)
```

**Gate H v1.0** : percentile≥95 %, correction multi-comparaisons par
maximum, enveloppe de calibration `k≥8` / `group_size∈[20,40]`,
`CALIBRATION_INSUFFICIENT` (jamais `DISCOVERY`) hors de cette enveloppe.
**Ceci est une enveloppe de calibration empirique opérationnelle,
validée sur quatre pools de fond indépendants (trois synthétiques
pré-enregistrés + un dérivé de données structurelles réelles du dépôt),
pas une loi universelle sur tous les futurs corpus de MetaHIA** — voir
`documentation/P4U2_Gate_H_V1_0_Frozen_2026-09-24.md` pour la
spécification complète et ses réserves explicites (notamment : le taux
de faux positifs est cohérent avec le niveau nominal de 5 %, jamais
prouvé exactement égal à 5 %). Aucune campagne de calibration C8 n'est
prévue.

### 15.3 Ce qui reste réellement ouvert (corrigé après vérification directe)

```text
P4-U.2 implémentation minimale       🟠 NEXT  (signature, Gate I, Gate H,
                                              module minimal -- protocole
                                              Sec. 17, jamais commencé)
P4-U.2 benchmark verrouillé V1-V4    🟠 APRÈS l'implémentation minimale
                                              (seuils numériques du
                                              benchmark, checklist
                                              Sec. 13 point 7, encore
                                              À FIXER)
P4-U.1 set-valued replay             ✅ DÉJÀ FAIT -- pas une étape
                                              future (voir 15.1)
E20-D                                  🔴 OPEN, sans changement
```

**Décision de trajectoire, à confirmer explicitement par le porteur du
projet avant de commencer** : la prochaine étape concrète de ce
chantier est l'implémentation minimale de P4-U.2 (protocole Sec. 17) et
la construction du futur benchmark verrouillé V1-V4 — pas une
réimplémentation du set-valued replay de P4-U.1, qui est un mécanisme
distinct, déjà achevé et déjà validé par tiers.
