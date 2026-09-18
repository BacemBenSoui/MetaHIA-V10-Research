# MetaHIA — M7 — Empirical LLM Loop v0.1 (Fact Proposer scope)

## 1. Statut

- M1–M6 : voir `documentation/MetaHIA_M6_Structural_Learning_V0_1.md` (M6 = `VALIDATED`).
- M7 : **VALIDATED** (2026-09-18, clôturé explicitement par le porteur du projet sur la base
  de deux exécutions externes indépendantes — voir Sec. 10 et `JOURNAL_DE_BORD.md`). Portée
  "témoin LLM" (fact-proposer) uniquement ; le parseur texte libre → structure reste un
  chantier séparé, non commencé.
- Kernel `kernel2.py` : inchangé.

## 2. Portée choisie (décidée explicitement avant implémentation, 2026-09-17)

Deux décisions prises avec l'utilisateur avant tout code :

1. **Fournisseur LLM : Ollama local**, backend propre à ce dépôt
   (`m7_llm_fact_proposer_v0_1.py`), sans lien avec `llm/ollama_backend.py` du dépôt de
   production — respecte la frontière de zéro-couplage déjà posée. Aucune clé API, aucun
   coût, aucun secret à gérer.
2. **Le LLM comme témoin indépendant sur le corpus déjà structuré** — même rôle que
   `family_tree_verification_claims_v0_1.json` pour M6 v0.2, pas un parseur texte→structure
   (élément resté explicitement différé par le roadmap).

Le principe d'architecture du roadmap est respecté littéralement : *« Le LLM reste une
branche d'observation/production ; il n'est pas le fondement du raisonnement structurel. »*
Le LLM ne décide jamais `SUPPORTED`/`CONTRADICTED` lui-même — il fournit seulement une preuve
`GROUNDED_ANALOGY` (jamais `GROUNDED_DIRECT`, jamais `UNGROUNDED_HUMAN`) à la même machinerie
réelle `acquire_cold_start()`/évaluateur que M4/M6.

## 3. Mécanisme

```text
kernel2 : rejeu contre evidence_facts (disjoint de discovery_facts, inchangé)
        -> une prédiction structurelle réelle (start, opérateur) -> predicted_object
                ↓
LLM local (Ollama), question ouverte SANS révéler predicted_object :
« Par analogie avec les faits suivants [...], quelle est la valeur la plus
plausible de l'objet dans OPERATEUR(sujet, ?) ? »
                ↓
comparaison mécanique : proposal.object == predicted_object ?
                ↓
égal -> preuve SUPPORT · différent -> preuve CHALLENGE · réponse inexploitable -> aucune preuve
```

**Bug trouvé et corrigé avant tout résultat retenu** : la première version du prompt
révélait `predicted_object` directement dans l'instruction ET dans l'exemple de format JSON
attendu — le LLM se contentait de le recopier. Résultat obtenu (trompeur) : 16/16
`SUPPORTED`. Corrigé en retirant toute mention de la valeur réelle du prompt ; le LLM ne
reçoit que le sujet, l'opérateur, et les faits de découverte comme contexte — jamais la
réponse attendue. Test de non-régression dédié :
`test_predicted_object_is_never_present_in_the_prompt`.

## 4. Résultat réel (corpus v0.2, `llama3.2:latest`, exécution du 2026-09-17)

Après correction du prompt : **16/16 `CONTRADICTED`** — diversité nulle, mais dans l'autre
sens que le bug initial, et pour une raison réelle et vérifiée, pas un artefact.

Exemple tracé directement : pour `MERE_DE(Alice, ?)`, le modèle répond `"David"` (le nom qui
apparaît dans le tout premier fait du contexte, `MERE_DE(Amanda, David)`) au lieu de la vraie
réponse `"Hugo"`. Constat : **`Alice` n'apparaît jamais comme source de `MERE_DE` dans les
`discovery_facts`** — le modèle n'a structurellement aucune base pour inférer cette relation
spécifique, et semble reproduire un nom saillant du contexte plutôt que raisonner par
analogie. Ce n'est pas un défaut du mécanisme (qui est réel, non circulaire, vérifié par
`test_predicted_object_is_never_present_in_the_prompt`) — c'est une limite empirique réelle
du petit modèle local sur cette tâche à livre fermé, sur ce corpus précis.

**Ce résultat n'est délibérément pas figé dans un test avec une valeur exacte attendue** —
contrairement à tous les mécanismes M6 (déterministes), un appel LLM réel n'est pas
reproductible à l'identique (modèle, température, matériel). `tests/test_m7_live_ollama_demo_v0_1.py`
n'affirme que les propriétés structurelles garanties (exécution réelle via
`acquire_cold_start()`, provenance `GROUNDED_ANALOGY`, exclusion honnête), jamais une
distribution d'issue précise. Ce test est **sauté proprement** (`pytest.mark.skipif`) sur
tout environnement sans Ollama accessible — la suite principale reste portable, comme
confirmé par les deux tiers externes de M6 qui n'avaient probablement pas Ollama installé.

## 5. Repli LAN sur le serveur sandbox (addendum 2026-09-17)

Configuré à la demande explicite : si l'instance Ollama locale est injoignable, l'appel
retombe sur le serveur sandbox du LAN (`192.168.1.11:11434`, confirmé actif — modèles
`gpt-oss:20b`, `deepseek-coder-v2:16b`, `qwen2.5-coder:3b`, `qwen2.5-coder:7b`). Modèle de
repli retenu : `qwen2.5-coder:7b`, cohérent avec le précédent déjà établi dans ce projet
(pipeline WP18 en production, entièrement sur `qwen2.5-coder`). Ceci reste une configuration
de point de terminaison réseau, pas une dépendance de code au dépôt de production — aucun
import de `llm/ollama_backend.py`.

**Le repli ne se déclenche que sur injoignabilité réelle** (échec de connexion), jamais
simplement parce que le modèle local répond de façon inexploitable — ce cas reste « aucune
proposition » du modèle local, pas une invitation à interroger un second modèle différent.

**Deux bugs réels trouvés et corrigés pendant la configuration, avant de garder un
résultat** :
1. Le premier essai réel avec le local coupé a échoué avec un timeout après 30 s sur le
   serveur LAN — pas un problème réseau (`/api/tags` répondait en 78 ms) mais un chargement à
   froid d'un modèle de 7B sur du matériel partagé. Corrigé par un délai de repli plus généreux
   (`fallback_timeout=90s` contre `primary_timeout=30s`), documenté avec la mesure réelle qui a
   motivé ce choix, pas une valeur arbitraire.
2. Une fois le repli déclenché avec succès, `LLMProposal.model` indiquait encore le modèle
   **local demandé** (`llama3.2:latest`) au lieu du modèle **qui avait réellement répondu**
   (`qwen2.5-coder:7b`) — une mauvaise attribution de provenance. Corrigé en faisant retourner
   à `ollama_generate_json_with_fallback()` le couple `(réponse, modèle_utilisé)` plutôt qu'un
   simple JSON, éliminant toute duplication de la logique de repli entre cette fonction et
   `propose_relation_llm()`. Testé bout en bout, y compris avec le local réellement coupé et le
   repli réel confirmant `model='qwen2.5-coder:7b'`.

Un troisième ajustement, mineur : la garde de saut du test de démonstration live vérifiait
l'accessibilité via un appel `/api/generate` complet (nécessite un modèle chargé) avec
seulement 5 s de délai — donnait un faux « injoignable » juste après un redémarrage du serveur
local. Corrigé en vérifiant `/api/tags` (léger, ne charge aucun modèle) à la place.

## 6. Intégration au pipeline de promotion M6 avec un corpus mixte (addendum 2026-09-18)

Question posée explicitement avant tout code (choisie de préférence à l'extension aux
patterns de longueur > 1 et à la préparation d'une validation tierce, précisément parce
que c'est la question la plus décisive pour la suite de l'investissement sur M7, au coût
le plus faible) : **l'évidence LLM (§1-5 ci-dessus), une fois injectée dans le même
pipeline de promotion M6 que le corpus adversarial déjà validé, aide-t-elle, dégrade-t-elle,
ou laisse-t-elle inchangée la calibration du holdout ?**

Mécanisme (`m7_corpus_mixed_v0_1.py`) : union des enregistrements du corpus adversarial
v0.2 (`m6_corpus_from_m4_m5_v0_2.build_real_corpus_v2()`, toutes profondeurs,
`GROUNDED_DIRECT`) et des enregistrements LLM (`build_llm_witnessed_corpus()`, profondeur 1
uniquement, `GROUNDED_ANALOGY`) — aucun nouveau mécanisme épistémique, uniquement une
union de deux flux d'enregistrements déjà validés séparément, rejouée telle quelle à
travers `split_by_rule`/`StructuralLearningPolicy`/`evaluate_promotion` (M6, inchangés).

**Propriété d'équité vérifiée avant toute comparaison** : le mécanisme LLM ne pose jamais
de question sur un pattern absent du corpus adversarial (il interroge les mêmes squelettes
de longueur 1 déjà découverts sur le même fichier de corpus) — donc l'ensemble des
signatures de règles est identique entre le corpus adversarial seul et le corpus combiné.
Avec la même graine, `split_by_rule` assigne donc exactement les mêmes règles au holdout
dans les deux cas : la comparaison porte sur « mêmes règles retenues en holdout, avec vs.
sans évidence LLM en entraînement », pas sur des holdouts de composition différente.
Vérifié programmatiquement (avec un `generate_fn` simulé, sans réseau) :
`test_llm_evidence_never_introduces_a_rule_absent_from_the_adversarial_corpus`.

**Résultat réel (exécution du 2026-09-18, `llama3.2:latest` local, seed=0,
`brier_threshold=0.5`)** :

| | Baseline (adversarial seul) | Mixte (adversarial + LLM) |
|---|---|---|
| Enregistrements train | 16 | 25 |
| Enregistrements holdout | 5 | 8 |
| Brier holdout | 0.48125 | 0.47 |
| ECE holdout | 0.025 | 0.025 |
| Décision de promotion | PROMOTE | PROMOTE |

Les 16 enregistrements LLM ajoutés sont, comme documenté en §4, **16/16 CONTRADICTED** —
le petit modèle local continue de systématiquement diverger de la prédiction structurelle
réelle sur cette tâche.

**Lecture honnête de ce résultat, pas une lecture optimiste** : le mouvement du Brier
(0.48125 → 0.47) est faible, sur un holdout de seulement 5 à 8 enregistrements — un
échantillon bien trop petit pour distinguer un effet réel d'un artefact d'échantillonnage.
Plus important : cet effet ne peut pas être attribué à un raisonnement analogique correct
du LLM, puisque son évidence est elle-même systématiquement biaisée (toujours
`CONTRADICTED`, indépendamment de la vérité). Toute ressemblance entre le biais introduit
à l'entraînement et la composition du holdout pour une même règle est un artefact
mécanique d'une source d'évidence biaisée apparaissant de façon cohérente dans les deux
sous-ensembles, pas une preuve de compétence. **Conclusion retenue : à l'échelle actuelle
du corpus et avec ce modèle, l'ajout de l'évidence LLM au pipeline de promotion est
neutre pour la calibration (ni gain, ni dégradation mesurable, décision de promotion
inchangée)** — ce résultat ne justifie pas, en l'état, un investissement supplémentaire
(extension aux patterns de longueur > 1, validation tierce) tant que la justesse
individuelle du LLM sur cette tâche (§4) n'est pas améliorée ou que le corpus n'est pas
agrandi pour distinguer un effet réel du bruit d'échantillonnage.

Tests :
- `tests/test_m7_mixed_corpus_promotion_v0_1.py` (7 tests, backend simulé injecté, aucun
  réseau) — mécanique de l'union, propriété d'équité du holdout, non-régression du nombre
  déjà validé de M6 v0.2 (0.48125), dégénérescence correcte vers « aucune différence »
  quand le LLM ne propose rien.
- `tests/test_m7_mixed_corpus_live_demo_v0_1.py` (1 test, sautable comme les autres
  démonstrations live) — exécute la comparaison réelle, n'affirme que les propriétés
  structurelles garanties, jamais une valeur exacte de Brier pour le run mixte (non
  reproductible à l'identique).

## 7. Invariants permanents testés

`tests/test_m7_llm_fact_proposer_invariants_v0_1.py` (17 tests, backend simulé injecté,
aucun réseau) :
- la valeur réelle prédite n'apparaît jamais dans le prompt envoyé au LLM ;
- toute réponse non-JSON, sans clé `object`, non-string, ou vide est traitée comme
  « aucune proposition », jamais fabriquée ;
- une proposition bien formée est acceptée, avec sujet/relation fournis par l'appelant
  (contexte déjà connu), seul l'objet est réellement sollicité du LLM ;
- la preuve est toujours `GROUNDED_ANALOGY`, jamais `GROUNDED_DIRECT` ni `UNGROUNDED_HUMAN` ;
- accord → `SUPPORT`, désaccord → `CHALLENGE` ;
- un hôte Ollama injoignable lève `OllamaUnavailable`, distinct d'une réponse inexploitable ;
- le repli LAN ne se déclenche que sur injoignabilité réelle, jamais sur réponse inexploitable ;
- le modèle attribué à une proposition est toujours celui qui a réellement répondu (local ou
  repli), jamais présumé.

## 8. Résultat local

373 tests passés (364 précédents + 9 cas critiques de validation tierce
`test_m7_critical_validation_v0_1.py`), 0 échec, 0 régression.

## 9. Hors périmètre de cette version

- Parseur texte libre → structure (roadmap : élément différé séparé, pas traité ici) ;
- amélioration de la justesse du LLM sur cette tâche (modèle plus grand, few-shot mieux
  choisi, chaîne de raisonnement) — signalé comme limite empirique réelle, pas corrigé ici
  pour ne pas fabriquer un résultat plus flatteur ; c'est aussi la limite qui explique la
  neutralité du résultat en §6 ;
- extension aux patterns de longueur > 1 (même limite que M6 v0.2 avant son extension) ;
  reste ouverte, et de priorité incertaine tant que §6 ne montre pas de bénéfice à
  l'évidence LLM même en longueur 1 ;
- amélioration de la justesse du LLM ou du corpus au-delà de ce qui est décrit en §6/§9 —
  la validation tierce ci-dessous porte sur le mécanisme, pas sur la compétence du modèle.

## 10. Validation tierce et clôture (2026-09-18)

`documentation/MetaHIA_ThirdParty_Validation_Protocol_M7_V0_1.md` (9 cas critiques C01-C09,
`tests/test_m7_critical_validation_v0_1.py`, délibérément sans dépendance réseau) a été
envoyé et exécuté par **deux relecteurs génuinement externes, dans deux environnements
indépendants** :

| | Retour #1 | Retour #2 |
|---|---|---|
| Environnement | zip GitHub, Python (version non précisée) | Linux 5.10.134, Python 3.11.2, pytest 7.2.1 |
| Cas critiques C01–C09 | 9/9 PASS | 9/9 PASS |
| Suite complète | 371 PASS / 2 SKIP / 0 FAIL | 371 PASS / 2 SKIP / 0 FAIL |
| Hashes gelés (9 fichiers) | 9/9 conformes | 9/9 conformes |
| Modification du dépôt | 0 | 0 |

Les 2 `SKIP` (démonstrations live Ollama) sont attendus et documentés — Ollama n'était
accessible dans aucun des deux environnements. Les deux relecteurs ont, chacun
indépendamment, correctement signalé la même réserve méthodologique honnête : une archive
sans `.git` ne permet pas de vérifier cryptographiquement le hash de commit, seulement le
contenu des fichiers gelés (qui, lui, correspondait exactement dans les deux cas). Aucun des
deux relecteurs n'a arrondi son verdict à une clôture de gate — chacun l'a explicitement
laissée à la décision du porteur du projet, conformément à la règle de gouvernance du
protocole. Détail complet, y compris les citations verbatim des deux verdicts, dans
`JOURNAL_DE_BORD.md` (entrée du 2026-09-18).

**Clôture** : sur la base de ces deux retours indépendants — même configuration factuelle qui
avait justifié la clôture de M6 le 2026-09-17 — le porteur du projet (Bacem Ben Soui) a
explicitement clôturé le gate de validation externe de M7 le 2026-09-18. C'est une décision
de gouvernance du porteur du projet, pas une auto-déclaration : ni l'assistant ni les
relecteurs n'ont conclu la clôture eux-mêmes.

**Ce que cette clôture établit** : le mécanisme M7 (fact-proposer + intégration corpus
mixte) est honnête, non circulaire, à échec fermé (fail-closed), et reproductible dans ses
parties déterministes, confirmé par deux exécutions indépendantes.

**Ce que cette clôture n'établit pas** (inchangé depuis §6/§9) : que le LLM est un témoin
compétent ou utile sur cette tâche ; que l'ajout de son évidence améliore la calibration en
général, sur un corpus plus grand, ou avec un autre modèle ; une extension aux patterns de
longueur > 1 ; un parseur texte libre → structure ; une quelconque readiness de production.

**Statut M7 : `VALIDATED`** (portée fact-proposer + intégration corpus mixte), au même titre
de gouvernance que M6.
