# P4-U.2 — Investigation empirique des candidats de représentation structurelle (2026-09-23)

Ce document répond à la question laissée explicitement ouverte par
`documentation/P4U2_Autonomous_Relation_Discovery_V0_3.md` Sec. 10 :
**quelles informations structurelles, déjà mesurables avec les
primitives K3 existantes, peuvent réellement différencier deux
opérateurs opaques ?** — une investigation directe par exécution, pas
une spéculation. Aucun code de production n'est créé ici ; tous les
tests ci-dessous ont été exécutés ligne de commande, jetables, jamais
committés en tant que tels.

**Toujours aucun protocole verrouillé, aucun code P4-U.2.**

## 1. Méthode

Pour chaque candidat, un corpus jouet est construit avec au moins deux
« relations cachées » (des étiquettes réelles connues du script de
test, jamais du mécanisme). Chaque observation reçoit ensuite un
opérateur masqué **individuel** (`OP#0001`, `OP#0002`, ...), exactement
la méthode gelée en Sec. 5 de la v0.3. Le candidat de signature est
calculé **uniquement** à partir du graphe masqué, avec les fonctions
déjà existantes de `kernel2.py`/`e20d_rationalization_v0_1.py`, sans
aucune modification. La vérité terrain n'est utilisée qu'après coup,
pour juger si la signature sépare effectivement les deux relations
cachées.

## 2. Candidat 1 — `path_properties().branching_at_start` /
   `.branching_at_end` (kernel2.py, INCHANGÉ)

**Test A — deux relations qui diffèrent réellement par leur rôle
topologique local** (une relation « HUB_REL » à fort éventail de
sortie contre une relation « PAIR_REL » strictement 1-à-1) :

```text
HUB_REL  branching_at_start : min=6  max=6  mean=6.00
PAIR_REL branching_at_start : min=1  max=1  mean=1.00
=> séparation parfaite par branching_at_start seul.
```

**Test B — deux relations avec un degré de départ IDENTIQUE (1-à-1
toutes les deux), mais dont l'une a une continuation en aval et l'autre
non** (`PAIR_REL_A` → continuation, `PAIR_REL_B` → impasse) :

```text
PAIR_REL_A branching_at_end : 2 (compte la continuation avale)
PAIR_REL_B branching_at_end : 1 (impasse)
=> séparation parfaite par branching_at_end seul, alors même que
   branching_at_start est identique (1) dans les deux groupes.
```

**Test C — cas limite délibéré : deux relations dont le rôle
topologique local est IDENTIQUE en tout point mesuré** (`TWIN_REL_A`
et `TWIN_REL_B`, toutes deux 1-à-1 avec une continuation avale de même
forme) :

```text
TWIN_REL_A signatures : {(1, 2)}
TWIN_REL_B signatures : {(1, 2)}
=> signatures RIGOUREUSEMENT identiques -- branching_at_start/end ne
   peut PAS distinguer ces deux relations, par construction.
```

**Conclusion sur ce candidat** : `path_properties()` (déjà existant,
zéro modification) est un candidat de signature réel et
identité-indépendant, capable de séparer des relations qui diffèrent
par leur rôle topologique local (Tests A/B) — mais il a une limite
nette, confirmée par construction (Test C) : deux relations partageant
exactement le même rôle topologique local restent indiscernables par
ce seul candidat. **C'est exactement la frontière que Gate I (v0.3
Sec. 2) doit détecter et rapporter honnêtement comme
`INSUFFICIENT_STRUCTURAL_INFORMATION` — pas un défaut du candidat, une
propriété attendue de toute signature purement locale.**

## 3. Candidat 2 — `ref_jaccard`/`structural_similarity`
   (`e20d_rationalization_v0_1.py`, INCHANGÉ, vivant)

**Test D — deux observations de la MÊME relation cachée, entités
totalement disjointes** (le style de corpus déjà utilisé par P4-U.1
lui-même — hubs/distracteurs jamais réutilisés) :

```text
ref_jaccard(o1, o2), opérateurs masqués, entités disjointes : 0.0
ref_jaccard(o1, o3), relation différente, entités disjointes : 0.0
=> AUCUN signal -- ref_jaccard sur les refs opaques bruts est
   totalement non-informatif quand les entités ne sont jamais
   réutilisées entre observations.
```

**Erreur de méthode trouvée et corrigée pendant ce test, avant de
conclure** : un premier essai avait laissé les opérateurs NON masqués
(littéralement partagés, ex. `REL_X` pour les deux observations),
donnant `ref_jaccard = 0.2` — un résultat trompeur, dû uniquement au
fait que `_opaque_refs()` collecte aussi la référence de l'opérateur
lui-même, pas à une véritable similarité structurelle. Refait avec un
masquage individuel correct (Sec. 1) : le signal disparaît totalement,
confirmant qu'un test mal construit peut donner l'illusion d'un signal
qui n'existe pas — corrigé avant d'écrire cette conclusion, pas après.

**Test E — deux observations de la MÊME relation cachée, PARTAGEANT
une entité réelle** (un « hub » nommé, ex. une même personne apparaissant
dans deux faits) :

```text
ref_jaccard(o4, o5), opérateurs masqués, entité HUB partagée : 0.2
ref_jaccard(o4, o6), relation différente, aucune entité partagée : 0.0
```

**Réserve méthodologique importante, à ne jamais confondre dans un
futur protocole** : ce signal de 0.2 mesure la **co-occurrence
d'entité** (« ces deux faits parlent de la même personne »), pas la
**similarité de type de relation**. Deux faits impliquant la même
personne mais de relations réellement DIFFÉRENTES (ex. « HUB
TRAVAILLE_À T4 » et « HUB HABITE_À T5 ») recevraient exactement le même
score `0.2`, pour la même raison structurelle — `ref_jaccard` ne peut
donc **pas**, à lui seul, servir de signature de similarité de
relation ; il détecte un phénomène différent (partage d'entité), utile
pour autre chose, mais pas pour ce que P4-U.2 doit résoudre.

## 4. Synthèse — ce que cette investigation apporte au futur protocole

| Candidat | Informatif pour distinguer des relations cachées ? | Condition |
|---|---|---|
| `path_properties().branching_at_start/end` | **Oui**, quand le rôle topologique local diffère réellement | Échoue par construction si deux relations partagent le même rôle local (Test C) — Gate I doit alors renvoyer `INSUFFICIENT_STRUCTURAL_INFORMATION` |
| `ref_jaccard`/`structural_similarity` sur les refs opaques bruts | **Non**, pour la similarité de TYPE de relation | Mesure la co-occurrence d'entité, pas la similarité relationnelle — confusion à proscrire explicitement dans tout futur protocole |

**Aucun candidat testé ici n'est, à lui seul, une solution complète** —
ce n'était pas l'objectif de cette investigation (qui reste une mesure,
pas une implémentation). Le résultat concret et utilisable pour le
futur protocole v0.1 :

1. `path_properties()` (profondeur 1 et au-delà, via `discover_paths()`
   à profondeur >= 2 pour des signatures plus riches que le simple
   `branching_at_start/end`) est le candidat le plus directement
   réutilisable comme composante de la représentation structurelle
   invariante-à-l'identité (v0.3 Sec. 8, étape 1) — mais son pouvoir de
   séparation dépend entièrement de la mesure dans laquelle les
   relations cachées d'un corpus donné diffèrent réellement par leur
   rôle topologique local. **Ceci implique directement la Gate I** :
   la démonstration d'identifiabilité d'un futur cas verrouillé devrait
   concrètement consister à vérifier que les relations cachées du
   corpus produisent des signatures `path_properties`/`discover_paths`
   distinctes — pas une assertion abstraite.
2. `ref_jaccard`/`structural_similarity` reste utile pour un problème
   voisin mais différent (détection de co-référence/entité partagée) —
   à ne pas réutiliser tel quel comme signature de similarité de
   relation, sous peine de confondre deux notions différentes.
3. Aucune nouvelle primitive n'a été nécessaire pour obtenir ces
   résultats — confirmant la piste déjà retenue par la v0.3 (Sec. 10) :
   la représentation manquante peut vraisemblablement être construite
   en COMBINANT des mesures déjà existantes (`path_properties` à
   plusieurs profondeurs via `discover_paths`), plutôt qu'en inventant
   un nouveau mécanisme de bas niveau.

## 5. Ce que cette investigation ne fait pas

Elle ne fixe aucune représentation définitive, aucun seuil, aucun
modèle nul. Elle fournit une base empirique honnête (candidats
testés, résultats bruts, limites confirmées par construction) pour la
question laissée ouverte par la v0.3 — la conception du protocole
formel reste une étape ultérieure, non commencée ici.
