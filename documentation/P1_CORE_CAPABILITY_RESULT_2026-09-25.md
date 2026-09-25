# Capacité du Core K3 sur des paires P1 structurées à la main — résultat (2026-09-25)

Pré-enregistrement : `validation/p1_core_capability_2026-09-25/PREREGISTRATION.md`,
figé (sha256) et poussé avant l'exécution, commit `72efe0d`. Une seule exécution
(`harness.py`), résultats bruts dans `results.json`. `kernel2.py` est inchangé
(`c76adfd2…efc9aa9`, vérifié avant et après). **Expérience de capacité du Core : ce
n'est ni un test de P1 ni une validation de V6.**

## 1. Résultats

| Hypothèse | Résultat | Détail |
|---|---|---|
| H-K3-COMPARE (descriptive) | **toutes les prédictions confirmées** | `None` sur S-SUB (8/8), S-ID (5/5), NEG (4/4), OPP (7/7) et C-03 ; `PATTERN` sur S-PERM (2/2) |
| **H-P1-STRUCT** | **PASS** | S-SUB 8/8 UNKNOWN, S-ID 5/5 SUPPORTED, S-PERM 2/2 UNKNOWN, **0 SUPPORTED hors S-ID** |
| **H-P1-NEG-A** | **PASS** | A1, A2 et A3 vrais sur 4/4 |
| **H-P1-PROJ-NEG** | **PASS** | NEG 4/4 CONTRADICTED, contrôle C-03 UNKNOWN |
| **H-P1-NEG-B** | **PASS** | sur 7/7 : B1 UNKNOWN, B2 CONTRADICTED, B3 CONTRADICTED, B4 UNKNOWN ; B0 `None` |

## 2. Ce que cela établit, et ce que cela n'établit pas

**Établi, avec K3 non modifié :**

1. **La séparation des couches est réalisable.** Une projection minimale qui ne
   s'appuie que sur les primitives publiques de K3 ne produit **jamais** SUPPORTED sur
   une substitution (*Oslo / Cairo*, *attorney / lawyer*, *red / blue*). Le faux
   SUPPORTED de P1 venait d'une couche **absente**, le raccourci lexical de
   `PredicateEntailment`, et non du Core.
2. **`compare()` n'est pas un comparateur de différences : c'est un découvreur de
   transformations.** Il renvoie `None` aussi bien pour deux structures identiques que
   pour une substitution. Seule une inversion de rôles, qu'une permutation explique,
   donne un `PATTERN`. Le résultat de `compare` ne peut donc **pas** servir d'entrée
   à un verdict : une projection doit s'appuyer sur `structural_equal` et sur le
   repérage des positions différentes. C'est la précision la plus utile de
   l'expérience pour concevoir la couche épistémique.
3. **La négation se représente sans nouvelle primitive.** `neg(P)` est un Node
   OBSERVATION ordinaire. La proposition niée est conservée à l'identique, et une
   négation placée sur un argument reste structurellement distincte d'une négation
   placée sur la proposition.
4. **K3 n'exploite pas lui-même l'opposition.** Sur les 7 paires opposées, `compare`
   donne `None` (B0). C'est la projection qui produit CONTRADICTED, et seulement quand
   une relation `incompatible(x, y)` est **fournie comme donnée**. Une relation sans
   rapport ne change rien (B4). **C'est la frontière exacte du Core actuel.** Le
   besoin d'extension commence là : obtenir ces relations (les observer, les dériver,
   les apprendre) et décider si leur exploitation doit entrer dans l'algèbre ou rester
   dans la projection.

**Non établi (limites déclarées d'avance) :**

- **La passerelle texte → structure n'est pas testée.** La structuration est
  manuelle, et c'est elle qui fait l'essentiel du travail : voix passive ramenée à
  l'actif (W-001 à W-003), temps supprimé, articles supprimés. C'est le **chaînon
  manquant principal**.
- **Le résultat est confirmatoire par construction.** Les 27 éléments sont
  déterministes, les prédictions viennent de la lecture du code, et la projection a
  été écrite par la même session. L'expérience montre **où** se placent les couches,
  pas une capacité de généralisation. Elle ne donne aucune statistique.
- **La projection n'a pas de subsomption** : une preuve plus détaillée que la claim
  donne UNKNOWN.

## 3. Écart descriptif avec les humains

Ce n'est pas un critère, mais il est instructif. Sur les 8 substitutions sans
relation, les humains répondent 5 fois CONTRADICTED : lieux « *right now* », couleurs
d'une même balle, jours. La projection répond UNKNOWN. Ce CONTRADICTED humain repose
sur des **relations implicites** : un lieu unique à un instant donné, une couleur
unique pour un objet, des jours différents. C'est exactement ce que B2 fournit
explicitement, et W-054-R le montre : la même paire *Oslo / Cairo* donne CONTRADICTED
dès que la relation est fournie.

De même, *attorney / lawyer* (humain : SUPPORTED) demanderait une relation
d'équivalence fournie ou observée, symétrique de l'incompatibilité. Ce cas n'a pas été
testé ici.

Les humains ne sont d'ailleurs pas stables sur ce point : *inside / outside the room*
est UNKNOWN (P1-089), mais *inside / outside the house* est CONTRADICTED (P1-054).

## 4. Conséquences pour la feuille de route (aucune décision prise ici)

```text
TEXTE ──[manquant : passerelle texte → Node/Apply]──► Node / Apply
                                                          │
                                                          ▼
                             Compare (transformations) + structural_equal (identité / positions)
                                                          │
                                                          ▼
      Projection épistémique : UNKNOWN par défaut ; SUPPORTED seulement si identité ;
      CONTRADICTED seulement via neg(P) contre P, ou via une relation fournie
                                                          │
                                                          ▼
      [manquant : source des relations (incompatible, équivalent…), avec provenance ;
       jamais une vérité du Core]
```

Deux chantiers distincts, dans l'ordre suggéré :

1. **La passerelle texte → structure**, morpho-syntaxique, sans lexique. Elle se mesure
   sur des paires dont la structure attendue est figée d'avance.
2. **La source contrôlée des relations** (opposition, incompatibilité, équivalence),
   chaque relation portant une provenance, en respectant la règle qui interdit à une
   dérivation de devenir une preuve.

Toute promotion vers V6 reste soumise au statut `EMPIRICALLY VALIDATED` et à une
décision du porteur du projet.
