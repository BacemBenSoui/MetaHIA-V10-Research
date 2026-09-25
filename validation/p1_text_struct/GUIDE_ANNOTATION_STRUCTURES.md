# Guide d'annotation des structures (P1-TEXT-STRUCT v0) — annotateurs A et B

Vous recevez environ 80 phrases anglaises. Pour chacune, vous écrivez sa **structure**,
selon une notation simple, en appliquant les règles de `STRUCTURE_CONVENTION.md` (jointe
à ce guide). Deux personnes font ce travail **séparément**. Leurs désaccords sont
ensuite tranchés, **avant** tout test d'un programme.

## 1. La notation, en 3 minutes

- Une **feuille** est un mot en minuscules, **à sa forme de base** : *man*, *park*,
  *oslo*, *2024*. Pas d'article, pas de pluriel, pas de temps (*children → child*,
  *ran → run*).
- Une **application** s'écrit `tête(argument, argument, …)`.
- **Abstention** : `none`, si la phrase sort de la convention (question, deux
  propositions, subordonnée).

| Phrase | Structure |
|---|---|
| *A dog eats food.* | `eat(dog, food)` |
| *The man is running in the park.* | `in(run(man), park)` |
| *The man is not running in the park.* | `neg(in(run(man), park))` |
| *The books are stamped by the librarian.* | `stamp(librarian, book)` |
| *The letter was signed.* | `sign(_, letter)` |
| *The front door is open.* | `attr(attr(door, front), open)` |
| *Two boys play.* | `play(card(boy, 2))` |
| *All passengers left.* | `leave(q_all(passenger))` |
| *Yesterday the boy slowly crossed the bridge.* | `yesterday(slowly(cross(boy, bridge)))` |
| *Did the bus stop?* | `none` |

## 2. La méthode, pour chaque phrase

1. **Trouvez le verbe principal** et mettez-le à sa forme de base : c'est la tête.
2. **Rangez les arguments** : d'abord celui qui agit, puis celui qui subit, puis le
   second objet. Au passif, celui qui suit *by* est celui qui agit ; sans *by*,
   écrivez `_`.
3. **Enveloppez** avec les compléments. Du plus intérieur au plus extérieur : manière,
   puis lieu, puis temps. C'est **une convention d'écriture**, pas un jugement sur la
   phrase : l'ordre des compléments dans la phrase n'y change rien.
4. **La négation enveloppe tout**, toujours en dernier : `neg(…)`. Jamais sur un seul
   mot.
5. **Relisez** : un article, un pluriel ou un temps oublié ? Un mot remplacé par un
   synonyme ? **Ne remplacez jamais un mot par un autre**, même proche.

## 3. Les pièges les plus fréquents

- Remplacer un mot par un synonyme : **interdit**. On écrit le mot de la phrase, à sa
  forme de base.
- Placer `neg` à l'intérieur : `run(neg(man))` est faux ; la forme juste est
  `neg(run(man))`.
- Inverser qui agit et qui subit au passif.
- Garder une expression figée : *give a speech* s'écrit `give(x, speech)`.

## 4. Le fichier à rendre

Un fichier texte, une ligne par phrase : `H-001<TAB>phrase<TAB>structure`. Votre fichier
peut être vérifié, par le porteur du projet sur son poste, avec :

```bash
python validation/p1_text_struct/gold_tools.py validate annotation_A.tsv
```

Cette commande signale les erreurs de forme (arité, `neg` mal placé, nombre attendu).
Elle ne dit **rien** du fond.

## 5. Indépendance

- Travaillez seul(e), sans IA, sans parler des phrases à l'autre annotateur.
- Remettez votre fichier **uniquement au porteur du projet**.
- Ne déposez rien sur le serveur du projet ni dans un dépôt Git.
- Les désaccords entre A et B sont tranchés ensuite par une **adjudication**, avant le
  gel. Vous pourrez y être consulté(e).
