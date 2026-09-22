# MetaHIA V10 — P8 : modèle de décision typée local (Jev/Kev) pour M7 v0.1

Date : 2026-09-21 (implémentation réelle 2026-09-22, voir Sec. 3bis/5/6)
Statut : **IMPLEMENTED_AWAITING_LIVE_CONNECTIVITY.** Le code
(`m7_jev_relation_choice_v0_1.py`) est écrit et testé (22 tests
réseau-free + 1 live demo qui skip proprement). Ce qui reste : que
l'utilisateur lance le serveur Kev lui-même sur `192.168.1.11` (Sec. 3bis
donne la commande exacte — **Kev n'est PAS hébergé via Ollama**, correction
d'une hypothèse fausse de ce document initial, voir Sec. 3bis) ; cette
session n'a pas d'accès shell à cette machine, seulement un accès réseau
HTTP déjà vérifié.

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

1. Compatible fil-à-fil avec `jev_client_v0_1.py`, utilisé pour produire
   le benchmark Sec. 2 (`POST /v1/systemone`, mêmes types
   `noul`/`choice`/`score`) — zéro changement de code, seul
   `TYPESAFE_BASE_URL` change. **Correction (2026-09-22)** : cette phrase
   affirmait à tort que `jev_client_v0_1.py` était « déjà présent dans ce
   dépôt » — vérifié par recherche directe, **il ne l'est pas** ; il
   n'existait que dans le zip externe
   `MetaHIA-V10-Jev-Parsing-Benchmark-v0.1.zip` exécuté en isolation pour
   produire ce benchmark, jamais committé ici. Le squelette
   `m7_jev_relation_choice_v0_1.py` (Sec. 5bis, `documentation/SEMANTIC_ABSTRACTION_GOVERNANCE_V0_1.md`
   Sec. 8ter) définit sa propre interface `client.decide(...)` injectable,
   sans dépendre de ce fichier absent.
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

## 3bis. Correction majeure (2026-09-22) : Kev n'est PAS hébergé via Ollama

Cette section corrige une hypothèse fausse du plan initial (Sec. 4
ci-dessous, telle qu'écrite le 2026-09-21). En préparant réellement
l'implémentation (l'utilisateur ayant confirmé l'infrastructure LAN
prête, Ollama actif sur `192.168.1.11:11434` — vérifié par appel HTTP
direct, modèles présents : `gpt-oss:20b`, `deepseek-coder-v2:16b`,
`qwen2.5-coder:3b`, `qwen2.5-coder:7b`, aucun modèle Jev/Kev), la lecture
directe du dépôt `jaredpalmer/kev` (README + `kev/serve.py`, via l'API
GitHub, pas un résumé) montre que **Kev n'est jamais servi via Ollama** :
c'est un serveur FastAPI/uvicorn autonome (`python -m kev.serve`, géré par
`uv`), qui charge lui-même un checkpoint (adaptateur LoRA + tête pointeur
sur une base Qwen3.5) et écoute `POST /v1/systemone` directement — pas un
GGUF importable dans Ollama. **Toute planification antérieure supposant
« héberger Kev via Ollama » était donc incorrecte** et est corrigée ici,
pas silencieusement remplacée.

**API réelle, vérifiée** (contrairement à la version simplifiée
initialement supposée en Sec. 5) :

```jsonc
POST /v1/systemone
{
  "state": "texte à évaluer",
  "model": "kev-latest",
  "questions": {
    "<id>": {                                   // l'id n'est jamais vu par le modèle
      "type": "choice",
      "instructions": "…",
      "criteria": {"OPTION_A": "description ou null", "OPTION_B": null}
    }
  }
}
```

Réponse : `answers["<id>"] = {"choice": "OPTION_A", "confidence": ..., "probabilities": {"OPTION_A": 0.91, ...}}`.

**Ceci confirme et simplifie le protocole STRICT/LABELED/GLOSSED**
(`documentation/SEMANTIC_ABSTRACTION_GOVERNANCE_V0_1.md` Sec. 3) : le
champ `criteria` de Kev EST le mécanisme natif pour les trois conditions
— une description `null` par option (nom opaque = STRICT, nom réel =
LABELED) ou une description explicite (nom réel + texte = GLOSSED) —
aucune simulation par texte libre n'est nécessaire, contrairement à ce
que le squelette précédent supposait.

**Contrainte réseau vérifiée** : `kev/serve.py::main()` appelle
`uvicorn.run(app, host="127.0.0.1", port=a.port)` **en dur, sans option
`--host`** — le serveur n'écoute donc PAS sur l'interface LAN par défaut,
même une fois lancé. Son propre README le dit explicitement : *« The
server binds to 127.0.0.1 and has no authentication. Keep it local unless
you add authentication yourself »*. Pour le rendre joignable depuis ce
dépôt (qui a un accès réseau réel et vérifié à `192.168.1.11`, mais pas
d'accès shell/SSH à cette machine — seul l'utilisateur peut exécuter des
commandes dessus), l'utilisateur doit lancer un petit script qui
surcharge le binding, PAS modifier le paquet `kev` lui-même :

```bash
git clone https://github.com/jaredpalmer/kev.git && cd kev
uv sync --extra serve
cat > serve_lan.py <<'PYEOF'
import sys
import uvicorn
_original_run = uvicorn.run
def _run_on_all_interfaces(app, **kwargs):
    kwargs["host"] = "0.0.0.0"
    return _original_run(app, **kwargs)
uvicorn.run = _run_on_all_interfaces
from kev.serve import main
sys.argv = ["kev.serve", "--run", "jaredpalmer/kev-0.8b", "--port", "8008"]
main()
PYEOF
uv run --extra serve python serve_lan.py
```

**Choix de taille pour ce premier test** : `kev-0.8b` (le plus petit,
~0,8B de paramètres, fonctionne sur CPU seul si aucun GPU n'est
disponible sur ce serveur — vérifié dans `kev/device.py`, qui retombe
proprement sur `cpu` si ni CUDA ni MPS ne sont détectés). Une fois la
connectivité confirmée par ce dépôt, l'utilisateur peut relancer avec
`--run jaredpalmer/kev-4b` (recommandé par le README du projet Kev
lui-même comme point de départ si le matériel le permet) ou `kev-9b`
sans changer quoi que ce soit côté MetaHIA — seul `--run` change.

**Avertissement de sécurité, à ne pas passer sous silence** : le serveur
Kev n'a aucune authentification par construction. L'exposer sur
`0.0.0.0` le rend joignable par toute machine du même réseau local — un
risque déjà accepté implicitement dans ce projet pour Ollama lui-même
(`LAN_FALLBACK_HOST`, également sans authentification), donc cohérent
avec la tolérance au risque déjà en vigueur sur ce LAN de sandbox, mais
explicitement signalé ici plutôt que passé sous silence.

## 4. Dépendance bloquante — infrastructure LAN

**État (2026-09-22)** : l'utilisateur a confirmé l'infrastructure prête et
Ollama actif sur `192.168.1.11` (vérifié par appel HTTP direct) — mais
**aucun modèle Jev/Kev n'est encore téléchargé/lancé**. Le blocage
d'origine (accès réseau au serveur) est donc levé ; il reste un blocage
plus étroit et actionnable : le serveur `kev.serve` lui-même doit être
lancé sur `192.168.1.11` par l'utilisateur (Sec. 3bis ci-dessus donne la
commande exacte) — cette session n'a pas d'accès shell/SSH à cette
machine, seulement un accès réseau HTTP déjà vérifié vers les ports
qu'elle expose. Une fois `serve_lan.py` lancé et le port `8008` (ou celui
choisi) confirmé joignable, l'implémentation Sec. 5 ci-dessous peut être
testée de bout en bout en conditions réelles.

## 5. Implémentation (2026-09-22, FAIT — connectivité réelle en attente de Sec. 3bis)

`m7_jev_relation_choice_v0_1.py` implémente désormais le vrai contrat
`POST /v1/systemone` (Sec. 3bis), pas l'esquisse initialement supposée
ci-dessous (conservée seulement pour mémoire de ce qui a changé) :

```python
class JevKevSystemOneClient:
    def __init__(self, base_url: str, *, model: str = "kev-latest", timeout: float = 60.0): ...
    def decide(self, *, state: str, instructions: str, criteria: Mapping[str, Optional[str]]) -> Optional[Tuple[str, float]]: ...
    def reachable(self) -> bool: ...  # GET /v1/models, sonde légère

@dataclass(frozen=True)
class JevProposal:
    subject: str; relation: str; object: str; positive_prob: float
    model: str; semantic_condition: str; raw_response: str

def propose_relation_jev(*, text, subject, obj, all_relations, semantic_condition, client, ...) -> Optional[JevProposal]:
    # construit criteria = {nom: description_ou_None} selon semantic_condition
    # (STRICT: symboles opaques, descriptions toujours None, + exemples travaillés obligatoires
    #  LABELED: noms réels, descriptions None  |  GLOSSED: noms réels + description)
    # échoue fermé : réponse invalide / hors-vocabulaire / probabilité malformée -> None
    # GARDE-FOU (justifié par T05/T08/T09) : sujet == objet -> None, avant même l'appel

def jev_evidence_for_prediction(proposal, *, candidate_id, predicted_relation, evidence_index) -> EvidenceRecord:
    # identique à llm_evidence_for_prediction : SUPPORT si accord, CHALLENGE sinon
    # confidence = positive_prob réel (calibré) ; metadata["semantic_condition"] posé
```

`m7_corpus_from_jev_v0_1.py` (miroir de `m7_corpus_from_llm_v0_1.py`,
construisant un corpus complet à partir des propositions JEV/Kev réelles)
**n'est pas encore écrit** — étape suivante logique une fois la
connectivité réelle confirmée (Sec. 3bis), pas avant : construire un
corpus complet sur un client encore jamais joint en pratique aurait
produit des chiffres non vérifiables.

### Configuration réseau

`JevKevSystemOneClient(base_url)` ne lit aucune variable d'environnement
lui-même — l'appelant fournit l'URL. Le seul endroit où une adresse LAN
concrète apparaît dans ce dépôt est
`tests/test_m7_jev_live_demo_v0_1.py` (`KEV_BASE_URL`, défaut
`http://192.168.1.11:8008`), exactement le même patron que `LOCAL_HOST`
pour Ollama. Aucune clé API n'est nécessaire par défaut (Kev n'en exige
pas).

### Tests

`tests/test_m7_jev_relation_choice_v0_1.py` (22 tests, réseau-free :
bijection stricte, opacité STRICT vérifiée par inspection directe,
LABELED/GLOSSED, garde-fous, `EvidenceRecord`, et le parsing de réponse
réel de `JevKevSystemOneClient` avec un `urlopen` simulé) +
`tests/test_m7_jev_live_demo_v0_1.py` (1 test, skip proprement si le
serveur LAN est injoignable — actuellement le cas, voir Sec. 3bis/4 —
mirroring `test_m7_live_ollama_demo_v0_1.py` exactement).

### Garde-fous non négociables (repris du benchmark Sec. 2), tous testés

- Jamais `GROUNDED_DIRECT` — toujours `GROUNDED_ANALOGY`.
- Rejet si `subject == object` (bug T05/T08/T09), avant même l'appel réseau.
- Une réponse hors du vocabulaire fermé est rejetée, jamais coercée vers
  la relation la plus proche (risque A05).
- Une probabilité hors `[0,1]` échoue fermé plutôt que de faire planter
  `EvidenceRecord.validate()` plus tard.
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

**Amendement au plan Sec. 5 ci-dessus — mis à jour deux fois** : un
premier squelette sans appel réseau a été écrit le 2026-09-22 (pas de
`client` réel, `relation_vocabulary_mode` deviné avant vérification de
l'API), puis **remplacé le même jour** par la vraie implémentation
(Sec. 3bis/5 ci-dessus) une fois l'API réelle de `jaredpalmer/kev` lue
directement. `propose_relation_jev()` porte désormais
`semantic_condition` (`STRICT`/`LABELED`/`GLOSSED`), implémenté via le
mécanisme natif de Kev (`criteria: {nom: description_ou_None}`), pas une
simulation en texte libre. `JevProposal` et chaque `EvidenceRecord`
produit portent le champ `semantic_condition` correspondant — jamais de
corpus mélangeant deux conditions sans pouvoir les distinguer a
posteriori. Le développement futur doit **prioriser `JEV-STRICT`** :
c'est la seule condition qui teste réellement l'hypothèse d'abstraction
structurelle de ce projet ; `JEV-LABELED` (déjà mesuré contre Jev
officiel) et `JEV-GLOSSED` restent des conditions expérimentales
informatives mais secondaires par rapport à cet objectif.

## 6. Décision

**P8 = `IMPLEMENTED_AWAITING_LIVE_CONNECTIVITY` (2026-09-22).**
`m7_jev_relation_choice_v0_1.py` implémente le vrai contrat
`POST /v1/systemone` (Sec. 3bis/5), 23 tests dont 22 réseau-free et 1
« live demo » qui skip proprement tant que le serveur n'est pas joignable
(état actuel, confirmé par sonde directe : Ollama répond sur
`192.168.1.11:11434`, rien n'écoute encore sur le port Kev). Prochaine
action côté assistant : aucune tant que l'utilisateur n'a pas lancé
`serve_lan.py` (Sec. 3bis) sur `192.168.1.11` — cette session n'a pas
d'accès shell à cette machine. Une fois lancé et confirmé joignable :
exécuter le test « live demo », comparer les métriques obtenues en LABELED
aux chiffres du benchmark officiel Jev (Sec. 2), documenter l'écart
honnêtement (comme pour chaque comparaison de ce projet), lancer un
premier test réel en `STRICT` (l'objectif prioritaire, jamais mesuré
avant ce chantier), puis décider de l'adoption dans le pipeline d'évidence
M7 (`m7_corpus_from_jev_v0_1.py`, pas encore écrit — Sec. 5).
