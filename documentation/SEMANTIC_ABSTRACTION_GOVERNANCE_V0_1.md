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
| M7 — parseur de texte (`m7_text_claim_parser_v0_1.py`) | 🟠 **LABELED, hors-axe** (Sec. 8bis) — vocabulaire fermé respecté et jamais injecté dans M1-M6/E20-D, mais la tâche elle-même est linguistique par construction, pas comparable à STRICT/LABELED/GLOSSED |
| M7 — proposeur LLM (`m7_llm_fact_proposer_v0_1.py`) | 🟠 **LABELED** confirmé par audit direct du code (Sec. 8bis) — vocabulaire fermé lisible, jamais glosé, jamais formellement étiqueté comme tel avant ce document |
| JEV-STRICT | ⏸ non encore mesuré (bloqué infra) — seule condition validant réellement l'hypothèse d'abstraction pour un LLM ; squelette de code prêt (Sec. 8ter) |
| JEV-LABELED | 🟢 mesuré (22/22 cas, `documentation/P8_Jev_Kev_Local_Decision_Model_V0_1.md` Sec. 2) — **reclassé** depuis « strict » implicite vers LABELED par ce document |
| JEV-GLOSSED | ⏸ non encore mesuré (bloqué infra) |
| Dictionnaire de synonymes manuel dans M1-M6/E20-D/P4-T | 🔴 interdit, absent, vérifié par lecture directe |
| Ontologie cachée dans M1-M6/E20-D/P4-T | 🔴 interdit, absent |

## 8bis. Audit rétroactif, par lecture directe du code (2026-09-22)

Demandé explicitement par l'utilisateur : appliquer la même grille
STRICT/LABELED/GLOSSED aux deux mécanismes M7 existants, en lisant leur
code réel — pas en supposant leur conformité par leur seule description.

### `m7_llm_fact_proposer_v0_1.py` → **LABELED**

`_build_prompt()` construit littéralement :

```python
facts_block = "\n".join(f"{rel}({subj}, {obj})" for rel, subj, obj in known_facts)
...
f'the object in {relation}("{subject}", ?)'
```

Le nom de relation (`rel`/`relation`, ex. `MERE_DE`) est inséré **tel
quel**, lisible, dans le prompt — aucune définition MetaHIA-fournie
(`MERE_DE = "X est la mère de Y"`) n'accompagne jamais ce nom. C'est
exactement `LABELED` : le vocabulaire fermé est lisible, jamais glosé.

Nuance par rapport à JEV-LABELED : la tâche n'est pas « choisir une
relation parmi un ensemble » (où le nom lisible de CHAQUE option peut
fuiter), mais « prédire une valeur d'objet, la relation étant déjà fixée
par l'appelant » — la surface de fuite sémantique porte sur un seul nom
de relation par appel, pas sur un choix parmi plusieurs noms lisibles
simultanément. Le risque reste réel mais plus étroit. Point favorable
déjà mesuré empiriquement (et déjà documenté ailleurs dans ce dépôt,
indépendamment de cet audit) : ce mécanisme produit un résultat dégénéré
(16/16 `CONTRADICTED`) sur le corpus family-tree — signe indirect que la
connaissance linguistique du nom de relation, même disponible, **n'aide
pas concrètement** le petit modèle local sur ce corpus synthétique
(entités fictives sans ancrage dans le monde réel). Cela ne change pas la
classification (`LABELED` reste `LABELED`, indépendamment du résultat
mesuré), mais nuance le risque pratique.

**Action** : aucune modification de code. Reclassification déclarative
uniquement — `m7_llm_fact_proposer_v0_1.py` reste un mécanisme M7
existant, déjà cantonné à `GROUNDED_ANALOGY`, jamais dans M1-M6/E20-D. Si
une version STRICT de ce mécanisme est un jour souhaitée (relation
présentée comme symbole opaque plutôt que `MERE_DE`), elle suivrait le
même patron que `m7_jev_relation_choice_v0_1.py` (Sec. 8ter) — non
demandé pour l'instant, non implémenté ici.

### `m7_text_claim_parser_v0_1.py` → **LABELED, mais hors de l'axe STRICT/LABELED/GLOSSED**

`_build_extraction_prompt()` liste aussi les relations sous forme lisible
(`relations_block`), sans glose — donc `LABELED` au sens strict de la
présentation du vocabulaire.

Mais ce mécanisme a une propriété que ni le proposeur ni JEV n'ont : sa
**tâche elle-même** est l'extraction d'une relation depuis une **phrase
française libre**. Le docstring du fichier le déclare explicitement,
avant même cet audit : *« instead of asking a closed question... the
model is given an independently-authored sentence and must extract the
FULL triple itself »*. Reconnaître que « Alice est la mère de Bob »
exprime `MERE_DE` exige la compétence linguistique française du modèle
sur le mot « mère » lui-même, dans le TEXTE, indépendamment de ce que
l'étiquette de sortie a l'air de vouloir dire. Passer ce mécanisme en
mode STRICT (étiquettes de sortie opaques) ne changerait donc **rien** à
la fuite réelle, qui a lieu dans la phrase d'entrée, pas dans le nom de
l'étiquette — contrairement à JEV/au proposeur, où la fuite mesurée
(cas A05) provient précisément du nom de l'étiquette de sortie.

**Conclusion** : ce mécanisme n'est **pas comparable** à l'axe
STRICT/LABELED/GLOSSED tel que défini Sec. 3 — cet axe mesure la fuite
sémantique par le **vocabulaire de sortie**, pas la compétence
linguistique sur un **texte d'entrée**, que ce mécanisme teste
délibérément et explicitement, par conception, depuis son origine
(2026-09-18). C'est déjà honnêtement disclosed dans
`documentation/MetaHIA_M7_TextClaimParser_V0_1.md` (fidélité de parsing
mesurée à 50 %, présentée comme un test de compétence linguistique, pas
de découverte structurelle). Aucune reclassification de fond n'est
nécessaire ; seule la nomenclature de ce document s'applique
partiellement (le sous-critère « vocabulaire lisible, jamais glosé » est
vrai, mais insuffisant pour classer ce mécanisme dans le même panier que
JEV/le proposeur).

**Action** : aucune modification de code. Note de gouvernance
uniquement, pour que ce mécanisme ne soit jamais comparé mécaniquement à
JEV-STRICT/LABELED/GLOSSED sans cette réserve.

## 8ter. Squelette de code JEV-STRICT, préparé avant implémentation

Voir `m7_jev_relation_choice_v0_1.py` (nouveau fichier, squelette
uniquement — aucun appel réseau réel, préparé pendant que l'utilisateur
provisionne l'infrastructure Kev sur `192.168.1.11`, conformément à
`documentation/P8_Jev_Kev_Local_Decision_Model_V0_1.md` Sec. 4, toujours
en vigueur).

**Correction factuelle trouvée en préparant ce squelette** : le plan P8
(Sec. 5, écrit 2026-09-21) affirmait que `jev_client_v0_1.py` était
« déjà présent dans ce dépôt ». Vérifié par recherche directe (`find`) :
**ce fichier n'existe pas** dans ce dépôt — il existait seulement dans le
zip externe `MetaHIA-V10-Jev-Parsing-Benchmark-v0.1.zip` exécuté en
isolation pour produire le résultat Sec. 2 du doc P8, jamais committé ici.
Corrigé dans `documentation/P8_Jev_Kev_Local_Decision_Model_V0_1.md`.

Contenu du squelette :

- `RelationVocabularyMode` (`"STRICT"` / `"LABELED"` / `"GLOSSED"`) et
  `JevProposal` (avec le champ `semantic_condition` prévu Sec. 5).
- `build_strict_symbol_map(vocabulary)` : bijection déterministe
  vocabulaire réel → symboles opaques (`R1`...`Rn`, ordre alphabétique du
  vocabulaire réel, jamais un ordre qui fuiterait une information) —
  testée indépendamment de tout réseau.
- Trois constructeurs de requête (`_build_choice_payload_strict/labeled/glossed`) :
  seul le mode `STRICT` exige des exemples travaillés
  (`worked_examples`, des couples texte+symbole déjà résolus) en plus du
  texte à classer, car un symbole opaque seul, sans aucun exemple, ne
  porte structurellement aucune information exploitable — ceci est
  documenté comme une exigence du mode, pas une option.
- `propose_relation_jev(...)` : signature complète, garde-fous déjà
  actifs et testés (sujet == objet rejeté — bug A05/T05/T08/T09 déjà
  mesuré ; réponse hors du vocabulaire fermé rejetée ; réponse non-JSON
  rejetée) ; le point d'appel réseau réel est un `client.decide(...)`
  injecté (mock testable dès maintenant, jamais un appel réel tant que
  Kev n'est pas hébergé).
- `jev_evidence_for_prediction(...)` : miroir exact de
  `llm_evidence_for_prediction` (toujours `GROUNDED_ANALOGY`, jamais
  `GROUNDED_DIRECT`).

`tests/test_m7_jev_relation_choice_v0_1.py` (réseau-free, comme tous les
tests M7 obligatoires de ce dépôt) : bijection STRICT correcte et
inversible, garde-fou sujet==objet, rejet hors-vocabulaire, mode STRICT
refuse de construire une requête sans `worked_examples` (jamais une
requête silencieusement dégradée), `semantic_condition` correctement
posé sur `JevProposal` selon le mode appelé.

**Ce squelette ne lève PAS le blocage d'infrastructure** — aucun appel
réseau réel n'est fait ni possible avec ce code seul ; il attend un
`client` réel (`Kev`/Ollama sur `192.168.1.11`) fourni par l'appelant une
fois l'infrastructure prête.

## 9. Décision

**Règle adoptée.** S'applique à toute future extension de M7 (JEV/Kev, et
tout mécanisme LLM ultérieur) : condition sémantique déclarée
explicitement (STRICT/LABELED/GLOSSED), jamais fusionnée sans
distinction. Ne modifie aucun code M7 existant — reclassifie a posteriori
le benchmark Jev déjà mesuré et les deux mécanismes M7 audités
(Sec. 8bis : proposeur LLM = `LABELED` confirmé, parseur de texte =
`LABELED` mais hors-axe par conception), et amende le plan
d'implémentation P8 déjà écrit. Un squelette de code JEV-STRICT est
maintenant prêt (Sec. 8ter, `m7_jev_relation_choice_v0_1.py`), sans appel
réseau réel — l'implémentation reste bloquée sur l'infrastructure
LAN/Ollama, en cours de provisionnement par l'utilisateur sur
`192.168.1.11`. E20-D reste `OPEN`, inchangé par ce document de
gouvernance.
