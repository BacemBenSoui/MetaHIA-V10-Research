# MetaHIA — M7 — Synthèse d'état (2026-09-18)

Point d'entrée unique pour connaître l'état réel de M7 sans parcourir les deux documents
détaillés (`MetaHIA_M7_LLM_Fact_Proposer_V0_1.md`, 10 sections ; `MetaHIA_M7_TextClaimParser_V0_1.md`,
15 sections) ni `JOURNAL_DE_BORD.md`. Ce document **ne remplace** aucun des deux — il pointe
vers eux pour le détail complet, le raisonnement de conception, et les citations verbatim des
relecteurs externes. En cas de divergence, les documents détaillés et `JOURNAL_DE_BORD.md`
font foi.

## En une phrase

M7 explore l'utilisation d'un LLM comme témoin ou parseur **indépendant**, jamais comme source
de vérité directe, alimentant en évidence `GROUNDED_ANALOGY` le pipeline M4/M6 déjà validé —
neuf mécanismes/décisions ont été testés, huit sont clos, un reste en configuration active.

## Tableau de synthèse

| # | Mécanisme | Fichiers | Statut | Chiffre clé | Limite connue |
|---|---|---|---|---|---|
| 1 | Témoin, question fermée, longueur 1 | `m7_llm_fact_proposer_v0_1.py`, `m7_corpus_from_llm_v0_1.py` | **VALIDATED** (2 tiers externes, 2026-09-18) | 16/16 `CONTRADICTED` | biais systématique du modèle local, jamais corrigé |
| 2 | Parseur texte libre, longueur 1 | `m7_text_claim_parser_v0_1.py`, `m7_corpus_from_text_claims_v0_1.py` | **VALIDATED** (2 tiers externes, 2026-09-18) | fidélité 8/16 (50 %) | instable d'un appel à l'autre (même phrase, réponses différentes) |
| 3 | Corpus mixte v0.1 (adversarial + témoin) | `m7_corpus_mixed_v0_1.py` | **VALIDATED** (fait partie du protocole #1) | Brier 0,47 (neutre) | mouvement non significatif sur holdout de 5-8 |
| 4 | Corpus mixte v0.2, 4 conditions (+ parseur) | `m7_corpus_mixed_v0_2.py` | **RETENU** (décision du porteur du projet) | `+both` : Brier 0,489, PROMOTE | pire que témoin seul (0,47) — retenu pour la diversité, pas la performance |
| 5 | Consensus même-mécanisme (2 modèles, parseur) | `m7_text_claim_parser_consensus_v0_1.py` + corpus builder | **FERMÉ** — hypothèse infirmée | Brier 0,585 (pire que non filtré) | le filtrage par accord aggrave, ne corrige pas |
| 6 | Consensus inter-mécanismes (témoin + parseur) | `m7_cross_mechanism_consensus_v0_1.py` + corpus builder | **FERMÉ** — dominé | 0 preuve produite sur 32 appels | coût = union simple, valeur nulle |
| 7 | Témoin, longueur > 1 (multi-sauts) | `m7_llm_fact_proposer_multihop_v0_1.py` + corpus builder | **NON PROMU** — expérimental isolé | 20/20 `CONTRADICTED`, Brier 0,426 | gain confirmé non causal (`CONFIRMED_MECHANICAL_ARTIFACT`), non robuste (8/10 graines) |
| 8 | Parseur, longueur > 1 | — (jamais implémenté) | **DIFFÉRÉ** | — | anticipé : même limite + coût par appel déjà plus élevé |
| 9 | Découverte transversale : base du holdout | `m6_structural_learning_v0_1.py` (inchangé, gelé) | **CONFIRMÉ** | 100 % `BASIS_GLOBAL_PRIOR` sur tout holdout de ce projet | aucun Brier/ECE de ce projet n'a jamais démontré d'apprentissage par-règle |

## Configuration réellement active aujourd'hui

`m7_corpus_mixed_v0_2.py`, condition `+both` : union du corpus adversarial + témoin
(longueur 1) + parseur (longueur 1). **32 appels LLM réels par exécution complète**, tous
locaux sauf repli LAN sur injoignabilité. Le témoin longueur > 1 et les deux mécanismes de
consensus existent dans le dépôt (testés, documentés) mais **ne sont pas branchés** à cette
configuration.

## Découverte transversale la plus importante (2026-09-18)

En vérifiant l'hypothèse d'un artefact mécanique pour le témoin longueur > 1, découverte que
**tout chiffre de calibration M6/M7 de ce projet — y compris le tout premier baseline
`VALIDATED` (Brier 0,48125) — n'a jamais exercé que `BASIS_GLOBAL_PRIOR`** sur le holdout,
jamais `EXACT_BUCKET`/`RULE_ONLY`. Cause structurelle et intentionnelle de `split_by_rule()`
(une règle ne peut jamais apparaître à la fois en entraînement et en holdout), pas un bug.
Conséquence : aucune validation de calibration de ce projet n'a jamais démontré
d'apprentissage spécifique à une règle — seulement une généralisation de la distribution de
classe globale. Corroboré indépendamment par un second relecteur le même jour. Détail complet :
`documentation/MetaHIA_M6_Structural_Learning_V0_1.md` Sec. 11.

## Fil chronologique condensé

1. 2026-09-17 — Témoin question fermée implémenté, repli LAN ajouté.
2. 2026-09-18 — Corpus mixte v0.1 (témoin) : neutre. Protocole tiers témoin envoyé, deux
   retours externes, **clôturé `VALIDATED`**.
3. 2026-09-18 — Parseur texte choisi comme jalon suivant (parmi 3 options), implémenté,
   protocole tiers envoyé, deux retours externes, **clôturé `VALIDATED`**.
4. 2026-09-18 — Corpus mixte v0.2 (3 sources, 4 conditions) : parseur seul dégrade,
   union sauve la promotion. **Configuration retenue** par décision explicite du porteur
   du projet (« les deux »), malgré un Brier moins bon que le témoin seul.
5. 2026-09-18 — Consensus même-mécanisme testé (résource trackée) : **hypothèse infirmée**.
6. 2026-09-18 — Consensus inter-mécanismes testé (résource trackée) : **dominé, fermé**.
7. 2026-09-18 — Extension longueur > 1 du témoin (choisie parmi 3 options) : mécanisme
   fonctionnel, mais gain de calibration confirmé comme artefact mécanique.
8. 2026-09-18 — Vérification de l'hypothèse d'artefact (Priorité 1) : découverte
   transversale du `BASIS_GLOBAL_PRIOR`, corroborée par un second relecteur, décisions
   P1.2/P1.3 (témoin longueur > 1 non promu, parseur longueur > 1 différé).

Détail complet, citations verbatim des relecteurs, et chronologie exhaustive :
`JOURNAL_DE_BORD.md`.

## Documents sources (à consulter pour le détail, pas dupliqués ici)

- `documentation/MetaHIA_M7_LLM_Fact_Proposer_V0_1.md` — témoin question fermée, repli LAN,
  corpus mixte v0.1, clôture de validation tierce.
- `documentation/MetaHIA_M7_TextClaimParser_V0_1.md` — parseur texte, clôture de validation
  tierce, corpus mixte v0.2, deux consensus, extension longueur > 1, découverte du prior
  global.
- `documentation/MetaHIA_ThirdParty_Validation_Protocol_M7_V0_1.md` et
  `documentation/MetaHIA_ThirdParty_Validation_Protocol_M7_TextClaimParser_V0_1.md` —
  protocoles gelés (hashes, cas critiques C01-C09).
- `documentation/MetaHIA_M6_Structural_Learning_V0_1.md` Sec. 11 — découverte transversale du
  `BASIS_GLOBAL_PRIOR`.
- `JOURNAL_DE_BORD.md` — chronologie complète, verbatim des relecteurs externes, décisions de
  gouvernance du porteur du projet.

## Ce qui reste ouvert

- Priorité 2 (hygiène documentaire) — ce document en fait partie ; élagage des sections 10/14
  de la roadmap.
- Priorité 3 (diversification du corpus, interface minimale M1-M6).
- Amélioration de la fidélité du parseur, multi-provider LLM au-delà d'Ollama : différés sans
  échéance.
