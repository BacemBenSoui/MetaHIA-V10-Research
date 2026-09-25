# Addendum GEL n°1-ter — P1-TEXT-STRUCT v0 (2026-09-25)

**Statut : validé tel quel par le porteur du projet le 2026-09-25, y compris
l'adjudication T3.4.** Il est figé par empreinte SHA-256 (`GEL1TER.sha256`) **avant** la
rédaction du corpus tenu à l'écart. Il ne touche ni la passerelle A, ni `run_heldout.py`, ni le rapport de
conformité (GEL n°3, `d2dd51a`), ni `scorer.py`, ni la convention (GEL n°1 et n°1-bis).

**Motif.** Les annotations humaines existantes (v0.1, test n°1, et une annotation
supplémentaire du paquet du test n°1) ne sont pas utilisables comme référence. Ce sont
des **labels de paires**, et non des structures. Leurs phrases ont en outre été vues par
le développeur. Il faut donc un corpus nouveau, annoté en structures. Pour réduire le
coût humain sans rien céder sur l'indépendance, cet addendum **réduit la taille décidée
d'avance** et **précise les rôles**.

## T1 — Taille et répartition (remplace le tableau du §3 de `CONSIGNES_CORPUS_HELDOUT.md`)

**40 phrases**, fixées avant la rédaction. La taille n'est jamais ajustée après coup.

| Catégorie | Nombre |
|---|---|
| Voix passive : avec *by* (4), sans *by* (2) | 6 |
| Négation : *not* (3), *never* (2), *no* + nom (1), *nobody* / *nothing* sujet (1) | 7 |
| Adjectifs, épithètes ou attributs | 5 |
| Au moins deux compléments parmi manière, lieu et temps, dans des ordres variés | 6 |
| Nombres (3) et quantificateurs *all/every/some/several* (3) | 6 |
| Deux personnes ou animaux dans des rôles différents | 4 |
| Hors convention : question (2), deux propositions coordonnées (2), subordonnée (2) | 6 |
| **Total** | **40** |

Les autres règles des consignes restent inchangées : 4 à 14 mots, vocabulaire varié,
pas de nom propre de personne réelle, pas d'expression figée, pas d'exemple réutilisé.

**Conséquence annoncée d'avance.** Avec environ 34 phrases dans la convention,
l'intervalle de confiance de l'exactitude sera large, de l'ordre de ± 0,15. Les
barrières de sûreté restent évaluées phrase par phrase, avec le seuil dur de 1,00.

## T2 — Rôles et indépendance

| Rôle | Qui | Conditions |
|---|---|---|
| **Concepteur du corpus** | un tiers | N'a jamais vu de fichier MetaHIA. N'est pas annotateur. Remet `heldout_sentences.txt` et `categories.tsv` au porteur seulement |
| **Annotateur A** | le porteur du projet (Bacem Ben Soui) | Voir la réserve ci-dessous |
| **Annotateur B** | un tiers | N'est ni le concepteur ni le développeur. Annote **les 40 phrases** : `run_heldout.py`, figé, compte comme un désaccord toute phrase absente de B |
| **Adjudicateur** | voir T3 | — |
| **Développeur** | session Claude Code | Ne voit rien du corpus tenu à l'écart avant l'exécution unique (pré-enregistrement, §2) |

**Réserve d'indépendance pour l'annotateur A.** Le porteur du projet n'est pas le
développeur de la passerelle. Il a cependant vu, dans les échanges de développement,
quelques sorties de la passerelle sur des phrases `dev`, et les exemples de la
convention. Il n'a vu **aucune** sortie sur le corpus tenu à l'écart, qui n'existe pas
encore. Il s'engage à annoter selon la seule convention figée (GEL n°1 et n°1-bis), sans
chercher à anticiper le comportement de la passerelle. Cette réserve figure dans le
rapport final.

## T3 — Adjudication

1. A et B annotent **séparément**. Aucun ne voit l'annotation de l'autre avant
   d'avoir remis la sienne.
2. Le porteur valide les deux fichiers sur son poste (`gold_tools.py validate`), puis
   liste les désaccords (`gold_tools.py compare`).
3. **Règle d'adjudication (normative)** : chaque désaccord est tranché **uniquement**
   par la question « Quelle structure impose la convention gelée ? », et jamais par
   « Quelle structure permettra à la passerelle de réussir ? ». Aucune information issue
   du développement (sorties de la passerelle, corpus `dev`, rapport de développement)
   n'est consultée pendant l'adjudication.
4. **Adjudicateur** : A étant aussi le porteur, un désaccord entre A et B est tranché
   par un **accord écrit entre A et B**, chaque décision étant motivée par la règle de
   la convention invoquée (R1 à R15, A1 à A4). À défaut d'accord, la phrase reçoit
   `none` : elle est jugée hors convention, et cette décision est consignée. Retenu par
   le porteur le 2026-09-25.
5. Le résultat est `gold_adjudicated.tsv`, avec la liste des décisions et leur motif.
   Il n'est **jamais** transmis aux annotateurs avant la fin de l'adjudication.

## T4 — GEL n°2 (inchangé dans son principe)

Les **cinq empreintes** de `heldout_sentences.txt`, `categories.tsv`, `annotation_A.tsv`,
`annotation_B.tsv` et `gold_adjudicated.tsv` sont transmises au développeur, sans les
fichiers, et committées seules dans `GEL2.sha256`. Les noms de fichiers sont exactement
ceux-là. Les fichiers ne sont remis qu'ensuite, pour l'exécution unique.

## T5 — Ce qui ne change pas

La convention (GEL n°1 et n°1-bis), la passerelle A et son audit (GEL n°3), `scorer.py`,
les barrières de sûreté (1,00 / 1,00 / 1,00, 0 violation), le caractère descriptif de
l'exactitude, l'absence de tout verdict, `kernel2.py`.
