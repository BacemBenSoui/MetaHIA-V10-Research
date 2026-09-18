# MetaHIA — M7 — Free-text Claim Parser v0.1

## 1. Statut

- M7 fact-proposer scope (question fermée) : voir
  `documentation/MetaHIA_M7_LLM_Fact_Proposer_V0_1.md` (`VALIDATED`, 2026-09-18).
- M7 parseur texte libre → preuve (ce document) : **VALIDATED** (2026-09-18, clôturé
  explicitement par le porteur du projet sur la base de deux exécutions externes
  indépendantes — voir Sec. 9 et `JOURNAL_DE_BORD.md`).
- Kernel `kernel2.py` : inchangé.

## 2. Rôle architectural choisi (décidé explicitement avant implémentation, 2026-09-18)

Deux options ont été présentées avant tout code :

1. **Texte → preuve sur une prédiction existante (retenue)** : le LLM extrait une seule
   affirmation (sujet, relation, objet) d'une phrase libre, comparée à la prédiction
   structurelle déjà calculée par rejeu — exactement le mécanisme témoin de
   `m7_llm_fact_proposer_v0_1.py`, avec une nouvelle porte d'entrée (extraire l'affirmation
   d'une phrase au lieu de poser une question fermée). Le LLM ne devient jamais une source
   de vérité directe : il reste au même palier de preuve `GROUNDED_ANALOGY`.
2. **Texte → nouveaux faits du graphe** (écartée pour cette version) : le LLM aurait
   directement créé de nouveaux nœuds d'observation dans le graphe structurel. Écartée
   parce qu'elle exige un nouveau palier de provenance ou une zone de faits non fiables
   pour ne pas violer « une dérivation ne peut pas être sa propre preuve » — question de
   conception non triviale, non nécessaire pour démontrer la capacité de base.

L'option retenue réutilise **100 % de la machinerie M4/M6/M7 déjà existante et déjà validée**
(`acquire_cold_start()`, `llm_evidence_for_prediction()`, le repli LAN sandbox) — la seule
pièce réellement nouvelle est l'extraction de la phrase en triplet structuré.

## 3. Mécanisme

```text
kernel2 : rejeu contre evidence_facts (disjoint de discovery_facts, inchangé)
        -> une prédiction structurelle réelle (start, opérateur) -> predicted_object
                ↓
phrase libre indépendamment rédigée (corpus/family_tree_text_claims_v0_1.json)
                ↓
LLM local (Ollama) : extraction fail-closed -> {"subject": ..., "relation": ..., "object": ...}
        -- relation DOIT appartenir au vocabulaire fermé déjà connu, sinon rejet total
                ↓
contrôle de fidélité : (sujet extrait, relation extraite) == (sujet, relation déclarés
        indépendamment par l'auteur du corpus) ?
        -- non -> EXCLU comme erreur de parsing (jamais apparié au mauvais candidat)
        -- oui -> comparaison mécanique : objet extrait == predicted_object ?
                ↓
égal -> preuve SUPPORT · différent -> preuve CHALLENGE · réponse inexploitable -> aucune preuve
```

Trois raisons d'exclusion honnêtement distinctes, jamais fusionnées ni cachées :

- `excluded_no_matching_text_claim` — aucune phrase du corpus ne porte sur ce candidat ;
- `excluded_no_parse` — extraction rejetée par le contrat fail-closed (JSON invalide, champ
  manquant, ou relation hors vocabulaire fermé) ;
- `excluded_parsing_mismatch` — extraction bien formée, mais sujet/relation ne correspondent
  pas à ce que la phrase est indépendamment connue pour affirmer (erreur de fidélité de
  parsing, distincte d'un désaccord sur l'objet, qui devient une preuve CHALLENGE, jamais une
  exclusion).

## 4. Corpus

`corpus/family_tree_text_claims_v0_1.json` — 16 phrases en français, chacune une affirmation
indépendamment rédigée sur un couple (sujet, relation) réellement rejouable dans
`corpus/family_tree_facts_v0_2.json` (même corpus que M6 v0.2 et M7 v0.1, longueur 1
uniquement, même limitation de périmètre assumée). 10 phrases sont vraies (l'objet affirmé
correspond à la prédiction réelle), 6 sont délibérément fausses (objet remplacé par un
placeholder `Personne_Inconnue_N` jamais utilisé ailleurs) — même discipline adversariale que
`family_tree_verification_claims_v0_1.json`.

Champ `asserted_object` : **jamais lu par le mécanisme de construction de preuve** — utilisé
uniquement par un contrôle de fidélité séparé (`scripts/print_text_claim_parsing_accuracy_v0_1.py`),
exactement comme `verdict` dans le corpus sœur reste documentation pure, jamais lu par le code
qui décide SUPPORT/CHALLENGE. Vérifié explicitement par
`test_perfect_parser_reproduces_the_corpus_authors_intended_diversity`.

11 des 14 patterns de longueur 1 découverts sont couverts par une phrase ; `ENFANT_DE` (les
deux directions) et `PERE_DE` (sens direct) n'ont aucune phrase associée — limite de
couverture du corpus assumée, pas un défaut du mécanisme d'appariement (voir C07/mécanisme
équivalent dans le mécanisme sœur M6 v0.2).

## 5. Résultat réel (`llama3.2:latest`, exécution du 2026-09-18)

**Contrôle de fidélité de parsing** (16 phrases, comparaison à `asserted_object`, contrôle
indépendant du mécanisme de preuve) : **8/16 (50 %)** extractions correctes sujet+relation.
Sur les 8 échecs : 7 rejets fail-closed (JSON inexploitable ou relation hors vocabulaire) et
1 erreur de fidélité (sujet/objet inversés, relation confondue avec son inverse — pour
« Duc est la mère de Personne_Inconnue_4 », le modèle a répondu
`(Personne_Inconnue_4, FILLE_DE, Duc)`).

**Mécanisme de preuve complet** (14 candidats considérés) :

| | Nombre |
|---|---|
| Enregistrements produits | 7 |
| `excluded_no_matching_text_claim` | 3 |
| `excluded_no_parse` | 7 |
| `excluded_parsing_mismatch` | 2 |
| Issue `SUPPORTED` | 5 |
| Issue `CONTRADICTED` | 2 |

**Lecture honnête** : contrairement au résultat dégénéré du mécanisme témoin à question
fermée (16/16 `CONTRADICTED`, voir `MetaHIA_M7_LLM_Fact_Proposer_V0_1.md` Sec. 4), ce
mécanisme produit une **diversité d'issue réelle** (5 `SUPPORTED`, 2 `CONTRADICTED`) parmi les
candidats effectivement parsés et appariés — le mécanisme fonctionne quand l'extraction
réussit. Mais la fidélité de parsing elle-même reste faible (50 %) avec ce petit modèle local
sur une tâche à livre fermé de compréhension de phrase simple en français — limite empirique
réelle, non corrigée ici (pas d'optimisation de prompt/modèle pour obtenir un résultat plus
flatteur, même discipline que pour le mécanisme témoin).

**Observation supplémentaire, non anticipée** : le contrôle de fidélité et la construction du
corpus de preuve appellent chacun le LLM séparément (pas de mise en cache) pour la même
phrase — sur au moins un cas, les deux appels réels ont produit des résultats différents pour
un texte identique, confirmant que ce petit modèle local n'est pas parfaitement stable d'un
appel à l'autre à température par défaut. Signalé ici honnêtement, pas lissé.

**Note technique, vérifiée et écartée comme non pertinente** : le script de diagnostic
(`scripts/print_text_claim_parsing_accuracy_v0_1.py`) a affiché les accents français sous
forme de caractères de remplacement (`�`) lors de sa première exécution — confirmé par
inspection directe des octets qu'il s'agit uniquement d'un artefact d'encodage de la console
Windows (`cp1252`) à l'affichage, pas d'une corruption réelle des données : le fichier corpus
est en UTF-8 correct, et `ollama_generate_json()` sérialise le prompt avec
`json.dumps(..., ensure_ascii=True).encode("utf-8")`, qui échappe tout caractère non-ASCII
avant l'envoi réseau — le texte réellement transmis au LLM était donc correct.

## 6. Invariants permanents testés

`tests/test_m7_text_claim_parser_v0_1.py` (11 tests, backend simulé injecté, aucun réseau) :
- réponse malformée / champ manquant / champ vide → aucune affirmation, jamais fabriquée ;
- relation hors du vocabulaire fermé → rejetée, jamais assimilée à la relation connue la plus
  proche ;
- affirmation bien formée et dans le vocabulaire → acceptée ;
- le prompt contient bien la phrase et la liste complète des relations autorisées ;
- un simulateur qui ne répond jamais → aucune preuve, tous les candidats comptés en
  `excluded_no_parse` ;
- un simulateur qui répond toujours avec un sujet absent du corpus → tous comptés en
  `excluded_parsing_mismatch`, jamais apparié au mauvais candidat ;
- **un simulateur de parseur parfait** (rejoue exactement `asserted_object` pour la phrase
  détectée dans le prompt) reproduit exactement la diversité voulue par la conception du
  corpus (10 `SUPPORTED`, 6 `CONTRADICTED`) — contrôle de câblage, pas une affirmation sur la
  compétence réelle du LLM ;
- le nombre de candidats considérés est identique à celui du mécanisme témoin sœur
  (même corpus, même périmètre longueur 1).

`tests/test_m7_text_claim_parser_live_demo_v0_1.py` (1 test, sautable comme les autres
démonstrations live) — exécute le mécanisme réel, n'affirme que les propriétés structurelles
garanties, jamais une distribution d'issue précise.

## 7. Résultat local

394 tests passés (385 précédents + 9 cas critiques de validation tierce
`test_m7_text_claim_parser_critical_validation_v0_1.py`), 0 échec, 0 régression.

## 8. Hors périmètre de cette version

- Extension aux patterns de longueur > 1 ;
- amélioration de la fidélité de parsing (modèle plus grand, few-shot, chaîne de
  raisonnement) — limite empirique réelle signalée en Sec. 5, pas corrigée ici ;
- option architecturale « texte → nouveaux faits du graphe » (Sec. 2, écartée pour cette
  version) ;
- intégration au corpus mixte de promotion (`m7_corpus_mixed_v0_1.py`) — suite naturelle
  possible maintenant que ce mécanisme est lui-même validé.

## 9. Validation tierce et clôture (2026-09-18)

`documentation/MetaHIA_ThirdParty_Validation_Protocol_M7_TextClaimParser_V0_1.md` (9 cas
critiques C01-C09, `tests/test_m7_text_claim_parser_critical_validation_v0_1.py`,
délibérément sans dépendance réseau) a été envoyé et exécuté par **deux relecteurs
génuinement externes, dans deux environnements indépendants** :

| | Retour #1 | Retour #2 |
|---|---|---|
| Environnement | non précisé, rapport en français | Linux 5.10.134, Python 3.11.2, pytest 7.2.1 |
| Cas critiques C01–C09 | 9/9 PASS | 9/9 PASS |
| Suite complète | 391 PASS / 3 SKIP / 0 FAIL | 391 PASS / 3 SKIP / 0 FAIL |
| Hashes gelés (8 fichiers) | 8/8 conformes | 8/8 conformes |
| Encodage UTF-8 du corpus français | PASS | PASS, échantillons vérifiés explicitement |
| Modification du dépôt | 0 | 0 |

Les 3 `SKIP` (démonstrations live Ollama) sont attendus et documentés. Les deux relecteurs
ont, chacun indépendamment, vérifié explicitement l'encodage UTF-8 du corpus français — point
que le protocole identifiait comme sensible après l'artefact de console rencontré pendant le
développement — et confirmé l'absence de corruption. Aucun des deux relecteurs n'a arrondi son
verdict à une clôture de gate — chacun l'a explicitement laissée à la décision du porteur du
projet. Détail complet, y compris les citations verbatim des deux verdicts, dans
`JOURNAL_DE_BORD.md` (entrée du 2026-09-18).

**Clôture** : sur la base de ces deux retours indépendants, le porteur du projet
(Bacem Ben Soui) a explicitement clôturé le gate de validation externe le 2026-09-18. C'est
une décision de gouvernance du porteur du projet, pas une auto-déclaration.

**Ce que cette clôture établit** : le mécanisme (extraction fail-closed, rejet du vocabulaire
fermé, exclusion honnête des erreurs de correspondance, non-circularité vis-à-vis de
`asserted_object`, câblage correct) est honnête, non circulaire, et reproductible dans ses
parties déterministes, confirmé par deux exécutions indépendantes.

**Ce que cette clôture n'établit pas** (inchangé depuis Sec. 5/8) : que le LLM est un parseur
français compétent (fidélité réelle 50 %) ; une extension aux patterns de longueur > 1 ; une
intégration au corpus mixte de promotion ; une quelconque readiness de production.

**Statut : `VALIDATED`**, au même titre de gouvernance que M6 et le mécanisme témoin M7.

## 10. Intégration au corpus mixte de promotion — comparaison à quatre conditions (2026-09-18)

Choisi explicitement comme prochain jalon, parmi trois options (amélioration de la fidélité
de parsing, extension longueur > 1, cette intégration) — retenu parce que ce mécanisme est le
premier des deux témoins LLM à produire une **diversité d'issue réelle** (Sec. 5), ce qui en
fait la source la plus prometteuse à tester dans le pipeline de décision réel, contrairement
au témoin à question fermée déjà connu comme neutre.

`m7_corpus_mixed_v0_2.py` (nouveau fichier — `m7_corpus_mixed_v0_1.py` reste gelé, son hash
étant fixé par le protocole du mécanisme témoin) étend l'union à trois sources et compare
quatre conditions sous les mêmes paramètres de partition :

| Condition | Composition |
|---|---|
| `baseline` | corpus adversarial seul (déjà validé) |
| `+ witness` | adversarial + témoin LLM à question fermée |
| `+ text claims` | adversarial + parseur texte libre (nouveau) |
| `+ both` | les trois sources combinées |

Propriété d'équité inchangée et revérifiée pour la troisième source : aucun des deux
mécanismes LLM ne peut introduire une signature de règle absente du corpus adversarial —
`split_by_rule` assigne donc le même ensemble de règles au holdout dans les quatre
conditions.

**Résultat réel (`llama3.2:latest`, seed=0, `brier_threshold=0.5`, exécution du 2026-09-18)** :

| Condition | Train | Holdout | Brier | ECE | Décision |
|---|---|---|---|---|---|
| `baseline` | 16 | 5 | 0,48125 | 0,025 | PROMOTE |
| `+ witness` | 25 | 8 | 0,47 | 0,025 | PROMOTE |
| `+ text claims` | 21 | 7 | **0,50794** | **0,09524** | **NE PROMEUT PAS** (`HOLDOUT_BRIER_ABOVE_THRESHOLD`) |
| `+ both` | 30 | 10 | 0,48889 | 0,06667 | PROMOTE |

Cette exécution a produit 8 enregistrements de preuve du parseur texte (6 `SUPPORTED`,
2 `CONTRADICTED`) — différent du run précédent documenté en Sec. 5 (7 enregistrements, 5/2) :
**nouvelle confirmation directe, et non plus seulement soupçonnée**, de l'instabilité d'un
appel à l'autre du petit modèle local déjà signalée en Sec. 5.

**Lecture honnête, contraire à l'hypothèse qui motivait ce choix** : ajouter *seul* le
parseur texte au pipeline de promotion **dégrade** la calibration du holdout au point de
bloquer la promotion au seuil actuel (Brier 0,48125 → 0,50794, ECE 0,025 → 0,095) — malgré sa
diversité d'issue réelle, contrairement à l'hypothèse qui motivait ce choix (Sec. « Rôle
architectural »/ROI). Ce n'est qu'en le combinant *aussi* avec le témoin à question fermée
(`+ both`) que la promotion redevient possible (Brier 0,48889, proche du niveau de base). Ce
résultat n'est pas dissimulé ni minimisé pour correspondre à l'hypothèse de départ : la bonne
lecture est que **l'ajout isolé d'une source d'évidence LLM prometteuse en apparence (diversité
réelle) peut dégrader la calibration nette**, et que seule une mesure réelle du pipeline
complet — pas la seule diversité d'issue d'une source — permet de juger de son utilité. Aucune
hypothèse causale définitive n'est avancée ici sur le mécanisme exact de cette dégradation
(candidat plausible : les nouvelles preuves `SUPPORTED` majoritaires du parseur texte
déplacent certains a-priori de bucket dans un sens qui dessert précisément les règles du
holdout) — non vérifiée plus avant, pour ne pas fabriquer une explication a posteriori
non testée.

**Conclusion retenue** : ce résultat ne justifie pas d'intégrer le parseur texte seul comme
source de promotion en l'état ; il justifie encore moins d'abandonner la piste, puisque la
combinaison des trois sources reste `PROMOTE`. Aucune action corrective n'est appliquée ici
(pas de réglage de seuil pour forcer un résultat plus flatteur, même discipline que partout
ailleurs dans ce projet).

Tests :
- `tests/test_m7_mixed_corpus_v0_2_promotion_v0_1.py` (6 tests, backends simulés injectés,
  aucun réseau) — équité de l'ensemble de règles à travers les quatre conditions, dégénérescence
  correcte vers le seul baseline quand aucune source LLM ne répond, union exacte des trois
  sources, non-régression du nombre déjà validé (0,48125), reproduction de la diversité connue
  du parseur texte via un simulateur de parseur parfait.
- `tests/test_m7_mixed_corpus_v0_2_live_demo_v0_1.py` (1 test, sautable) — exécute la
  comparaison réelle à quatre conditions, n'affirme que les propriétés structurelles garanties
  (holdout non vide, Brier dans `[0, 2]`), jamais qu'une condition précise doit promouvoir —
  ce test passe même quand `+ text claims` seul ne promeut pas, comme observé réellement.

## 11. Consensus multi-modèles sur le parseur texte (2026-09-18)

Question posée directement par le résultat de la Sec. 10 : l'ajout non filtré de l'évidence du
parseur texte dégrade la calibration — **exiger l'accord de deux modèles indépendants
avant d'accepter une extraction filtre-t-il les cas non fiables et corrige-t-il ce
problème ?** Choisi explicitement, parmi trois options, comme le test le plus directement
motivé par ce constat (plutôt qu'un consensus inter-mécanismes témoin/parseur, ou les deux
combinés — gardés pour un axe de variation unique afin que le résultat reste interprétable).

Mécanisme (`m7_text_claim_parser_consensus_v0_1.py` + `m7_corpus_from_text_claims_consensus_v0_1.py`,
nouveaux fichiers, aucune modification des mécanismes gelés) : les deux modèles déjà câblés
(`llama3.2:latest` local et `qwen2.5-coder:7b` du LAN sandbox) sont **toujours tous deux
appelés en votants indépendants** (pas en primaire/repli) sur la phrase identique ; l'évidence
n'est acceptée que si les deux extraient exactement le même triplet (sujet, relation, objet).
Quatre raisons d'exclusion honnêtement distinctes : un votant échoue à son propre contrat
fail-closed, désaccord entre les deux votants, ou accord des deux votants sur un sujet/relation
qui ne correspond pas à ce que la phrase est censée affirmer.

**Résultat réel (`llama3.2:latest` + `qwen2.5-coder:7b`, 2026-09-18)** :

| | Nombre |
|---|---|
| Candidats considérés | 14 |
| Enregistrements produits | 6 |
| `excluded_voter_failed` | 9 (dont 7 échecs du seul votant local) |
| `excluded_disagreement` | 1 |
| `excluded_parsing_mismatch` | 0 |
| Issue `SUPPORTED` | 4 |
| Issue `CONTRADICTED` | 2 |

Effet sur la calibration (adversarial + preuve filtrée par consensus, seed=0,
`brier_threshold=0.5`) : **Brier holdout = 0,58527, ECE = 0,21849, NE PROMEUT PAS**
(`HOLDOUT_BRIER_ABOVE_THRESHOLD`).

**Lecture honnête, contraire à l'hypothèse qui motivait ce test** : le filtrage par consensus
n'a pas corrigé le problème de la Sec. 10 — il l'a **aggravé**. Le Brier holdout (0,58527) est
pire que celui du parseur texte non filtré seul (0,50794) et pire que le baseline (0,48125).
Hypothèse plausible, non vérifiée davantage pour ne pas fabriquer une explication a posteriori :
les deux modèles ne commettent pas des erreurs indépendantes mais partiellement corrélées sur
cette tâche simple — le consensus filtre alors surtout les cas où un modèle a échoué
franchement (`excluded_voter_failed`, majoritairement le modèle local), pas nécessairement les
cas où les deux se trompent de la même façon en étant d'accord ; il retire aussi de l'information
potentiellement valable d'un seul votant qui aurait répondu correctement pendant que l'autre
échouait à son contrat fail-closed. Aucune conclusion causale définitive n'est retenue.

**Conclusion retenue** : l'hypothèse « le consensus multi-modèles améliore la fiabilité de
l'évidence LLM » n'est **pas confirmée** sur ce corpus et ces deux modèles — c'est même
l'inverse qui est observé. Ce résultat négatif est documenté tel quel, sans réglage de seuil ni
changement de modèle pour obtenir un résultat plus flatteur, même discipline que partout
ailleurs dans ce projet. Il ne clôt pas la piste du consensus en général (un consensus
inter-mécanismes, ou avec des modèles moins corrélés, pourrait se comporter différemment) mais
ferme, en l'état, la piste consensus-même-mécanisme testée ici.

Tests :
- `tests/test_m7_text_claim_parser_consensus_v0_1.py` (7 tests) et
  `tests/test_m7_corpus_from_text_claims_consensus_v0_1.py` (5 tests), backends simulés
  injectés, aucun réseau — accord/désaccord/échec de votant distingués honnêtement, jamais
  résolus arbitrairement ; un simulateur de deux votants parfaitement d'accord reproduit
  exactement la diversité déjà connue (10 `SUPPORTED`, 6 `CONTRADICTED`) — contrôle de câblage,
  pas une affirmation sur la compétence réelle des modèles.
- `tests/test_m7_text_claim_parser_consensus_live_demo_v0_1.py` (1 test, sautable — nécessite
  les DEUX hôtes Ollama accessibles, pas seulement le local) — exécute le mécanisme réel,
  n'affirme que les propriétés structurelles garanties, jamais une distribution d'issue ou une
  décision de promotion précise.

## 12. Consensus inter-mécanismes (témoin + parseur) et coût en ressources (2026-09-18)

Dernière piste de consensus restante après l'échec du consensus même-mécanisme (Sec. 11) :
au lieu de deux modèles sur la **même** question, exiger l'accord entre **deux mécanismes
structurellement différents** — le témoin à question fermée (`m7_llm_fact_proposer_v0_1.py`,
inchangé) et le parseur de phrase (`m7_text_claim_parser_v0_1.py`, inchangé) — sur le même
candidat, chacun utilisant son propre backend réel par défaut (local en primaire, repli LAN
uniquement sur injoignabilité réelle — pas le schéma « toujours les deux hôtes » du consensus
même-mécanisme).

`m7_cross_mechanism_consensus_v0_1.py` + `m7_corpus_from_cross_mechanism_consensus_v0_1.py`
(nouveaux fichiers, aucune modification des mécanismes gelés) — six issues honnêtement
distinctes : accord, échec du témoin, échec du parseur, échec des deux, erreur de fidélité du
parseur (comme en Sec. 5/10), désaccord entre les deux mécanismes.

**Mesure de la surcharge ressource réelle** (script dédié
`scripts/measure_m7_mechanism_resource_overhead_v0_1.py`, instrumentation du client HTTP réel,
aucune estimation) :

| Mécanisme | Appels réseau réels | Temps mur | Enregistrements produits |
|---|---|---|---|
| Témoin seul | 16 | 69,6 s | 16 |
| Parseur seul | 16 | 105,4 s | 9 (variable d'un run à l'autre, cf. instabilité déjà signalée) |
| Consensus inter-mécanismes | **32** | **184,5 s** | **0** |

**Résultat réel du consensus inter-mécanismes (2026-09-18)** : sur les 14 candidats (11 avec
une phrase associée), **0 enregistrement produit**. Détail : 9 échecs du parseur seul
(`PARSER_FAILED`), 6 désaccords entre témoin et parseur, 1 erreur de fidélité du parseur, 0
échec du témoin. **Sur les 7 cas où le parseur a réussi à répondre, aucun n'a jamais coïncidé
avec la réponse du témoin.**

**Lecture honnête, décisive** : le consensus inter-mécanismes est **strictement dominé**. Il
coûte au moins autant que d'exécuter les deux mécanismes séparément (32 appels, 184,5 s —
plus cher que la somme des deux temps mesurés séparément, 69,6 + 105,4 = 175 s, l'écart
s'expliquant par la variance normale d'appels réseau réels) et ne produit **strictement aucune
évidence utilisable**, contre le résultat déjà obtenu par la simple union des deux mécanismes
(Sec. 10, `+both` : mêmes 32 appels, mais 30 enregistrements d'entraînement, `PROMOTE`).
Le témoin et le parseur, quand ils répondent tous deux, ne convergent tout simplement jamais
vers la même réponse brute sur ce corpus — leurs modes de raisonnement (question fermée avec
contexte structuré vs extraction depuis une phrase indépendante) semblent produire des
divergences plutôt qu'un accord, contrairement à l'espoir initial. Aucune conclusion causale
définitive n'est avancée au-delà de ce constat empirique.

**Conclusion retenue** : la piste consensus inter-mécanismes est fermée en l'état — elle
n'apporte aucune valeur pour un coût égal ou supérieur à l'union simple déjà validée.

Tests : `tests/test_m7_cross_mechanism_consensus_v0_1.py` (6 tests) et
`tests/test_m7_corpus_from_cross_mechanism_consensus_v0_1.py` (6 tests), backends simulés
injectés, aucun réseau ; `tests/test_m7_cross_mechanism_consensus_live_demo_v0_1.py` (1 test,
sautable) — passe même avec zéro enregistrement produit, par conception (propriétés
structurelles uniquement).

### Décision à trancher par le porteur du projet

Sur la base de ces mesures de coût réel et de leur effet sur la calibration (Sec. 10), les
options restantes, classées par coût croissant :

| Option | Coût (appels/run) | Effet sur la calibration | Brier holdout |
|---|---|---|---|
| **Témoin seul** | 16 | Neutre, légèrement meilleur que le baseline | 0,47 (meilleur résultat de toutes les conditions testées) |
| **Parseur seul** | 16 | Dégrade, bloque la promotion | 0,508 |
| **Les deux (union simple)** | 32 (double coût) | Passe la promotion, mais moins bien que le témoin seul | 0,489 |
| ~~Consensus inter-mécanismes~~ | ~~32~~ | ~~Aucune évidence produite~~ | **Écarté** (dominé) |

Le consensus inter-mécanismes est déjà écarté par les données (dominé). Reste à trancher entre
témoin seul, parseur seul, ou les deux — voir la question posée à l'issue de ce document.

## 13. Résultat local

427 tests passés (414 précédents + 6 invariants du consensus inter-mécanismes + 6 invariants
du corpus consensus inter-mécanismes + 1 démonstration live), 0 échec, 0 régression.
