# P1-TEXT-STRUCT-A — rapport de développement de la passerelle (2026-09-25)

**Ceci n'est pas une mesure.** Toutes les structures attendues de `dev_corpus.jsonl` ont
été écrites par le développeur de la passerelle, sur des phrases des jeux de
développement P1 ou construites pour le développement. Aucune n'est un gold
indépendant. Aucun contact avec le corpus tenu à l'écart : aucun fichier held-out
ouvert, reçu ou copié. `kernel2.py` n'a pas été modifié et le Core n'est pas appelé.
Aucun verdict n'est produit, et aucun fichier du GEL n°1 n'a été modifié.

## 1. Livrables

| Fichier | Rôle |
|---|---|
| `gateway_a.py` | Passerelle déterministe. Elle utilise uniquement des classes fermées et de la morphologie, toutes déclarées dans `RESOURCES` (24 ressources, 9 catégories permises). Elle ne dépend que de `re` et de `typing` |
| `dev_corpus.jsonl` | 58 phrases de développement : structure selon la convention, et politique de la passerelle (structure ou abstention, avec la raison) |
| `tests/test_p1_text_struct_gateway_a_v0_1.py` | **101 tests** : le corpus dev, tous les cas obligatoires du mandat, les cas adversariaux, les invariants (déterminisme, pas de Core, pas de verdict, pas de `neg` sur un argument) et 5 tests de non-contamination injectés dans le **vrai** code source |
| `run_compliance_audit.py` | Ligne de commande pour `compliance_audit.py`, qui reste inchangé (gelé au GEL n°1). Rapport en trois niveaux |
| `run_heldout.py` | Exécution unique, à figer au GEL n°3. Elle refuse de tourner sans GEL n°2 et GEL n°3 dont les empreintes concordent ; elle refuse une seconde exécution. Vérifié : elle refuse bien en l'absence de GEL n°3 |

## 2. Conformité, en trois niveaux (tels que demandés)

1. **Audit statique** : **0 violation**. Pendant le développement, il a détecté une vraie
   non-conformité (une liste de mots non déclarée), corrigée.
2. **Tests négatifs** : les 5 injections dans le code réel de la passerelle (synonymes,
   liste d'entités, `import spacy`, `import os`, lexique lu dans un fichier) sont toutes
   détectées.
3. **Manifeste et environnement** : empreinte de la passerelle, modules effectivement
   chargés à l'import (`typing` seulement, en plus de `re`), version de Python.

**Non vérifié par l'audit** : une connaissance sémantique cachée dans le flux de contrôle
ou dans des chaînes littérales à l'intérieur des fonctions. Le code en contient
quelques-unes, toutes grammaticales : *by*, *no*, *few*, *being*, *been*, *be*, et les
suffixes *-ing*, *-ed*, *-ly*. La justesse des listes fermées elles-mêmes relève
également d'une revue. Un audit statique ne prouve pas l'absence de sémantique : il
documente ce qui a été contrôlé.

## 3. Information de développement (ce n'est pas une mesure)

Sur `dev` (58 phrases), score calculé contre la structure de la convention :

| Mesure | Valeur |
|---|---|
| Barrières : négation conservée / portée / rôles | 1,00 / 1,00 / 1,00 |
| Exactitude dans la convention (une abstention compte comme un échec) | 0,85 |
| Couverture dans la convention | 0,85 |
| Abstention correcte hors convention | 1,00 |

Ces chiffres sont **circulaires** : les attentes ont été écrites par le développeur. Ils
ne disent rien de la capacité réelle de la passerelle.

## 4. Politique d'abstention (fail-closed)

Quand les classes fermées et les règles gelées ne suffisent pas à décider, la passerelle
renvoie `null`. Deviner risquerait de déplacer un rôle ou une négation, ce qui est une
faute de sûreté. Abstentions délibérées :
- **mot nu en début de phrase ou après le verbe**, sans élément de classe fermée devant
  lui. Exemples : *Yesterday…*, *Right now…*, *eats food*, *works today*. Sans lexique
  ouvert, *today* et *food* sont indiscernables ;
- **verbe à la forme de base après un sujet au pluriel** : *Two boys play* ;
- **deux groupes en *in / on / at***, dont l'ordre de sérialisation (R9) dépend d'une
  classe (lieu ou temps) indécidable ;
- **plusieurs adverbes en *-ly***, **adverbe devant un nombre** (*exactly ten*),
  **déterminant possessif**, **préposition non couverte** (*with*, *for*, *to*, *from*,
  *of*…), **ponctuation interne** ;
- les cas de la convention elle-même : question, coordination, subordonnée (R15).

Erreurs morphologiques connues, qui n'affectent que les mesures descriptives :
- *buses* → *buse* : règle *-ses*, qui est juste pour *houses* et *exercises* ;
- *hit*, *cut*, *put* au passé : identiques à la forme de base, donc non reconnus comme
  verbes en l'absence d'auxiliaire.

## 5. Lacunes de la convention découvertes pendant le développement (à trancher par le porteur)

Le GEL n°1 est fermé. Ces points ne peuvent donc être tranchés que par un **addendum**
daté et empreinté. Il doit précéder le **GEL n°2** et, idéalement, le travail des
annotateurs. Sinon, les annotateurs A et B risquent de diverger, et l'adjudication
tranchera à la place de la convention.

1. **Conflit R2 / R4 (copule + participe sans *by*)**. R4 dit « copule avec adjectif
   **ou participe** → `attr` » ; R2 dit « sans *by*, l'agent est `_` ». *The letter was
   signed.* peut donc donner `attr(letter, signed)` ou `sign(_, letter)`. Le guide des
   annotateurs donne `sign(_, letter)`. **La passerelle s'abstient.** Proposition
   d'addendum : participe passé après une copule = R2, même sans *by* ; R4 est réservée
   aux adjectifs.
2. ***nobody*, *nothing* en sujet**. R10 les mentionne mais ne donne pas la structure du
   sujet : `neg(open(_, door))` ? ou `neg(open(somebody, door))` ? **La passerelle
   s'abstient.** Proposition : `neg(verbe(_, objet))`.
3. **Déterminants possessifs** (*his*, *her*, *their*…). R3 supprime les articles et les
   démonstratifs, mais ne dit rien des possessifs. **La passerelle s'abstient.**
   Proposition : les supprimer comme les articles (R3).
4. **Adverbes déictiques de temps** (*yesterday*, *today*, *now*, *tonight*). Ce sont des
   classes fermées de fait, mais elles ne figurent pas parmi les catégories permises (§4
   de la convention). Les consignes au concepteur en donnent pourtant un exemple
   (*Yesterday the boy slowly crossed the bridge*). **La passerelle s'abstient** sur ces
   phrases. Proposition : permettre une catégorie `deictic_adverbs`. C'est un addendum à
   la convention **et** à `compliance_audit.py`, et donc au GEL n°1.
5. **Catégories des phrases tenues à l'écart**. Le pré-enregistrement prévoit des
   résultats ventilés par catégorie, mais les consignes au concepteur ne lui demandent
   pas d'indiquer la catégorie de chaque phrase. Proposition : un fichier
   `categories.tsv` (`H-001<TAB>catégorie`), fourni par le concepteur et empreinté au
   GEL n°2. `run_heldout.py` l'accepte déjà en option.

## 6. Prochaine étape

Selon les décisions sur le §5 :
- **pas d'addendum** : GEL n°3 immédiat, avec la passerelle en l'état. Les abstentions
  correspondantes feront baisser la couverture, sans jamais toucher aux barrières ;
- **addendum** : GEL n°1-bis (convention, et audit si le point 4 est retenu), puis
  adaptation de la passerelle sur `dev`, nouvel audit, et enfin GEL n°3.

Dans les deux cas, le GEL n°3 reste antérieur à toute remise du corpus tenu à l'écart.

## 7. Révision après le GEL n°1-bis (même jour)

Le porteur du projet a tranché les cinq lacunes du §5 par l'addendum
`ADDENDUM_GEL1BIS.md`, figé et poussé **avant** toute modification de la passerelle
(commit `7e4ea4c`). La passerelle a été réadaptée **sur `dev` uniquement** :

| Point | Mise en œuvre |
|---|---|
| A1 | Copule suivie d'un participe passé morphologique → R2, `by` facultatif (*The letter was signed.* → `sign(_, letter)`). Adjectif → R4. Conséquence morphologique : *The nurse is tired.* → `tire(_, nurse)` |
| A2 | *nobody* ou *nothing* sujet → `neg(verbe(_, …))`. Hors position sujet, ou *no one* / *none* → `null` |
| A3 | Possessifs → `null`, sans suppression (comportement déjà en place, désormais conforme à l'addendum) |
| A4 | `DEICTIC_ADVERBS` = *yesterday, today, now, tonight*, déclarée `deictic_adverbs`. Traités **aux bords de la phrase** seulement ; au milieu (*is now running*) → `null`. Un déictique initial avec un groupe temporel → `null` (proximité au verbe indécidable) |
| A5 | `run_heldout.py` accepte déjà `categories.tsv`, qui sera vérifié contre le GEL n°2 |

**Information de développement** (ce n'est pas une mesure ; 67 phrases, attentes écrites
par le développeur) :
- barrières 1,00 / 1,00 / 1,00 ;
- exactitude et couverture dans la convention : 0,90 ;
- abstention correcte hors convention : 1,00.

Ce chiffre **n'est pas un objectif à pousser vers 1,00** : la couverture est une propriété
mesurée du système (addendum A7).

**Vérifications** :
- 129 tests P1-TEXT-STRUCT ;
- suite V10 complète : **876 passed** (747 préexistants inchangés, plus 129) ;
- audit de conformité : 0 violation ;
- fichiers du GEL n°1 intacts, hormis `compliance_audit.py`, modifié d'une ligne selon A6 et
  empreinté au GEL n°1-bis ;
- `kernel2.py` inchangé ;
- aucun contact avec le corpus tenu à l'écart.
