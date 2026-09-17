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

## 5. Invariants permanents testés

`tests/test_m7_llm_fact_proposer_invariants_v0_1.py` (11 tests, backend simulé injecté,
aucun réseau) :
- la valeur réelle prédite n'apparaît jamais dans le prompt envoyé au LLM ;
- toute réponse non-JSON, sans clé `object`, non-string, ou vide est traitée comme
  « aucune proposition », jamais fabriquée ;
- une proposition bien formée est acceptée, avec sujet/relation fournis par l'appelant
  (contexte déjà connu), seul l'objet est réellement sollicité du LLM ;
- la preuve est toujours `GROUNDED_ANALOGY`, jamais `GROUNDED_DIRECT` ni `UNGROUNDED_HUMAN` ;
- accord → `SUPPORT`, désaccord → `CHALLENGE` ;
- un hôte Ollama injoignable lève `OllamaUnavailable`, distinct d'une réponse inexploitable.

## 6. Résultat local

350 tests passés (338 précédents + 11 invariants M7 + 1 démonstration live Ollama), 0
échec, 0 régression.

## 7. Hors périmètre de cette version

- Parseur texte libre → structure (roadmap : élément différé séparé, pas traité ici) ;
- amélioration de la justesse du LLM sur cette tâche (modèle plus grand, few-shot mieux
  choisi, chaîne de raisonnement) — signalé comme limite empirique réelle, pas corrigé ici
  pour ne pas fabriquer un résultat plus flatteur ;
- extension aux patterns de longueur > 1 (même limite que M6 v0.2 avant son extension) ;
- validation tierce de ce mécanisme ;
- intégration dans `split_by_rule`/`evaluate_promotion` avec un corpus mixte
  (claims adversariales + preuve LLM) — chaque source reste testée séparément pour l'instant.
