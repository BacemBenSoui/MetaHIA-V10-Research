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

**Prochaine étape : non encore décidée explicitement** — options restantes sans nouveau
LLM ni Évolution Cognitive : (a) étape « hypothèses → sélection/rationalisation »
manquante (Sec. 8 du document P4-T) — quand plusieurs paires source/cible candidates
existent, rien ne choisit encore laquelle retenir ; (b) brancher la Porte G sur le modèle
ROI d'E20-D.19 via un adaptateur ; (c) concevoir un vrai protocole de holdout avec corpus
verrouillé séparément par un tiers (au lieu des données synthétiques construites dans le
même fichier que les tests) ; (d) cinquième domaine M6 si la non-monotonie de la Sec. 4
de P7 doit être étudiée plus finement. Aucune de ces quatre n'est urgente ; à décider
explicitement avant de commencer, comme pour chaque étape précédente de ce chantier.
