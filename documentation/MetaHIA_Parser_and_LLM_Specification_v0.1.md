# MetaHIA — Specification des couches non encore implémentées v0.1

## 1. Principe
Le package actuel fournit un noyau structurel fonctionnel. Le parseur et la passerelle LLM ne sont pas déclarés implémentés. Ils sont spécifiés pour éviter de polluer M1–M5 avec des dépendances de génération.

## 2. Parseur texte → structure

### Entrée
Texte brut, métadonnées de source, langue, contexte documentaire optionnel.

### Sortie canonique attendue
Un conteneur structurel compatible avec MetaHIA Core : nœuds, propositions, arguments ordonnés, opérateurs/portées, qualifiers, identity/coreference, ambiguities, conflicts, provenance.

### Contraintes
1. aucune inférence non explicitement soutenue pendant l’extraction ;
2. les ambiguïtés restent représentées ;
3. la négation reste séparée du prédicat ;
4. provenance et offsets source sont conservés ;
5. la confiance ne vaut jamais vérité ;
6. texte→structure est séparable de structure→inférence.

### Tests à prévoir
- conservation des faits ;
- scope ;
- négation ;
- coréférence ;
- conflits ;
- UNKNOWN/UNOBSERVED/UNCONFIRMED ;
- reconstruction ;
- invariance inter-modèles après normalisation ;
- contamination nulle vers l’inférence.

## 3. Passerelle LLM

### Interface minimale
```text
request_id
provider
model
prompt_version
input
structured_output
latency_ms
token_usage
cost
raw_response_hash
error
```

### Exigences
- multi-provider ;
- timeout et retry bornés ;
- cache optionnel ;
- coût et latence mesurés ;
- hash de réponse ;
- aucun secret dans le frontend ;
- traçabilité provider/model/prompt/version ;
- possibilité de remplacer le provider sans modifier M1–M5.

### Séparation des rôles
Le LLM peut fournir observation, extraction, reformulation ou evidence candidate. Il ne peut pas convertir lui-même une sortie en `SUPPORTED` sans passer par M2 et ses règles d’indépendance.

## 4. Intégration future
```text
SOURCE → PARSER/LLM → NORMALIZER → M1/M3 → M2 → M4 → M5 → M6
```

M7 devra comparer au minimum : LLM seul, MetaHIA sans boucle LLM live, et LLM + MetaHIA, avec coûts et latences réellement mesurés.
