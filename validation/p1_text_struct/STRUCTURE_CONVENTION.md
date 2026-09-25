# Convention de structure cible, texte → Node/Apply (P1-TEXT-STRUCT v0)

**Statut : validée par le porteur du projet le 2026-09-25, avec trois amendements
(R9, R10, §5).** Elle est figée au GEL n°1, avant la rédaction du corpus tenu à l'écart,
des structures de référence et de la passerelle. Elle définit la sortie attendue ; ce
n'est pas un algorithme.

## 1. Notation

- **Feuille** : chaîne en minuscules. C'est le lemme d'un nom, d'un adjectif, d'un
  adverbe ou d'un nombre, par exemple `"man"`, `"oslo"`, `"2024"`. Elle devient un
  `NodeRef` opaque.
- **Application** : liste `[tête, arg1, arg2, …]`, qui devient
  `apply(node_ref("op:" + tête), …)`. La tête est le lemme d'un verbe, d'une
  préposition ou d'un adverbe, ou l'un des opérateurs réservés du §3.
- Aucune autre forme n'est permise. La structure est un **arbre** : pas de variable,
  pas de coréférence.

## 2. Règles de construction

| # | Règle | Exemple |
|---|---|---|
| R1 | Proposition verbale : `[verbe_lemme, agent, patient?, objet2?]`, arguments dans l'ordre **agent, patient, second objet** | *A dog eats food.* → `["eat","dog","food"]` |
| R2 | **Voix passive ramenée à l'actif** : le complément d'agent (*by X*) devient l'agent. Sans *by*, l'agent est le réservé `"_"` | *The books are stamped by the librarian.* → `["stamp","librarian","book"]` |
| R3 | Temps, aspect, modaux, auxiliaires, articles, démonstratifs et nombre grammatical sont **supprimés** | *is running*, *ran*, *will run* → `run` |
| R4 | Copule avec adjectif ou participe : `["attr", entité, adjectif]` | *The door is open.* → `["attr","door","open"]` |
| R5 | Adjectif épithète : l'entité devient `["attr", nom, adjectif]`, avec un niveau par adjectif, dans l'ordre du texte, le plus proche du nom en premier | *the front door* → `["attr","door","front"]` |
| R6 | Copule avec préposition de lieu : `[préposition, entité, lieu]` | *The woman is inside the house.* → `["inside","woman","house"]` |
| R7 | Complément circonstanciel prépositionnel : `[préposition, proposition, objet]` qui enveloppe la proposition | *runs in the park* → `["in",["run","man"],"park"]` |
| R8 | Adverbe (de manière, de temps) : `[adverbe, proposition]` qui enveloppe la proposition | *opened the gate slowly* → `["slowly",["open","man","gate"]]` |
| R9 | **Ordre canonique de sérialisation** des compléments : manière, puis lieu, puis temps, de l'intérieur vers l'extérieur ; à catégorie égale, ordre du texte, le plus proche du verbe à l'intérieur. **Cet ordre est une convention de représentation**, nécessaire pour comparer deux arbres. **Ce n'est ni une préférence linguistique ni une relation sémantique.** Deux phrases qui ne diffèrent que par l'ordre de leurs compléments ont la même structure | *run quickly in Tunis today* et *run in Tunis quickly today* → `["today",["in",["quickly",["run","x"]],"tunis"]]` |
| R10 | **Négation propositionnelle** : `["neg", proposition]`, **couche canonique la plus extérieure**, au-dessus de tous les compléments (portée de phrase). Couvre *not*, *never*, *no* déterminant et *nobody* sujet. Une négation n'est **jamais** placée sur un argument (`run(neg(man))` est interdit) | *The dog never enters the house.* → `["neg",["enter","dog","house"]]` |
| R11 | Nombre cardinal : `["card", entité, "n"]` | *Two boys play.* → `["play",["card","boy","2"]]` |
| R12 | Quantificateur : `["q_all" \| "q_some", entité]` pour *all/every/each* et *some/several/a few* | *All passengers left.* → `["leave",["q_all","passenger"]]` |
| R13 | **Aucune expression figée** : *give a speech* → `["give","x","speech"]`, et *finish line* → `["attr","line","finish"]`. Un nom composé est traité comme un adjectif épithète (R5) | |
| R14 | **Aucune normalisation lexicale** : un synonyme reste une feuille différente (*attorney* ≠ *lawyer*, *sofa* ≠ *couch*) | |
| R15 | Phrase hors convention (question, subordonnée complexe, coordination de propositions) : la sortie attendue est **`null`**, c'est-à-dire une abstention | *Did the man run?* → `null` |

## 3. Opérateurs réservés

`attr`, `neg`, `card`, `q_all`, `q_some`, `_` (agent absent). Aucun autre opérateur
réservé ne peut être ajouté après le gel.

## 4. Ressources permises à la passerelle (critère 7)

**Permises**, c'est-à-dire des classes fermées et de la morphologie :
- articles et déterminants ;
- pronoms ;
- prépositions ;
- auxiliaires, copules et modaux ;
- négateurs ;
- conjonctions ;
- quantificateurs ;
- mots de nombre ;
- règles morphologiques de suffixe (*-s*, *-es*, *-ed*, *-ing*, *-ies*) ;
- table des **formes irrégulières** des verbes et des noms (*ran → run*,
  *children → child*). C'est de la morphologie, pas du sens.

**Interdites**, c'est-à-dire toute connaissance de sens :
- synonymes, antonymes, hyperonymes ;
- listes d'entités (gazetteers, villes, couleurs, métiers) ;
- relations entre mots, polarité affective ;
- expressions figées ;
- tout modèle entraîné sur du sens (plongements de mots, LLM).

**Décision du porteur (2026-09-25) : la passerelle est à base de règles déterministes
(option A).** Un analyseur statistique externe (spaCy) fera l'objet d'une expérience
ultérieure distincte (P1-TEXT-STRUCT-B). Il n'est pas permis ici.

La conformité à ce paragraphe est vérifiée par un **audit de conformité du système**
(`compliance_audit.py` : audit statique, manifeste des dépendances, fichiers autorisés,
tests négatifs). Le scorer ne peut pas l'observer à partir de paires (prédiction,
référence).

## 5. Barrières de sûreté (amendement du porteur)

Une négation perdue ou déplacée, ou deux arguments échangés, **ne sont pas des
approximations acceptables**. Ce sont des fautes de sûreté, évaluées par le scorer sur
les adresses de position (voir `scorer.py`) : indépendamment de la forme des têtes, une
erreur de morphologie ne compte donc pas comme une faute de rôle.
