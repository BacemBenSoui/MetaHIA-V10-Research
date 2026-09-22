# MetaHIA V10 — Gouvernance : invariant d'abstraction sémantique (M1-M6/E20-D/P4-T vs M7/JEV)

Date : 2026-09-22
Statut : **règle de gouvernance adoptée, applicable à tout chantier futur
touchant M7/JEV/Kev et à toute revue de conformité de P4-T/E20-D**

Origine : revue externe (2026-09-22) confirmant que la règle « pas de
dictionnaire sémantique, partiel ou total » reste un invariant de ce
projet, et alertant sur une zone sensible spécifique à JEV. Cette revue a
été **vérifiée contre le code et les résultats déjà mesurés dans ce dépôt**
avant adoption (Sec. 2 ci-dessous) — pas acceptée telle quelle sur récit,
conformément à la discipline déjà établie dans ce dépôt pour toute revue
externe.

## 1. La règle, inchangée

> **MetaHIA ne doit pas dépendre d'un dictionnaire sémantique, partiel ou
> complet, pour découvrir ses relations, propriétés, oppositions, bindings
> ou opérations.**

Interdit dans M1-M6/E20-D/P4-T, sans exception :

```text
semantic_dictionary   alias_map              synonym_map
relation_equivalence_map                     manual opposition table
manual binding rules  domain-specific ontology
```

Autorisé (couche structurelle) :

```text
RAW DATA -> structural parsing -> opaque symbols -> Compare -> Pattern -> Operation
```

Cette règle est **déjà respectée par construction**, pas seulement par
intention : `operator_space_v0_1.py` le déclare lui-même dans son propre
docstring (code déjà existant, non modifié pour cette revue) — *« Operator
properties are treated as opaque structural tokens. No semantic property
detector is hard-coded here »*. `kernel2.py` opère exclusivement sur
`Node`/`NodeRef`/`RefObject` opaques. P4-T (`p4t_structural_transformation_induction_v0_1.py`)
raisonne uniquement sur position/liaison/direction/motif — jamais sur ce
qu'une relation « signifie ».

## 2. Vérification, pas acceptation sur récit : l'exemple A05 confirme la règle ET révèle une nuance manquante

La revue distingue deux modes JEV : **STRICT** (vocabulaire fermé opaque,
aucune glose) et **GLOSSÉ** (définition linguistique explicite fournie,
ex. `EPOUX_DE = "X est l'époux de Y"`).

En relisant le benchmark Jev déjà exécuté et documenté dans ce dépôt
(`documentation/P8_Jev_Kev_Local_Decision_Model_V0_1.md` Sec. 2, 22 cas
réels contre `jev-1.13.0`), **ce benchmark n'était ni l'un ni l'autre** :
le vocabulaire fermé était présenté à Jev sous forme d'**étiquettes
lisibles** (`EPOUX_DE`, `MERE_DE`, ...), sans définition
MetaHIA-fournie, mais sans non plus être des symboles opaques
(`R1`...`R9`). Le cas adversarial A05 le prouve directement : Jev a
**coercé** « conjoint » (synonyme non autorisé, jamais fourni dans aucune
glose par ce projet) en `EPOUX_DE` avec une confiance de 0,98. Ceci ne
peut s'expliquer que par la connaissance linguistique **préexistante** du
modèle sur le mot français « époux » contenu dans le nom même de
l'étiquette — une fuite sémantique réelle, mesurée, qui existe **même
sans glose explicite fournie par MetaHIA**.

**Conclusion, plus stricte que la proposition initiale de la revue** : une
étiquette de relation lisible par un humain (`EPOUX_DE`) n'est **jamais**
sémantiquement neutre pour un modèle de langage déjà entraîné sur du
texte général — contrairement à un symbole véritablement opaque (`R4`).
Le clivage STRICT/GLOSSÉ à deux niveaux ne suffit donc pas à isoler la
condition qui teste réellement l'hypothèse d'abstraction structurelle. Il
faut un **troisième niveau intermédiaire**, et le benchmark déjà réalisé
doit être reclassé dans ce niveau intermédiaire, jamais confondu avec une
condition « sans information sémantique ».

## 3. Protocole à trois niveaux (remplace le clivage à deux niveaux proposé)

| Condition | Vocabulaire fourni au modèle | Ce qui est mesuré |
|---|---|---|
| **JEV-STRICT** | Symboles opaques (`R1`...`R9`, ou hash), aucune étiquette lisible | Capacité de décision purement structurelle/contextuelle — la seule condition qui teste réellement l'hypothèse d'abstraction de MetaHIA |
| **JEV-LABELED** *(= le benchmark déjà exécuté, Sec. 2 de ce document)* | Étiquettes lisibles du vocabulaire fermé (`EPOUX_DE`, `MERE_DE`, ...), **aucune** définition MetaHIA-fournie | Effet de la connaissance linguistique déjà acquise par le modèle sur le nom des relations — un intermédiaire, pas une preuve d'abstraction pure |
| **JEV-GLOSSED** | Étiquettes + définition linguistique explicite (`EPOUX_DE = "X est l'époux de Y"`) | Gain maximal apporté par une information sémantique externe explicite |

Trois comparaisons possibles, chacune instructive séparément :

```text
STRICT -> LABELED   : effet de la fuite sémantique par le NOM de l'étiquette seul
LABELED -> GLOSSED   : effet de la définition linguistique explicite en plus
STRICT -> GLOSSED   : effet total de toute l'information sémantique ajoutée
```

## 4. Vocabulaire fermé ≠ dictionnaire sémantique — mais seulement si le vocabulaire lui-même est opaque

Point corrigé par rapport à la revue (Sec. 5 de la revue) : la revue
affirme que le contrat de sortie (`relation ∈ {EPOUX_DE, EPOUSE_DE, ...}`)
n'est « pas en soi une violation ». C'est vrai pour M1-M6/E20-D/P4-T, qui
ne lisent **jamais** le nom de l'étiquette (uniquement son identité
structurelle — `NodeRef`/position). Ce n'est **plus automatiquement vrai**
dès qu'un modèle de langage entraîné sur du texte général (JEV, tout LLM)
reçoit ce même vocabulaire sous forme d'étiquettes lisibles — Sec. 2
ci-dessus le démontre par la mesure, pas par la théorie. La distinction
correcte est donc :

- Vocabulaire fermé **opaque** (positions/`NodeRef`/symboles arbitraires)
  → jamais une violation, quel que soit le consommateur.
  Vocabulaire fermé **lisible** (`EPOUX_DE`) → neutre pour M1-M6/E20-D/P4-T
  (qui ne lisent jamais le nom), **mais pas neutre** pour un LLM — à
  comptabiliser comme information expérimentale (Sec. 5).

## 5. Comptabilisation obligatoire de l'information sémantique (nouvelle règle, opérationnalisée)

La revue recommande (Sec. 10) que *« toute abstraction sémantique fournie
à un modèle externe doit être explicitement comptabilisée comme
information expérimentale »*. Rendu concret et exécutable, pas seulement
déclaratif : tout futur mécanisme de preuve M7 (JEV/Kev inclus) doit
porter un champ explicite sur chaque enregistrement de preuve produit,
par exemple `semantic_condition: "STRICT" | "LABELED" | "GLOSSED"`, aux
côtés du `provenance="GROUNDED_ANALOGY"` déjà systématique pour toute
preuve LLM/JEV dans ce projet. Aucun corpus ne doit mélanger des preuves
de conditions différentes sans que ce champ permette de les séparer a
posteriori.

## 6. Frontière architecturale — déjà en place, pas à construire

La revue propose (Sec. 9) une séparation `STRUCTURAL CORE` (M1-M6/E20-D)
vs `M7` (LLM/JEV/Kev), convergeant vers la validation. **Cette séparation
existe déjà dans le code et la documentation de ce dépôt**, elle n'est pas
une nouveauté à construire :

- `documentation/P8_Jev_Kev_Local_Decision_Model_V0_1.md` Sec. 1 : *« ce
  mécanisme ne peut jouer aucun rôle dans M1-M6/E20-D... vérifié par
  lecture directe de `operator_space_v0_1.py` »*.
- Toute preuve LLM/JEV entre dans le pipeline exclusivement via
  `provenance="GROUNDED_ANALOGY"`, jamais `GROUNDED_DIRECT` — déjà la
  règle pour `m7_llm_fact_proposer_v0_1.py` et pour le plan JEV (Sec. 5 du
  doc P8).
- `m7_text_claim_parser_v0_1.py` (parseur de texte libre) reste, par
  construction déjà documentée, un test de la **compétence linguistique du
  LLM**, jamais une entrée dans la découverte structurelle — cohérent avec
  cette règle sans modification nécessaire.

Ce que ce document ajoute : la nomenclature STRICT/LABELED/GLOSSED
(Sec. 3) et le champ de comptabilisation obligatoire (Sec. 5), pour que
cette frontière déjà réelle reste **mesurable**, pas seulement déclarée.

## 7. Impact sur le plan P8 déjà conçu

`documentation/P8_Jev_Kev_Local_Decision_Model_V0_1.md` Sec. 5 (plan
d'implémentation, toujours bloqué sur l'infrastructure Ollama/LAN promise
par l'utilisateur — **aucun changement à ce blocage**) doit être étendu,
au moment de son implémentation, avec :

- un paramètre `relation_vocabulary_mode` sur `propose_relation_jev()`
  (`"STRICT"` = positions/symboles opaques générés par le corpus, jamais
  les noms `EPOUX_DE` etc. ; `"LABELED"` = comportement déjà planifié,
  inchangé ; `"GLOSSED"` = étiquettes + définition) ;
- le champ `semantic_condition` (Sec. 5 ci-dessus) sur `JevProposal` et
  sur chaque `EvidenceRecord` produit ;
- trois corpus **séparés**, jamais fusionnés silencieusement
  (`m7_corpus_from_jev_strict_v0_1.py`,  `..._labeled_...`,
  `..._glossed_...`, ou un seul fichier paramétré — décision
  d'implémentation à prendre au moment venu, pas ici) ;
- le résultat déjà mesuré (Sec. 2 de ce document, benchmark officiel Jev)
  est **reclassé LABELED** dans toute mention future — ni STRICT ni
  GLOSSED.

Aucune ligne de code n'est écrite par ce document : il reste bloqué sur
la même dépendance d'infrastructure que le plan P8 original.

## 8. Table de conformité (mise à jour, granularité JEV corrigée)

| Élément | Conformité |
|---|---|
| M1/K3 | 🟢 |
| M2-M6 | 🟢 |
| E20-D / P4-T | 🟢 principe respecté (positions/motifs, jamais de noms de relation lus) |
| Ancienne P4 inter-domaines | 🔴 rejetée (2026-09-19) |
| P4-R | 🟠 abandonnée comme voie principale |
| M7 — parseur de texte (`m7_text_claim_parser_v0_1.py`) | 🟢 vocabulaire fermé respecté, LLM testé sur sa compétence linguistique, jamais injecté dans M1-M6/E20-D |
| M7 — proposeur LLM (`m7_llm_fact_proposer_v0_1.py`) | 🟠 **LABELED** de facto (vocabulaire fermé lisible, jamais glosé) — jamais formellement étiqueté comme tel jusqu'à ce document |
| JEV-STRICT | ⏸ non encore mesuré (bloqué infra) — seule condition validant réellement l'hypothèse d'abstraction pour un LLM |
| JEV-LABELED | 🟢 mesuré (22/22 cas, `documentation/P8_Jev_Kev_Local_Decision_Model_V0_1.md` Sec. 2) — **reclassé** depuis « strict » implicite vers LABELED par ce document |
| JEV-GLOSSED | ⏸ non encore mesuré (bloqué infra) |
| Dictionnaire de synonymes manuel dans M1-M6/E20-D/P4-T | 🔴 interdit, absent, vérifié par lecture directe |
| Ontologie cachée dans M1-M6/E20-D/P4-T | 🔴 interdit, absent |

## 9. Décision

**Règle adoptée.** S'applique à toute future extension de M7 (JEV/Kev, et
tout mécanisme LLM ultérieur) : condition sémantique déclarée
explicitement (STRICT/LABELED/GLOSSED), jamais fusionnée sans
distinction. Ne modifie aucun code existant — reclassifie a posteriori le
benchmark Jev déjà mesuré, et amende le plan d'implémentation P8 déjà
écrit, avant même que ce plan ne soit exécuté (toujours bloqué sur
l'infrastructure LAN/Ollama). E20-D reste `OPEN`, inchangé par ce
document de gouvernance.
