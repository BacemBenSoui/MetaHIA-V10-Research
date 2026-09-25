# Consignes pour le concepteur du corpus tenu à l'écart (P1-TEXT-STRUCT v0)

Document destiné au **tiers** qui écrit les phrases. Il n'a besoin que de ce document.

## 1. Ce qu'on vous demande

Écrire **80 phrases courtes en anglais**, une par ligne, réparties selon le tableau du
§3. Ces phrases serviront à mesurer si un programme sait retrouver la **structure
grammaticale** d'une phrase : qui fait quoi, à qui, où, quand, et avec quelle négation.
**Vous n'écrivez aucune réponse** : d'autres personnes écriront les structures.

## 2. Prérequis (à confirmer par écrit au porteur du projet avant de commencer)

- [ ] Anglais courant, niveau C1 ou plus.
- [ ] Vous n'avez jamais participé au projet MetaHIA et n'avez vu aucun de ses
  fichiers.
- [ ] Vous ne serez **pas** l'un des deux annotateurs des structures.
- [ ] Aucun outil d'IA générative, ni pour inventer ni pour reformuler.
- [ ] **Confidentialité stricte** : vous remettez le fichier **uniquement au porteur du
  projet** (Bacem Ben Soui). Ni les phrases ni le fichier ne doivent être déposés sur
  le serveur du projet, dans un dépôt Git ou dans un outil partagé.

## 3. Répartition des 80 phrases

| Catégorie | Nombre | Exemple de *forme* (ne pas réutiliser) |
|---|---|---|
| Voix passive, avec *by …* (8) ou sans (4) | 12 | *The letter was signed by the mayor.* |
| Négation : *not* (5), *never* (3), *no* + nom (3), *nobody* sujet (3) | 14 | *The baker never closes the shop.* |
| Adjectifs, épithètes ou attributs (*is + adjectif*) | 10 | *The tired nurse is happy.* |
| Au moins deux compléments parmi manière, lieu et temps, **dans des ordres variés** | 12 | *Yesterday the boy slowly crossed the bridge.* |
| Nombres (5) et quantificateurs *all/every/some/several* (5) | 10 | *Three pilots landed the plane.* |
| Deux personnes ou animaux dans des rôles différents (qui agit sur qui) | 10 | *The goat pushed the farmer.* |
| **Hors convention** : questions (4), deux propositions coordonnées (4), subordonnée (4) | 12 | *Did the bus stop?* / *The cat ate and the dog slept.* / *The man who sang left.* |

## 4. Règles d'écriture

1. Une phrase par ligne, **de 4 à 14 mots**, terminée par un point, sauf les questions.
2. Vocabulaire courant et varié : un même nom ou verbe dans **3 phrases au plus**.
3. Pas de nom propre de personne réelle, pas de marque, pas d'expression figée
   (*kick the bucket*, *break a leg*).
4. Pas de double négation, d'ironie ni de sens figuré.
5. **N'utilisez aucun exemple** de ce document ni aucune phrase trouvée en ligne.

## 5. Remise

Un fichier texte `heldout_sentences.txt` : une ligne par phrase, au format
`H-001<TAB>phrase`. Remis **uniquement** au porteur du projet, qui l'empreinte
(sha256) et le transmet aux deux annotateurs, séparément.
