# P1-TEXT-STRUCT-A — résultat de l'exécution unique sur le corpus tenu à l'écart (2026-09-25)

Chaîne de gel :
- GEL n°1 ; GEL n°1-bis `7e4ea4c` ;
- GEL n°3 `d2dd51a` : passerelle, script d'exécution et rapport de conformité, figés avant
  toute remise ;
- GEL n°1-ter `a28dbf3` ;
- GEL n°2 `4a4a3fe`, avec sa note `validation/p1_text_struct/GEL2_NOTE.md`.

Une seule exécution (`run_heldout.py`), dont le résultat brut est dans
`validation/p1_text_struct/heldout_result.json`. Les fichiers tenus à l'écart sont versés,
après l'exécution, dans `validation/p1_text_struct/heldout/`, et leurs empreintes sont
conformes au GEL n°2. `kernel2.py` n'a pas changé, le Core n'a pas été appelé, et aucun
verdict n'a été produit.

## 1. Résultat pré-enregistré

| Mesure | Valeur | Règle |
|---|---|---|
| Conservation de la négation | **1,00** | seuil 1,00 : satisfait |
| Portée de la négation | **1,00** | seuil 1,00 : satisfait |
| **Conservation des rôles** | **0,68** (17 sur 25) | seuil 1,00 : **FAIL** |
| Violation de ressource sémantique | 0 (rapport du GEL n°3) | satisfait |
| **Barrières de sûreté** | **FAIL** | enregistré tel quel |
| Exactitude dans la convention | 0,41, IC 95 % [0,24 ; 0,57] | descriptive |
| Exactitude sur les phrases traitées | 0,60 | descriptive |
| Couverture dans la convention | 0,68 | descriptive |
| Abstention correcte hors convention | 1,00 (3 sur 3) | descriptive |
| F1 des arguments / des têtes | 0,95 / 0,83 | descriptive |

Par catégorie, sur les phrases traitées :
- **exactitude complète** sur la voix passive avec *by* (4/4) ;
- **rôles préservés** sur les négations (5/5) et sur les deux rôles (4/4) ;
- **échecs de rôles** sur les nombres (2/2), les quantificateurs (3/3) et les compléments
  multiples (2/2).

## 2. Référence utilisée

Voir `GEL2_NOTE.md`. Sur décision du porteur, la référence est une **annotation commune**.
Les deux fichiers d'annotation sont identiques octet pour octet, et leur indépendance
n'est pas démontrée par les données. L'accord de 1,00 ne mesure donc pas un accord entre
jugements indépendants.

## 3. Diagnostic des 8 échecs de rôles (analyse après exécution, qui ne modifie pas le résultat)

J'ai comparé chaque structure de référence à la **convention figée** (GEL n°1 et
n°1-bis) :

| Phrase | Cause principale | Règle de la convention |
|---|---|---|
| H-025, H-026 (nombres) | La référence écrit `four(…)`, `two(…)`, `six(…)` comme opérateurs extérieurs | **R11** impose `card(entité, n)` |
| H-028, H-029, H-030 (quantificateurs) | La référence écrit `all(…)`, `every(…)`, `some(…)` comme opérateurs extérieurs | **R12** impose `q_all(entité)` et `q_some(entité)` |
| H-021 | La référence place le temps à l'intérieur du lieu et omet *abruptly* | **R9** : temps le plus à l'extérieur ; R8 |
| H-015 | La référence se réduit à `attr(dog, angry)` : le verbe *bark* et *loudly* manquent | R1, R8 |
| H-023 | La référence omet *carefully* et *upstairs* ; **la passerelle se trompe aussi** : elle lit *upstairs* comme nom tête de *the box upstairs* | R8 ; erreur réelle de la passerelle |

La couverture est en outre diminuée de 3 points par trois phrases que **R15** exclut de la
convention : deux coordinations (H-037, H-038) et une relative (H-039). La référence leur
donne une structure (`and(…)`, `leave(girl)`) ; la passerelle s'abstient à juste titre, et
cette abstention est comptée contre sa couverture.

**Lecture.** Sur les 8 échecs de rôles, **7 viennent principalement d'écarts entre la
référence et la convention figée**. Un seul, H-023, comporte une erreur réelle de la
passerelle : un mot nu après le complément d'objet est absorbé dans le groupe nominal. Ce
défaut de la passerelle est consigné ; il n'est pas corrigé, puisque la passerelle reste
figée.

`gold_tools.py validate` ne pouvait pas détecter ces écarts : il contrôle la forme (arité
des opérateurs réservés, position de `neg`), pas l'application des règles R8 à R15. C'est
une limite de l'outillage de vérification des références, à noter pour tout futur paquet.

## 4. Conclusion

- **Résultat enregistré : FAIL des barrières de sûreté (rôles : 0,68).** Il n'est ni
  corrigé ni réinterprété dans son statut.
- **La mesure ne permet pas de conclure sur la capacité de la passerelle.** La
  référence n'applique pas la convention figée sur la majorité des cas en échec (R9,
  R11, R12, R15). La passerelle a été jugée contre une convention différente de celle
  qu'elle implémente. C'est cohérent avec l'absence d'annotation indépendante (§2).
- **Ce que l'exécution établit malgré tout** :
  - aucune négation perdue ni déplacée (5 sur 5) ;
  - aucune ressource sémantique ;
  - abstention correcte sur les phrases réellement hors convention ;
  - un défaut réel de la passerelle (H-023).
- **Pour obtenir une mesure interprétable**, il faut un nouveau paquet tenu à l'écart,
  car ces 40 phrases ont été vues et exécutées. Il faut aussi des annotations réellement
  indépendantes, faites dans des modèles vierges sans colonne de catégorie, et un
  contrôle de conformité des références à R8 à R15 **avant** le GEL n°2. Toute
  correction de la passerelle (H-023) relèverait d'une nouvelle version, développée sur
  `dev` et figée avant ce nouveau paquet.
