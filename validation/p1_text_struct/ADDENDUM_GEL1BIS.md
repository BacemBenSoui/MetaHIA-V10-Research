# Addendum GEL n°1-bis — P1-TEXT-STRUCT v0

**Date : 2026-09-25.** Décision du porteur du projet (Bacem Ben Soui).

Cet addendum complète `STRUCTURE_CONVENTION.md` du GEL n°1, qui n'est pas réécrit. En cas
de conflit, **l'addendum prime**. Il ne modifie aucun principe architectural du Core et
ne demande aucun verdict épistémique.

## A1 — R2 / R4 : participe passé après une copule

La règle R4 est désormais réservée aux **adjectifs**.

Lorsqu'un élément qui suit une copule est identifiable, selon la convention
morphologique, comme un **participe passé verbal**, il relève de R2. *by* est facultatif
pour cette forme passive.

- *The letter was signed.* → `sign(_, letter)`
- *The door is open.* → `attr(door, open)` (adjectif attributif, R4)

Cette distinction est une règle de représentation. Elle n'implique aucune décision
sémantique.

*Conséquence notée à la mise en œuvre* : l'identification est **morphologique**. Une
forme en *-ed* après une copule relève donc de R2 même quand un lecteur y verrait un
adjectif. Exemple : *The nurse is tired.* → `tire(_, nurse)`.

## A2 — Sujets négatifs *nobody* / *nothing*

En position de sujet, *nobody* et *nothing* sont représentés par l'agent réservé `_`, sous
négation.

- *Nobody opened the gate.* → `neg(open(_, gate))`
- *Nothing broke the window.* → `neg(break(_, window))`

Cette représentation est une **simplification structurelle**. Ici, `_` représente un sujet
négatif non individualisé : il ne doit pas être interprété comme strictement équivalent
à l'omission d'un agent dans une autre phrase. Aucun nouvel opérateur réservé n'est
ajouté.

## A3 — Déterminants possessifs

Les déterminants possessifs *my, your, his, her, its, our, their* ne sont ni supprimés,
ni représentés implicitement. Il n'existe pas d'opérateur réservé pour la possession ;
une phrase qui exige cette relation est donc **hors couverture de la passerelle A** et
reçoit `null`.

- *Her brother opened the gate.* → `null`

Cette règle est volontairement fail-closed : aucune information présente dans le texte
ne doit être supprimée silencieusement.

## A4 — Adverbes temporels déictiques

La convention ajoute la catégorie fermée `deictic_adverbs`, qui comprend
**exclusivement** : *yesterday, today, now, tonight*. Ce sont des adverbes temporels
couverts par R8, donc des ressources fermées permises à la passerelle A.

- *The boy crossed the bridge yesterday.* → `yesterday(cross(boy, bridge))`

Cet amendement n'ajoute aucun autre adverbe temporel.

## A5 — Catégorie des phrases tenues à l'écart

Le corpus tenu à l'écart est accompagné d'un fichier `categories.tsv`, au format
`H-001<TAB>catégorie`, avec une seule catégorie par identifiant. Les catégories sont
celles du protocole (§3 de `CONSIGNES_CORPUS_HELDOUT.md`). Elles servent uniquement à
ventiler les résultats : ce ne sont ni une structure de référence, ni une information
fournie à la passerelle pendant l'exécution. `categories.tsv` est un artefact tenu à
l'écart, inclus dans le **GEL n°2** par son empreinte SHA-256.

## A6 — Conséquences sur la conformité

- La catégorie `deictic_adverbs` est ajoutée aux catégories autorisées de
  `compliance_audit.py`. **Aucun autre changement à l'audit.**
- `scorer.py` reste inchangé.
- Le Core, `kernel2.py` et tout mécanisme de verdict restent exclus.

## A7 — Point de gel

Le GEL n°1-bis comprend cet addendum et la modification minimale de l'audit (A6). La
convention du GEL n°1 reste inchangée et complétée par cet addendum.

Il est créé et empreinté **avant** la génération du corpus tenu à l'écart, les
annotations A et B, l'adjudication et le GEL n°2. La passerelle A est ensuite réadaptée
sur `dev` uniquement, puis repassée par l'audit avant le GEL n°3.

**Principe de couverture** : la couverture est une **propriété mesurée** du système, et
non une cible que l'on atteindrait en ajoutant des heuristiques. Une structure non
déterminable sans hypothèse supplémentaire donne `null`.

## Diffusion (note opérationnelle)

Cet addendum est transmis :
- **avec** `STRUCTURE_CONVENTION.md` et `GUIDE_ANNOTATION_STRUCTURES.md` aux annotateurs
  A et B (points A1 à A4) ;
- **avec** `CONSIGNES_CORPUS_HELDOUT.md` au concepteur du corpus (point A5) : c'est le
  concepteur qui fournit `categories.tsv` avec `heldout_sentences.txt`.
