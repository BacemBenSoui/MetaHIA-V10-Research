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

---

## 2026-09-23 — Clôture du gate P4-T.7 : validation par tiers humain et porteur du projet

### Paquet et procédure
Un mode opératoire dédié à l'exécution humaine du protocole,
`MetaHIA — Procédure de validation humaine P4-T.7.md` (dérivé du
protocole de référence, `documentation/MetaHIA_ThirdParty_Validation_Protocol_P4T_V0_1.md`,
même 10 cas critiques C01-C10, mêmes 11 hashes, même commit
`98bb4477ce4a504f8e6056b336dd955816ee8992`, mêmes commandes exactes),
a été rédigé pour guider une exécution manuelle pas à pas, avec fiche
de validation structurée en fin de procédure (Sec. 17) et rappel
explicite (Sec. 2) que l'exécution par le porteur du projet lui-même
reste une auto-validation, pas une clôture tierce.

### Deux exécutions indépendantes, résultats identiques
1. **Porteur du projet (Bacem Ben Soui)** : a exécuté lui-même
   l'intégralité de la procédure, au commit prescrit.
2. **Ingénieur système, entreprise externe** : a suivi la même
   procédure à la lettre, indépendamment, sur Linux Ubuntu Server
   24 LTS.

Les deux exécutions rapportent exactement le même résultat :

```text
Commit         : 98bb4477ce4a504f8e6056b336dd955816ee8992
Hashes          : 11/11 conformes
P4-T critique   : 63/63 PASS
C01-C10         : PASS (chacun, y compris 7/7 pour C06 et 6/6 pour C07)
Suite complète  : 677 passed, 0 failure
Arbre git final : propre
Modification de code : aucune
```

Le nombre « 677 passed » est vérifié ici comme cohérent avec l'état
réel du dépôt à ce commit précis (confirmé indépendamment dans cette
session : `98bb4477` est exactement le commit du diagnostic de
transfert contextuel M6, avant les deux commits M6-INTERNAL suivants
qui ont porté la suite à 687 puis 704 tests) — un signe convergent
d'exécution réelle au bon commit, pas une coïncidence de chiffres
arrondis.

### Décision explicite du porteur du projet
> « le protocole a été établi pour moi, le porteur du projet, mais il a
> aussi été exécuté par un ingénieur système externe, je voulais
> confirmer que nous avions les mêmes résultats et c'est le cas,
> clôturez le gate. »

Conformément à la règle de gouvernance déjà énoncée dans le protocole
lui-même et dans ce journal (même principe que pour M6 et M7) : la
clôture d'un gate de validation tierce est une décision réservée au
porteur du projet, jamais une auto-déclaration de cet assistant. Cette
décision est maintenant prise explicitement, sur la base d'une
exécution par un tiers réellement externe (ingénieur système d'une
entreprise extérieure, sans lien de subordination avec ce projet)
confirmant exactement le résultat du porteur du projet lui-même — la
même structure de preuve (deux exécutions convergentes, dont au moins
une réellement indépendante, décision de clôture explicite du porteur
du projet) qui a déjà fermé les gates M6 (2026-09-17) et M7
(2026-09-18).

### Portée exacte de la clôture — ce qui EST démontré
```text
P4-T (Gates A-G, benchmarks verrouillés v0.1/v0.2,
      structure émergente P4-T.5, adaptateur ROI P4-T.6)
= PASS_INDEPENDENT_SCOPE, tiers réellement indépendant confirmé
= GATE FERMÉ
```
non circulaire, sans fuite de provenance, fail-closed face aux données
adversariales, honnête dans la sélection d'hypothèses, aveugle dans ses
benchmarks verrouillés (statique+dynamique), déterministe, capable de
vérifier une structure émergente sans la fabriquer, honnête dans son
calcul de ROI — dans le périmètre actuel de P4-T (familles
REFERENCE-EQUALITY/PERMUTATION/RECURSIVE/SELECTION, transformation
induite à partir de paires données).

### Ce qui N'EST PAS démontré par cette clôture — répété explicitement, comme l'exige la procédure elle-même (Sec. 18)
- **`E20-D` n'est pas fermé.** Cette clôture ferme la question de
  savoir si le mécanisme P4-T est honnête et non circulaire dans son
  périmètre actuel — elle ne ferme aucune des 4 conditions globales
  d'E20-D par elle-même (voir la matrice de clôture,
  `documentation/P4T_Structural_Transformation_Induction_V0_1.md`
  Sec. 9.1, qui reste par ailleurs à jour : plusieurs cases restent
  🟠/manquantes indépendamment de cette clôture).
- **La découverte autonome générale d'une relation dans un graphe non
  structuré (`P4-U`, discutée le même jour) n'est ni couverte ni
  démontrée par ce protocole** — la procédure humaine elle-même le
  précise explicitement en Sec. 1 et Sec. 19 : P4-T reste
  « transformation induction » à partir de paires données, P4-U
  (découverte structurelle autonome) reste une étape distincte,
  explicitement non commencée.

### Clôture de l'étape
**FERMÉ (2026-09-23).** `P4-T.7 = CLOSED — validation par tiers humain
et porteur du projet.` Décision du porteur du projet, sur la base de
deux exécutions convergentes dont une réellement indépendante.

---

## 2026-09-23 — P4-U.1 : module minimal construit, implémentation mise en pause sur une tension protocolaire réelle (Gate B vs Gate C)

### Contexte
Suite à la validation explicite par le porteur du projet du protocole
`documentation/P4U1_Unsupervised_Compositional_Pattern_Discovery_V0_2.md`
et à l'instruction *« Validé, fixez les valeurs numériques manquantes
et lancez l'implémentation »*.

### Ce qui a été construit et testé
`p4u1_unsupervised_pattern_discovery_v0_1.py` (extraction de squelette,
découverte de candidats avec filtrage de profondeur et exclusion des
squelettes « aller-retour » sur une même relation, modèle nul par
pool, statistique du maximum sous modèle nul, percentile, évaluation
Gate B/Gate C, `FrozenPatternU1` avec `structural_digest` au même
format que `freeze()` de P4-T, énumération des départs admissibles,
rejeu via `kernel2.replay_path_pattern_holdout` non modifié) +
`tests/test_p4u1_unsupervised_pattern_discovery_v0_1.py` (22 tests
déterministes, tous passants). Trois bugs réels trouvés et corrigés
avant toute calibration — détail complet dans
`documentation/P4U1_Unsupervised_Compositional_Pattern_Discovery_V0_2.md`
Sec. 20 : `max_paths=None` retombant silencieusement sur la limite par
défaut de `kernel2` (1000) ; deux modèles nuls à préservation exacte du
degré prouvés mathématiquement invariants pour un support de
composition à 2 sauts ; squelettes « aller-retour » sur une même
relation dominant la statistique du maximum par explosion
combinatoire. Suite complète : 726 tests collectés (716 passed / 10
deselected en excluant les démonstrations réseau, 0 régression).

### La tension protocolaire trouvée en calibrant les seuils — non résolue unilatéralement
En tentant de fixer les valeurs numériques manquantes de la checklist
(Sec. 16, points 2/7/8) sur des corpus d'essai (jamais sur le
benchmark verrouillé lui-même, qui n'existe pas encore — conforme à la
règle du protocole « seuils fixés avant de voir un résultat de
holdout ») :

- **Gate B exige une structure concentrée (« hub »)** pour produire une
  séparation statistique réelle par rapport au modèle nul — une
  structure « plate » (chaque nœud-pont de degré 1) a une valeur
  ATTENDUE sous le modèle nul strictement égale à son propre support
  réel (propriété algébrique démontrée, pas un défaut de mélange) et
  ne peut donc, par construction, jamais dépasser un seuil de
  percentile 99 du maximum nul.
- **Gate C, via `kernel2.replay_path_pattern_holdout()` réutilisé sans
  modification (`max_candidates_per_step=1` par défaut), retourne
  systématiquement `AMBIGUOUS` (jamais `REPLAYED`) dès qu'un nœud a
  plus d'une continuation valide** — exactement la structure à
  fan-out concentré que Gate B exige.

**Aucune structure de corpus ne peut donc satisfaire les deux portes
simultanément** avec la combinaison actuelle (statistique de support
brut pour Gate B, mécanisme de rejeu à candidat unique par étape pour
Gate C). Ce n'est pas un problème de réglage de corpus ni un bug
d'implémentation — c'est une propriété du couple de définitions de
portes tel qu'il est actuellement écrit dans le protocole v0.2.

### Ce qui n'a délibérément pas été fait
Aucun contournement unilatéral n'a été choisi à partir de ce constat
(assouplir `max_candidates_per_step`, changer la statistique de Gate B,
accepter une structure plate en sachant qu'elle ne peut statistiquement
pas réussir Gate B). Ce sont des décisions de protocole, réservées au
porteur du projet, exactement comme chaque étape précédente de ce
chantier. Quatre options non tranchées sont documentées dans
`documentation/P4U1_Unsupervised_Compositional_Pattern_Discovery_V0_2.md`
Sec. 20.

### État après cette entrée
```text
Module minimal (p4u1_unsupervised_pattern_discovery_v0_1.py) : ÉCRIT, TESTÉ (22 tests)
Cas verrouillés U1/U2/U3 (cases/witness/runner)              : PAS ÉCRITS
Valeurs numériques de la checklist (Sec. 16, points 2/7/8)   : PAS FIGÉES
Run réel                                                      : PAS LANCÉ
```

**Implémentation en pause.** Décision requise du porteur du projet
avant de reprendre la construction du premier benchmark verrouillé.

---

## 2026-09-23 — P4-U.1 v0.3 : résolution Gate B / Gate C par une revue méthodologique du porteur du projet

### Décision explicite du porteur du projet
Après une revue détaillée en 13 points de la tension trouvée dans la
v0.2 (Sec. 20), le porteur du projet a tranché explicitement, en
rejetant les options 2 et 3 (« je ne choisirais pas l'option 2 en
première intention [...] Je ne choisirais absolument pas l'option 3 »)
et en reformulant l'option 1 plus rigoureusement plutôt que de
l'accepter telle quelle (« pas comme simple "au moins une continuation
correspond" [...] Transformer Gate C en un rejeu structurel à valeur
d'ensemble »).

### Ce qui a été décidé
```text
Gate B      : INCHANGÉE
kernel2     : INCHANGÉ (replay_path_pattern_holdout conservé comme
              diagnostic secondaire, jamais comme critère principal)
Gate C      : REDÉFINIE -- rejeu à valeur d'ensemble (existence d'au
              moins une continuation compatible avec FrozenPattern,
              jamais unicité)
Nouveau     : p4u1_set_valued_replay_v0_1.py (adaptateur séparé, pas
              encore écrit -- réutilise les primitives kernel2 sans
              les modifier)
```

Point de discipline explicitement rappelé par le porteur du projet et
repris tel quel dans le protocole : le témoin ne doit jamais servir à
choisir une branche de rejeu pendant l'exécution du mécanisme (aucune
sélection `witness dit B → choisir B`) — seulement à scorer la
décision après coup, exactement la même discipline d'aveuglement que
P4-T.

Rédigé intégralement dans
`documentation/P4U1_Unsupervised_Compositional_Pattern_Discovery_V0_3.md`
(Sec. 10 pour la nouvelle sémantique de Gate C, Sec. 10.5 pour la règle
anti-circularité, Sec. 11 pour la couverture redéfinie et le nouveau
diagnostic `mean_valid_continuations_per_replicating_start`, Sec. 16
pour la séquence de travail mise à jour). La v0.2 reste comme
historique de la revue et du diagnostic (bandeau `SUPERSEDED` ajouté en
tête du document, même convention que v0.1 → v0.2).

### État après cette entrée
```text
Protocole v0.3                                        : GELÉ
Adaptateur p4u1_set_valued_replay_v0_1.py              : PAS ENCORE ÉCRIT
Cas verrouillés U1/U2/U3 (cases/witness/runner)        : PAS ÉCRITS
Valeurs numériques de la checklist (Sec. 16, pts 2/7/8/11) : PAS FIGÉES
Run réel                                               : PAS LANCÉ
```

Prochaine étape : écrire `p4u1_set_valued_replay_v0_1.py` avec ses
tests déterministes (y compris un test de non-circularité explicite),
avant de fixer les valeurs numériques et de construire le benchmark
verrouillé.

---

## 2026-09-23 — Adaptateur `p4u1_set_valued_replay_v0_1.py` écrit et testé (13 tests) ; le hub résout bien la tension

### Ce qui a été construit
`p4u1_set_valued_replay_v0_1.py`, conforme à la Sec. 10 de la v0.3 :
`skeleton_matching_paths_from_start` / `compatible_paths_from_start`
(réutilisent `kernel2.discover_paths()` sans le modifier),
`replay_set_valued` (décision `REPLICATED(start)` par existence),
`replay_on_all_admissible_starts_set_valued` (agrégat, couverture
redéfinie + nouveau diagnostic `mean_valid_continuations_per_replicating_start`),
`evaluate_gate_c_set_valued` (mêmes trois conditions que l'ancienne
Gate C, appliquées à la nouvelle statistique), et
`legacy_unique_replay_status` (diagnostic secondaire, appelle
`kernel2.replay_path_pattern_holdout()` non modifié). 13 nouveaux
tests déterministes, tous passants ; suite complète : 729 passed / 10
deselected (0 régression, +13 par rapport à l'entrée précédente).

### La démonstration centrale
Sur le même corpus (un nœud H avec trois branches
`H --REL_A--> Ci --REL_B--> Gi`) :
```text
kernel2.replay_path_pattern_holdout() (non modifié) : AMBIGUOUS
p4u1_set_valued_replay_v0_1 (nouveau)                : REPLICATED = True
```
Test `test_legacy_status_is_ambiguous_at_the_same_hub_where_the_adapter_says_replicated`
— confirme, sur les mêmes données, exactement la divergence qui motivait
cette révision : la même structure qui échouait Gate C sous la v0.2
réussit maintenant Gate C sous la v0.3, sans que Gate B ni `kernel2`
n'aient été modifiés.

### Constat honnête trouvé en écrivant les tests, non anticipé par le protocole
`kernel2.discover_paths()` interdit de revisiter un nœud déjà présent
dans le chemin en cours — toute `PathRecord` qu'elle produit a donc des
positions deux à deux distinctes. Conséquence : `position_groups`
(le champ `structure` du `FrozenPattern`) ne peut jamais être non
trivial pour un candidat issu du pipeline de découverte standard —
la vérification de co-référence de Gate C
(`_position_groups_satisfied`) reste appliquée uniformément mais sa
branche de rejet est aujourd'hui inatteignable en pratique. `REPLICATED`
se réduit donc, avec les données que ce pipeline peut produire
aujourd'hui, à une pure question d'existence d'au moins un chemin de
bon squelette — ce qui reste exactement la propriété recherchée et
résout bien la tension, seulement sans le raffinement de co-référence
que `structure` pourrait un jour apporter. Documenté en détail dans
`documentation/P4U1_Unsupervised_Compositional_Pattern_Discovery_V0_3.md`
Sec. 10.7, et testé directement sur des `PathRecord` construits à la
main (seule façon de l'exercer aujourd'hui).

### État après cette entrée
```text
Protocole v0.3                                        : GELÉ
Adaptateur p4u1_set_valued_replay_v0_1.py              : ÉCRIT, TESTÉ (13 tests)
Cas verrouillés U1/U2/U3 (cases/witness/runner)        : PAS ÉCRITS
Valeurs numériques de la checklist (Sec. 16, pts 2/7/8/11) : PAS FIGÉES
Run réel                                               : PAS LANCÉ
```

Prochaine étape (séquence Sec. 16 de la v0.3) : fixer les valeurs
numériques manquantes et construire le benchmark verrouillé U1/U2/U3,
avant tout run réel.

---

## 2026-09-23 — Benchmark verrouillé U1/U2/U3 construit et exécuté ; run réel conforme au témoin sur les 7 candidats déclarés

### Calibration numérique (avant tout code de benchmark verrouillé)
Valeurs numériques manquantes de la checklist v0.3 (Sec. 16, pts
2/7/8/11) fixées par calibration directe sur des corpus JETABLES,
jamais sur le fichier de cas verrouillé lui-même — enregistrement
complet dans
`documentation/P4U1_Locked_Benchmark_Numeric_Calibration_2026-09-23.md`.
Deux corrections réelles trouvées pendant cette calibration, avant de
rien figer :
1. Une première structure « hub multi-branches » (plusieurs branches de
   degré 1 partageant une origine) s'est révélée être exactement la
   structure « plate » déjà prouvée invariante face au modèle nul
   (v0.2 Sec. 20 / v0.3 Sec. 10.7) — le null-max mesuré dépassait même
   parfois le signal réel. Corrigée par une structure « pont unique »
   (P parents convergeant vers UN nœud, Q enfants en divergeant,
   support = P×Q) — la vraie source de séparation statistique de Gate B.
2. `max_paths=None` (recommandation par défaut de la Sec. 13) s'est
   révélé prohibitivement lent (jusqu'à ~60 s par distribution nulle à
   200 réplicats) dès qu'un réplicat concentre du degré par hasard —
   remplacé par la limite fixe que la Sec. 13 prévoit elle-même en
   repli, `max_paths=1000`, appliquée uniformément partout.

Valeurs retenues : `N_null=200`, `S_min=15`, `K_min=15`,
`coverage_min=0.10`, `max_paths=1000`, `null_percentile=99.0` — chacune
choisie avec une marge réelle mesurée (jamais un seuil à la limite),
détaillée dans le document de calibration cité ci-dessus.

### Benchmark construit
`p4u1_locked_benchmark_cases_v0_1.py` (train+holdout, sans vérité),
`p4u1_locked_benchmark_witness_v0_1.py` (vérité seule, séparée),
`p4u1_locked_benchmark_runner_v0_1.py` (même discipline mécanique
d'ordre d'import que P4-T : preuve dynamique via `sys.modules`, pas
seulement textuelle). Optimisation trouvée pendant l'écriture du
runner : la distribution du maximum nul côté holdout ne doit être
calculée qu'UNE FOIS par cas, jamais une fois par candidat partageant
le même `G_holdout` — réduit le temps du run complet de 160 s à 106 s.
`tests/test_p4u1_locked_benchmark_v0_1.py` : vérifications statiques
(aucune mention du module témoin dans les fonctions de découverte/
commit) et dynamiques (`sys.modules`), plus un test de déterminisme
(deux exécutions complètes, prédictions identiques hors horodatage).

### Résultat du run réel (auto-administré, PAS une validation tierce)
Les 7 candidats déclarés correspondent TOUS aux 3 gates attendus par
le témoin, sans aucune divergence :
```text
U1 REAL_MOTIF       : DISCOVERED, RETAINED, REPLICATED
U1 DECOY_SUB_SEUIL  : DISCOVERED, REJECTED (SUB_THRESHOLD), NOT_APPLICABLE
U1 DECOY_DEPTH1     : NOT_DISCOVERED
U1 DECOY_TRAIN_ONLY : DISCOVERED, RETAINED, FAILED
U2 REAL_MOTIF       : DISCOVERED, RETAINED, FAILED
U3 (2 candidats)    : DISCOVERED, REJECTED (NOT_NULL_SIGNIFICANT), NOT_APPLICABLE
```
Démonstration empirique complète de la séparation recherchée : Gate B
(inchangée) sépare les structures concentrées des trop petites/trop
peu profondes ; Gate C (redéfinie, set-valued) sépare ensuite, parmi
les structures concentrées, celle qui existe réellement dans le
holdout (REAL_MOTIF) de celle qui n'existe qu'en train (DECOY_TRAIN_ONLY,
U2) ; U3 confirme qu'un graphe sans régularité ne dépasse jamais son
propre seuil statistique.

### Portée exacte — ce qui N'EST PAS établi
Exécution auto-administrée par cet assistant, pas une validation par
un tiers indépendant (même distinction que pour tous les gates M6/M7/
P4-T avant leur clôture tierce). Établit l'honnêteté et la
non-circularité du mécanisme SUR CE benchmark et CES seuils précis —
n'établit ni la généralisation à un graphe réel de provenance inconnue,
ni une quelconque readiness de production. Décision de clôture
(validation tierce, extension vers `P4-U.2`, ou autre) : réservée au
porteur du projet.

### État après cette entrée
```text
Protocole v0.3                                        : GELÉ
Adaptateur p4u1_set_valued_replay_v0_1.py              : ÉCRIT, TESTÉ (13 tests)
Cas verrouillés U1/U2/U3 (cases/witness/runner)        : ÉCRITS, TESTÉS
Valeurs numériques de la checklist                     : FIGÉES (voir calibration)
Run réel                                               : LANCÉ -- conforme au témoin sur 7/7 candidats
Validation tierce                                      : NON commencée
```

---

## 2026-09-23 — Décision de gouvernance P4-U.1 : statut retenu, P4-U.2 en attente, paquet de validation tierce préparé

### Décision explicite du porteur du projet, sur la base du résultat 7/7 ci-dessus
Après revue méthodologique du résultat, le statut suivant est
explicitement retenu — pas `CLOSED` :
```text
P4-U.1 = MECHANISM VALIDATED ON LOCKED SELF-ADMINISTERED BENCHMARK
         / GENERALIZATION OPEN
```
Raison, non plus technique mais expérimentale : les seuils numériques
et les témoins ont été calibrés puis gelés dans le même environnement
qui les a ensuite vérifiés — un résultat 7/7 est une preuve d'intégrité
du protocole, pas une preuve d'indépendance vis-à-vis de son propre
constructeur. Même principe de gouvernance déjà appliqué à M6, M7 et
P4-T.7 avant leurs clôtures tierces respectives.

### Décisions explicites associées
- **`P4-U.2` (découverte autonome de relations inconnues) reste en
  attente** — ne pas commencer avant la validation tierce de P4-U.1.
- **`position_groups` (Sec. 10.7) reste ouvert mais non bloquant** — ne
  pas modifier `kernel2.discover_paths()` pour le rendre atteignable ;
  un tel changement serait une évolution nouvelle du mécanisme, à
  traiter et justifier séparément.

### Paquet préparé
`documentation/MetaHIA_ThirdParty_Validation_Protocol_P4U1_V0_1.md`, au
commit `3e3c21b83aec22e6ed852e862ece378f2f569df7`, même format que les
protocoles M6/M7/P4-T.7 : 10 cas critiques (C01-C10), 6 fichiers à hash
gelé (`kernel2.py` + les 5 modules P4-U.1), commande exacte de suite
critique (3 fichiers de tests), avertissement explicite sur le temps
d'exécution réel (~2,5-3 min, calcul statistique réel, pas un blocage),
limitations déjà divulguées reprises explicitement (périmètre
composition-sur-graphe-déjà-étiqueté, non-discriminance actuelle de
`position_groups`, calibration dans le même environnement que la
vérification).

### État après cette préparation
Le paquet est prêt mais **n'a pas encore été envoyé à un tiers
réellement indépendant** — même situation que P4-T.7 avant son premier
envoi. Statut : `P4-U.1` non fermé, en attente d'une exécution externe
réelle.

---

## 2026-09-23 — Précision de packaging : distinction explicite entre le commit des artefacts de benchmark et le commit du paquet documentaire

### Point soulevé par le porteur du projet
Le protocole de validation tierce a été ajouté dans `4f70d35`, alors que
les artefacts de benchmark faisant foi (les 6 fichiers à hash gelé) ont
été construits, calibrés et exécutés en aveugle au commit `3e3c21b`. Un
validateur qui clonerait `3e3c21b` seul ne trouverait pas encore le
protocole ; il fallait donc rendre explicite lequel des deux commits
cloner, et prouver — pas seulement affirmer — que les fichiers gelés
n'ont pas changé entre les deux.

### Vérification directe
```text
git diff 3e3c21b 4f70d35 -- kernel2.py p4u1_unsupervised_pattern_discovery_v0_1.py \
  p4u1_set_valued_replay_v0_1.py p4u1_locked_benchmark_cases_v0_1.py \
  p4u1_locked_benchmark_witness_v0_1.py p4u1_locked_benchmark_runner_v0_1.py
```
→ **sortie vide** : les 6 fichiers sont strictement identiques entre les
deux commits (`4f70d35` n'a touché que de la documentation, le journal,
`release_manifest.json`, le manifeste de hashes global, les logs de
régression, et les fichiers de prédictions horodatés — jamais l'un des
6 fichiers gelés).

### Correctif apporté au protocole
`documentation/MetaHIA_ThirdParty_Validation_Protocol_P4U1_V0_1.md`
précise désormais explicitement :
- `3e3c21b` = commit de construction des artefacts de benchmark (celui
  auquel les hashes et le résultat 7/7 se réfèrent) ;
- `4f70d35` (ou tout commit ultérieur) = paquet documentaire / ce
  protocole lui-même ;
- cloner au commit du protocole lui-même (pas `3e3c21b` seul, qui ne
  contient pas encore ce document) ;
- la commande `git diff` ci-dessus, à exécuter par le validateur
  lui-même si son commit de checkout est postérieur à `3e3c21b`, ajoutée
  comme élément obligatoire du rapport attendu (Sec. « Required
  report ») — jamais une simple affirmation à prendre pour acquise.

### Décision réaffirmée
Aucune modification de `discover_paths()` ni de la logique
`position_groups` avant la validation tierce — l'expérience indépendante
doit rester définie exactement comme elle l'est aujourd'hui.

---

## 2026-09-23 — Bug réel trouvé en préparant le paquet zip du tiers : la commande « suite complète » n'excluait pas les tests live M7

### Contexte
Demande du porteur du projet : préparer le paquet zip à envoyer au tiers
pour P4-U.1. Avant tout envoi, vérification directe du paquet lui-même
(pas seulement du dépôt de travail) : `git archive --format=zip HEAD`
(commit `be25f79`), extraction dans un dossier propre, sans `.git`,
recalcul des 6 hashes gelés (conformes) et **exécution réelle** des deux
commandes du protocole depuis l'archive extraite.

### Constat
La suite critique (3 fichiers) passe bien en ~3 min, sans réseau. Mais la
commande « suite complète » du protocole, telle qu'écrite,
`python -m pytest -q` (sans filtre), a collecté et exécuté les 10 tests
`tests/test_m7_*_live_demo_v0_1.py` — des démonstrations LLM/Ollama en
direct, entièrement étrangères à P4-U.1 — et a pris **28 minutes** dans
cet environnement (qui a pu joindre un backend LLM). Dans un
environnement sans accès réseau ou sans backend joignable, ces mêmes
tests risqueraient fortement de bloquer beaucoup plus longtemps sur des
timeouts de connexion plutôt que d'échouer proprement. Ceci contredisait
directement l'affirmation du protocole lui-même (« No network access...
is required or used anywhere in this protocol ») — une vraie
incohérence, trouvée par exécution réelle du paquet avant envoi, pas
supposée.

### Correctif
`documentation/MetaHIA_ThirdParty_Validation_Protocol_P4U1_V0_1.md`
corrigé : la commande de suite complète devient
`python -m pytest -q -k "not live"` (même filtre déjà utilisé partout
ailleurs dans ce dépôt pour les runs de régression), avec une explication
explicite du pourquoi (les 10 tests M7 live, leur non-pertinence pour
P4-U.1, et le résultat réel du premier essai sans filtre : 28 minutes).
Même discipline déjà appliquée par les protocoles M6/M7/P4-T.7 pour leur
propre suite critique — ici corrigée après coup, sur le paquet destiné au
tiers, avant tout envoi.

### Reconfirmation après correctif
Depuis l'archive extraite : suite critique = 46/46 PASS (~3 min) ; les 6
hashes gelés restent conformes (le correctif ne touche aucun des 6
fichiers gelés). Nouveau commit à produire pour le paquet final, puis
nouvelle archive à reconstruire au commit corrigé.

---

## 2026-09-23 — Premier retour d'exécution P4-U.1 (tiers humain externe, confirmé par le porteur du projet)

### Paquet envoyé
`MetaHIA-V10-Research-P4U1-ThirdPartyValidation-7b47edb.zip`
(`git archive --format=zip`, sans `.git`), commit `7b47edb`.

### Point de vigilance soulevé et résolu avant d'enregistrer ce retour
Le rapport reçu mentionne un chemin de sortie
`/mnt/agents/output/P4U1_Validation_Report_2026-09-23.md`, qui évoque a
priori un sandbox d'agent plutôt qu'un poste humain — signal identique à
celui qui, pour P4-T.7, avait correspondu à une exécution NON
indépendante (assistant auto-administré dans un environnement isolé).
Question posée explicitement au porteur du projet avant tout
enregistrement : qui/quoi a exécuté ce test ? **Réponse confirmée : un
humain externe, d'une organisation tierce** (l'usage d'un agent/outil
pour piloter les commandes n'enlève rien à l'indépendance de la personne
qui a suivi le protocole).

### Retour reçu
- Environnement : Linux 5.10.134 (glibc 2.36), Python 3.11 + pytest
  7.2.1 (le Python 3.12 par défaut du système n'avait pas `pytest`) —
  distinct de l'environnement de développement (Windows).
- Source : archive zip extraite dans un sandbox **sans accès réseau**
  (aucun LLM/Ollama/service externe) — confirme directement que le
  correctif du filtre `-k "not live"` (commit `5bbd6e3`/`7b47edb`) était
  nécessaire et suffisant : la suite complète tourne bien sans réseau.
- **6/6 hashes gelés conformes**, avant et après exécution.
- Suite critique (3 fichiers) : **46/46 PASS en 97,36 s**.
- Suite complète : **740 passed, 10 deselected en 124,29 s** — les 10
  tests live M7 correctement désélectionnés via `-k "not live"`.
- **10/10 cas critiques (C01-C10) PASS**, chacun rapporté nommément.
- Aucun fichier source modifié ; seuls les JSON de prédictions ont été
  régénérés (artefact de sortie explicitement autorisé par le
  protocole) — `witness_module_imported_yet: false` confirmé pour
  P4-U.1.

### Écarts honnêtement signalés par le relecteur lui-même
- Absence de `.git` dans l'archive (méthode `git archive` déjà annoncée
  par ce protocole, Option A comme pour M7/P4-T.7 round 1) — impossible
  de rapporter `git rev-parse HEAD` ou d'exécuter le `git diff` demandé
  en Sec. « Required report » ; contrôle équivalent effectué à la
  place : vérification SHA-256 des 6 fichiers gelés + comparaison
  d'arborescence complète — même limitation méthodologique déjà
  rencontrée et disclosed lors des rounds M7/P4-T.7 sur ZIP sans `.git`.
- Python 3.11 utilisé au lieu de 3.12 (pytest absent de ce dernier) —
  3.11+ est la version recommandée par le protocole, donc conforme.

### État après ce retour
`P4-U.1 = PASS_INDEPENDENT_SCOPE` (niveau mécanisme), confirmé par une
première exécution véritablement externe. Conformément à la même
discipline déjà appliquée à M6/M7/P4-T.7 (deux exécutions convergentes,
dont au moins une réellement indépendante, avant toute décision de
clôture) : **ce retour, seul, ne clôture pas le gate** — c'est au
porteur du projet de décider s'il souhaite clôturer sur la base de cette
unique exécution externe ou attendre une seconde exécution convergente,
comme cela avait été fait pour M6/M7/P4-T.7. Décision non prise ici par
cet assistant.

### Clôture de l'étape
**Non close.** Statut retenu inchangé :
`P4-U.1 = MECHANISM VALIDATED ON LOCKED SELF-ADMINISTERED BENCHMARK /
GENERALIZATION OPEN`, avec désormais une première confirmation externe
réelle et positive. Décision de clôture : en attente du porteur du
projet.

---

## 2026-09-23 — Second retour d'exécution P4-U.1, par une IA (pas un tiers humain) : échec rapporté sur C10, non reproduit par investigation directe

### Nature de ce retour
Le porteur du projet a lui-même qualifié ce second retour de
« confirmation par une IA », pas par un humain. Conséquence de
gouvernance immédiate, indépendante de tout résultat technique : une
exécution par une IA **ne compte pas** comme validation tierce
indépendante au sens de ce projet (même règle déjà énoncée pour M6/M7/
P4-T.7 — « no simulated or self-administered "external" run counts »).
Ce retour est donc examiné pour sa valeur diagnostique, jamais comme un
second round de validation tierce à comptabiliser.

### Le rapport reçu, en résumé
Rapport technique très détaillé et honnête (traces `faulthandler`,
recherche binaire sur la suite complète, isolation précise du test
bloquant) :
- C01-C09 : PASS (45/46 tests critiques hors C10).
- **C10 (`test_committed_predictions_file_is_deterministic_across_runs`)
  : TIMEOUT** — la seconde invocation de `run_locked_benchmark()` dans
  le MÊME interpréteur Python (le fixture en fait une première fois,
  puis ce test lui-même en refait une seconde) ne serait jamais revenue
  en 10 minutes, avec une pile d'appel bloquée dans
  `null_max_support_distribution() -> discover_candidates() ->
  kernel2.discover_paths()`.
- Suite complète (`-k "not live"`) : n'aurait pas terminé non plus,
  avec un second indice indépendant (le 501e test collecté, un test M7
  sans rapport avec P4-U.1, ferait bloquer l'exécution cumulative alors
  qu'il passe seul).
- Vérification complémentaire honnête du relecteur : deux invocations
  du runner dans des process Python **séparés** (pas le même
  interpréteur) produisent bien des prédictions identiques.

### Investigation directe menée avant toute conclusion (discipline du projet : ne jamais accepter un rapport sans vérification)
1. Recherche de tout état mutable partagé au niveau module dans
   `kernel2.py` et les modules P4-U.1 (caches, compteurs globaux,
   arguments par défaut mutables) : **aucun trouvé**.
2. Reproduction directe, dans CE dépôt, du scénario exact décrit : trois
   appels consécutifs de `run_locked_benchmark()` dans le MÊME
   interpréteur Python, avec heartbeat et `faulthandler` actifs :
   ```text
   1er appel : 81,51 s
   2e appel (même interpréteur) : 61,99 s
   3e appel (même interpréteur) : 65,82 s
   ```
   **Aucun blocage, aucune dégradation cumulative** — le 2e et le 3e
   appel sont, si quoi que ce soit, légèrement plus rapides que le 1er.
3. Le PREMIER retour externe (2026-09-23, tiers humain confirmé) avait
   déjà, par la conception même du test C10, exécuté exactement ce même
   scénario (fixture + second appel dans le même process) avec succès
   en 97,36 s pour la suite critique entière — la « condition de
   réentrance » rapportée par le second retour ne s'est donc PAS
   manifestée non plus lors de la seule exécution humaine confirmée
   dont ce projet dispose à ce jour.

### Conclusion honnête de cette investigation
Aucune reproduction du blocage rapporté, ni sur cette machine de
référence (3 exécutions consécutives), ni dans l'exécution humaine
externe déjà confirmée (qui exerçait déjà ce même chemin de code avec
succès). Cause la plus plausible, non certaine : un phénomène propre à
l'environnement d'exécution du second rapport (sandbox d'agent
fortement contraint en CPU/quota — un phénomène d'infrastructure
courant dans ce type d'environnement, connu pour transformer un calcul
Python CPU-intensif normalement rapide en blocage apparent), plutôt
qu'un défaut réel de réentrance dans le code. **Ce point reste
néanmoins consigné honnêtement comme non totalement résolu** — l'écart
entre les deux rapports externes n'a pas de cause root confirmée à
100 %, seulement une explication plausible et une non-reproduction
robuste.

### Ce que cette investigation ne change PAS
- Le retour n'étant pas humain, il ne compte de toute façon pas pour la
  clôture du gate, indépendamment de son résultat technique.
- Aucune modification de code n'a été faite à partir de ce rapport — ni
  au runner, ni à `kernel2.py`, ni aux seuils — conformément à la
  décision déjà prise de ne rien changer avant une validation tierce
  humaine complète.
- Le statut retenu reste inchangé :
  `P4-U.1 = MECHANISM VALIDATED ON LOCKED SELF-ADMINISTERED BENCHMARK /
  GENERALIZATION OPEN`, avec une confirmation humaine externe positive
  (premier retour) et ce second signal diagnostique (IA, non
  reproduit) consigné pour mémoire.

---

## 2026-09-23 — Clôture du gate de validation tierce P4-U.1 : décision du porteur du projet, sur la base d'un unique retour humain externe

### Paquet et procédure
`documentation/MetaHIA_ThirdParty_Validation_Protocol_P4U1_V0_1.md`,
même format que M6/M7/P4-T.7 : 10 cas critiques (C01-C10), 6 fichiers à
hash gelé, paquet `MetaHIA-V10-Research-P4U1-ThirdPartyValidation-7b47edb.zip`
(`git archive`, sans `.git`, commit `7b47edb`, contenu vérifié
byte-identique au commit de construction `3e3c21b` pour les 6 fichiers
gelés).

### Résultat retenu comme base de la clôture
Le retour humain externe (2026-09-23, entreprise extérieure, confirmé
explicitement par le porteur du projet) :
```text
Environnement    : Linux 5.10.134 (glibc 2.36), Python 3.11, pytest 7.2.1
Sandbox          : sans accès réseau
Hashes           : 6/6 conformes, avant et après exécution
Suite critique   : 46/46 PASS en 97,36 s
Suite complète   : 740 passed, 10 deselected en 124,29 s (0 régression)
Cas critiques    : C01-C10 = 10/10 PASS
Fichiers modifiés: aucun (seuls les JSON de prédictions régénérés,
                    artefact de sortie explicitement autorisé)
```
Le second retour reçu le même jour (exécuté par une IA, pas un tiers
humain — voir l'entrée précédente) ne compte pas pour cette clôture,
conformément à la règle de gouvernance déjà appliquée : son signal de
blocage sur C10 a par ailleurs été investigué directement et n'a été
reproduit ni sur la machine de référence ni dans l'exécution humaine
elle-même, qui exerçait déjà le même chemin de code avec succès.

### Décision explicite du porteur du projet
> « Clôturez le gate sur la base de ce seul retour humain. »

**Écart assumé et documenté par rapport au précédent M6/M7/P4-T.7** :
ces trois gates avaient chacun requis deux exécutions convergentes
(dont au moins une réellement indépendante) avant clôture. Ici, le
porteur du projet décide explicitement de clôturer sur la base d'une
SEULE exécution externe humaine — une décision de gouvernance qui lui
revient pleinement, prise en connaissance de cause (le résultat 7/7 du
run auto-administré avait déjà été reproduit fidèlement par ce tiers,
et le second retour, bien que non comptabilisé, a été investigué plutôt
qu'ignoré). Conformément à la règle déjà énoncée dans le protocole
lui-même et dans ce journal (même principe que pour M6, M7 et P4-T.7) :
la clôture d'un gate de validation tierce est une décision réservée au
porteur du projet, jamais une auto-déclaration de cet assistant — elle
est maintenant prise explicitement.

### Portée exacte de la clôture — ce qui EST démontré
```text
P4-U.1 (discover -> Gate B (inchangée) -> freeze -> set-valued replay
        -> Gate C (redéfinie, v0.3) -> commit -> reveal,
        benchmark verrouillé U1/U2/U3)
= PASS_INDEPENDENT_SCOPE, tiers humain externe confirmé
= GATE DE VALIDATION TIERCE FERMÉ
```
Le pipeline complet est honnête, non circulaire, aveugle mécaniquement
(vérifié statiquement et dynamiquement), et reproductible sur un
checkout indépendant, avec les seuils numériques gelés
(`GATE_PARAMS`) — dans le périmètre exact de ce benchmark verrouillé.

### Ce qui N'EST PAS démontré par cette clôture — répété explicitement, comme l'exige le protocole lui-même (section « Scientific non-closure »)
- **La généralisation des seuils gelés à un graphe réel de provenance
  inconnue n'est pas établie** — le statut retenu au niveau du
  mécanisme reste donc `GENERALIZATION OPEN`, une question distincte de
  la clôture du gate de validation tierce elle-même.
- **`P4-U.2`** (découverte autonome de relations inconnues) reste hors
  périmètre et non commencé — cette clôture ne l'autorise pas
  automatiquement ; un cadrage explicite séparé reste nécessaire avant
  tout travail sur `P4-U.2`.
- Le raffinement de co-référence (`position_groups`, Sec. 10.7 de la
  v0.3) reste non discriminant en pratique sous `kernel2.discover_paths()`
  — non résolu par cette clôture, et `kernel2.py` reste non modifié.
- Aucune readiness de production.

### Statut retenu après cette clôture
```text
P4-U.1 = MECHANISM VALIDATED (THIRD-PARTY CONFIRMED, HUMAN, SINGLE ROUND)
         / GENERALIZATION OPEN
```
Le gate de validation tierce est **FERMÉ**. Le statut de généralisation
reste **OUVERT** — deux questions distinctes, jamais confondues.

### Clôture de l'étape
**FERMÉ (2026-09-23).** `P4-U.1 = Gate de validation tierce CLOSED —
validation par tiers humain externe, décision du porteur du projet, sur
la base d'un unique retour convergent.` Prochaine étape possible,
distincte de cette clôture : cadrage explicite de `P4-U.2`, réservé au
porteur du projet.

---

## 2026-09-23 — Cadrage de P4-U.2 (découverte autonome de relations inconnues) — aucun code, aucun protocole verrouillé

### Demande explicite
« Cadrez P4-U.2 » — demandé par le porteur du projet immédiatement
après la clôture du gate P4-U.1.

### Revue directe du dépôt avant toute proposition (agent Explore)
Confirmé par lecture directe de code, pas supposé :
- `kernel2.py` (`reference_equal`/`structural_equal`) ne peut
  aujourd'hui, dans AUCUN cas, juger que deux arêtes à `NodeRef`
  d'opérateur distincts instancient la même relation — c'est
  précisément le vide que P4-U.2 doit combler, identifié comme la
  SEULE pièce manquante réelle.
- `reify_path_link`/`materialize_reified_link`/`reinject_reified_links`
  (kernel2.py) existent déjà, vivants (via
  `m3_recursive_structural_closure_v0_1.py`), et sont directement
  réutilisables pour réifier un candidat regroupé — sans modification.
- `Hypothesis.status` (kernel2.py) fournit déjà le contrat épistémique
  UNKNOWN-par-défaut requis — à réutiliser tel quel.
- `ref_jaccard`/`structural_similarity`
  (`e20d_rationalization_v0_1.py`, VIVANT, appelé par P4-T) est le
  seul moteur de similarité réel du dépôt — brique la plus directement
  réutilisable pour la pièce manquante, moyennant une extension (1
  candidat contre 1 pool -> clusterisation multi-paires).
- Les 4 autres fichiers `e20d_*` morts (`operator_relation`,
  `operator_behavior`, `property_discovery`, `emergent_structure`)
  relus directement : aucun n'opère sur des opérateurs non déjà
  identifiés — confirmé n'être PAS le chaînon manquant.
  `e20d_operation_synthesis_v0_1.py` (mort) porte en revanche déjà le
  contrat IDENTIFIED_EXISTING/CREATED_NEW/AMBIGUOUS exact dont
  l'étape finale de P4-U.2 aurait besoin — réactivation envisageable,
  mais jamais silencieuse.
- Aucun énoncé exact de « une dérivation ne peut pas être sa propre
  preuve » n'existe dans ce dépôt V10-Research (vérifié absent, pas
  supposé) ; l'équivalent le plus proche est
  `m3_recursive_structural_closure_v0_1.py:13` (« DERIVED structures
  are never treated as epistemic evidence ») — érigé en contrainte non
  négociable du cadrage.

### Document produit
`documentation/P4U2_Autonomous_Relation_Discovery_V0_1.md` — cadrage
seul, aucun code, aucun seuil numérique, aucun cas de test. Contenu :
distinction précise avec P4-T/P4-U.1 ; identification du vide réel
(regroupement par similarité malgré des opérateurs distincts, jamais
par égalité exacte) ; inventaire des pièces réutilisables sans
modification (Sec. 3) ; squelette d'architecture proposé (Sec. 5) ;
risque méthodologique central signalé comme PLUS sévère qu'en P4-U.1
(une statistique de similarité par PAIRE, `O(n²)` sur le pool de
candidats, contre un compte par squelette `O(n)` en P4-U.1 — risque de
faux positifs structurellement plus grand, non résolu ici) ; décisions
déjà prises à ne pas rouvrir (kernel2.py non modifié, pas de
réactivation silencieuse des `e20d_*` morts, pas de dictionnaire
sémantique, UNKNOWN par défaut) ; trois questions ouvertes nécessitant
une décision explicite du porteur du projet avant tout protocole v0.1
(comment simuler une « relation inconnue » dans le premier corpus ;
portée du premier increment ; réactivation ou non de
`operation_synthesis`).

### État après cette entrée
```text
P4-U.2 : CADRÉ (ce document), PAS ENCORE PROTOCOLE, PAS DE CODE
Décision du porteur du projet requise sur 3 questions ouvertes (Sec. 9)
avant toute écriture de protocole v0.1
```

---

## 2026-09-23 — Cadrage P4-U.2 v0.2 : correction d'une faille de non-identifiabilité dans le cadrage v0.1

### La faille identifiée par la revue du porteur du projet
Le cadrage v0.1 formulait le vide à combler comme « comparer deux
arêtes après avoir ignoré/masqué leur opérateur ». Faille : deux
observations binaires `op1(a,b)` et `op2(c,d)`, une fois l'opérateur
ignoré, deviennent presque identiques du point de vue de la forme K3
locale (`BINARY(source,target)` dans les deux cas) — un algorithme
naïf regrouperait alors TOUTES les relations binaires entre elles,
simplement parce qu'elles partagent la même forme. Un problème de
non-identifiabilité structurelle, pas une découverte.

### Reformulation retenue
```text
P4-U.2 n'est PAS : comparer des arêtes après avoir ignoré leur opérateur.
P4-U.2 EST       : découvrir des classes d'opérateurs partageant un
                    comportement structurel OBSERVABLE, indépendant de
                    leur identité nominale.
```
La représentation utilisée pour comparer deux arêtes ne peut donc pas
être leur forme locale nue — elle doit capturer un comportement
(contextes de composition, autres relations avec lesquelles l'opérateur
apparaît, etc.). La construction exacte de cette représentation reste
délibérément non résolue par le cadrage — question centrale déférée au
futur protocole v0.1.

### Point ajouté, plus fondamental que les 3 questions ouvertes de la v0.1
Critère d'identifiabilité préalable : il faut démontrer, avant toute
exécution, qu'un corpus donné contient réellement un signal structurel
distinguant les classes. Vocabulaire de sortie enrichi en conséquence :
`DISCOVERED` / `AMBIGUOUS` / `INSUFFICIENT_STRUCTURAL_INFORMATION` /
`REJECTED` — un résultat `INSUFFICIENT_STRUCTURAL_INFORMATION` est un
résultat scientifique légitime, jamais un bug à corriger.

### Les 3 questions de la v0.1, tranchées explicitement par le porteur du projet
1. **Masquage** : identité d'opérateur masquée INDIVIDUELLEMENT par
   observation (`OP#001`, `OP#002`, ... jamais partagée entre
   observations de la même relation d'origine — sinon le masquage
   laisserait filtrer l'information à découvrir), vérité terrain cachée
   réservée à l'évaluation post-hoc. Explicitement rejeté : un
   opérateur `UNKNOWN_RELATION` unique et partagé (donnerait une
   catégorie déjà prête).
2. **Pool** : sélection différée. P4-U.2.1 se limite à un pool défini
   par des critères STRUCTURELS objectifs uniquement (observation
   binaire valide, profondeur admissible) — jamais une sélection
   sémantique/intelligente, différée à un incrément ultérieur, pour ne
   jamais mélanger « quelles arêtes comparer » et « lesquelles
   représentent la même relation ».
3. **`e20d_operation_synthesis_v0_1.py`** : PAS réactivé — son contrat
   (IDENTIFIED_EXISTING/CREATED_NEW/AMBIGUOUS) synthétise une opération
   à partir d'une relation DÉJÀ découverte, un problème différent.
   Nouveau contrat dédié retenu : `RELATION_HYPOTHESIS`
   (hypothesis_id, member_edge_ids, structural_signature, support,
   contradiction_support, status=UNKNOWN par défaut, provenance) —
   jamais de promotion automatique « cluster cohérent ⇒ relation
   identifiée ».

### Risque `O(n²)` (similarité par paire) — confirmé, optimisation différée
Ordre de résolution retenu explicitement : (1) représentation
invariante-à-l'identité, (2) identifiabilité, (3) modèle nul, (4)
clusterisation, (5) seulement ensuite optimisation du coût — ne jamais
optimiser un objet scientifique mal défini.

### Document produit
`documentation/P4U2_Autonomous_Relation_Discovery_V0_2.md` remplace
intégralement la v0.1 (bandeau `SUPERSEDED` ajouté à la v0.1, même
convention que pour P4-U.1). Objectif retenu et gelé : « P4-U.2 —
Autonomous Structural Relation Discovery ». Verrou scientifique
central explicité : P4-U.2 doit démontrer qu'une relation inconnue est
IDENTIFIABLE à partir de sa structure observable — pas simplement
qu'un algorithme sait clusteriser des objets auxquels on a
artificiellement retiré leur nom.

### État après cette entrée
```text
P4-U.2 v0.2 : CADRÉ (avec correction méthodologique), TOUJOURS PAS
              DE PROTOCOLE, TOUJOURS AUCUN CODE
Question centrale non résolue, déférée au futur protocole v0.1 :
  quelle représentation structurelle capture un comportement
  d'opérateur indépendant de son identité nominale ?
```

---

## 2026-09-23 — Cadrage P4-U.2 v0.3 : Gate I formelle, hiérarchie structure/hypothèse/relation, exclusions gelées

### Raffinements apportés par la seconde revue du porteur du projet
1. **Gate I — Identifiability**, élevée du statut de simple critère
   (v0.2) à celui de gate formelle et nommée, au même rang que les
   Gates A/B/C de P4-U.1 — vérifiée AVANT toute tentative de
   regroupement. `Gate I = FAIL` produit obligatoirement
   `INSUFFICIENT_STRUCTURAL_INFORMATION`, jamais un échec à corriger.
   Règle ajoutée : un cas de contrôle délibérément non identifiable
   doit exister dans tout futur benchmark verrouillé (même rôle que U3
   pour P4-U.1) — sinon risque de démonstration circulaire.
2. **Hiérarchie structure/hypothèse/relation, jamais confondues** :
   correction de la formulation « plusieurs observations → hypothèse
   d'une relation inconnue » (v0.2), jugée trop directe. Chaîne
   obligatoire en trois étapes distinctes :
   ```text
   similarité -> structure commune -> hypothèse de classe structurale
   -> validation -> ÉVENTUELLE relation découverte
   ```
   Une classe structurale validée n'est PAS encore une relation ; la
   « relation découverte » est une interprétation opérationnelle
   produite séparément, jamais un renommage automatique de
   l'hypothèse. `RELATION_HYPOTHESIS` (v0.2) renommé
   `STRUCTURAL_CLASS_HYPOTHESIS` en conséquence — aucun champ
   `relation_name`/`relation_id` sur cet objet, délibérément.
3. **Exclusions gelées en liste explicite** (remplace la formulation
   dispersée de la v0.2) : sélection intelligente du pool,
   dictionnaire sémantique, relation cible fournie, ancrage à la
   vérité terrain pendant la découverte, synthèse d'opération
   (`e20d_operation_synthesis_v0_1.py`), et — ajout explicite — la
   découverte de composition P4-U.1 elle-même (orthogonale, jamais
   tentée simultanément).
4. **Modèle nul** : principe précisé — casser la cohérence
   inter-observations qui permet le regroupement, tout en conservant
   les propriétés marginales pertinentes du corpus. Reconnu
   explicitement comme un risque accru par rapport à P4-U.1 : la
   statistique de cohésion à comparer au modèle nul reste entièrement
   à déterminer, pas une simple adaptation du maximum-statistique déjà
   éprouvé pour les squelettes de composition.

### Document produit
`documentation/P4U2_Autonomous_Relation_Discovery_V0_3.md` remplace
intégralement la v0.2 (bandeau `SUPERSEDED` ajouté à la v0.2). La
reformulation de l'objectif et les décisions Q1/Q2/Q3 de la v0.2
restent valides, reprises sans changement.

### Prochaine étape explicitement demandée par le porteur du projet
Avant tout protocole expérimental : investigation empirique directe du
dépôt existant pour déterminer quelles informations structurelles
peuvent réellement différencier deux opérateurs opaques — en
s'appuyant uniquement sur les primitives K3 déjà existantes
(`discover_paths`, `group_by_skeleton`, `ref_jaccard`/
`structural_similarity`, `path_properties`), sans en inventer une
nouvelle avant d'avoir vérifié ce qui est déjà mesurable. Un exercice
de lecture/mesure directe, pas encore une implémentation de P4-U.2.

### État après cette entrée
```text
P4-U.2 v0.3 : CADRÉ, TOUJOURS AUCUN CODE, TOUJOURS AUCUN PROTOCOLE
Prochaine action : investigation empirique des candidats de
représentation structurelle (Sec. 10 de la v0.3)
```

---

## 2026-09-23 — Investigation empirique des candidats de représentation structurelle pour P4-U.2

### Méthode
Corpus jouets construits avec des relations cachées connues du script
de test uniquement, opérateurs masqués INDIVIDUELLEMENT (méthode gelée,
v0.3 Sec. 5), signatures calculées uniquement à partir du graphe
masqué, avec les primitives déjà existantes de `kernel2.py`/
`e20d_rationalization_v0_1.py`, sans aucune modification. Vérité
terrain utilisée seulement après coup pour juger la séparation.

### Candidat 1 — `path_properties().branching_at_start/end` (kernel2.py, inchangé)
- Test A (rôles topologiques réellement différents, hub à fort éventail
  vs relation 1-à-1) : séparation parfaite par `branching_at_start`
  seul (6 contre 1).
- Test B (même degré de départ, continuation avale différente) :
  séparation parfaite par `branching_at_end` seul (2 contre 1), alors
  que `branching_at_start` est identique dans les deux groupes.
- Test C, cas limite délibéré (rôle topologique local RIGOUREUSEMENT
  identique dans les deux groupes) : signatures identiques confirmées
  — **ce candidat ne peut pas, par construction, distinguer deux
  relations partageant le même rôle local**. Exactement la frontière
  que Gate I (v0.3 Sec. 2) doit détecter et rapporter comme
  `INSUFFICIENT_STRUCTURAL_INFORMATION`, pas un défaut du candidat.

### Candidat 2 — `ref_jaccard`/`structural_similarity` (e20d_rationalization_v0_1.py, vivant, inchangé)
- Sur des entités totalement disjointes (style de corpus déjà utilisé
  par P4-U.1) : aucun signal (0.0 dans tous les cas), qu'il s'agisse de
  la même relation cachée ou non.
- **Erreur de méthode trouvée et corrigée avant de conclure** : un
  premier essai avait laissé les opérateurs NON masqués par erreur,
  produisant un faux signal (0.2) dû au partage littéral de la
  référence d'opérateur, pas à une similarité structurelle réelle —
  refait avec le masquage correct, le signal disparaît entièrement.
- Sur des entités PARTAGÉES (un « hub » réutilisé) : signal non nul
  (0.2), mais réserve méthodologique importante confirmée : ce signal
  mesure la CO-OCCURRENCE D'ENTITÉ, pas la similarité de TYPE de
  relation — deux faits impliquant la même entité mais de relations
  réellement différentes recevraient le même score. **`ref_jaccard` ne
  doit donc jamais être réutilisé tel quel comme signature de
  similarité de relation dans un futur protocole.**

### Document produit
`documentation/P4U2_Structural_Signature_Investigation_2026-09-23.md`
— détail complet, résultats bruts, synthèse. Section 11 ajoutée à
`documentation/P4U2_Autonomous_Relation_Discovery_V0_3.md` pointant
vers ce résultat (le cadrage v0.3 lui-même n'est pas modifié dans ses
décisions — cette investigation nourrit la question ouverte de la
Sec. 8 étape 1, elle ne la referme pas).

### Conclusion utile pour le futur protocole
Aucune nouvelle primitive nécessaire : la représentation manquante
peut vraisemblablement se construire en combinant `path_properties`/
`discover_paths` à plusieurs profondeurs déjà existantes. La
démonstration d'identifiabilité (Gate I) d'un futur cas verrouillé
devrait concrètement consister à vérifier que les relations cachées du
corpus produisent des signatures distinctes par cette combinaison — pas
une assertion abstraite.

### État après cette entrée
```text
P4-U.2 : cadrage v0.3 + investigation empirique complétée
Toujours aucun protocole verrouillé, aucun code P4-U.2
Prochaine étape : écriture du protocole formel v0.1, informée par
cette investigation
```

---

## 2026-09-23 — Expérience d'identifiabilité sur une signature candidate multi-profondeur

### Étape demandée explicitement par le porteur du projet
Séquence fixée avant tout protocole : investigation (faite) → signature
candidate → **expérience d'identifiabilité (cette entrée)** → protocole
P4-U.2 v0.1 → modèle nul → benchmark aveugle. Le commit précédent
(`b1f58bf`) devait être considéré comme la clôture de l'enquête
exploratoire, pas une validation de l'algorithme — cette expérience
teste une hypothèse de représentation, pas un résultat déjà acquis.

### Signature testée (hypothèse, jamais présentée comme acquise)
Combinaison profondeurs 1/2/3 via `discover_paths` (INCHANGÉ) : compte
de chemins par profondeur + séquences de direction observées, filtrés
aux chemins dont le premier pas correspond à l'arête masquée étudiée.

### Trois corpus, trois verdicts
1. `SEPARABLE` confirmé (signal net, continuation systématique contre
   absence systématique).
2. `INSUFFICIENT_STRUCTURAL_INFORMATION` confirmé, y compris par
   vérification indépendante au niveau du groupe (100 % de
   continuation des deux côtés — signal authentiquement nul).
3. **Constat le plus important de cette expérience** : un chevauchement
   partiel (80 % contre 20 % de continuation) a d'abord reçu un verdict
   FAUX (`INSUFFICIENT`) par une vérification naïve d'égalité exacte de
   signature par observation. Corrigé avant de conclure : un test
   statistique à deux proportions au niveau du groupe révèle un signal
   réel et significatif (z=3,79, p<0,05) — la vérification naïve
   confondait « aucun signal » et « signal réel mais bruité ».

### Conséquence directe pour le futur protocole
Gate I ne peut pas se limiter à une égalité de signature par
observation — elle doit intégrer une comparaison statistique de groupe
face à un modèle nul, dès sa première version. Ce n'est plus une
anticipation théorique (déjà notée en v0.3 Sec. 7) mais une nécessité
démontrée par exécution directe.

### Document produit
`documentation/P4U2_Identifiability_Experiment_2026-09-23.md`. Sec. 12
ajoutée à
`documentation/P4U2_Autonomous_Relation_Discovery_V0_3.md` pointant
vers ce résultat (les décisions déjà gelées de la v0.3 restent
inchangées).

### État après cette entrée
```text
P4-U.2 : cadrage v0.3 + investigation + expérience d'identifiabilité
         complétées
Toujours aucun protocole verrouillé, aucun code P4-U.2
Prochaine étape : écriture du protocole formel P4-U.2 v0.1, avec Gate I
intégrant une comparaison statistique de groupe dès sa première version
```

---

## 2026-09-23 — Protocole P4-U.2 v0.1 écrit — toujours aucun code

### Demande explicite
« Écrivez le protocole P4-U.2 v0.1 » — dernière étape de la séquence
fixée par le porteur du projet (cadrage → investigation → expérience
d'identifiabilité → protocole).

### Document produit
`documentation/P4U2_Protocol_V0_1.md` — nouveau document, distinct de
la lignée de cadrage (`P4U2_Autonomous_Relation_Discovery_V0_*.md`),
même convention de séparation que pour P4-T (document de conception vs
protocole de validation tierce, deux lignées distinctes). Formalise,
sans les rouvrir, toutes les décisions déjà gelées par la v0.3 du
cadrage :
- Objectif, entrée/interdits, masquage individuel, portée du pool
  P4-U.2.1, exclusions — repris tels quels.
- Signature structurelle candidate (profondeurs 1/2/3 via
  `discover_paths`, INCHANGÉ) — retenue comme hypothèse de travail pour
  le premier benchmark, explicitement pas comme définition close ;
  révision du protocole prévue si le futur benchmark la montre
  insuffisante.
- **Gate I formalisée avec le changement non négociable imposé par
  l'expérience d'identifiabilité** : comparaison d'une statistique de
  COHÉSION DE GROUPE contre un modèle nul (N_null réplicats,
  percentile, correction multi-comparaisons si plusieurs candidats) —
  jamais une égalité de signature par observation, avec la preuve
  empirique déjà établie (z=3,79 sur le cas de chevauchement partiel)
  citée comme justification directe.
- **Gate H, nouvelle, distincte de Gate I** : valide qu'une
  `STRUCTURAL_CLASS_HYPOTHESIS` n'est pas contredite (support vs
  contradiction_support, même discipline que `Hypothesis.status` de
  kernel2.py) — jamais fusionnée avec la significativité statistique de
  Gate I.
- Modèle nul : principe gelé repris, mais **la procédure exacte de
  randomisation reste explicitement non résolue** — contrairement à
  P4-U.1, aucun pool par étiquette n'existe à permuter puisque les
  opérateurs sont masqués individuellement ; deux pistes proposées
  (permuter le graphe entier vs permuter l'assignation aux candidats),
  non tranchées, à décider par calibration.
- **Quatre cas verrouillés spécifiés** (V1-V4, un par résultat de
  sortie possible) : V1 (régularité nette, DISCOVERED attendu), V2
  (rôle topologique rigoureusement identique, INSUFFICIENT attendu),
  V3 (contrôle nul pur), et **V4, ajouté spécifiquement** — reproduction
  exacte du cas de chevauchement partiel ayant révélé la faille
  méthodologique de l'expérience d'identifiabilité, pour garantir que
  toute implémentation future ne régresse jamais vers la vérification
  naïve déjà prouvée fausse.
- Checklist de pré-enregistrement (7 points) — toutes les valeurs
  numériques explicitement marquées « À FIXER », jamais avant
  calibration, jamais après avoir vu un résultat de holdout.

### État après cette entrée
```text
P4-U.2 : PROTOCOLE v0.1 ÉCRIT ET GELÉ
Toujours aucun code de production, aucune valeur numérique fixée,
aucun benchmark verrouillé construit
Prochaine étape : calibration jetable des valeurs numériques
manquantes (Sec. 13 du protocole), jamais sur le futur benchmark
verrouillé lui-même
```

---

## 2026-09-23 — P4-U.2 : calibration jetable exécutée (statistique de cohésion × modèle nul × Gate H) — résultat décisif sur le modèle nul, toujours aucun code

Suite au protocole v0.1 gelé (entrée précédente), exécution de la
calibration jetable demandée explicitement par le porteur du projet sur
les trois verrous prioritaires (jamais sur le futur benchmark verrouillé
lui-même — script jetable, non committé, exécuté depuis le scratchpad de
session, même discipline que `scripts/_scratch_p4u1_calibration.py` pour
P4-U.1). Rapport complet :
`documentation/P4U2_Calibration_Experiment_2026-09-23.md`.

- **Modèle nul — résultat décisif, empiriquement démontré, pas
  théorique** : sur un corpus TWIN construit pour être rigoureusement
  homogène (4 cycles orientés disjoints, toute arête a une signature
  strictement identique), `group-resample-only` (topologie réelle fixe,
  ré-échantillonnage de l'appartenance au groupe) répond correctement
  « aucune distinction » (z=0.0 exact, les trois statistiques de
  cohésion). `topology-only` (casser la topologie de tout le graphe),
  et `combined` qui en hérite, déclarent au contraire une significativité
  massive (z jusqu'à 31,7) — un **faux positif net et démontré** : casser
  la topologie détruit la régularité globale de TOUT le graphe, pas
  seulement celle du groupe candidat, donc mesure une question
  différente de celle posée par Gate I. **Conclusion directe : le modèle
  nul principal de Gate I doit être construit autour du
  ré-échantillonnage de l'appartenance au groupe, jamais autour de la
  seule cassure de topologie globale.**
- **Statistique de cohésion — pas encore tranché** : sur le cas facile
  (SEP, signal net), les trois candidats (`Cohesion_A` proportion de
  traits communs, `Cohesion_B` distance intra-groupe, `Cohesion_C`
  concentration multi-profondeur) détectent tous le signal sans
  ambiguïté. Sur le cas difficile (PARTIAL, reproduction exacte du
  Corpus 3 de l'expérience d'identifiabilité, 80 %/20 %), sous le modèle
  nul jugé valide (`group-resample-only`), les trois atterrissent au
  même niveau, juste sous le seuil conventionnel de 95 %/z=1,96 — un
  résultat honnête de puissance limitée à cette taille d'échantillon
  (groupe de 20, N_null=200), pas un échec de calibration. Aucune des
  trois n'est éliminée ni retenue seule.
- **Gate H — pilote `contradiction_support`** : comportement linéaire et
  prévisible confirmé (0 %, 5 %, 15 %, 30 % de membres remplacés →
  `contradiction_support` = 0.000/0.050/0.150/0.300 exactement). Fourchette
  provisoire de tolérance `τ` proposée entre 0.10 et 0.15 — un jugement
  de calibration, pas une valeur tranchée par ce seul pilote.
- **Deux erreurs de méthode trouvées et corrigées avant toute
  conclusion, pas après** (discipline déjà appliquée aux investigations
  précédentes) : (1) une première construction de TWIN mélangeait deux
  rôles structurels différents dans le pool de ré-échantillonnage,
  refaisant sans le vouloir le même test que SEP plutôt qu'un vrai cas
  nul — corrigée par la reconstruction en cycles rigoureusement
  homogènes ; (2) un percentile en convention "<=" saturait à 100 % sur
  un cas nul parfaitement dégénéré (TWIN/group-resample, z=0.0 réel) —
  corrigé par une convention mid-rank standard.
- **Explicitement non testé dans cette calibration** : la correction
  multi-comparaisons (protocole Sec. 13, point 6) — cette calibration
  n'a évalué qu'un seul groupe candidat à la fois, jamais le scénario
  réaliste à plusieurs candidats simultanés (l'équivalent direct du
  max-statistic de P4-U.1). Reste entièrement à faire avant tout gel.

### État après cette entrée
```text
P4-U.2 : PROTOCOLE v0.1 GELÉ, CALIBRATION JETABLE #1 EXÉCUTÉE
Acquis : modèle nul principal = ré-échantillonnage de groupe (topologie
fixe), démontré empiriquement, pas seulement argumenté
Ouvert : choix final de la statistique de cohésion (les 3 sont à égalité
sur le cas difficile), N_null/percentile à geler, correction
multi-comparaisons (non testée), tolérance Gate H exacte
Toujours aucun code de production, aucune valeur numérique gelée,
aucun benchmark verrouillé construit
Prochaine étape : décision du porteur du projet -- gel numérique, ou
prolongation de la calibration (statistique combinée / correction
multi-comparaisons / tolérance Gate H)
```

---

## 2026-09-24 — P4-U.2 : calibration jetable, campagne 2 (puissance de Gate I, correction multi-comparaisons démontrée nécessaire, Gate H sweep fin) — toujours aucun code

Suite directe à la critique du porteur du projet sur `854b32e` : ce
premier résultat n'était pas suffisant pour un gel, ayant isolé
`group-resample-only` sur un seul corpus (TWIN) et laissé ouvertes trois
questions. Campagne 2 exécutée, script jetable non committé (même
discipline). Rapport complet :
`documentation/P4U2_Calibration_Campaign2_2026-09-24.md`.

- **Puissance de Gate I — question centrale de la campagne 1 tranchée
  par exécution directe** : balayage de force de signal (p_group de 0.5
  à 1.0, taille fixe 20) donne une croissance strictement monotone du
  z-score pour les trois statistiques de cohésion, sans irrégularité.
  Balayage de taille d'échantillon (signal fixe 80/20, taille de 10 à
  80) montre qu'augmenter uniquement la taille augmente nettement la
  puissance (dès taille 40, le signal 80/20 franchit largement le seuil
  conventionnel). Balayage de `N_null` (200 à 2000, signal et taille
  fixes) montre un percentile/z stable. **Conclusion directe : le
  résultat limite du cas PARTIAL en campagne 1 est un effet de TAILLE
  D'ÉCHANTILLON démontré, pas un défaut de statistique de cohésion ni un
  modèle nul trop conservateur** — les deux autres hypothèses sont
  explicitement écartées par exécution, pas par supposition.
- **Correction multi-comparaisons — testée pour la première fois,
  démontrée nécessaire et suffisante** : corpus à 1 vrai groupe (90 % de
  prolongement) + 9 candidats sans signal réel, tirés d'un fond
  purement aléatoire. Le seuil corrigé (95ᵉ percentile du maximum de la
  statistique sur 10 groupes simultanés, discipline reprise de
  P4-U.1 mais testée ici plutôt que supposée acquise) donne **0/9 faux
  positifs pour les trois statistiques**, tout en détectant
  correctement le vrai groupe. **Sans correction, `Cohesion_A` laisse
  passer 3 candidats sur 9 sans aucun signal réel** (33 % de fausse
  découverte sur cette exécution) — un risque concret et démontré,
  écarté uniquement par la correction. Réserve : une seule graine
  aléatoire, pas encore une calibration multi-graines.
- **Gate H — sweep fin, comportement confirmé mais question du porteur
  du projet toujours non résolue** : remplacement par pas de 5 % de 0 %
  à 50 % confirme la linéarité déjà observée en campagne 1, sans
  irrégularité. **Ce balayage ne distingue toujours pas les deux
  frontières demandées séparément** (bruit de mesure naturel sur un
  groupe réellement cohérent vs rejet d'un groupe manifestement
  hétérogène) — il ne fait varier qu'une seule dimension (fraction
  injectée). Explicitement laissé ouvert, pas présenté comme résolu.
- **Modèle nul `group-resample-only`** : confirmé sur un balayage complet
  de force de signal et de taille d'échantillon, pas seulement sur
  TWIN — l'évidence en sa faveur s'élargit sans se répéter à l'identique,
  toujours pas formellement gelé.

### État après cette entrée
```text
P4-U.2 : PROTOCOLE v0.1 GELÉ, CALIBRATION #1 ET #2 EXÉCUTÉES
Acquis : puissance de Gate I comprise (effet de taille d'échantillon,
pas de statistique ni de null) ; correction multi-comparaisons
démontrée nécessaire et suffisante (0/9 vs jusqu'à 3/9 faux positifs)
Ouvert : taille du futur benchmark verrouillé (tension conception vs
puissance), N_null/percentile à formellement geler, frontière
d'acceptation de Gate H face au bruit naturel (corpus dédié requis),
choix final de la statistique de cohésion, calibration multi-graines
de la correction multi-comparaisons
Toujours aucun code de production, aucune valeur numérique gelée,
aucun benchmark verrouillé construit
Prochaine étape : décision du porteur du projet
```

---

## 2026-09-24 — P4-U.2 : calibration jetable, campagne 3 (Gate H bruit vs hétérogénéité, robustesse multi-graines, taille finale) — toujours aucun code

Exécute la campagne ciblée en trois points explicitement demandée par le
porteur du projet après lecture de la campagne 2 (`97981f0`). Script
jetable non committé, même discipline. Rapport complet :
`documentation/P4U2_Calibration_Campaign3_2026-09-24.md`.

- **Gate H — résultat décisif, généralisation nécessaire de
  `contradiction_support`** : deux corpus construits pour représenter
  deux CAUSES différentes du même désaccord — bruit naturel (une seule
  relation réelle, échecs idiosyncrasiques par tirage de Bernoulli,
  30 répétitions par niveau) vs hétérogénéité manifeste (deux vraies
  classes internes uniformes mélangées). **À un niveau de
  `contradiction_support` quasiment identique (~0,10), les deux causes
  sont numériquement indiscernables sur cette seule mesure (0,105 vs
  0,100) mais nettement séparées sur la cohésion interne du sous-groupe
  dissident (0,537 vs 1,000 exactement)** — le bruit naturel produit une
  minorité dispersée qui se dégrade encore avec le niveau de bruit
  (0,772 → 0,406), l'hétérogénéité manifeste produit systématiquement
  une cohésion de minorité parfaite. **Conséquence proposée, pas encore
  endossée** : Gate H devrait exiger conjointement `contradiction_support`
  au-dessus d'un seuil ET une cohésion interne élevée de la minorité —
  un raffinement issu de cette calibration, à valider explicitement par
  le porteur du projet avant toute écriture dans le protocole.
- **Correction multi-comparaisons — robustesse confirmée sur 20
  graines**, répétant le scénario 1-vrai-groupe + 9-candidats-nuls de la
  campagne 2 : taux de faux positifs corrigé toujours nettement sous le
  seuil nominal de 5 % pour les trois statistiques (1,7 %/0,6 %/0,0 %),
  vrai signal détecté sur les 20 graines et les trois statistiques sans
  exception. `Cohesion_A` reste, sur 20 graines, la plus vulnérable sans
  correction (16,7 % en moyenne — même ordre de grandeur que le 33 % à
  une seule graine de la campagne 2, pas un hasard de graine).
- **Taille finale de groupe — proposition concrète et justifiée** :
  balayage de taille (20 à 60) sur V1 (p=0,9) et V4/PARTIAL (p=0,8)
  simultanément. `group_size=40` est la plus petite taille testée où le
  cas difficile franchit le seuil conventionnel avec une marge réelle
  (z=2,18, pas seulement 1,96) pour les trois statistiques, tandis que
  V1 reste très largement significatif et le contrôle négatif (p=0,5)
  reste toujours nettement non significatif sans dérive avec la taille.
  Les tailles 20/30 (utilisées implicitement en campagnes 1-2) sont
  maintenant démontrées insuffisantes pour éloigner V4 de la frontière
  de puissance.

### État après cette entrée
```text
P4-U.2 : PROTOCOLE v0.1 GELÉ, CALIBRATION #1/#2/#3 EXÉCUTÉES
Acquis : correction multi-comparaisons robuste sur 20 graines ; taille
de groupe proposée (40) avec marge de puissance démontrée ; limite de
contradiction_support seul démontrée pour Gate H, avec un raffinement
proposé (cohésion de minorité) non encore endossé
Ouvert : endosser ou rejeter le raffinement de Gate H, geler ses seuils
numériques, geler formellement group_size=40, choix final de la
statistique de cohésion
Toujours aucun code de production, aucune valeur numérique gelée,
aucun benchmark verrouillé construit
Prochaine étape : décision du porteur du projet
```

---

## 2026-09-24 — P4-U.2 : mini-campagne Gate H (campagne 4) — résultat négatif honnête sur les seuils fixes, architecture null-comparison proposée à la place

Exécute la mini-campagne Gate H exclusivement demandée par le porteur du
projet après la campagne 3 (`38b1f74`) : trois décisions demandées (règle
de partition, seuil de contradiction, seuil de cohésion), sans choisir
arbitrairement des nombres ronds. Rapport complet :
`documentation/P4U2_Calibration_Campaign4_2026-09-24.md`.

- **Règle R1 (partition par vote majoritaire sur un vecteur de traits
  déjà gelé, jamais recherché)** : spécifiée et utilisée partout, sans
  exception — répond directement au risque de circularité soulevé par le
  porteur du projet (aucune optimisation de partition n'a lieu).
- **Résultat inattendu, trouvé avant toute conclusion** : à petits
  effectifs de dissidents (2 à 6), le bruit naturel peut, par pure
  coïncidence, atteindre une cohésion de minorité parfaite (1,000) —
  le modèle de bruit synthétique n'a que trois modes d'échec discrets.
  Conséquence vérifiée par exécution : `max(cohésion sous bruit) = 1,0000`
  touche exactement `min(cohésion sous hétérogénéité) = 1,0000` sur la
  grille testée — **aucun seuil fixe unique ne sépare les deux causes.**
- **Une comparaison à un modèle nul (à la Gate I) a été testée
  directement, pas supposée** : à petits effectifs (k≈5-6), elle NE
  RÉSOUT PAS le problème (coïncidence de bruit à percentile 97,2 contre
  99,0 pour la vraie hétérogénéité — presque indiscernables). À grands
  effectifs (k≈18), elle fonctionne parfaitement (0 % de faux positifs
  sur 20 répétitions de bruit, contre percentile 100 %/z=14,8 pour
  l'hétérogénéité). **La frontière de fiabilité a été localisée entre
  k≈7 et k≈10** (taux de faux positifs 7,1 %/6,7 % en dessous, 0,0 % à
  partir de k≈9,7).
- **Réponse réelle aux trois décisions demandées** : la décision 1 est
  résolue (Règle R1). Les décisions 2 et 3 ne sont PAS deux nombres
  isolés — reformulées en un plancher d'effectif absolu de dissidents
  (~9-10, pas une fraction fixe) et une comparaison à un modèle nul
  (pas un seuil fixe sur la cohésion, prouvé dangereux). **Conséquence
  d'architecture** : Gate H devrait être structurée comme Gate I
  (statistique de groupe contre modèle nul, avec un plancher d'effectif
  sous lequel elle échoue proprement en INSUFFICIENT_STRUCTURAL_INFORMATION),
  pas avec des seuils fixes — proposition issue de cette calibration, pas
  encore endossée.

### État après cette entrée
```text
P4-U.2 : PROTOCOLE v0.1 GELÉ, CALIBRATION #1/#2/#3/#4 EXÉCUTÉES
Acquis : règle de partition de Gate H résolue (R1) ; seuils fixes sur la
cohésion de minorité démontrés dangereux ; comparaison à un modèle nul
validée au-delà d'un plancher d'effectif (~9-10), pas en-deçà
Ouvert : localisation précise du plancher, protocole exact du modèle nul
pour ce sous-test, robustesse à d'autres modèles de bruit, endossement
de l'architecture proposée pour Gate H
Toujours aucun code de production, aucune valeur numérique gelée,
aucun benchmark verrouillé construit
Prochaine étape : décision du porteur du projet
```
