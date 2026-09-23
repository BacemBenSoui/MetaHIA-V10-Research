# P4-U.2 — Expérience d'identifiabilité sur une signature structurelle candidate multi-profondeur (2026-09-23)

Ce document exécute l'étape explicitement demandée par le porteur du
projet, distincte de l'investigation du 2026-09-23
(`documentation/P4U2_Structural_Signature_Investigation_2026-09-23.md`)
et distincte du futur protocole P4-U.2 v0.1 :

```text
Investigation 2026-09-23 (candidats isolés, testée)
        ↓
candidate structural signature   <- CE DOCUMENT
        ↓
identifiability experiment        <- CE DOCUMENT
        ↓
P4-U.2 protocol v0.1 (pas commencé)
```

**La signature testée ici est une HYPOTHÈSE EXPÉRIMENTALE, pas une
définition déjà acquise.** Ce document ne fige aucune représentation
définitive pour le futur protocole — il rapporte un résultat de test,
positif ou négatif, les deux étant scientifiquement utiles. **Toujours
aucun protocole verrouillé, aucun code P4-U.2.**

## 1. Signature candidate testée

Construite uniquement à partir de primitives K3 déjà existantes
(`discover_paths`, `build_structural_graph`), sans modification, sans
utiliser l'identité de l'opérateur masqué de l'arête elle-même :

```text
Signature(observation masquée) =
    ( nombre de chemins de profondeur 1 partant de cette arête,
      nombre de chemins de profondeur 2 partant de cette arête,
      nombre de chemins de profondeur 3 partant de cette arête,
      multiset des séquences de direction observées à ces profondeurs )
```

Calculée en filtrant `discover_paths(graph, start=source_de_l_arête,
max_depth=3, allow_reverse=True)` aux seuls chemins dont le PREMIER pas
correspond exactement à l'arête étudiée (`p.steps[0].edge_id ==
edge.edge_id`).

## 2. Trois corpus, trois verdicts attendus, tous testés par exécution

### Corpus 1 — attendu `SEPARABLE`
`REL_A` (dépasse toujours en profondeur 2 vers une continuation)
contre `REL_B` (jamais de continuation).

```text
REL_A : signature unique parmi ses propres instances
REL_B : signature unique parmi ses propres instances
Aucun chevauchement entre REL_A et REL_B
VERDICT : SEPARABLE
```

### Corpus 2 — attendu `INSUFFICIENT_STRUCTURAL_INFORMATION`
`REL_A2` et `REL_C`, toutes deux avec une continuation de profondeur 2
strictement identique, par construction (extension du cas `TWIN`
de l'investigation précédente à la signature combinée).

```text
REL_A2 et REL_C : signature identique, 100% de chevauchement
VERDICT : INSUFFICIENT_STRUCTURAL_INFORMATION
```

Reconfirmé par une vérification indépendante au niveau du groupe (pas
seulement par observation) : `REL_A2` et `REL_C` ont TOUTES DEUX une
fraction de 100 % de continuation de profondeur 2 — un signal
strictement nul, pas un artefact de méthode de vérification.

### Corpus 3 — un résultat honnête qui a corrigé la méthode de vérification elle-même

`REL_D` (80 %, 16/20, de ses instances ont une continuation) contre
`REL_E` (20 %, 4/20, en ont une aussi, par chevauchement partiel
délibéré).

**Premier verdict, avec une vérification NAÏVE par égalité exacte de
signature par observation** :
```text
REL_D : 2 signatures distinctes parmi ses instances
REL_E : 2 signatures distinctes parmi ses instances (LES MÊMES 2)
VERDICT (naïf) : INSUFFICIENT_STRUCTURAL_INFORMATION -- INCORRECT
```

**Ce verdict naïf est faux**, et l'erreur a été trouvée et corrigée
avant de conclure, pas après : une vérification par égalité exacte de
signature ignore la PROPORTION de chaque signature dans chaque groupe
— elle confond « aucun signal du tout » (Corpus 2, réellement 100 %
partout) avec « un signal réel mais bruité » (Corpus 3, 80 % contre
20 %). Un test statistique correct au niveau du groupe (test à deux
proportions) révèle un signal réel et significatif :

```text
REL_D : fraction avec continuation = 0,80 (16/20)
REL_E : fraction avec continuation = 0,20 (4/20)
z (test à deux proportions) = 3,79  (|z| > 1,96 -> p < 0,05, significatif)
VERDICT CORRIGÉ : signal réel détecté -- ni SEPARABLE (les instances
    individuelles se chevauchent) ni INSUFFICIENT (le groupe se
    distingue statistiquement) -- exactement le cas AMBIGUOUS/
    statistiquement-séparable-mais-bruité que le futur protocole devra
    trancher par un modèle nul, pas par une simple égalité de
    signature.
```

## 3. Constat méthodologique central — plus important que les trois verdicts eux-mêmes

**Une comparaison de signature par égalité exacte, observation par
observation, n'est PAS une opérationnalisation suffisante de
l'identifiabilité.** Elle confond deux situations réellement
différentes :
- absence totale de signal (Corpus 2) ;
- signal réel mais distribué/bruité au niveau du groupe (Corpus 3).

**Une comparaison STATISTIQUE au niveau du groupe** (ex. test à deux
proportions ici, à généraliser dans le futur protocole) est nécessaire
pour distinguer ces deux cas correctement. **C'est exactement le rôle
du modèle nul déjà anticipé par la v0.3 (Sec. 7)** — cette expérience
en fournit maintenant une preuve empirique concrète, pas seulement une
anticipation théorique : Gate I ne peut pas être une simple vérification
d'égalité de signature, elle doit intégrer une statistique de groupe
comparée à un modèle nul, dès sa première version.

## 4. Ce que cette expérience établit, et ce qu'elle n'établit pas

**Établi, par exécution directe** :
- La signature multi-profondeur candidate (Sec. 1) contient une
  information réelle et exploitable dans au moins un cas construit
  (Corpus 1, séparation parfaite) et dans un cas plus subtil (Corpus 3,
  séparation statistique significative une fois la bonne méthode de
  comparaison appliquée).
- Cette même signature candidate a une limite réelle et confirmée
  (Corpus 2) — un cas où le signal est authentiquement nul, pas
  seulement mal mesuré.
- La vérification par égalité exacte de signature est insuffisante
  pour Gate I ; une statistique de groupe est nécessaire.

**Non établi, délibérément** :
- Que cette signature candidate (Sec. 1) est LA représentation
  définitive du futur protocole P4-U.2 v0.1 — elle reste une
  hypothèse testée, pas un choix figé.
- Aucun seuil numérique, aucun modèle nul complet, aucun benchmark
  verrouillé.

## 5. Prochaine étape

Conformément à la séquence fixée par le porteur du projet, l'étape
suivante est l'écriture du protocole P4-U.2 v0.1 formel — en y
intégrant explicitement la distinction entre ce qui est empiriquement
observé ici (Sec. 2-3), ce qui reste une hypothèse de représentation
(Sec. 1, jamais présentée comme déjà validée), et ce qui reste à
démontrer par un vrai modèle nul et un benchmark verrouillé aveugle
(Sec. 3-4). Le commit qui clôt cette expérience ne doit pas être lu
comme une validation de l'algorithme P4-U.2 — seulement comme la
clôture de l'enquête exploratoire précédant le protocole.
