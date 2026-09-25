# Pré-enregistrement H-P1-TEXT-STRUCT — PROJET v0.1 (2026-09-25), non figé

**Question.** Une passerelle texte → Node/Apply peut-elle produire automatiquement la
structure cible définie dans `STRUCTURE_CONVENTION.md`, **sans injecter la sémantique
que l'on prétend tester** ?

**Aucun verdict épistémique n'est demandé** : ni SUPPORTED, ni CONTRADICTED, ni
UNKNOWN. On ne mesure que la structure. Il s'agit de séparer deux sources d'erreur :

```text
erreur de structuration  ≠  erreur de raisonnement
```

## 1. Risque méthodologique principal et parade

Si la même personne, ou la même session, écrit la passerelle **et** les structures de
référence, le résultat est confirmatoire par construction : la passerelle reproduit
les conventions de son auteur. Parade proposée :

- **Deux corpus séparés.**
  - `dev`, pour construire la passerelle. Il peut reprendre des phrases des jeux de
    développement P1 (v0.1, test n°1, 9 842).
  - `heldout`, pour mesurer : environ 80 phrases **nouvelles**, avec leurs structures
    de référence. **Le développeur de la passerelle ne voit jamais ce corpus avant
    l'exécution unique.**
- **Les structures de référence de `heldout` sont écrites par une personne autre que
  le développeur**, selon la convention figée. Elles sont empreintées et scellées avant
  que la passerelle soit figée.
- Répartition cible de `heldout` :
  - voix passive ;
  - négation (dont *never*, *no* déterminant, *nobody*) ;
  - adjectifs épithètes et attributs ;
  - compléments de lieu et de temps imbriqués ;
  - cardinaux et quantificateurs ;
  - inversions de rôles ;
  - environ 15 % de phrases **hors convention**, dont l'abstention attendue est
    `null`.

## 2. Mesures (`scorer.py`, déjà écrit et testé, 7 tests)

| # | Mesure | Proposition de seuil PASS (à valider) |
|---|---|---|
| 1 | Structure exacte, sur les phrases traitées | ≥ 0,80 |
| 2 | Conservation des arguments (F1 des feuilles) | ≥ 0,95 |
| 3 | **Conservation de la négation : nombre et portée** | **= 1,00** : une négation perdue ou déplacée est une faute de sûreté |
| 4 | Conservation des rôles (F1 sur les triplets tête, position, argument) | ≥ 0,90 |
| 5 | Normalisation morpho-syntaxique (F1 des têtes) | ≥ 0,90 |
| 6 | Abstention : taux dans la convention / abstention correcte hors convention | ≤ 0,20 / ≥ 0,80 |
| 7 | Audit des ressources (`audit_resources`, plus revue du code) | 0 violation |

Tout est rapporté par catégorie de phénomène. Un FAIL est enregistré tel quel.

## 3. Décisions du porteur, requises avant le gel

1. **Quel type de passerelle ?**
   - **a)** Des règles écrites dans le dépôt, sans dépendance, limitées aux classes
     fermées et à la morphologie (convention, §4). C'est la plus fidèle au principe
     « pas de sens injecté », mais elle sera fragile face à la syntaxe réelle.
   - **b)** Un analyseur syntaxique statistique (spaCy), dont la sortie serait projetée
     vers la convention. Plus robuste, mais c'est une dépendance nouvelle, et ses
     modèles encodent des statistiques de corpus : il faudrait les déclarer et les
     auditer.
2. **Qui écrit le corpus `heldout` et ses structures de référence ?** Il faut une
   personne qui ne développe pas la passerelle et qui applique la convention. Il peut
   s'agir du porteur, à condition qu'il ne transmette rien au développeur avant
   l'exécution, ou d'un tiers formé à la convention.
3. **La convention et les seuils** : les valider tels quels, ou les amender. Ce n'est
   qu'ensuite que le gel n°1 a lieu.

## 4. Points de gel

```text
1. Validation porteur : convention + seuils + type de passerelle
2. GEL n°1 : STRUCTURE_CONVENTION.md + scorer.py + ce document (sha256)
3. Rédaction de heldout + structures de référence (par l'auteur désigné) → GEL n°2 (empreinte, scellé)
4. Développement de la passerelle sur dev uniquement → GEL n°3 (sha256 du code et des ressources)
5. Exécution unique : passerelle figée sur heldout → scorer → rapport
```
