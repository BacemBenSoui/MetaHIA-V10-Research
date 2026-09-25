# Pré-enregistrement P1-TEXT-STRUCT v0 (H-P1-TEXT-STRUCT-A) — GEL n°1 (2026-09-25)

**Question.** Une passerelle **déterministe**, limitée à la morphologie et aux classes
fermées, peut-elle retrouver à partir du texte la structure cible d'une convention
**indépendante** (`STRUCTURE_CONVENTION.md`), sans que la sémantique soit introduite
clandestinement dans le protocole ?

**Aucun verdict épistémique** n'est demandé dans cette expérience : ni SUPPORTED, ni
CONTRADICTED, ni UNKNOWN. On mesure la structure, pour séparer deux sources d'erreur :

```text
erreur de structuration  ≠  erreur de raisonnement
```

**Exclu de cette expérience** : toute modification de `kernel2.py`, toute PR
d'intégration vers V6, tout analyseur statistique. L'analyseur statistique fera
l'objet d'une expérience ultérieure distincte, P1-TEXT-STRUCT-B.

## 1. Décisions du porteur du projet (2026-09-25), figées ici

| Élément | Décision |
|---|---|
| Passerelle | **A : règles déterministes** dans le dépôt, morphologie et classes fermées uniquement, aucune ressource sémantique |
| Corpus tenu à l'écart | **Écrit par un tiers** (`CONSIGNES_CORPUS_HELDOUT.md`), 80 phrases |
| Structures de référence | **Double annotation indépendante** (A et B, `GUIDE_ANNOTATION_STRUCTURES.md`), puis **adjudication avant le gel** |
| Convention | Représentation canonique ; ordre des compléments = convention de sérialisation (R9) ; négation = couche canonique la plus extérieure (R10) ; pas d'expression figée (R13) ; abstention permise hors convention (R15) |

## 2. Isolement du développeur (règle absolue)

Le développeur de la passerelle, **y compris toute session Claude Code travaillant sur
ce dépôt ou sur le serveur 192.168.1.11**, ne voit **ni les phrases tenues à l'écart,
ni leurs structures**, tant que la passerelle et son protocole d'exécution ne sont pas
figés cryptographiquement (GEL n°3).

- Le corpus, les annotations A et B et le fichier adjugé restent **hors du dépôt et
  hors du serveur**, chez le porteur du projet.
- Seules leurs **empreintes sha256** sont committées, au GEL n°2.
- Le porteur valide et compare les annotations **sur son propre poste**, avec
  `gold_tools.py` (`validate`, `compare`).
- Les fichiers ne sont transmis qu'après le GEL n°3, pour l'exécution unique.
- La passerelle est développée **uniquement** sur un corpus `dev` tiré des jeux de
  développement P1 (v0.1, test n°1, 9 842), avec des structures écrites par le
  développeur. `dev` sert au développement : il n'est jamais une mesure.

## 3. Mesures

`scorer.py` est purement fonctionnel : (structure prédite, structure de référence) →
métriques.

**Barrières de sûreté**, avec des seuils durs, évaluées sur les phrases traitées dans la
convention :

| Barrière | Seuil |
|---|---|
| Conservation de la négation (même nombre de `neg`) | **1.00** |
| Portée de la négation (mêmes adresses de `neg`) | **1.00** |
| Conservation des rôles (chaque feuille commune à la même adresse) | **1.00** |
| Ressource sémantique interdite (`compliance_audit.py`) | **0 violation** |

Les barrières portent sur les **adresses de position** (indices seulement). Une erreur
de morphologie sur une tête n'est donc jamais comptée comme une faute de rôle ou de
portée : elle relève de la mesure descriptive des têtes.

**Mesures descriptives**, sans seuil PASS/FAIL dans cette première expérience :

- **exactitude structurelle dans la convention**, avec son intervalle de confiance à
  95 % par bootstrap (10 000 tirages, graine 20260925). **Une abstention compte comme
  non exacte**, si bien que l'abstention ne peut jamais améliorer l'exactitude ;
- exactitude sur les phrases traitées ;
- **couverture** dans la convention : taux de phrases traitées, et non `null` ;
- abstention correcte hors convention ;
- F1 des arguments et F1 des têtes (normalisation morpho-syntaxique) ;
- toutes les mesures ventilées par catégorie du §3 des consignes.

**Accord entre annotateurs** : accord exact de A et B avant adjudication, avec la liste
des désaccords tranchés. Il est rapporté, pour distinguer un désaccord humain d'une
erreur de la passerelle.

**Conformité du système** (`compliance_audit.py`, en dehors du scorer) :
- audit statique du code de la passerelle ;
- manifeste des dépendances, limité à la bibliothèque standard ;
- ressources déclarées dans `RESOURCES` avec une catégorie permise ;
- aucun nom évoquant une connaissance sémantique ;
- aucune entrée/sortie ni import dynamique ;
- un seul fichier autorisé ;
- tests négatifs dans `tests/test_p1_text_struct_scorer_v0_1.py`.

## 4. Issue

- **Barrières de sûreté** : PASS seulement si les quatre sont satisfaites. Tout écart
  est un FAIL de sûreté enregistré tel quel.
- **Performance** : décrite, jamais convertie en PASS/FAIL dans cette expérience.

## 5. Points de gel

```text
GEL n°1 (ce commit) : STRUCTURE_CONVENTION.md, scorer.py, compliance_audit.py, gold_tools.py,
                      CONSIGNES_CORPUS_HELDOUT.md, GUIDE_ANNOTATION_STRUCTURES.md, ce document
Rédaction heldout (tiers) → annotations A et B (séparées) → adjudication, chez le porteur
GEL n°2 : sha256 de heldout_sentences.txt, annotation_A.tsv, annotation_B.tsv, gold_adjudicated.tsv
          (empreintes seulement ; fichiers hors dépôt)
Développement de la passerelle sur dev uniquement
GEL n°3 : sha256 de la passerelle, de run_heldout.py et du rapport d'audit de conformité (0 violation exigée)
Remise des fichiers → vérification des empreintes du GEL n°2 → exécution unique → rapport
```
