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

## 6quinquies. P8.2 — Ablation d'ordre des démonstrations, STRICT uniquement (2026-09-22) : effet causal réel, mais pas celui attendu

Demandé explicitement en réponse à P8.1 : la baisse de précision positive
de STRICT (62,5 % → 50,0 %) était-elle un effet d'ordre/récence des
démonstrations (`MERE_DE` immédiatement suivi de `PERE_DE` dans
`demonstration_set`, vérifié directement) ou une limite réelle du
mécanisme ? **Précision de périmètre, vérifiée dans le code avant tout
run** : seul STRICT reçoit `demonstration_set`
(`m7_jev_benchmark_v0_2.run_benchmark` passe `worked_examples=()` à
LABELED/GLOSSED) — P8.2 est donc une ablation STRICT-only par
construction, pas un protocole 3-conditions réduit. Rejouer LABELED/
GLOSSED sous des « ordres » différents aurait été une expérience nulle :
rien dans leur requête ne peut dépendre d'un ordre qu'ils ne reçoivent
jamais.

Protocole (`m7_jev_order_ablation_v0_1.py`) : mêmes 24 démonstrations,
mêmes 39 cas d'évaluation, même modèle, même serveur — seul l'ordre de
présentation des démonstrations à STRICT varie, sur 11 ordres : 1 ordre
« interleaved » conçu délibérément pour séparer `MERE_DE`/`PERE_DE` ET
`EPOUX_DE`/`EPOUSE_DE` (jamais adjacents, dans aucun tour ni à la
frontière entre tours), et 10 permutations aléatoires (seeds 1 à 10,
déterministes et reproductibles). L'ordre original (baseline P8.1) n'est
**pas** rejoué — son résultat existe déjà, réel et sauvegardé
(`validation/jev_benchmark_v0_2_results_2026-09-22.json`). **Deux vrais
bugs trouvés par les 9 tests déterministes
(`tests/test_m7_jev_order_ablation_v0_1.py`) avant tout run réseau** :
l'ordre de groupe alphabétique pour l'entrelacement reproduisait
exactement l'adjacence `MERE_DE`→`PERE_DE` qu'il devait casser (dans
l'alphabet, `MERE_DE` précède directement `PERE_DE`) — corrigé par un
ordre de groupe explicite (`MERE_DE, EPOUX_DE, PERE_DE, EPOUSE_DE,
AUCUNE`) qui sépare bien les deux paires confondables documentées.

**Résultat réel** (`validation/jev_order_ablation_v0_1_results_2026-09-22.json`,
429 appels HTTP réels, ~1568 s / ~26 min, 0 échec réseau sur les 429) :

| Ordre | Global | Positifs | Adversariaux | « conjoint » résiste ? |
|---|---:|---:|---:|---:|
| Original (P8.1, référence, non rejoué) | 56,4 % | 50,0 % | 63,2 % | Non |
| **Interleaved (conçu)** | **74,4 %** | 75,0 % | 73,7 % | Non |
| 10 seeds aléatoires — moyenne | **47,2 %** (σ=10,8) | 37,5 % (σ=20,8, min 0 %, max 62,5 %) | 55,8 % (σ=29,6, min 15,8 %, max 94,7 %) | Oui pour 2/10 |

**Lecture honnête, en quatre points, aucun lissé :**

1. **L'ordre a un effet causal réel et large** — jusqu'à 30 points
   d'écart sur la précision globale selon l'ordre exact, à contenu de
   démonstration strictement identique. Ce n'est pas du bruit de mesure.
2. **Mais ce n'est pas un simple effet de récence générique.** Un ordre
   aléatoire quelconque est, EN MOYENNE, **pire** que l'ordre original
   (47,2 % vs 56,4 %) — réordonner au hasard ne corrige rien en moyenne,
   il déplace juste le problème. Seul un ordre **conçu délibérément**
   pour séparer les paires confondables connues (interleaved, 74,4 %)
   fait mieux que le baseline. La baisse de précision positive de P8.1
   était donc bien, en partie, un **artefact de cet ordre précis** —
   mais la solution n'est pas « n'importe quel autre ordre », c'est
   « un ordre informé par les confusions déjà mesurées ».
3. **Découverte nouvelle, plus large que la question `PERE_DE`/`MERE_DE`
   initiale : STRICT est intrinsèquement fragile à la présentation.**
   La précision positive individuelle varie de 0 % (seed10 : les 16 cas
   positifs TOUS ratés) à 62,5 % (seed8) selon le seul ordre des
   démonstrations. C'est un résultat de **robustesse**, indépendant de
   la précision moyenne : un mécanisme dont la performance individuelle
   peut s'effondrer à 0 % selon un facteur de présentation qui ne
   devrait, en principe, rien changer au contenu de l'information
   fournie, n'est pas encore un mécanisme stable.
4. **Corrélation négative modérée-forte entre précision positive et
   précision adversariale à travers les 10 seeds (Pearson r = −0,66,
   calculé directement, pas estimé).** Les ordres qui rendent STRICT bon
   pour rejeter les cas adversariaux (répondre `AUCUNE`) le rendent
   systématiquement moins bon pour affirmer une vraie relation, et
   vice-versa (ex. seed10 : positifs 0 %, adversarial 89,5 % ; seed8 :
   positifs 62,5 %, adversarial 31,6 %). L'ordre ne fait donc pas
   seulement varier la précision : il déplace un **axe de biais**
   (tendance à s'engager sur une relation réelle vs tendance à se
   rabattre sur `AUCUNE`) — pas un phénomène de bruit incohérent.

**Sur la confusion `PERE_DE`/`MERE_DE` spécifiquement** : jamais
reproduite à 100 % dans aucun des 10 seeds (maximum 80 %, seed2) ni en
interleaved (80 % également — la ligne `PERE_DE` de la matrice de
confusion interleaved montre encore 4 `MERE_DE` sur 5 cas). **Le simple
fait de séparer positionnellement `MERE_DE` et `PERE_DE` ne suffit donc
pas à éliminer la confusion** — elle est atténuée par un ordre bien
conçu (74,4 % de précision globale malgré tout) mais pas résolue,
suggérant une confusion sémantique réelle entre les deux relations
(toutes deux « parent de », sans indice de genre explicite dans un
symbole opaque `R_n`), modulée mais pas causée uniquement par l'ordre.

**Sur `EPOUX_DE`/`EPOUSE_DE`** : taux de confusion très variable selon
l'ordre (0 % à 100 % dans les deux sens selon le seed) — confirme (comme
en P8.1) une confusion réelle, mais montre qu'elle est fortement
modulée par la présentation, contrairement à ce que Sec. 6quater
suggérait initialement (« pas un biais de position/ordre partagé ») —
**correction à cette lecture antérieure** : l'ordre module bien
l'intensité de cette confusion en STRICT, même s'il ne l'élimine jamais
complètement dans cet échantillon de 11 ordres.

**Sur « conjoint »** : ne résiste que dans 2/10 ordres aléatoires
(seeds 1 et 5), et **échoue même dans l'ordre interleaved conçu
spécifiquement pour améliorer STRICT**. Contrairement à la confusion
`PERE_DE`/`MERE_DE`, ceci n'est donc **pas principalement un artefact
d'ordre** — la coercition « conjoint » → `EPOUX_DE` en STRICT est
robuste à la plupart des réordonnancements testés, ce qui la rapproche
davantage d'une limite réelle du mécanisme (absence de vocabulaire
sémantique = aucun moyen de reconnaître un quasi-synonyme comme
hors-vocabulaire) que d'un effet de présentation.

**Conséquence pour la classification STRICT** (révision de Sec. 6
ci-dessous) : STRICT reste un mécanisme scientifiquement validé sur
l'axe adversarial général (Cas A confirmé), avec un plafond de
performance réel et élevé (74,4 % avec un ordre bien conçu, meilleur que
le résultat v0.1 original sur presque tous les axes) — mais sa
**sensibilité à l'ordre de présentation**, non résolue, en fait un objet
d'étude, pas encore un candidat opérationnel, indépendamment de son
plafond de performance. Ceci ne change rien à la décision LABELED (P8.2
est STRICT-only par construction) ; la confusion `EPOUX_DE`/`EPOUSE_DE`
de LABELED reste une question ouverte séparée, non testée ici.

Couvert par 9 tests déterministes
(`tests/test_m7_jev_order_ablation_v0_1.py`) : génération d'ordre
(l'entrelacement est bien une permutation, sépare effectivement les deux
paires confondables ; l'ordre aléatoire est déterministe par seed et
diffère entre seeds), STRICT-only par construction (jamais un nom de
relation réel envoyé comme clé de critère), l'ordre fourni atteint bien
le client (texte des démonstrations dans l'ordre donné), agrégation
(moyenne/écart-type/min/max, taux de confusion par paire, taux de
résistance « conjoint ») vérifiée contre des valeurs calculées à la
main, y compris le cas d'une ligne de confusion vide (division par
zéro évitée). **Deux bugs réels trouvés avant tout run réseau** :
l'entrelacement alphabétique ne séparait pas réellement `MERE_DE` de
`PERE_DE` (corrigé, voir plus haut).

## 6sexies. P8.3a — Ablation d'ordre des critères LABELED (2026-09-22) : la confusion EPOUX_DE/EPOUSE_DE résiste à la réorganisation, la robustesse « conjoint » non

Demandé explicitement en réponse à P8.2 : avant de traiter le résultat
LABELED de P8.1 (74,4 % global, Brier 0,377, ECE 0,137 — candidat par
défaut pour `m7_corpus_from_jev_v0_1.py`) comme acquis, poser la même
question de sensibilité à l'ordre, mais sur le seul axe dont LABELED
dépend réellement : **l'ordre des clés de `criteria`**, construit
directement à partir de `all_relations`
(`criteria = {r: None for r in all_relations}`, vérifié dans le code).
LABELED ne reçoit jamais de démonstrations (P8.2 n'a donc rien à en
dire) — P8.3a est un axe distinct, nécessitant sa propre ablation. Fait
motivant, vérifié directement : `relation_vocabulary` du corpus place
`EPOUX_DE` et `EPOUSE_DE` — la seule paire que P8.1 a mesurée comme
réellement confondue par LABELED (4/4, sens inverse de STRICT) —
**adjacents**.

Protocole (`m7_jev_label_order_ablation_v0_1.py`) : 3 ordres conçus,
délibérément non confondus entre eux — `separated` (paires confondables
jamais adjacentes, `AUCUNE` reste en dernière position comme dans
l'original — isole la variable « adjacence ») ; `aucune_first`
(`AUCUNE` en première position, `EPOUX_DE`/`EPOUSE_DE` gardent leur
adjacence d'origine — isole la variable « position de l'option de
rejet ») ; `reversed` (ordre original inversé) — plus 10 permutations
aléatoires déterministes (seeds 1 à 10, même convention que P8.2).
L'ordre original (baseline P8.1) n'est pas rejoué. **9 tests
déterministes** (`tests/test_m7_jev_label_order_ablation_v0_1.py`) :
aucun bug trouvé cette fois (contrairement à P8.2) — à signaler
honnêtement, pas tous les modules ne révèlent un bug avant le run réel.

**Résultat réel** (`validation/jev_label_order_ablation_v0_1_results_2026-09-22.json`,
507 appels HTTP réels, ~268 s / ~4,5 min — LABELED est nettement plus
rapide que STRICT, aucun few-shot à traiter) :

| Ordre | Global | Positifs | Adversariaux | « conjoint » résiste ? | Brier | ECE |
|---|---:|---:|---:|---:|---:|---:|
| Original (P8.1, référence, non rejoué) | 74,4 % | 75,0 % | 73,7 % | Oui (4/4) | 0,377 | 0,137 |
| **Separated (conçu)** | 74,4 % | 75,0 % | 73,7 % | **Oui (4/4)** | 0,373 | **0,084** |
| Aucune_first (conçu) | 74,4 % | 75,0 % | 68,4 % | **Non** | 0,373 | 0,132 |
| Reversed (conçu) | **61,5 %** | 75,0 % | **47,4 %** | Non | 0,464 | 0,147 |
| 10 seeds aléatoires — moyenne | 72,6 % (σ=7,6) | 79,4 % (σ=7,8, min 75,0, max 93,8) | 64,7 % (σ=11,1, min 47,4, max 73,7) | 4/10 |  |  |

**Lecture honnête, en cinq points, aucun lissé :**

1. **LABELED est globalement moins fragile à l'ordre que STRICT, mais
   pas insensible.** Écart-type global sur les 10 seeds : 7,6 points
   (LABELED) contre 10,8 points (STRICT, P8.2) — LABELED ne s'effondre
   jamais à 0 % comme STRICT (positive_accuracy min = 75,0 %, jamais
   pire que le baseline lui-même), mais l'écart global reste de plus de
   20 points selon l'ordre (61,5 % à 82,1 %).
2. **La confusion `EPOUX_DE`→`EPOUSE_DE` n'est PAS résolue par
   `separated`, contrairement à l'hypothèse motivant ce test** : elle
   reste à 100 % (5/5) dans les 3 ordres conçus (`separated`,
   `aucune_first`, `reversed`), qu'ils séparent ou non la paire. Elle
   varie en revanche fortement selon les seeds aléatoires (`EPOUX_DE→
   EPOUSE_DE` moyenne 0,62, σ=0,45, de 0 à 1 ; `EPOUSE_DE→EPOUX_DE`
   moyenne 0,18, σ=0,33). **Régularité nouvelle et non triviale** :
   dans chaque ordre pris individuellement, la confusion n'est jamais
   bidirectionnelle — soit `EPOUX_DE` est absorbé par `EPOUSE_DE`, soit
   l'inverse, jamais les deux à la fois. Mais la position relative ou
   absolue des deux labels dans l'ordre **ne prédit pas** quel sens
   l'emporte (vérifié directement : ni « celui qui vient en premier
   gagne » ni « celui qui vient en dernier gagne » ne tient sur les 10
   seeds) — un phénomène réel mais dont le mécanisme précis reste
   ouvert, pas fabriqué de fausse règle ici.
3. **`MERE_DE`/`PERE_DE` n'est JAMAIS confondu par LABELED, dans aucun
   des 13 ordres testés** (taux = 0,0 exactement, écart-type 0,0 sur
   les 10 seeds) — confirmation nette que le nom réel (lisible,
   porteur de genre) élimine cette confusion, contrairement à STRICT où
   elle apparaissait sous plusieurs ordres (P8.2).
4. **La position de `AUCUNE` a un effet réel et mesurable, mais pas
   énorme** : la déplacer en première position (`aucune_first`, tout le
   reste inchangé) fait passer la robustesse « conjoint » de 4/4 à un
   échec (au moins 1/4 coercé) et l'adversarial de 73,7 % à 68,4 % —
   inverser tout l'ordre (`reversed`, qui déplace aussi `AUCUNE` en
   première position mais change tout le reste) dégrade beaucoup plus
   (adversarial 47,4 %, seulement 9/19 cas `AUCUNE` corrects contre
   ~14/19 au baseline).
5. **La robustesse « conjoint » à 4/4 mesurée en P8.1 n'est PAS une
   propriété invariante de LABELED** — elle tient pour l'ordre précis
   testé en P8.1 et pour `separated`, mais échoue dans 6/10 ordres
   aléatoires et dans 2/3 ordres conçus (`aucune_first`, `reversed`).
   `near_synonym_resistance_rate` sur l'ensemble des 13 ordres testés :
   seulement 6/13 (4/10 seeds + `separated`, pas `aucune_first` ni
   `reversed`).

**Corrélation positifs/adversarial à travers les 10 seeds : Pearson
r = +0,37 (calculé directement)** — signe **opposé** à celui mesuré
pour STRICT en P8.2 (r = −0,66). LABELED ne présente donc pas le même
axe de biais « s'engager sur une relation vs se rabattre sur `AUCUNE`
» que STRICT — les deux mécanismes répondent différemment, pas
seulement en amplitude, à une perturbation d'ordre.

**Point positif inattendu** : l'ordre `separated` obtient la
**meilleure calibration (ECE) de tous les ordres testés, y compris le
baseline** (0,084 contre 0,137), à précision strictement identique
(74,4 % / 75,0 % / 73,7 %, chiffre pour chiffre) — séparer les paires
confondables dans l'ordre des critères n'élimine pas la confusion
`EPOUX_DE`/`EPOUSE_DE` elle-même, mais améliore la calibration de la
confiance du modèle sur l'ensemble du corpus. À creuser si LABELED est
retenu comme candidat final.

**Conséquence pour la décision** : les chiffres phares de P8.1 (74,4 %,
Brier 0,377, ECE 0,137, « conjoint » 4/4) sont réels mais **ne sont pas
pleinement invariants à l'ordre des critères** — ils représentent un
point dans une distribution qui va, sur ce seul axe, de 61,5 % à 82,1 %
en précision globale, et dont l'affirmation la plus vendable
(robustesse totale sur « conjoint ») ne survit pas à la majorité des
réordonnancements testés. Ceci renforce, avec des données réelles, la
prudence déjà demandée avant d'en faire la référence verrouillée de
`m7_corpus_from_jev_v0_1.py` — sans pour autant renverser LABELED comme
candidat par défaut (aucun ordre testé ne fait mieux que `separated`
sur l'ensemble précision+calibration, et LABELED reste strictement plus
stable que STRICT sur cet axe).

Couvert par 9 tests déterministes
(`tests/test_m7_jev_label_order_ablation_v0_1.py`) : génération d'ordre
(les trois ordres conçus isolent bien chacun leur variable ; l'ordre
aléatoire est déterministe par seed et diffère entre seeds), l'ordre
fourni atteint bien le client (ordre exact des clés de `criteria`
vérifié), LABELED n'envoie jamais de description (`None` partout),
réutilisation sans modification de `summarize_order_ablation`
(P8.2) sur des rapports LABELED — la fonction d'agrégation est
générique sur ce qui varie entre rapports, pas spécifique à STRICT.

## 6septies. P8.3b — Robustesse à la formulation de `instructions`, LABELED (2026-09-22) : l'axe le plus stable mesuré à ce jour

Demandé explicitement en suite de P8.3a, avec les paramètres par défaut
proposés : avant de conclure sur la fragilité de LABELED, tester le
seul autre input LABELED-spécifique non encore perturbé — la
formulation exacte de `instructions` (toujours la même chaîne fixe,
`DEFAULT_LABELED_GLOSSED_INSTRUCTIONS = "Which relation applies to this
sentence?"`, dans P8.1 et tout P8.3a). **Extension nécessaire de
`m7_jev_relation_choice_v0_1.py`** (module modifié en place, travail en
cours) : nouveau paramètre optionnel `instructions_override`, `None`
par défaut — préserve exactement le comportement de tout appelant
existant. Seule approche viable pour éviter de dupliquer la validation
déjà testée de `propose_relation_jev` (rejet self-loop, rejet
hors-vocabulaire, probabilité malformée) juste pour faire varier une
chaîne.

Protocole (`m7_jev_instruction_robustness_v0_1.py`) : 5 reformulations
conçues pour une variété réelle de registre (formel, impératif, question
indirecte, verbeux, procédural), **ordre des critères fixé** à l'ordre
original du corpus (celui du baseline P8.1) pour ne jamais confondre
cet axe avec celui de P8.3a. L'original lui-même n'est pas rejoué (déjà
mesuré et sauvegardé). 5 tests déterministes
(`tests/test_m7_jev_instruction_robustness_v0_1.py`, plus 1 nouveau
test dans `tests/test_m7_jev_relation_choice_v0_1.py` pour
`instructions_override` lui-même) : aucun bug trouvé.

**Résultat réel** (`validation/jev_instruction_robustness_v0_1_results_2026-09-22.json`,
195 appels HTTP réels, ~111 s / ~1,85 min) :

| Formulation | Global | Positifs | Adversariaux | « conjoint » résiste ? | Brier | ECE |
|---|---:|---:|---:|---:|---:|---:|
| Original (P8.1, référence, non rejouée) | 74,4 % | 75,0 % | 73,7 % | Oui | 0,377 | 0,137 |
| formal | 76,9 % | 75,0 % | 73,7 % | Oui | 0,336 | 0,176 |
| **imperative_short** | **79,5 %** | **87,5 %** | 73,7 % | Oui | 0,347 | 0,182 |
| alt_phrasing | 74,4 % | 75,0 % | 68,4 % | Oui | 0,395 | 0,152 |
| verbose_careful | 74,4 % | 75,0 % | 73,7 % | Oui | 0,352 | 0,178 |
| procedural | 76,9 % | 75,0 % | 73,7 % | Oui | 0,354 | 0,139 |
| **5 variantes — moyenne** | **76,4 % (σ=2,1)** | 77,5 % (σ=5,6) | 72,6 % (σ=2,4) | **5/5** |  |  |

**Lecture honnête : le résultat le plus rassurant mesuré sur LABELED à
ce jour, et le plus net contraste avec P8.3a.**

1. **La formulation de `instructions` est un axe BEAUCOUP plus stable
   que l'ordre des critères.** Écart-type global : 2,1 points (5
   formulations) contre 7,6 points (13 ordres, P8.3a) et 10,8 points
   (STRICT, P8.2). Aucune reformulation ne fait pire que le baseline
   sur la précision globale (toutes ≥ 74,4 %) ; `imperative_short` fait
   même mieux que le baseline sur tous les axes (79,5 % global, 87,5 %
   positifs).
2. **« conjoint » résiste dans les 5 formulations sur 5** — contraste
   frontal avec P8.3a, où la même vérification échouait dans 8 ordres
   sur 13. **La fragilité identifiée en P8.3a est donc spécifique à
   l'axe « ordre des critères », pas une fragilité générale de
   LABELED** — une précision importante que ce test seul permet
   d'établir, pas supposable a priori.
3. **`MERE_DE`/`PERE_DE` reste à 0 % de confusion dans les 5
   formulations** — troisième confirmation indépendante (après
   l'original et les 13 ordres de P8.3a) que LABELED ne confond jamais
   cette paire, sous aucune perturbation testée à ce jour.
4. **`EPOUX_DE`→`EPOUSE_DE` reste présent dans toutes les formulations**
   (moyenne 0,76, de 0,40 à 1,00, jamais éliminé), **toujours dans le
   même sens** (`EPOUSE_DE`→`EPOUX_DE` = 0,0 exactement dans les 5) —
   cohérent avec l'hypothèse de P8.3a selon laquelle c'est l'ordre des
   critères (ici fixé, donc constant) qui détermine le sens de la
   confusion, la formulation ne modulant que son intensité (40 % à
   100 %), jamais son élimination ni son inversion.

**Conséquence pour la décision** : contrairement à P8.3a, P8.3b ne
révèle **aucune fragilité nouvelle** — il confirme au contraire que la
formulation exacte de l'instruction n'est pas le facteur qui menaçait
la robustesse de LABELED. Combiné à P8.3a, l'image se précise :
LABELED est robuste à la formulation des instructions, robuste à la
confusion `MERE_DE`/`PERE_DE` sous toute perturbation testée, mais
**reste sensible à l'ordre des critères spécifiquement**, avec un
impact mesurable sur la robustesse « conjoint » et sur la confusion
`EPOUX_DE`/`EPOUSE_DE`. Le risque principal avant adoption définitive
reste donc concentré sur un seul axe, pas diffus sur toute la surface
d'entrée de LABELED — une conclusion plus précise, et plus favorable à
LABELED, que ce que P8.3a seul aurait suggéré.

Couvert par 5 tests déterministes
(`tests/test_m7_jev_instruction_robustness_v0_1.py`) + 1 test ajouté à
`tests/test_m7_jev_relation_choice_v0_1.py` pour `instructions_override`
lui-même (26 tests désormais dans ce fichier) : distinction des 5
formulations entre elles et de l'original, chaque formulation atteint
bien le client avec le texte exact, ordre des critères resté fixe
(vérifié directement, jamais confondu avec l'axe de P8.3a),
réutilisation sans modification de `summarize_order_ablation` sur ces
rapports (troisième réutilisation générique de cette fonction, après
P8.2 et P8.3a).

## 6. Décision

**P8 = `FIVE_EXPERIMENTS_COMPLETE, LABELED_FRAGILITY_ISOLATED_TO_CRITERIA_ORDER` (2026-09-22).**
`m7_jev_relation_choice_v0_1.py` implémente le vrai contrat
`POST /v1/systemone` (Sec. 3bis/5), désormais avec distribution de
probabilité complète (nécessaire au Brier/ECE de Sec. 6quater) et un
paramètre optionnel `instructions_override` (Sec. 6septies). 78 tests
au total (25 relation-choice + 3 live demo + 8 benchmark v0.1 + 15
benchmark v0.2/P8.1 + 9 order-ablation/P8.2 + 9 label-order-ablation/P8.3a
+ 9 instruction-robustness/P8.3b) — **tous exécutés, dont 22 cas × 3
conditions (v0.1, Sec. 6ter), 39 cas × 3 conditions (v0.2/P8.1, Sec.
6quater), 11 ordres × 39 cas en STRICT seul (P8.2, Sec. 6quinquies),
13 ordres × 39 cas en LABELED seul (P8.3a, Sec. 6sexies), puis 5
formulations d'instructions × 39 cas en LABELED seul (P8.3b, Sec.
6septies) en conditions réelles contre le serveur Kev-0.8B de
l'utilisateur — 1314 appels HTTP réels au total sur l'ensemble de P8
(66 + 117 + 429 + 507 + 195)**.

**Réponse au cadre A/B/C posé pour P8.1, complétée par P8.2** : Cas A
confirmé sur l'axe adversarial (STRICT 16,7 % → 63,2 % avec le few-shot
enrichi). La baisse inattendue de précision positive (62,5 % → 50,0 %)
s'est révélée, par P8.2, **partiellement un artefact de l'ordre de
présentation précis choisi en P8.1** — un ordre délibérément conçu pour
séparer les paires confondables porte le résultat à 74,4 % — mais **pas
un simple effet de récence corrigible par n'importe quel réordonnancement** :
la moyenne de 10 ordres aléatoires (47,2 %) est **pire** que l'ordre
original (56,4 %), et la variance individuelle est énorme (précision
positive de 0 % à 62,5 % selon le seul ordre). STRICT a donc un plafond
de performance réel et élevé, mais une **fragilité de présentation non
résolue** — une découverte plus large que la question initiale
`PERE_DE`/`MERE_DE`, qui reste elle-même non totalement expliquée par
l'ordre (jamais éliminée à 100 %, même en interleaved).

**La classification provisoire est adoptée, affinée par P8.1 ET P8.2** :

```text
JEV/KEV STRICT   = test scientifique d'abstraction — mécanisme validé
                    pour la robustesse adversariale générale (Cas A),
                    plafond de performance élevé (74,4 % avec un ordre
                    bien conçu) MAIS fragilité de présentation non
                    résolue (P8.2 : σ=10,8 pts sur 10 ordres aléatoires,
                    positifs de 0 % à 62,5 %) -- PAS un candidat
                    opérationnel en l'état, quel que soit son plafond
JEV/KEV LABELED  = candidat opérationnel M7 -- fragilité désormais
                    ISOLÉE à un seul axe, pas diffuse. P8.3a : résultat
                    P8.1 PAS pleinement invariant à l'ordre des critères
                    (global 61,5 % à 82,1 % selon l'ordre, σ=7,6 pts ;
                    robustesse « conjoint » 4/4 échoue dans 8/13 ordres ;
                    confusion EPOUX_DE/EPOUSE_DE jamais résolue par la
                    séparation positionnelle, contrairement à
                    l'hypothèse testée). P8.3b, à l'inverse, montre que
                    la FORMULATION de `instructions` est un axe stable
                    (σ=2,1 pts sur 5 formulations, « conjoint » résiste
                    5/5, aucune formulation ne fait pire que le
                    baseline) -- la fragilité de LABELED n'est donc PAS
                    diffuse sur toute sa surface d'entrée, elle est
                    concentrée sur l'ordre des critères spécifiquement.
                    MERE_DE/PERE_DE JAMAIS confondu, sous aucune
                    perturbation testée à ce jour (13 ordres + 5
                    formulations) -- contraste net avec STRICT
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
du même phénomène. **Nuance apportée par P8.2** : en STRICT, l'intensité
de cette confusion varie fortement avec l'ordre (0 % à 100 % selon le
seed) — la confusion elle-même est réelle mais son intensité mesurée en
P8.1 dépendait aussi de l'ordre précis testé, pas seulement du contenu.
**Nuance complémentaire apportée par P8.3a** : en LABELED, la confusion
est, à l'inverse de STRICT, **robuste aux 3 ordres conçus** (toujours
100 %, jamais réduite en séparant la paire) mais variable selon les
seeds aléatoires (0 à 100 %), et toujours strictement unidirectionnelle
au sein d'un même ordre (jamais les deux sens à la fois) sans qu'une
règle de position simple (premier/dernier, avant/après) explique quel
sens l'emporte — un phénomène réel, non expliqué par ce test, pas
inventé ici.

Décision d'adoption pour `m7_corpus_from_jev_v0_1.py` (Sec. 5, toujours
pas écrit) : **LABELED reste le candidat par défaut le mieux justifié
par les données, et l'image s'est précisée plutôt qu'aggravée** entre
P8.3a et P8.3b. P8.3a avait montré une fragilité réelle sur l'axe
« ordre des critères » ; P8.3b montre que cette fragilité **ne se
généralise pas** à la formulation des instructions, l'autre input
LABELED-spécifique testable — LABELED n'est donc pas fragile de façon
diffuse, sa seule faiblesse mesurée à ce jour est concentrée sur
l'ordre de présentation des critères. **Adoption définitive toujours
pas prononcée** ; corriger EPOUX_DE/EPOUSE_DE et, si LABELED est
retenu, fixer son ordre de critères à `separated` (meilleure
calibration mesurée, Sec. 6sexies) restent ouverts. Prochaine étape
possible, non commencée : paraphrases supplémentaires des phrases
d'entrée elles-mêmes (au-delà des 4 cas `positive_paraphrase` déjà
couverts en P8.1/Sec. 6quater), pour compléter la cartographie de
robustesse de LABELED avant un verrouillage définitif de
`m7_corpus_from_jev_v0_1.py`.
