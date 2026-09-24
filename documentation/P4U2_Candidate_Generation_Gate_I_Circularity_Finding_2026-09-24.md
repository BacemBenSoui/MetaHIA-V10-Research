# P4-U.2 — Gate I trivialement toujours PASS sur les candidats de `group_by_signature()` : trouvé en préparant V1-V4, benchmark NON construit (2026-09-24)

Répond à la demande explicite « Validez ce cadrage, construisez les
corpus V1-V4 ». Le protocole lui-même (Sec. 14) exige, avant tout run,
« une démonstration explicite de [l']identifiabilité attendue » pour
chaque cas — cette vérification, faite par exécution directe avant de
construire quoi que ce soit, **a révélé un défaut de mécanisme bloquant,
pas une case de cadrage à ajuster.** Conséquence : **aucun corpus V1-V4
n'a été construit.** Ce document explique pourquoi, avec des preuves
directes, pas une hypothèse.

## 1. Le test qui devait valider V1 a révélé le problème

Le cadrage (Sec. 5) exige que les buckets-leurres d'un cas comme V1 ne
déclenchent PAS Gate I. Test direct, avant toute construction verrouillée :

```python
# 3 classes de signature arbitraires, AUCUNE régularité injectée --
# exactement ce que group_by_signature() trouverait dans n'importe quel
# corpus mixte réaliste.
buckets = {'cont1': [...40 arêtes 1-saut...],
           'cont2': [...40 arêtes 2-sauts...],
           'dead':  [...40 impasses...]}

group_by_signature(sigs)   -> 3 buckets trouvés
evaluate_gate_i(bucket)    -> PASS, percentile=100.0   -- pour LES TROIS
```

**Les trois buckets, y compris des classes purement arbitraires sans
aucune régularité injectée, franchissent Gate I à 100 % de percentile.**
Reproduit une seconde fois sur un corpus à 2 classes (60 arêtes) : même
résultat, les deux buckets PASS. Ce n'est pas un cas limite ni un choix
malheureux de graine — c'est systématique.

## 2. Cause racine, comprise après vérification

`group_by_signature()` regroupe par ÉGALITÉ EXACTE de signature — donc
**tout bucket qu'elle produit est, par définition, parfaitement
homogène** : tous ses membres partagent une signature identique. Or
`Cohesion_B` mesure la distance intra-groupe moyenne — sur un groupe
dont tous les membres sont identiques, cette distance est **toujours
exactement 0**, donc la cohésion est **toujours exactement 1,0**, quel
que soit le contenu du bucket, réel ou arbitraire.

En comparaison, un ré-échantillonnage nul de même taille tiré d'un pool
contenant PLUSIEURS classes de signature ne donnera presque jamais une
cohésion parfaite (un tirage aléatoire mélange presque toujours des
classes différentes). **Résultat mécanique, pas statistique** : dès que
le pool contient plus d'une classe de signature, N'IMPORTE QUEL bucket
produit par `group_by_signature()` paraîtra « exceptionnellement
cohérent » face au modèle nul — y compris un bucket entièrement
arbitraire, sans aucune régularité réelle.

## 3. Conséquence directe sur V1-V4 — pourquoi la construction s'arrête ici

```text
V1 (signal net)     -- les buckets-leurres, censés échouer Gate I,
                       passeraient TOUS -- le cas ne peut pas démontrer
                       ce qu'il est censé démontrer
V2 (TWIN)           -- le bucket TWIN lui-même, censé échouer Gate I
                       (INSUFFICIENT_STRUCTURAL_INFORMATION), passerait
                       -- l'exact opposé du résultat attendu
V3 (nul pur)        -- tout bucket généré par le modèle nul aurait
                       encore ses propres buckets internes trivialement
                       homogènes -- même problème
V4 (chevauchement)  -- moins directement affecté (le candidat n'est PAS
                       homogène par construction dans ce cas précis),
                       mais reste construit sur le même mécanisme non
                       fiable pour la génération de candidats
```

**Construire ces corpus maintenant verrouillerait un benchmark qui ne
peut structurellement jamais échouer** — un benchmark où tout candidat
« découvre » quelque chose n'a aucune valeur scientifique, exactement
le piège que ce projet s'est toujours refusé (voir la discipline U1/U2/U3
de P4-U.1 : un mécanisme qui ne peut jamais dire non n'a rien démontré).

## 4. P4-U.1 avait déjà évité ce piège — pas par accident

`p4u1_unsupervised_pattern_discovery_v0_1.py`'s `group_by_skeleton()`
regroupe **aussi** par égalité exacte (de squelette de chemin, pas de
signature d'arête) — structurellement le même type de regroupement.
**Mais son Gate B ne teste jamais une cohésion interne** : il teste le
**SUPPORT** (le nombre d'instances partageant ce squelette) contre un
modèle nul, précisément parce qu'une cohésion interne à une classe déjà
égalée exactement est triviale et non informative. `CandidateSupport.support`
est un COMPTE, jamais une distance intra-groupe. **P4-U.2 a réutilisé
`Cohesion_B` — calibrée par les campagnes C1-C7 sur des groupes construits
à la main, JAMAIS produits par une génération de candidats par égalité
exacte — sans remarquer que cette combinaison particulière (égalité
exacte -> cohésion interne) est dégénérée par construction.** Aucune
campagne de calibration n'avait testé cette combinaison précise avant
aujourd'hui — c'est exactement la réserve de circularité déjà signalée
dans le cadrage d'implémentation (Sec. 2.2), maintenant confirmée plus
sévère que ce que sa formulation initiale laissait entendre : ce n'est
pas « une partie » de ce que Gate I mesure qui est imposée par la
génération de candidat, c'est la totalité, dès que le pool contient plus
d'une classe.

## 5. Ce qui n'est PAS remis en cause

`p4u2_autonomous_relation_discovery_v0_1.py` n'est pas modifié par ce
document. `Cohesion_B`, le modèle nul corrigé, la correction
multi-comparaisons, et Gate H v1.0 restent valides exactement pour
l'usage sur lequel ils ont été calibrés et testés (campagnes C1-C7 et
les 7 tests du commit `2174d00`) : des groupes candidats déjà construits,
jamais eux-mêmes homogènes par construction. Aucun de ces 7 tests ne
combine `group_by_signature()` avec `evaluate_gate_i()` — ils restent
valides, aucune régression.

## 6. Deux pistes de correction possibles — ni l'une ni l'autre décidée ici

```text
Piste A : statistique de SUPPORT, pas de cohésion, pour tout candidat
          issu de group_by_signature() -- mirroir direct du Gate B de
          P4-U.1 : tester si la TAILLE du bucket (nombre de membres
          partageant cette signature) dépasse ce qu'un modèle nul
          produirait, jamais la cohésion interne du bucket lui-même.

Piste B : modèle nul de Gate I reproduisant la PROCÉDURE COMPLÈTE de
          génération de candidat sous le null -- reconstruire le graphe
          sous un modèle nul, ré-exécuter group_by_signature() sur ce
          graphe nul, comparer une propriété du bucket résultant (taille
          ou cohésion) -- mirroir exact de la correction déjà appliquée
          à Gate H en campagne 5 pour le même type de défaut de
          sélection non reproduite sous le null.
```

Les deux pistes méritent d'être testées empiriquement avant tout choix
— exactement la discipline déjà appliquée à chaque décision de ce fil
(campagnes 1 à 7). Aucune des deux n'est implémentée ici.

## 7. État après cette découverte

```text
p4u2_autonomous_relation_discovery_v0_1.py    INCHANGÉ, toujours valide
                                                pour son usage calibré
Cadrage V1-V4 (documentation/P4U2_V1V4_Locked_Benchmark_Scope_V0_1.md)  
                                                PARTIELLEMENT INVALIDÉ --
                                                la Sec. 5 (spécification
                                                des 4 cas) ne peut pas
                                                être construite telle
                                                quelle tant que ce défaut
                                                n'est pas corrigé
Corpus V1-V4                                   NON CONSTRUITS
```

## 8. Prochaine étape

Avant toute construction de corpus verrouillé : calibrer explicitement
(sur des corpus jetables, jamais sur V1-V4 eux-mêmes) le comportement de
Gate I appliqué à des candidats produits par `group_by_signature()` --
piste A, piste B, ou une combinaison, testées empiriquement. Ce n'est
qu'après cette calibration que la construction de V1-V4 pourra reprendre
sur des bases vérifiées. Décision explicite du porteur du projet requise
avant de lancer cette calibration.
