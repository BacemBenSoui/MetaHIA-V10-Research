# MetaHIA V10 — P8 : modèle de décision typée local (Jev/Kev) pour M7 v0.1

Date : 2026-09-21
Statut : **PRIORISÉ — EN ATTENTE D'INFRASTRUCTURE.** Ne pas commencer
l'implémentation avant que l'utilisateur fournisse l'accès/la configuration
nécessaire pour héberger un modèle Kev via Ollama sur le serveur LAN
`192.168.1.11` (mirror du pattern déjà établi pour le repli LAN de M7,
`LAN_FALLBACK_HOST` dans `m7_llm_fact_proposer_v0_1.py`).

## 1. Origine et périmètre

Ce chantier fait suite à deux étapes déjà réalisées et documentées dans ce
même dépôt :

- **Benchmark réel contre l'API Jev officielle** (`documentation/MetaHIA_Jev_Parsing_Benchmark_V0_1.md`,
  zip `MetaHIA-V10-Jev-Parsing-Benchmark-v0.1.zip`) : exécuté en direct
  (l'auteur du zip n'avait pas pu, DNS bloqué dans son environnement — testé
  ici avec succès), 22/22 cas contre `jev-1.13.0`.
- **Vérification de trois pistes locales proposées par l'utilisateur**
  (OpenJev, LocalJev, Kev) — confirmées réelles par requête directe à l'API
  GitHub (étoiles, dates de push, README complet), pas acceptées sur la foi
  d'un résumé de blog.

**Portée stricte** : ce mécanisme ne peut jouer aucun rôle dans M1-M6/E20-D
(`kernel2.py`, `operator_space_v0_1.py`, `m6_structural_learning_v0_1.py`
n'opèrent que sur des `Node`/`NodeRef`/`RefObject` opaques, jamais sur du
texte — vérifié par lecture directe de `operator_space_v0_1.py`, qui le
déclare lui-même : *« Operator properties are treated as opaque structural
tokens »*). Le seul point de contact possible est la frontière M7
(texte → preuve).

## 2. Résultat du benchmark réel contre Jev officiel (rappel factuel)

22 cas (16 positifs T01-T16, 6 adversariaux A01-A06), modèle `jev-1.13.0` :

| Dimension | Résultat mesuré |
|---|---|
| Relation (Choice, vocabulaire fermé), cas positifs | 16/16 = 100 % |
| Sujet, cas positifs | 16/16 = 100 % |
| Objet, cas positifs | 13/16 = 81,2 % — 3 échecs (T05/T08/T09) : objet prédit = copie du sujet |
| Négation / question / conditionnel / absence de claim (A01,A02,A03,A06) | Correctement traités (probabilité positive basse, relation=NONE) |
| Relation hors-vocabulaire « travaille avec » (A04) | Probabilité positive 0,97 malgré l'absence de la relation dans le vocabulaire fermé — incohérent |
| Quasi-synonyme non autorisé « conjoint » (A05) | **Coercé** en `EPOUX_DE`, confiance 0,98 — échec net, exactement le risque que ce projet a toujours refusé |
| Coût | ~1765 tokens entrée + 1195 sortie par cas (22 appels) |

Conclusion déjà posée : Jev officiel n'est pas adopté tel quel comme
remplaçant du rejet fermé du vocabulaire ; il pourrait servir de
**proposition d'évidence analogique** (jamais de vérité acceptée seule) ou
de **pré-filtre bon marché** pour les cas clairement non positifs.

## 3. Alternatives locales — vérifiées réelles, pas hallucinées

| Projet | Statut vérifié | Mécanisme de probabilité | Matériel requis |
|---|---|---|---|
| `jaredpalmer/kev` | Réel, 1880★, Apache-2.0, poids + checksums sur Hugging Face, CI publique | **Lecture de logits**, température calibrée par checkpoint, ECE publié | CUDA (NVIDIA) ou Apple Silicon ; Kev-4B/9B veulent un GPU correct ou un Mac ≥32 Go |
| `razorback16/openjev` | Réel, 260★ | Lecture de logits (DiffusionGemma 26B) | GPU NVIDIA (vLLM) ou Mac (MLX) |
| `githubnext/localjev` | Réel, 684★, org GitHub officielle | **Auto-rapporté par le modèle** (le README le déclare lui-même : « pas mathématiquement équivalent à une lecture de logits ») | Bun + un serveur oMLX (Apple Silicon) |

**Choix recommandé : Kev**, pour deux raisons vérifiées, pas supposées :

1. Compatible fil-à-fil avec `jev_client_v0_1.py` déjà présent dans ce
   dépôt (`POST /v1/systemone`, mêmes types `noul`/`choice`/`score`) — zéro
   changement de code, seul `TYPESAFE_BASE_URL` change.
2. Probabilités **réellement calibrées par lecture de logits**, pas
   auto-rapportées — c'est la même distinction que ce projet applique déjà
   ailleurs entre confiance structurellement fondée et confiance déclarée
   par un LLM.

Chiffres publiés par Kev lui-même (honnêtes, pas hype — ils déclarent que
leur comparaison à Jev n'est pas contrôlée puisqu'ils ignorent les données
d'entraînement de Jev) :

| Modèle Kev | Brier (sources nouvelles) |
|---|---:|
| Kev-0.8B | 0,499 |
| Kev-4B | 0,299 |
| Kev-9B | 0,286 |
| Jev (hébergé) | 0,211 |

## 4. Dépendance bloquante — infrastructure LAN

Ce chantier ne peut pas démarrer avant que l'utilisateur fournisse :

- l'accès/la configuration nécessaire pour héberger un modèle Kev (taille à
  déterminer selon le matériel réel du serveur `192.168.1.11` — GPU présent
  ou non) via **Ollama** sur ce serveur ;
- confirmation de la taille de modèle jouable (Kev-0.8B si CPU seul ;
  Kev-4B/9B si GPU CUDA disponible sur ce serveur).

Tant que cette information n'est pas fournie, **aucun code d'intégration
n'est écrit** — seul ce document de planification existe.

## 5. Plan d'implémentation déjà conçu (à exécuter une fois l'infrastructure fournie)

Deux nouveaux fichiers, miroir exact du patron déjà validé pour Ollama
(`m7_llm_fact_proposer_v0_1.py`) :

### `m7_jev_relation_choice_v0_1.py`

```python
@dataclass(frozen=True)
class JevProposal:
    subject: str
    relation: str
    object: str
    positive_prob: float
    model: str

def propose_relation_jev(*, text, all_relations, entity_candidates, client=None) -> Optional[JevProposal]:
    # appelle JevClient.decide(...) -- mêmes questions que jev_benchmark_v0_1.py
    # échoue fermé : réponse invalide / non-dict / choice manquant -> None, jamais fabriqué
    # GARDE-FOU (justifié par T05/T08/T09) : si proposal.subject == proposal.object -> None

def jev_evidence_for_prediction(proposal, *, candidate_id, predicted_object, evidence_index) -> EvidenceRecord:
    # identique à llm_evidence_for_prediction : SUPPORT si accord, CHALLENGE sinon
    # kind=EXTERNAL, analogy=True, jamais direct=True -- jamais GROUNDED_DIRECT
```

### `m7_corpus_from_jev_v0_1.py`

Miroir de `m7_corpus_from_llm_v0_1.py` : construit un corpus
`StructuralOutcomeRecord` à partir des propositions Jev/Kev,
`provenance="GROUNDED_ANALOGY"` systématique — jamais accepté comme fait
direct, toujours réinjecté dans le même `acquire_cold_start()`/évaluateur
que M4/M6 utilisent déjà.

### Configuration réseau

Mirror exact de `LAN_FALLBACK_HOST` (déjà dans `m7_llm_fact_proposer_v0_1.py`) :
`TYPESAFE_BASE_URL=http://192.168.1.11:<port_ollama_kev>`,
`TYPESAFE_API_KEY` optionnel (Kev n'exige pas de clé par défaut). Aucune
clé ni endpoint écrit en dur dans le code committé.

### Tests

Miroir de `test_m7_llm_fact_proposer_invariants_v0_1.py` + un test dédié au
garde-fou sujet≠objet + un test « live demo » optionnel (skip proprement
si le serveur LAN est injoignable, comme `test_m7_live_ollama_demo_v0_1.py`
le fait déjà pour Ollama).

### Garde-fous non négociables (repris du benchmark Sec. 2)

- Jamais `GROUNDED_DIRECT` — toujours `GROUNDED_ANALOGY`.
- Rejet si `subject == object` (bug T05/T08/T09).
- Le choix de relation reste dans le vocabulaire fermé par construction
  (type `Choice`), mais **le résultat n'est jamais accepté seul** pour une
  relation proche d'une autre (risque A05) — toujours combiné à d'autres
  preuves via l'évaluateur existant.
- M7 exclu de M1-M6/E20-D, sans exception.

## 5bis. Amendement de gouvernance (2026-09-22) : condition sémantique explicite

Une revue externe a alerté sur une zone sensible spécifique à JEV : la
distinction entre un test qui respecte réellement l'invariant « pas de
dictionnaire sémantique » et un test qui, même sans dictionnaire écrit à
la main, laisse fuiter de la sémantique par un autre canal. Analysée en
détail, formalisée et **vérifiée contre le benchmark Sec. 2 ci-dessus**
dans `documentation/SEMANTIC_ABSTRACTION_GOVERNANCE_V0_1.md`.

**Constat vérifié, pas supposé** : le benchmark Sec. 2 (22 cas contre
`jev-1.13.0`) n'était pas un test « sans information sémantique » — le cas
A05 (« conjoint » coercé en `EPOUX_DE`, confiance 0,98) prouve que Jev a
exploité sa propre connaissance linguistique du mot français contenu dans
le NOM de l'étiquette `EPOUX_DE`, sans qu'aucune glose n'ait été fournie
par ce projet. **Le benchmark Sec. 2 est donc reclassé `JEV-LABELED`**,
pas `JEV-STRICT` — voir le document de gouvernance pour la nomenclature à
trois niveaux (`STRICT` / `LABELED` / `GLOSSED`) qui remplace le clivage
binaire initialement proposé par la revue.

**Amendement au plan Sec. 5 ci-dessus**, à appliquer au moment de
l'implémentation (toujours bloquée sur l'infrastructure LAN/Ollama — ceci
ne lève pas ce blocage) :

- `propose_relation_jev()` gagne un paramètre `relation_vocabulary_mode`
  (`"STRICT"` : vocabulaire présenté sous forme de symboles opaques
  générés par le corpus, jamais les noms `EPOUX_DE`/`MERE_DE`/... ;
  `"LABELED"` : comportement déjà planifié ci-dessus, inchangé ;
  `"GLOSSED"` : étiquettes + définition linguistique explicite).
- `JevProposal` et chaque `EvidenceRecord` produit portent un champ
  `semantic_condition` correspondant — jamais de corpus mélangeant deux
  conditions sans pouvoir les distinguer a posteriori.
- Le développement futur doit **prioriser `JEV-STRICT`** : c'est la seule
  condition qui teste réellement l'hypothèse d'abstraction structurelle de
  ce projet ; `JEV-LABELED` (déjà mesuré) et `JEV-GLOSSED` restent des
  conditions expérimentales informatives mais secondaires par rapport à
  cet objectif.

## 6. Décision

**P8 = PRIORISÉ, bloqué sur infrastructure.** Prochaine action côté
assistant : aucune, en attente des informations de configuration Ollama/LAN
promises par l'utilisateur. Une fois fournies : implémenter les deux
fichiers Sec. 5, vérifier par exécution réelle contre le serveur Kev
hébergé, comparer les métriques mesurées ici (Sec. 2) à celles obtenues en
local, documenter l'écart honnêtement (comme pour chaque comparaison de ce
projet), puis décider de l'adoption.
