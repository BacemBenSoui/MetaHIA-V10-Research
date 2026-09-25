# Convention de structure cible, texte → Node/Apply (H-P1-TEXT-STRUCT) — PROJET v0.1

**Statut : projet à valider par le porteur du projet.** Une fois validée, cette
convention est figée par empreinte **avant** la rédaction du corpus, des structures
de référence et de la passerelle. Elle définit la sortie attendue ; elle n'est pas un
algorithme.

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
| R2 | **Voix passive ramenée à l'actif** : le complément d'agent (*by X*) devient l'agent. Sans *by*, l'agent est le réservé `"_"` | *The books are stamped by the librarian.* → `["stamp","librarian","books"]` |
| R3 | Temps, aspect, modaux, auxiliaires, articles, démonstratifs et nombre grammatical sont **supprimés** | *is running*, *ran*, *will run* → `run` |
| R4 | Copule avec adjectif ou participe : `["attr", entité, adjectif]` | *The door is open.* → `["attr","door","open"]` |
| R5 | Adjectif épithète : l'entité devient `["attr", nom, adjectif]`, avec un niveau par adjectif, dans l'ordre du texte, le plus proche du nom en premier | *the front door* → `["attr","door","front"]` |
| R6 | Copule avec préposition de lieu : `[préposition, entité, lieu]` | *The woman is inside the house.* → `["inside","woman","house"]` |
| R7 | Complément circonstanciel prépositionnel : `[préposition, proposition, objet]` qui enveloppe la proposition | *runs in the park* → `["in",["run","man"],"park"]` |
| R8 | Adverbe (de manière, de temps) : `[adverbe, proposition]` qui enveloppe la proposition | *opened the gate slowly* → `["slowly",["open","man","gate"]]` |
| R9 | **Ordre des enveloppes** quand plusieurs compléments s'appliquent : manière, puis lieu, puis temps, de l'intérieur vers l'extérieur ; à catégorie égale, ordre du texte, le plus proche du verbe à l'intérieur | *Right now X is speaking in Oslo.* → `["now",["in",["speak","x"],"oslo"]]` |
| R10 | **Négation propositionnelle** : `["neg", proposition]`, **la plus extérieure**, au-dessus de tous les compléments (portée de phrase). Couvre *not*, *never*, *no* déterminant et *nobody* sujet | *The dog never enters the house.* → `["neg",["enter","dog","house"]]` |
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

**Le choix d'un analyseur syntaxique statistique (par exemple spaCy) reste une
décision du porteur.** Ses modèles encodent des statistiques de corpus, mais aucune
relation lexicale ne lui est injectée. S'il est retenu, il sera déclaré comme ressource
et audité à part.
