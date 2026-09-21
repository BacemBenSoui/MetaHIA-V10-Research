# MetaHIA V10 — CLI préproduction M1-M6 v0.1

Date : 2026-09-21
Statut : **implémenté et testé — répond à la question initiale de ce chantier**

## 1. Objet

Ce chantier avait commencé par la question : *le core algébrique (kernel + core +
parser + ...) peut-il être mis en préprod pour test humain ?* La réponse à ce
moment-là était non — `m1_m6_interface_v0_1.py`/`v0_2.py` sont des contrats de
composition internes typés, pas une surface utilisable par un humain sans lire
le code Python.

`cli_preprod_v0_1.py` est cette surface, volontairement minimale : elle
n'ajoute aucune nouvelle capacité, elle expose seulement ce qui existe déjà et
est déjà validé (`build_real_corpus_v2`, `build_organization_corpus`,
`StructuralLearningPolicy`, `split_by_rule`) derrière quatre commandes.

## 2. Commandes

```bash
python cli_preprod_v0_1.py manifest
python cli_preprod_v0_1.py list-records --domain family|organization|supply_chain|combined
python cli_preprod_v0_1.py regression --domain family|organization|supply_chain|combined [--seed N]
python cli_preprod_v0_1.py predict --domain family|organization|supply_chain|combined --record-id <id> [--seed N]
```

`supply_chain` (added 2026-09-21, P6) is a third, structurally distinct domain
(industrial supply chain: workers/workshops/factories/markets/parts) — see
`documentation/P6_Third_Domain_Supply_Chain_V0_1.md`.

`combined` (added 2026-09-21) pools all three real domains — it mirrors
`p6_three_domain_regression_v0_1.py`'s `combined_three` exactly (same 74
records, 44 rules, Brier holdout 0,35556 at seed 0). **Ce n'est pas une
revendication de transfert inter-domaines** : chaque domaine a son propre
vocabulaire de relations, donc `split_by_rule()` ne peut jamais placer la
règle d'un domaine dans le holdout d'un autre — `manifest` cite ce
disclaimer explicitement dans son champ `combined_domain_caveat`, pas
seulement ici.

Chaque sortie est un JSON structuré sur stdout.

## 3. Discipline de transparence (non négociable)

`predict` renvoie systématiquement le champ `basis` de
`StructuralPrediction` — jamais masqué, jamais arrondi vers une confiance plus
haute. `regression` renvoie `basis_distribution_over_holdout`, qui montre
directement que 100 % des prédictions holdout de ce projet reposent sur
`BASIS_GLOBAL_PRIOR` (voir `documentation/MetaHIA_M6_Structural_Learning_V0_1.md`
Sec. 11) — un testeur humain voit cette limite dès la première commande
`regression`, pas seulement dans un document séparé.

`manifest` cite explicitement cette limite dans son champ
`known_limitation`, avant même qu'un testeur ne lance une régression.

## 4. Portée explicitement exclue

- M7 (couche LLM) : jamais importé par ce fichier — vérifié par exécution
  (`manifest.m7_excluded = true`), pas seulement par lecture du code.
- Aucun appel réseau, aucune dépendance à un serveur LAN.
- Aucune modification de M1/M6 : ce fichier ne fait qu'appeler l'API publique
  déjà existante et déjà testée séparément.
- Ce n'est pas une API HTTP, ni un service — c'est un exécutable en ligne de
  commande pour un testeur humain local.

## 5. Vérification

`tests/test_cli_preprod_v0_1.py` (11 tests, sous-processus réels, pas de
mock) :

1. `manifest` exclut M7 et cite la limite `BASIS_GLOBAL_PRIOR` ;
2. `list-records` retourne exactement les 24 enregistrements du corpus
   Organisation ;
3. `regression --domain family` reproduit exactement le baseline déjà
   validé (Brier holdout 0,48125, 26 enregistrements, 20 règles) ;
4. `regression --domain organization` reproduit exactement le baseline déjà
   validé (Brier holdout 0,6953125, 24 enregistrements, 12 règles) ;
5. `regression --domain supply_chain` reproduit exactement le baseline déjà
   validé (Brier holdout 0,375, 24 enregistrements, 12 règles) ;
6. `regression --domain combined` reproduit exactement le baseline P6
   `combined_three` (Brier holdout 0,35556, 74 enregistrements, 44 règles) ;
7. `manifest` liste `combined` et cite explicitement qu'il ne s'agit pas
   d'une revendication de transfert ;
8. `list-records --domain combined` regroupe exactement les trois préfixes
   de domaine (`realv2`, `orgv1`, `supplyv1`), aucun perdu ni dupliqué ;
9. `predict` ne masque jamais son `basis` et l'issue prédite correspond à
   l'issue réelle listée par `list-records` ;
10. `predict` échoue fermé (code de sortie non nul, message explicite) sur un
    `record_id` inconnu ;
11. tout enregistrement réellement en holdout pour la graine testée reçoit
    bien `basis = GLOBAL_PRIOR` — vérifié en itérant sur tous les
    enregistrements Famille, pas supposé.

## 6. Limites déclarées

- Portée M1-M6 uniquement (M7 exclu par construction, comme l'interface
  v0.2).
- Quatre domaines sélectionnables (Famille, Organisation, Chaîne
  d'approvisionnement, Combiné) — `combined` pool les trois domaines réels,
  ce n'est pas un cinquième corpus indépendant.
- Aucune persistance, aucun état entre appels — chaque commande reconstruit le
  corpus et réentraîne la politique à chaque exécution (corpus assez petit
  pour que ce ne soit pas un problème de performance).
- Ce n'est pas une clôture de gate scientifique : `predict`/`regression`
  exposent les mêmes chiffres déjà connus, ils ne prouvent rien de nouveau.
