# MetaHIA V10.0 — Journal de bord

Journal chronologique des jalons de gouvernance du dépôt `MetaHIA-V10-Research` (lignée de
recherche K3). Complète, sans le remplacer, l'historique détaillé déjà tenu dans
`documentation/MetaHIA_Roadmap_Complete_v0.5.5_2026-09-17.md` et
`documentation/MetaHIA_Documentation_Consolidee_2026-09-17.md` — ce fichier est le registre
des événements de validation externe, pas une re-rédaction de la doc technique.

---

## 2026-09-17 — Validation tierce de M6 (mécanisme de base v0.1 + mécanisme non dégénéré v0.2)

### Paquet initial envoyé
- Commit exporté : `613c4cdbdf3b55195c2ae8b70a28b185b52287d8`
- Contenu : `MetaHIA_ThirdParty_Validation_Protocol_M6_V0_1.md` (9 cas C01–C09) +
  `MetaHIA_ThirdParty_Validation_Protocol_M6_NonDegenerate_V0_2.md` (7 cas C01–C07), fichiers
  gelés, corpus, suites de tests critiques.
- Remis en paquet zip autonome (dépôt GitHub privé, pas de partage d'accès ni de changement
  de visibilité).

### Retour externe #1 (extraction fraîche, sans modification du paquet)

| Vérification | Résultat |
|---|---|
| M6 v0.1 — critical | 13/13 PASS |
| M6 v0.2 — non-degenerate | 7/7 PASS |
| Intégration corpus réel + holdout | 10/10 PASS |
| Invariants M6 | 24/24 PASS |
| Suite complète | 338/338 PASS |
| Rejeu complet (répétabilité) | 338/338 PASS |
| Fichiers source modifiés pendant les tests | 0 |

- Scan de fuite sémantique : aucune règle sémantique dans le cœur de l'apprentissage M6 ;
  seul un littéral `MERE_DE` dans la fixture `demo_contradicted_case()` (test négatif),
  signalé séparément, sans impact.
- **Point d'intégrité détecté** : hash annoncé pour `m6_corpus_from_m4_m5_v0_1.py`
  (`f075f730...`) ≠ hash réel du fichier livré (`d78ebf1b...`). Les 5 autres hashes contrôlés
  correspondaient. Aucun test affecté.
- Verdict explicite du relecteur : *« le mécanisme M6 passe techniquement l'ensemble des
  tests du package, mais je ne classe pas encore cette exécution comme validation tierce
  indépendante. La divergence de hash est le seul écart d'intégrité constaté. »*

### Diagnostic et correctif (même jour)
- Cause identifiée par `git diff` direct contre le commit d'origine du protocole
  (`5834a2a`) : le commit `634126a` (« M6 INDEPENDENT HOLDOUT step ») avait par erreur ajouté
  une constante de confort (`CORPUS_PATH_V0_2`) à `m6_corpus_from_m4_m5_v0_1.py`, fichier déjà
  gelé par le protocole v0.1 — violation réelle de la discipline « fichier gelé = jamais
  retouché », introduite après l'auto-exécution PASS_INDEPENDENT_SCOPE (donc sans invalider ce
  PASS-là, obtenu avant la dérive).
- Corrigé : fichier restauré exactement à son contenu d'origine (`git show` du commit
  d'authoring, hash revérifié `f075f730...`) ; le test dépendant redéfinit localement sa
  propre constante au lieu de l'importer du fichier gelé.
- Les 13 hashes des deux protocoles M6 revérifiés individuellement après correctif — tous
  conformes.
- Commit du correctif : `045b5ccdfbca5072efd9868cf8a0aeb3f40ece45`.
- Paquet corrigé renvoyé, revérifié en conditions isolées puis directement depuis le fichier
  zip final avant envoi (20/20 cas critiques, 338/338 suite complète).

### Retour externe #2 (environnement indépendant)
- Environnement : `python3.11.2`, `pytest 7.2.1` — différent de l'environnement de
  développement (Windows, Python 3.13.14, pytest 9.1.1) et du retour externe #1.
- Commande : `python3.11 -m pytest -q` (suite complète), exécutée depuis la racine du paquet.
- Résultat : **338 passed**, code retour 0, durée 6,12 s (pytest) / 6,39 s (totale).
- Confirme la portabilité inter-environnement du résultat, indépendamment de la correction
  de hash (l'exécution ne portait pas spécifiquement sur la vérification des hashes).

### Clôture de l'étape
**Validée explicitement par Bacem Ben Soui (porteur du projet), le 2026-09-17**, sur la base
des deux exécutions externes ci-dessus (13/13, 7/7, 10/10, 24/24, 338/338 répété, 0
modification, une divergence d'intégrité trouvée puis corrigée et revérifiée, et une seconde
confirmation 338/338 dans un environnement Python/pytest indépendant).

Cette clôture est une décision de gouvernance du porteur de projet, pas une auto-déclaration :
la formulation de chaque protocole (« a local PASS does not close the independent gate »)
reste vraie pour toute exécution auto-jouée par l'assistant ; ici, c'est le porteur du projet
qui exerce son autorité de décision sur son propre projet, au vu de preuves d'exécution
externes réelles et reproduites deux fois.

**Statut M6 après cette entrée** : `VALIDATED` (base v0.1 + mécanisme non dégénéré v0.2).
Voir `documentation/MetaHIA_M6_Structural_Learning_V0_1.md` Sec. 6 et
`documentation/MetaHIA_Roadmap_Complete_v0.5.5_2026-09-17.md` Sec. 3/10 pour la mise à jour de
statut correspondante.

---

## 2026-09-18 — Validation tierce de M7 (fact-proposer + intégration corpus mixte)

### Paquet envoyé
- Commit exporté : `0c9776aff754ac14755277e77f661697685634be`
- Contenu : `MetaHIA_ThirdParty_Validation_Protocol_M7_V0_1.md` (9 cas C01–C09), fichiers gelés,
  `tests/test_m7_critical_validation_v0_1.py`.
- Remis en paquet zip autonome (dépôt GitHub privé, pas de partage d'accès ni de changement de
  visibilité), **sans le répertoire `.git`**.

### Retour externe #1 (ZIP complet, environnement Python propre, aucune modification déclarée)

| Vérification | Résultat |
|---|---|
| M7 critique (C01–C09) | 9/9 PASS |
| Suite complète | 373 collectés — 371 PASS / 2 SKIP / 0 FAIL |
| Hashes gelés (9 fichiers) | 9/9 conformes |
| Fichiers source modifiés pendant les tests | 0 |

- Les 2 `SKIP` sont les deux démonstrations live Ollama
  (`test_m7_live_ollama_demo_v0_1.py`, `test_m7_mixed_corpus_live_demo_v0_1.py`) — Ollama
  n'était pas accessible dans l'environnement du relecteur, comportement attendu et documenté
  dans le protocole (non requis pour le verdict PASS).
- **Réserve méthodologique explicite et honnête soulevée par le relecteur lui-même** : le ZIP
  fourni ne contenant pas `.git`, `git rev-parse HEAD` n'a pas pu être exécuté à l'intérieur du
  paquet pour prouver cryptographiquement que son contenu correspond exactement au commit
  `0c9776a...`. Les 9 hashes gelés correspondent exactement au contenu attendu, ce qui est une
  preuve forte de conformité du contenu, mais pas une preuve cryptographique directe du hash de
  commit lui-même — distinction que le relecteur a lui-même correctement posée, sans la
  minimiser ni la maximiser.
- Verdict explicite du relecteur, non arrondi par l'assistant : *« Validation de reproductibilité
  indépendante du package : PASS — 9/9 critères critiques M7, 373 tests collectés, 371 PASS,
  2 SKIP, 0 FAIL, hashes critiques 9/9 conformes. Fermeture officielle du gate "genuinely
  external reviewer" : NON encore clôturé [...] cette exécution constitue une exécution
  indépendante dans un nouvel environnement, mais elle ne doit pas être artificiellement
  présentée comme la validation par un tiers humain externe si [la] définition de gouvernance
  exige effectivement un reviewer externe au projet. »*

### État après ce retour
Une seule exécution externe reçue à ce stade (contre deux pour M6 avant clôture). Le protocole
M7 lui-même reste au statut qu'il portait déjà : *« this protocol has not yet been executed by
a genuinely external reviewer [...] and self-execution does not count »* — cette entrée
consigne un premier retour, elle ne referme pas le gate. La décision de clôturer (avec un seul
retour, ou après un second comme pour M6) reste une décision de gouvernance du porteur du
projet, pas une auto-déclaration de l'assistant.

**Statut M7 après cette entrée** : `IMPLEMENTATION` (inchangé) — `PASS_INDEPENDENT_SCOPE`
(reproductibilité confirmée par une première exécution externe réelle), gate de clôture externe
toujours `OPEN`.

### Retour externe #2 (archive GitHub `MetaHIA-V10-Research-main.zip`, environnement indépendant)

- Environnement : `Linux-5.10.134-18.0.12.lifsea8.x86_64`, `Python 3.11.2`, `pytest 7.2.1` —
  distinct de l'environnement de développement (Windows, Python 3.13.14, pytest 9.1.1) et
  rédigé avec un luxe de détail (rootdir, sortie brute complète avec codes couleur ANSI, durée
  d'exécution 1,28 s puis 6,96 s) qui le distingue clairement du retour #1.

| Vérification | Résultat |
|---|---|
| M7 critique (C01–C09), détail par cas | 9/9 PASS, chacun nommément identifié à sa fonction de test |
| Suite complète | 371 PASS / 2 SKIP / 0 FAIL |
| Hashes gelés (9 fichiers) | 9/9 conformes |
| Fichiers source modifiés pendant les tests | 0 |

- Mêmes 2 `SKIP` attendus (démonstrations live Ollama, serveur injoignable dans cet
  environnement) — comportement documenté et non requis pour le verdict.
- **Même réserve méthodologique, formulée indépendamment** : archive GitHub sans `.git`,
  `git rev-parse HEAD` inexécutable, hash de commit non vérifiable cryptographiquement depuis
  l'archive — signalée explicitement comme « procedural discrepancy with the protocol », les 9
  hashes de fichiers gelés restant le contrôle d'intégrité substantiel et concluant.
- Écart mineur additionnel signalé, sans impact : l'interpréteur `python3.12` par défaut de cet
  environnement n'avait pas `pytest` installé ; l'exécution a donc utilisé `/usr/bin/python3.11`
  explicitement — disclosed, pas une déviation substantielle du protocole (Python 3.11+
  recommandé).
- Verdict explicite du relecteur, non arrondi par l'assistant : *« M7 = PASS_INDEPENDENT_SCOPE
  (mechanism-level), subject to the governance rule that the final independent gate is closed
  by the project owner. »*

### Bilan après ces deux retours
Deux exécutions externes indépendantes (environnements distincts, formats de rapport distincts,
durées distinctes) confirment toutes deux, sans exception : 9/9 cas critiques, hashes gelés
9/9 conformes, zéro régression, zéro modification, même réserve méthodologique honnête sur
l'absence de `.git` dans une archive zip (jamais dissimulée ni par l'un ni par l'autre
relecteur). C'est la même configuration factuelle qui avait conduit à la clôture de M6 le
2026-09-17 (deux retours indépendants, tous deux PASS, zéro régression) — sans que l'assistant
ne préjuge ici de la décision de gouvernance, qui reste celle du porteur du projet.

**Statut M7 après ces deux entrées** : `IMPLEMENTATION` (inchangé) — `PASS_INDEPENDENT_SCOPE`
confirmé deux fois indépendamment. Clôture du gate externe : décision en attente du porteur du
projet.

### Clôture de l'étape

**Validée explicitement par Bacem Ben Soui (porteur du projet), le 2026-09-18** : *« oui, je
clôture le gate M7 sur ces deux retours »* — sur la base des deux exécutions externes
ci-dessus (9/9 cas critiques deux fois, 371/371 hors démonstrations live deux fois, 9/9
hashes conformes deux fois, 0 modification, même réserve méthodologique honnête sur
l'absence de `.git` dans une archive zip soulevée indépendamment par les deux relecteurs sans
jamais être dissimulée).

Cette clôture est une décision de gouvernance du porteur de projet, pas une auto-déclaration :
la formulation du protocole (« a local PASS does not close the independent gate ») reste vraie
pour toute exécution auto-jouée par l'assistant ; ici, c'est le porteur du projet qui exerce
son autorité de décision sur son propre projet, au vu de deux preuves d'exécution externes
réelles et concordantes — exactement la même configuration qui avait justifié la clôture de M6
le 2026-09-17.

**Statut M7 après cette entrée** : `VALIDATED` (portée fact-proposer + intégration corpus
mixte). Voir `documentation/MetaHIA_M7_LLM_Fact_Proposer_V0_1.md` Sec. 10 et
`documentation/MetaHIA_Roadmap_Complete_v0.5.5_2026-09-17.md` pour la mise à jour de statut
correspondante.

---

## 2026-09-18 — Validation tierce de M7 — parseur texte libre (text-claim parser)

### Paquet envoyé
- Commit exporté : `157f04664e6ca93f4d21e427dc070d6f69f803af`
- Contenu : `MetaHIA_ThirdParty_Validation_Protocol_M7_TextClaimParser_V0_1.md` (9 cas C01–C09),
  fichiers gelés (dont `corpus/family_tree_text_claims_v0_1.json`, contenu français
  accentué), `tests/test_m7_text_claim_parser_critical_validation_v0_1.py`.

### Retour externe #1 (aucune modification déclarée)

| Vérification | Résultat |
|---|---|
| Critique (C01–C09) | 9/9 PASS |
| Suite complète | 391 PASS / 3 SKIP / 0 FAIL |
| Hashes gelés (8 fichiers) | 8/8 conformes |
| Encodage UTF-8 du corpus français | PASS, aucun mojibake constaté |
| Démonstration live Ollama | SKIP (Ollama indisponible dans cet environnement) |
| Fichiers source modifiés pendant les tests | 0 |

- Les 3 `SKIP` (contre 2 pour les protocoles précédents) sont attendus : les deux
  démonstrations live déjà existantes plus la nouvelle démonstration live du parseur de
  phrases, toutes sautées faute d'Ollama accessible — comportement documenté, non requis
  pour le verdict.
- Le relecteur a spécifiquement vérifié l'encodage UTF-8 du corpus français, point que le
  protocole identifiait explicitement comme sensible après l'artefact de console rencontré
  pendant le développement — confirmé sans corruption, cohérent avec la vérification
  d'octets bruts déjà faite avant l'envoi.
- Verdict explicite du relecteur, non arrondi par l'assistant : *« M7 Free-text Claim Parser
  v0.1 — mécanisme : PASS_INDEPENDENT_SCOPE pour cette exécution indépendante [...] cela ne
  valide pas l'exactitude du LLM français [...] la fermeture officielle du gate "genuinely
  external reviewer" reste distincte : l'archive ne contient pas .git [...] cette exécution
  ne doit pas être présentée comme une validation par un tiers humain externe si cette
  condition de gouvernance est maintenue. »*

### État après ce retour
Une seule exécution externe reçue à ce stade pour ce mécanisme (contre deux pour M6 et pour
le mécanisme témoin M7 avant clôture). Cette entrée consigne un premier retour, elle ne
referme pas le gate. La décision de clôturer reste celle du porteur du projet.

**Statut M7 parseur texte→preuve après cette entrée** : `IMPLEMENTATION` (inchangé) —
`PASS_INDEPENDENT_SCOPE` (reproductibilité confirmée par une première exécution externe
réelle), gate de clôture externe toujours `OPEN`.

### Retour externe #2 (archive GitHub, environnement indépendant)

- Environnement : `Linux-5.10.134-18.0.12.lifsea8.x86_64`, `Python 3.11.2`, `pytest 7.2.1` —
  même signature d'environnement que le retour #2 déjà reçu pour M6 et pour le mécanisme
  témoin M7, distinct du retour #1 ci-dessus (rootdir, sortie ANSI colorée, durée 1,61 s puis
  7,78 s, rapport en anglais).

| Vérification | Résultat |
|---|---|
| Critique (C01–C09), détail par cas | 9/9 PASS, chacun nommément identifié à sa fonction de test |
| Suite complète | 391 PASS / 3 SKIP / 0 FAIL |
| Hashes gelés (8 fichiers) | 8/8 conformes |
| Encodage UTF-8 du corpus français | PASS — échantillons vérifiés explicitement (« Mai est l'épouse de Hoang. », etc.), aucun mojibake |
| Démonstration live Ollama (3 tests) | SKIP, Ollama injoignable dans cet environnement |
| Fichiers source modifiés pendant les tests | 0 |

- Même réserve méthodologique, formulée indépendamment : archive sans `.git`,
  `git rev-parse HEAD` inexécutable — signalée explicitement comme « procedural
  discrepancy with the protocol », les hashes de fichiers gelés restant le contrôle
  d'intégrité substantiel et concluant.
- Verdict explicite du relecteur, non arrondi par l'assistant : *« M7 free-text claim parser
  = PASS_INDEPENDENT_SCOPE (mechanism-level), subject to the governance rule that the final
  independent gate is closed by the project owner. »*

### Bilan après ces deux retours
Deux exécutions externes indépendantes (environnements distincts, langues de rapport
distinctes, formats distincts) confirment toutes deux, sans exception : 9/9 cas critiques,
hashes gelés 8/8 conformes, zéro régression, zéro modification, vérification explicite et
concordante de l'encodage UTF-8 du corpus français. C'est la même configuration factuelle qui
avait justifié la clôture de M6 (2026-09-17) et du mécanisme témoin M7 (2026-09-18) — sans que
l'assistant ne préjuge ici de la décision de gouvernance, qui reste celle du porteur du
projet.

**Statut M7 parseur texte→preuve après ces deux entrées** : `IMPLEMENTATION` (inchangé) —
`PASS_INDEPENDENT_SCOPE` confirmé deux fois indépendamment. Clôture du gate externe : décision
en attente du porteur du projet.

### Clôture de l'étape

**Validée explicitement par Bacem Ben Soui (porteur du projet), le 2026-09-18** : *« clôturer
le gate de validation externe du parseur texte sur la base de ces deux retours »* — sur la
base des deux exécutions externes ci-dessus (9/9 cas critiques deux fois, 391/391 hors
démonstrations live deux fois, 8/8 hashes conformes deux fois, 0 modification, vérification
explicite et concordante de l'encodage UTF-8 du corpus français par les deux relecteurs
indépendamment).

Cette clôture est une décision de gouvernance du porteur de projet, pas une auto-déclaration :
la formulation du protocole (« a local PASS does not close the independent gate ») reste vraie
pour toute exécution auto-jouée par l'assistant ; ici, c'est le porteur du projet qui exerce
son autorité de décision sur son propre projet, au vu de deux preuves d'exécution externes
réelles et concordantes — exactement la même configuration qui avait justifié la clôture de
M6 (2026-09-17) et du mécanisme témoin M7 (2026-09-18).

**Ce que cette clôture établit** : le mécanisme du parseur texte→preuve (extraction
fail-closed, rejet du vocabulaire fermé, exclusion honnête des erreurs de correspondance,
non-circularité vis-à-vis de `asserted_object`, câblage correct vérifié par simulation de
parseur parfait) est honnête, non circulaire, et reproductible dans ses parties
déterministes, confirmé par deux exécutions indépendantes.

**Ce que cette clôture n'établit pas** (inchangé depuis le document du protocole) : que le
LLM est un parseur français compétent (fidélité réelle 50 %) ; une extension aux patterns de
longueur > 1 ; une intégration au corpus mixte de promotion ; une quelconque readiness de
production.

**Statut M7 parseur texte→preuve** : `VALIDATED`. Voir
`documentation/MetaHIA_M7_TextClaimParser_V0_1.md` Sec. 9 (nouvelle) et
`documentation/MetaHIA_Roadmap_Complete_v0.5.5_2026-09-17.md` pour la mise à jour de statut
correspondante.

---

## 2026-09-18 — Décision de configuration : union des deux sources retenue

Après quatre expériences réelles chiffrées (témoin seul, parseur seul, union simple, consensus
même-mécanisme, consensus inter-mécanismes — voir `documentation/MetaHIA_M7_TextClaimParser_V0_1.md`
Sec. 10–12), un tableau de coût/valeur mesuré a été soumis au porteur du projet :

| Option | Appels réels | Temps mur | Brier holdout | Décision de promotion |
|---|---|---|---|---|
| Témoin seul | 16 | 69,6 s | 0,47 (meilleur résultat) | PROMOTE |
| Parseur seul | 16 | 105,4 s | 0,508 | NE PROMEUT PAS |
| Les deux (union) | 32 | ~175 s | 0,489 | PROMOTE |
| Consensus inter-mécanismes | 32 | 184,5 s | — (0 preuve) | Écarté (dominé) |

**Choix explicite de Bacem Ben Soui (porteur du projet), le 2026-09-18** : *« Les deux (union
simple) »* — retenue malgré un Brier légèrement moins bon que le témoin seul (0,489 contre
0,47), au bénéfice de préserver la diversité d'issue réelle du parseur dans le corpus
d'entraînement (seule source ayant jamais produit un mélange `SUPPORTED`/`CONTRADICTED` non
dégénéré côté parseur), utile si le mécanisme s'améliore plus tard (modèle différent, corpus
étendu).

**Configuration retenue pour le pipeline d'évidence M7** : `m7_corpus_mixed_v0_2.py`,
condition `+ both` (union du corpus adversarial + témoin à question fermée + parseur texte),
32 appels LLM réels par exécution complète. Le consensus même-mécanisme et le consensus
inter-mécanismes restent fermés (résultats négatifs/dominés, non reproduits ici).

C'est une décision de configuration du porteur du projet, informée par des données de coût et
de calibration réelles — pas une clôture de gate de validation tierce (aucune des quatre
options n'a nécessité de nouveau protocole, chacune ne faisant que recombiner des mécanismes
déjà individuellement validés).

---

## 2026-09-22 — Paquet de validation tierce de P4-T.7 préparé (pas encore envoyé)

### Contexte
Rééquilibrage explicite demandé par le porteur du projet le même jour (voir
`documentation/P8_Jev_Kev_Local_Decision_Model_V0_1.md` Sec. 6octies) : arrêt des ablations
JEV/Kev sur LABELED, effort redirigé vers le chemin critique E20-D, en commençant par P4-T.7 —
la seule étape non commencée de la séquence P4-T.1→P4-T.7
(`documentation/P4T_Structural_Transformation_Induction_V0_1.md` Sec. 9.2).

### Paquet préparé
- `documentation/MetaHIA_ThirdParty_Validation_Protocol_P4T_V0_1.md`, même format que les
  protocoles M6/M7 : 10 cas critiques (C01–C10), 11 fichiers à hash gelé (`kernel2.py`,
  `e20d_protocol.py`, `e20d_cognitive_control_v0_1.py`, le module P4-T principal, les deux
  trios de benchmark verrouillé v0.1/v0.2, l'adaptateur de structure émergente).
- Contrairement aux protocoles M6/M7, **aucun nouveau fichier de test n'a été écrit** : les 10
  cas critiques réutilisent des tests déjà existants et déjà vérifiés (cités par nom exact,
  chacun confirmé résoudre vers exactement un test réel par collection `pytest -k` avant
  finalisation du document) — tout le mécanisme P4-T était déjà déterministe et sans réseau,
  contrairement au proposeur LLM de M7 qui avait justifié un fichier critique dédié
  sans-réseau.

### Auto-exécution (2026-09-22, PAS un retour tiers)
- Commande critique (4 fichiers) : 10/10 cas critiques PASS, 63/63 tests.
- Suite complète déterministe (`-k "not live"`) : 660 passed / 10 deselected, 0 régression.
- Aucune modification de fichier.
- **`P4-T = PASS_INDEPENDENT_SCOPE` (niveau mécanisme, auto-administré)** — même statut que M7
  après son premier round, avant tout retour externe.

### État après cette préparation
Le paquet est prêt à être envoyé, mais **n'a pas encore été envoyé à un tiers réellement
indépendant** — aucun tiers de ce type n'était disponible dans cette session, exactement comme
noté dans `documentation/P4T_Structural_Transformation_Induction_V0_1.md` Sec. 9.2 avant ce
travail. Règle inchangée, rappelée explicitement dans le nouveau protocole lui-même : une
auto-exécution ne ferme jamais ce gate (même règle que M6/M7, et même leçon méthodologique que
le gate d'annotation P1 — un porteur de projet, même rigoureux, n'est pas un tiers pleinement
indépendant). La clôture de cette étape reste une décision du porteur du projet, sur la base
d'une exécution externe réelle, jamais une auto-déclaration de cet assistant.

### Clôture de l'étape
**Non close.** Statut : paquet prêt, en attente d'un tiers réellement disponible.

---

## 2026-09-23 — Premier retour d'exécution P4-T.7 (environnement isolé, PAS un tiers pleinement indépendant)

### Paquet envoyé
- ZIP sans `.git`, produit par `git archive --format=zip` au commit
  `98bb4477ce4a504f8e6056b336dd955816ee8992`, transmis par le porteur du
  projet à un tiers de son choix (méthode « Option A » proposée dans la
  session, mirroir du round 1 de M7).

### Retour reçu
- Environnement : `Linux localhost 6.18.44`, Python 3.13.5, git 2.47.3 — indépendant de
  l'environnement de développement de cette session (sandbox Windows).
- **11/11 hashes SHA-256 conformes** au protocole — **revérifiés indépendamment ici même** (les
  11 fichiers du dépôt actuel produisent exactement les mêmes empreintes que celles rapportées),
  confirmant que le contenu réellement évalué correspond bien au commit annoncé.
- Suite critique (4 fichiers, commande exacte du protocole) : **63/63 PASS**, C01–C10 **10/10
  PASS**, chacun avec sa propre justification (fuites de provenance, sondes anti-triche,
  sélection d'hypothèses, correspondance witness v0.1 7/7 et v0.2 6/6, déterminisme, structure
  émergente, ROI).
- Suite complète : `-q` ne s'est pas terminé proprement dans son environnement (disclosure
  honnête du relecteur — il ne présente pas de sortie `-q` qu'il n'a pas réellement obtenue) ;
  rejoué immédiatement en `-vv` sans changement de code : **667 passed, 10 skipped, 38,61 s**,
  les 10 `skipped` étant les démonstrations réseau/LLM optionnelles (Ollama/Kev LAN
  indisponibles dans son environnement) — nombre **identique** à celui déjà obtenu dans cette
  session (667 passed / 10 deselected), corroboration croisée réelle, pas seulement déclarée.
- Aucune modification persistante : exécuté sur une copie jetable, les deux fichiers
  `validation/p4t_locked_benchmark_predictions_v0_1/_v0_2.json` (régénérés par les runners,
  comme prévu et documenté dans le protocole) et les `__pycache__` ont été restaurés/supprimés
  avant contrôle final ; le ZIP source lui-même n'a jamais été modifié.
- `git rev-parse HEAD` non disponible (pas de `.git` dans le ZIP, exactement le même
  écueil méthodologique déjà rencontré et disclosé honnêtement au round 1 de M7) — la
  référence de commit a été vérifiée par comparaison des hashes de fichiers, pas
  cryptographiquement via git.

### Réserve explicite, formulée par le relecteur lui-même, retenue telle quelle
> « Je ne qualifierais pas cette exécution de véritable "tiers humain indépendant" : c'est une
> exécution indépendante de l'environnement de développement, mais réalisée par cette même
> session d'assistant. »

Cette réserve est prise au sérieux, pas minimisée : elle signifie que ce round apporte une
**confirmation croisée réelle du mécanisme dans un environnement matériellement indépendant**
(OS, version Python, absence totale de code partagé avec la session de développement), mais ne
satisfait **pas** le critère « tiers réellement indépendant » que ce projet exige pour clôturer
un gate de validation tierce (même règle que M6/M7, et même leçon que le gate d'annotation P1 —
voir `documentation/MetaHIA_ThirdParty_Validation_Protocol_P4T_V0_1.md`, section
« Governance rule »).

### État après ce retour
`P4-T = PASS_INDEPENDENT_SCOPE` (niveau mécanisme) est confirmé une seconde fois, dans un
environnement matériellement distinct — un signal réel, pas négligeable. Mais la clôture du
gate de validation tierce reste, comme annoncé avant l'envoi du paquet, une décision du porteur
du projet sur la base d'une exécution par un tiers **réellement** indépendant (humain ou
organisation distincte, pas une session d'assistant) — non satisfaite par ce round.

### Clôture de l'étape
**Toujours non close.** Un round d'exécution supplémentaire dans un environnement isolé est
enregistré ; le critère d'indépendance réelle reste ouvert.
