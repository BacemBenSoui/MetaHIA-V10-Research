# MetaHIA V10 — P8 : modèle de décision typée local (Jev/Kev) pour M7 v0.1

Date : 2026-09-21 (implémentation réelle + connectivité confirmée +
deux benchmarks multi-cas complets, dont P8.1 -- STRICT enriched
few-shot -- 2026-09-22, voir Sec. 3bis/5/6bis/6ter/6quater)
Statut : **TWO_BENCHMARKS_COMPLETE, CLASSIFICATION_REFINED.** Le code
(`m7_jev_relation_choice_v0_1.py` + `m7_jev_benchmark_v0_1.py` +
`m7_jev_benchmark_v0_2.py`) est écrit, testé (50 tests) et **vérifié
contre le vrai serveur Kev-0.8B de l'utilisateur**, exposé sur
`192.168.1.11:8009` (**Kev n'est PAS hébergé via Ollama**, correction
d'une hypothèse fausse de ce document initial, voir Sec. 3bis). Deux
résultats réels : 22 cas × 3 conditions (Sec. 6ter), puis 39 cas × 3
conditions après enrichissement du few-shot STRICT (Sec. 6quater,
demandé explicitement pour distinguer un déficit d'exemples d'une
limite réelle du mécanisme). Réponse : robustesse adversariale de STRICT
16,7 % → 63,2 % (le déficit était bien largement un déficit
d'exemples), mais précision positive en baisse (62,5 % → 50,0 %),
systématique, pas aléatoire. **Découverte la plus robuste, confirmée
deux fois indépendamment** : Kev-0.8B confond `EPOUX_DE`/`EPOUSE_DE` en
LABELED et STRICT (sens opposés), jamais en GLOSSED. Classification
retenue : LABELED = candidat opérationnel M7 (meilleur compromis ET
meilleure calibration mesurée) ; STRICT = test scientifique
d'abstraction (mécanisme validé sur l'adversarial général, pas encore
sur le quasi-synonyme) ; GLOSSED = condition maximale d'assistance
sémantique (précision parfaite, mais pire calibration -- confiant à tort
sur ses erreurs). Reste : construire `m7_corpus_from_jev_v0_1.py` sur
LABELED, en gardant la confusion EPOUX_DE/EPOUSE_DE comme point à
corriger avant adoption définitive.

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

## 6bis. Premier test réel de bout en bout (2026-09-22) — connectivité confirmée

L'utilisateur a lancé Kev-0.8B sur `192.168.1.11`, d'abord lié à
`127.0.0.1:8009` (confirmé injoignable depuis ce dépôt — `curl` direct,
« Connection refused », cohérent avec la Sec. 3bis) puis exposé sur les
trois interfaces réseau de la machine (`0.0.0.0:8009`, choix retenu par
l'utilisateur plutôt que le forward `socat` initialement proposé). Vérifié
par appel HTTP direct depuis ce dépôt (`GET /v1/models` réussit,
`run: jaredpalmer/kev-0.8b`, `device: cpu`, `temperature: 2.406`).

**Précision importante donnée à l'utilisateur pendant ce chantier** :
« STRICT »/« LABELED »/« GLOSSED » ne sont **pas** des modes du serveur
Kev lui-même — Kev n'expose que `POST /v1/systemone` (+ `/permute`,
`/separate`, `GET /v1/models`). C'est une convention construite
entièrement côté client, dans `propose_relation_jev()` de ce dépôt, qui
remplit le champ natif `criteria` différemment selon le mode avant
d'appeler le même endpoint standard. Une session opérant directement sur
le serveur (sans visibilité sur ce dépôt) avait cherché « LABELED/STRICT »
dans le code de `jaredpalmer/kev` et ne l'avait, à raison, pas trouvé.

**Premier appel réel, les trois modes, sur la même phrase** (« Alice est
la mère de Bob. », vocabulaire `EPOUX_DE`/`EPOUSE_DE`/`MERE_DE`/`PERE_DE`) :

| Mode | Réponse | Probabilité | Détail |
|---|---:|---:|---|
| STRICT | `MERE_DE` (correct) | **0,69** | Résolu depuis le symbole opaque `R3`, avec 3 exemples travaillés (`Claire`→`MERE_DE`, `Eve`→`MERE_DE`, `Guy`→`PERE_DE`) — aucune étiquette lisible envoyée à Kev |
| LABELED | `MERE_DE` (correct) | **0,85** | Étiquettes réelles, aucune définition |
| GLOSSED | `MERE_DE` (correct) | **0,92** | Étiquettes réelles + définition explicite par relation |

**Lecture honnête, pas sur-interprétée** : les trois modes trouvent la
bonne réponse, et le gradient de confiance (STRICT < LABELED < GLOSSED)
va dans le sens attendu par l'hypothèse de ce projet — moins
d'information sémantique fournie, confiance mesurée plus basse. **Ceci
est un test de fumée sur un seul cas (n=1), pas un benchmark contrôlé** :
aucune conclusion statistique n'en est tirée ici ; il démontre seulement
que (a) le pipeline fonctionne réellement de bout en bout contre un
serveur externe, jamais testé avant ce jour, et (b) le mécanisme STRICT
fonctionne concrètement — Kev peut résoudre une relation depuis un
symbole opaque et des exemples structurels seuls, sans jamais voir le nom
réel de la relation. C'est la première preuve empirique, même minimale,
que l'hypothèse d'abstraction structurelle de ce projet tient pour un
modèle de décision externe, pas seulement pour le moteur K3 lui-même.

Couvert par 3 nouveaux tests « live demo »
(`tests/test_m7_jev_live_demo_v0_1.py`, un par mode, tous passants
contre le serveur réel — pas de valeur figée, seulement les propriétés
structurelles garanties, puisqu'un modèle externe réel n'est jamais
déterministe d'une exécution à l'autre).

## 6ter. Benchmark multi-cas réel (2026-09-22) — 22 cas × 3 conditions contre Kev-0.8B

**Précision méthodologique préalable, à ne pas passer sous silence** :
les 22 cas originaux du benchmark Jev officiel (Sec. 2) n'ont **jamais
été committés dans ce dépôt** — vérifié par recherche directe avant
d'écrire quoi que ce soit, pas supposé. Ce chantier construit donc un
**nouveau corpus**, de même échelle et des mêmes catégories
adversariales que l'original (16 cas positifs + 6 adversariaux), mais ce
n'est **pas** une rejouée littérale de l'original — voir
`corpus/jev_benchmark_cases_v0_1.json` pour le détail et cette réserve
explicite dans son propre `purpose`.

**Extension nécessaire du vocabulaire** : sans option « aucune relation
», l'appel `choice` de Kev force un choix parmi les 4 relations réelles
même pour une phrase qui n'en exprime aucune — exactement le risque de
coercition que les cas A04/A05 originaux mesuraient déjà. Une cinquième
option `AUCUNE` a donc été ajoutée au vocabulaire fermé pour ce
benchmark spécifiquement (`m7_jev_benchmark_v0_1.py`), sans modifier
`propose_relation_jev()` — elle est simplement passée comme n'importe
quel autre membre de `all_relations`.

**Résultat réel** (`validation/jev_benchmark_v0_1_results_2026-09-22.json`,
66 appels HTTP réels contre `192.168.1.11:8009`, ~57s, **reproduit à
l'identique sur deux exécutions successives** — Kev-0.8B est déterministe
ici, pas seulement calibré) :

| Condition | Précision globale | Précision (16 positifs) | Précision (6 adversariaux) | Confiance moyenne |
|---|---:|---:|---:|---:|
| STRICT | 50,0 % | 62,5 % | **16,7 %** | 0,51 |
| LABELED | 72,7 % | 75,0 % | **66,7 %** | 0,68 |
| GLOSSED | 86,4 % | **100,0 %** | 50,0 % | 0,84 |

**Sur les cas positifs, le gradient attendu se confirme nettement** :
STRICT (62,5 %) < LABELED (75 %) < GLOSSED (100 %) — GLOSSED résout
**tous** les 16 cas positifs correctement.

**Sur les cas adversariaux, le résultat est différent — et plus
instructif — que ne le suggérait le test de fumée à un cas de la
Sec. 6bis. Rapporté tel quel, pas lissé** :

| Cas | Catégorie | STRICT | LABELED | GLOSSED |
|---|---|---|---|---|
| A01 | Négation | ❌ (PERE_DE) | ✅ | ✅ |
| A02 | Question | ❌ (PERE_DE) | ❌ (PERE_DE) | ❌ (PERE_DE) |
| A03 | Conditionnel | ❌ (EPOUX_DE) | ❌ (EPOUSE_DE) | ❌ (EPOUX_DE) |
| A04 | Relation hors-vocabulaire | ❌ (MERE_DE) | ✅ | ✅ |
| A05 | Quasi-synonyme (« conjoint ») | ❌ (EPOUX_DE) | ✅ | ❌ (EPOUX_DE, confiance 0,94) |
| A06 | Aucune affirmation | ✅ | ✅ | ✅ |

Deux constats réels, non anticipés, à ne pas arrondir :

1. **STRICT échoue sur presque tous les cas adversariaux nuancés**
   (négation, question, conditionnel, hors-vocabulaire, quasi-synonyme) —
   ne réussit que le cas sans aucun contenu relationnel du tout (A06). Les
   5 exemples travaillés (1 par classe, dont 1 pour `AUCUNE`) ne
   suffisent visiblement pas à faire apprendre à Kev la frontière fine de
   `AUCUNE` face à des marqueurs grammaticaux (négation, interrogation,
   conditionnel) à partir d'un seul exemple structurel par classe — ce
   n'est pas une réfutation de l'hypothèse d'abstraction en soi (rien
   n'indique que plus d'exemples ne résoudrait pas ceci ; non testé ici),
   mais une limite réelle et mesurée du protocole minimal actuel.
2. **GLOSSED fait moins bien que LABELED sur les cas adversariaux
   (50 % contre 66,7 %), contrairement au gradient attendu** — et la
   raison est précise, pas un bruit statistique : le cas A05 (« Ugo est
   le conjoint de Vicky ») est correctement rejeté en LABELED
   (`AUCUNE`, confiance 0,56) mais **coercé en `EPOUX_DE` avec une
   confiance de 0,94 en GLOSSED** — une reproduction quasi exacte de
   l'échec A05 déjà mesuré sur Jev officiel (Sec. 2 : « conjoint » coercé
   en `EPOUX_DE`, confiance 0,98). La définition explicite fournie
   (« X est l'époux de Y ») semble avoir **augmenté** la propension de
   Kev à généraliser sémantiquement au-delà du vocabulaire fermé plutôt
   que de l'en empêcher — l'effet inverse de ce que GLOSSED était censé
   apporter. Ceci confirme, avec un second modèle indépendant
   (Kev-0.8B, pas seulement Jev hébergé), que le risque A05 identifié
   dès le premier benchmark est réel et robuste, pas un artefact d'un
   seul modèle.

**Lecture honnête d'ensemble** : le gradient STRICT < LABELED < GLOSSED
n'est **pas** une loi générale — il tient pour les cas positifs
(signal clair), mais pas pour la robustesse adversariale, où LABELED >
GLOSSED > STRICT. Ce sont deux axes de mesure différents, qui ne doivent
plus être supposés covarier dans le même sens sans le vérifier à chaque
fois.

Couvert par 8 tests déterministes
(`tests/test_m7_jev_benchmark_v0_1.py`, client factice) : forme du
corpus (22 cas, 16 positifs + 6 adversariaux, vocabulaire à 5 relations),
**disjonction vérifiée programmatiquement** entre les entités des
exemples travaillés et celles du corpus de test (pas seulement affirmée
en commentaire), couverture des glosses/exemples travaillés pour les 5
relations y compris `AUCUNE`, exactitude de l'agrégation
(précision/confiance moyenne/comptage honnête des « pas de réponse »),
STRICT reçoit bien les exemples travaillés et LABELED/GLOSSED non,
sérialisation JSON du rapport.

**Prochaine étape, pas encore faite** : construire
`m7_corpus_from_jev_v0_1.py` (Sec. 5) en s'appuyant sur ce résultat réel
— décision d'adoption à prendre en tenant compte du compromis mesuré
(GLOSSED maximise la précision positive mais dégrade la robustesse
adversariale ; LABELED est le meilleur compromis global sur ce corpus).
Envisager aussi d'enrichir `WORKED_EXAMPLES` en mode STRICT (plusieurs
exemples par classe, y compris des exemples de négation/question pour
`AUCUNE`) pour vérifier si l'échec adversarial de STRICT est un
artefact du few-shot minimal ou une limite plus profonde.

## 6quater. P8.1 — STRICT enriched few-shot (2026-09-22) : 39 cas × 3 conditions, résultat riche et non lissé

Demandé explicitement, avec un cadre de décision à trois issues (Cas A :
few-shot insuffisant, le problème se résout ; Cas B : positifs
s'améliorent mais l'adversarial reste faible, limite réelle du
mécanisme ; Cas C : aucun changement). **Précision méthodologique** :
`corpus/jev_benchmark_cases_v0_2.json` (nouveau fichier, v0.1 laissé
inchangé) sépare pour la première fois un vrai `demonstration_set` (24
exemples : 3 par relation réelle + 2 par sous-catégorie adversariale) de
39 cas d'évaluation (16 positifs inchangés + 19 adversariaux, 3-4
paraphrases par catégorie à sujet/objet constants + 4 cas
« positive_paraphrase » testant une structure syntaxique jamais montrée
dans aucune démonstration — le test H1 vs H2 demandé). Disjonction
démonstration/évaluation vérifiée programmatiquement (pas seulement
affirmée), même discipline que P4-T.2 v0.2.

**Résultat réel** (`validation/jev_benchmark_v0_2_results_2026-09-22.json`,
117 appels HTTP réels, ~199s) :

| Condition | Global | Positifs (16) | Adversariaux (19) | Paraphrase struct. (4) | « conjoint » résiste ? | Brier | ECE | Confiance moy. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| STRICT | 56,4 % | 50,0 % | **63,2 %** | 50,0 % | ❌ Non | 0,640 | 0,195 | 0,395 |
| LABELED | 74,4 % | 75,0 % | 73,7 % | 75,0 % | **✅ Oui** | **0,377** | **0,137** | 0,646 |
| GLOSSED | 74,4 % | **100,0 %** | 47,4 % | 100,0 % | ❌ Non | 0,470 | 0,222 | 0,821 |

**Réponse au cadre A/B/C, sur l'axe adversarial : Cas A confirmé, sans
ambiguïté.** La robustesse adversariale de STRICT passe de 16,7 % (v0.1,
5 exemples) à **63,2 %** (v0.2, 24 exemples) — le déficit few-shot
minimal de v0.1 explique bien la majeure partie de l'échec observé.
C'est un résultat clair, positif, qui valide l'approche.

**Mais un résultat inattendu, non lissé, sur l'axe positif** : la
précision positive de STRICT **baisse** (62,5 % → 50,0 %) — et ce n'est
pas du bruit, c'est **systématique** : les 4 cas `PERE_DE` sont
**tous** prédits `MERE_DE` (nouveau dans v0.2 ; v0.1 avait une erreur
partielle, moins systématique, dans l'autre sens). Ceci mérite une
investigation séparée (hypothèse non vérifiée : effet d'ordre/récence
dans le prompt few-shot, les exemples `MERE_DE` et `PERE_DE` étant
regroupés consécutivement dans `demonstration_set` — non testé ici,
piste pour un P8.2).

**La découverte la plus robuste de tout ce chantier, confirmée deux fois
indépendamment (v0.1 ET v0.2, corpus différents)** : **Kev-0.8B confond
systématiquement `EPOUX_DE` et `EPOUSE_DE`**, dans LABELED comme dans
STRICT, mais **jamais** en GLOSSED :

| Condition | v0.1 (T09-T16) | v0.2 (T09-T16 + P03) |
|---|---|---|
| STRICT | 4/4 `EPOUSE_DE` prédits `EPOUX_DE` | identique, + P03 (paraphrase) aussi confondu |
| LABELED | 4/4 `EPOUX_DE` prédits `EPOUSE_DE` (sens inverse !) | identique, + P03 confondu |
| GLOSSED | 8/8 corrects | 8/8 + P03 corrects |

Les deux conditions sans glose se trompent, **dans des sens opposés
l'une de l'autre** (LABELED biaise vers `EPOUSE_DE`, STRICT vers
`EPOUX_DE`) — ce n'est donc pas un biais de position/ordre partagé, mais
une incapacité réelle à distinguer les deux sans l'indice de genre
explicite. GLOSSED, avec ses définitions (« le mari » / « la femme »),
résout ce cas précis **parfaitement, deux fois**. Lecture honnête : ce
n'est pas que « plus d'information sémantique aide toujours » (le
résultat `EPOUX_DE`/`conjoint` de la Sec. 6ter montre le contraire) —
c'est que **l'information sémantique aide précisément quand elle lève
une ambiguïté que le nom seul (réel ou opaque) ne lève pas**, et nuit
précisément quand elle invite le modèle à généraliser au-delà du
vocabulaire fermé. Deux mécanismes différents, pas un seul « plus =
mieux ».

**Test H1 vs H2 (`positive_paraphrase`, structure jamais démontrée)** :
les trois conditions généralisent à la nouvelle syntaxe
(« La `RELATION` de Y s'appelle X ») dans une mesure réelle — STRICT
50 % (2/4), LABELED 75 % (3/4, le seul échec étant à nouveau la
confusion `EPOUX_DE`/`EPOUSE_DE`), GLOSSED 100 %. Aucune des trois ne
s'effondre à 0 %, ce qui est en soi une preuve, même modeste, contre
l'hypothèse H1 pure (mémorisation de motif de surface uniquement) —
mais l'échantillon (4 cas) est trop petit pour trancher plus finement.

**Calibration multiclasses, mesurée pour la première fois (Brier +
ECE)** : LABELED est le **mieux calibré** des trois (Brier 0,377, ECE
0,137) — pas seulement le meilleur compromis en précision brute. GLOSSED
a le **pire ECE** (0,222) malgré sa précision positive parfaite : sa
confiance moyenne élevée (0,821) inclut une confiance **tout aussi
élevée sur ses erreurs** (les 4 cas `conjoint`, confiance 0,83 à 0,96
alors qu'ils sont incorrects) — GLOSSED n'est donc pas seulement moins
robuste sur l'adversarial, il est **confiant à tort** sur précisément
les cas où la discipline « pas de dictionnaire sémantique, pas de
coercition vers une relation voisine » compte le plus. C'est un
argument quantitatif, pas seulement qualitatif, contre une adoption
aveugle de GLOSSED.

**« conjoint » reste-t-il `AUCUNE` sur les 4 paraphrases (A05a-d) ?**
Non pour STRICT (4/4 coercé en `EPOUX_DE`, confiance ~0,30-0,34 — une
coercition peu confiante, mais une coercition quand même). **Oui pour
LABELED** (4/4 correctement `AUCUNE`, confiance 0,47-0,72) — un résultat
meilleur que le test à un cas de la Sec. 6bis ne le laissait présager,
confirmé sur 4 formulations différentes, pas une seule. Non pour GLOSSED
(4/4 coercé en `EPOUX_DE`, confiance élevée 0,83-0,96) — confirme, avec
un échantillon élargi, l'échec déjà mesuré en Sec. 6ter sur un seul cas.

39 cas × 3 conditions couverts par 15 tests déterministes
(`tests/test_m7_jev_benchmark_v0_2.py`) : forme du corpus, disjonction
démonstration/évaluation vérifiée, contrôle expérimental (sujet/objet
constants par catégorie adversariale), matrice de confusion, Brier
multiclasses et ECE (vérifiés contre des valeurs calculées à la main,
même formule que `m6_structural_learning_v0_1.py`, réimplémentation
autonome car ce module est couplé à un autre modèle de données), le
test de régression permanent « conjoint reste `AUCUNE` ». **Deux bugs
réels trouvés par ces tests avant tout run réseau** : `positive_accuracy`
utilisait `category.startswith("positive")`, qui capturait aussi
`positive_paraphrase` par accident — corrigé pour une comparaison
d'égalité exacte de catégorie.

**Extension nécessaire de `m7_jev_relation_choice_v0_1.py`** (module
existant modifié en place, pas une nouvelle version — travail en cours,
pas encore verrouillé) : `JevDecideClient.decide()` retourne désormais
`(choix, probabilité_choisie, distribution_complète)` au lieu de
`(choix, probabilité_choisie)` seul — nécessaire pour calculer un vrai
Brier/ECE multiclasses (`positive_prob` seul ne dit rien de la
répartition sur les options non choisies). Tous les clients factices des
tests existants mis à jour en conséquence ; `JevProposal` porte
désormais `probabilities`, et `jev_evidence_for_prediction()` la
transmet dans `metadata["probabilities"]`.

## 6. Décision

**P8 = `TWO_BENCHMARKS_COMPLETE, CLASSIFICATION_REFINED` (2026-09-22).**
`m7_jev_relation_choice_v0_1.py` implémente le vrai contrat
`POST /v1/systemone` (Sec. 3bis/5), désormais avec distribution de
probabilité complète (nécessaire au Brier/ECE de Sec. 6quater). 50 tests
au total (24 relation-choice + 3 live demo + 8 benchmark v0.1 + 15
benchmark v0.2/P8.1) — **tous exécutés, dont 22 cas × 3 conditions
(v0.1, Sec. 6ter) puis 39 cas × 3 conditions (v0.2/P8.1, Sec. 6quater)
en conditions réelles contre le serveur Kev-0.8B de l'utilisateur**.

**Réponse au cadre A/B/C posé pour P8.1** : Cas A confirmé sur l'axe
adversarial (STRICT 16,7 % → 63,2 % avec le few-shot enrichi — le
déficit de v0.1 était bien largement un déficit d'exemples), mais avec
un résultat inattendu non anticipé par le cadre initial : la précision
positive de STRICT a **baissé** (62,5 % → 50,0 %), de façon systématique
(confusion `PERE_DE`→`MERE_DE` nouvelle en v0.2), pas aléatoire —
piste ouverte pour un P8.2 (effet d'ordre des exemples few-shot, non
testé ici).

**La classification provisoire proposée est adoptée, affinée par les
données** :

```text
JEV/KEV STRICT   = test scientifique d'abstraction — mécanisme validé
                    pour la robustesse adversariale générale (Cas A),
                    mais échoue encore spécifiquement sur le
                    quasi-synonyme (« conjoint ») et sur EPOUX_DE/EPOUSE_DE
JEV/KEV LABELED  = candidat opérationnel M7 — meilleur compromis
                    ET meilleure calibration mesurée (Brier 0,377,
                    ECE 0,137) ; résiste à « conjoint » sur 4/4
                    paraphrases ; reste à corriger : confusion
                    EPOUX_DE/EPOUSE_DE (biais inverse de STRICT)
JEV/KEV GLOSSED  = condition maximale d'assistance sémantique —
                    précision positive parfaite (100 %, deux fois),
                    mais pire ECE (0,222) : confiant à tort précisément
                    sur les cas de coercition « conjoint »
```

**Découverte la plus robuste, confirmée deux fois indépendamment** :
Kev-0.8B confond `EPOUX_DE`/`EPOUSE_DE` en LABELED et en STRICT (dans
des sens opposés), mais jamais en GLOSSED — l'information sémantique
explicite aide précisément quand elle lève une ambiguïté que le nom seul
ne lève pas, et nuit précisément quand elle invite à généraliser
au-delà du vocabulaire fermé (« conjoint »). Ce ne sont pas deux facettes
du même phénomène.

Décision d'adoption pour `m7_corpus_from_jev_v0_1.py` (Sec. 5, toujours
pas écrit) : **LABELED reste le candidat par défaut le mieux justifié
par les données** (meilleur compromis global, meilleure calibration,
seule condition à passer le test de non-coercition sur 4/4 paraphrases)
— mais le corriger sur la confusion EPOUX_DE/EPOUSE_DE avant adoption
définitive reste ouvert, pas encore fait.
