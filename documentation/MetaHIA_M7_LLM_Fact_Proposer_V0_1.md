# MetaHIA — M7 — Empirical LLM Loop v0.1 (Fact Proposer scope)

## 1. Statut

- M1–M6 : voir `documentation/MetaHIA_M6_Structural_Learning_V0_1.md` (M6 = `VALIDATED`).
- M7 : **IMPLEMENTATION** (local, 2026-09-17) — pas de validation tierce à ce stade.
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

## 6. Invariants permanents testés

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

## 7. Résultat local

356 tests passés (338 précédents + 17 invariants M7 + 1 démonstration live Ollama), 0 échec,
0 régression.

## 8. Hors périmètre de cette version

- Parseur texte libre → structure (roadmap : élément différé séparé, pas traité ici) ;
- amélioration de la justesse du LLM sur cette tâche (modèle plus grand, few-shot mieux
  choisi, chaîne de raisonnement) — signalé comme limite empirique réelle, pas corrigé ici
  pour ne pas fabriquer un résultat plus flatteur ;
- extension aux patterns de longueur > 1 (même limite que M6 v0.2 avant son extension) ;
- validation tierce de ce mécanisme ;
- intégration dans `split_by_rule`/`evaluate_promotion` avec un corpus mixte
  (claims adversariales + preuve LLM) — chaque source reste testée séparément pour l'instant.
