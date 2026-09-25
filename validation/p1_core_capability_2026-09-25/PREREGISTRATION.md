# Pré-enregistrement — capacité du Core K3 sur des paires P1 structurées à la main (2026-09-25)

**Nature : expérience de capacité du Core.** Ce n'est ni un test du vérificateur P1, ni
une validation de V6. Décision du porteur du projet du 2026-09-25, à la suite de l'audit
`documentation/P1_VERIFIER_LAYER_AUDIT_2026-09-25.md`.

Contraintes :
- **aucune modification de `kernel2.py`**, vérifiée par empreinte avant et après
  l'exécution : `c76adfd2…efc9aa9` ;
- aucune intégration dans V6 ;
- aucune ressource lexicale ;
- une seule exécution.

Ce document, `pairs.json` et `harness.py` sont figés par empreinte dans
`PREREGISTRATION.sha256`, puis committés et poussés **avant** l'exécution.

## 1. Principe de séparation testé

```text
K3 structural result  ≠  semantic interpretation  ≠  epistemic verdict
```

K3 (Node/Apply/Compare) ne produit aucun verdict. Les verdicts SUPPORTED, UNKNOWN et
CONTRADICTED viennent uniquement de la **couche de projection** définie dans
`harness.py` (fonction `project`). Cette couche est hors de K3 et fait elle-même
l'objet du test. Elle n'utilise que des primitives publiques de K3 : `apply`,
`node_ref`, `structural_equal`.

## 2. Matériel

**27 éléments**, dont 24 paires tirées des jeux de développement (P1 v0.1 et test n°1,
cas où les deux annotateurs s'accordent) et 3 contrôles construits (`C-01` à `C-03`).

**Structuration à la main**, selon des règles fixes :
- le verbe (sous forme de lemme), la préposition ou le modificateur devient
  l'opérateur `op:<tête>` ;
- les arguments deviennent des `NodeRef` opaques ;
- la normalisation est **seulement morpho-syntaxique** :
  - temps et aspect supprimés ;
  - voix passive ramenée à l'ordre agent puis patient ;
  - nombre et articles supprimés ;
- **aucune normalisation lexicale** : *attorney* reste différent de *lawyer*, et
  *wide_open* de *firmly_shut*.

La négation est représentée par un opérateur ordinaire `op:neg` qui enveloppe la
proposition : `neg(P)`. **Rien n'est ajouté au noyau.**

Convention : la claim est l'hypothèse, la preuve est la prémisse. Les labels humains
sont rapportés à titre descriptif. Ils ne sont **pas** un critère : l'expérience teste
ce que fait le Core, pas son accord avec les humains.

## 3. Couche de projection (figée dans `harness.py`)

1. Si `structural_equal(claim, preuve)` → **SUPPORTED**. C'est le seul chemin vers
   SUPPORTED.
2. Si une seule des deux est `neg(X)` : **CONTRADICTED** si `X` est structurellement
   égal à l'autre, sinon **UNKNOWN**.
3. Sinon, on calcule les positions différentes (récursivement, avec
   `structural_equal`). Si **une seule** feuille diffère, `(x, y)`, et qu'une relation
   `incompatible(x, y)` est **fournie comme donnée**, lue dans les deux sens → 
   **CONTRADICTED**.
4. Dans tous les autres cas → **UNKNOWN**.

## 4. Hypothèses et prédictions

### H-K3-COMPARE (descriptive : c'est ma lecture du contrat de `compare`)

`compare()` cherche une **transformation**, c'est-à-dire une permutation de positions.
Il ne rend pas un différentiel. Prédictions :

| Catégorie | `compare(preuve, claim)` prédit |
|---|---|
| S-SUB (feuille substituée) | `None` : aucune permutation n'apporte la valeur absente |
| S-ID (identiques) | `None` : rien à réifier |
| S-PERM (rôles inversés) | `PATTERN` : une permutation unique réconcilie les deux |
| NEG | `None` |
| OPP | `None` : **K3 seul ne relie pas deux opérateurs opposés** |

Un écart est consigné comme une erreur de ma lecture du code. Il n'invalide pas à lui
seul les hypothèses ci-dessous.

### H-P1-STRUCT (décisionnelle)

Pour une même forme avec des feuilles différentes et aucune relation connue, la
projection donne **UNKNOWN**, jamais SUPPORTED.

**PASS si les quatre conditions sont réunies** :
- 8/8 éléments S-SUB donnent UNKNOWN ;
- 5/5 éléments S-ID donnent SUPPORTED ;
- 2/2 éléments S-PERM donnent UNKNOWN ;
- **aucun SUPPORTED** en dehors de S-ID, toutes catégories et conditions confondues.

### H-P1-NEG-A (décisionnelle : représentation, sans modifier K3)

Pour chacun des 4 éléments NEG :
- **A1** : `neg(P)` est un Node OBSERVATION ordinaire, dont le premier enfant est
  `op:neg` et le second est le Node de `P` ;
- **A2** : la proposition enveloppée est structurellement égale à la forme affirmative
  correspondante (la portée est conservée) ;
- **A3** : une négation placée sur un argument (`run(neg(man))`) est structurellement
  distincte à la fois de `neg(run(man))` et de `run(man)` (la portée est
  discriminante).

**PASS** si A1, A2 et A3 sont vraies pour les 4 éléments.

### H-P1-PROJ-NEG (décisionnelle : projection de la négation)

- 4/4 éléments NEG → CONTRADICTED ;
- le contrôle C-03 (`neg(run(man))` contre `run(woman)`) → UNKNOWN.

### H-P1-NEG-B (décisionnelle : opposition fournie comme donnée)

Pour chacun des 7 éléments OPP :

| Condition | Verdict prédit |
|---|---|
| B0 : `compare` seul | `None`, voir H-K3-COMPARE |
| B1 : aucune relation fournie | UNKNOWN |
| B2 : relation `incompatible(x, y)` fournie | CONTRADICTED |
| B3 : même relation, dans l'ordre inverse | CONTRADICTED |
| B4 : relation fournie mais sans rapport (celle de l'élément OPP suivant) | UNKNOWN |

**PASS** si B1 à B4 donnent le verdict prédit pour les 7 éléments.

## 5. Ce que chaque issue voudra dire

- **H-P1-STRUCT PASS** : K3 non modifié et une projection minimale suffisent à ne
  jamais produire SUPPORTED sur une substitution. Le faux SUPPORTED *Oslo / Cairo*
  vient donc d'une couche absente, pas du Core.
- **H-P1-NEG-A PASS** : la négation se représente avec K3 existant, sans nouvelle
  primitive.
- **H-P1-NEG-B PASS avec B0 = `None`** : K3 **n'exploite pas** lui-même l'opposition,
  c'est la projection qui le fait à partir d'une relation fournie. Voilà exactement
  **où commence le besoin d'une extension** : dériver ou apprendre ces relations, et
  décider si leur exploitation doit entrer dans l'algèbre.
- **Limites déclarées d'avance** :
  - la structuration est manuelle, donc la passerelle texte → structure n'est **pas**
    testée ;
  - la projection minimale n'a pas de subsomption : une preuve plus détaillée que la
    claim donne UNKNOWN ;
  - 27 éléments, déterministes : il n'y a ni statistique ni généralisation à tirer.

Tout FAIL est enregistré tel quel, puis expliqué, jamais effacé.
