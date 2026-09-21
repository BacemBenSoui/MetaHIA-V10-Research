# MetaHIA V10 — P6 : troisième domaine indépendant (chaîne d'approvisionnement) v0.1

Date : 2026-09-21
Statut : **implémenté, vérifié par exécution réelle — ne change pas la conclusion
« transfert inter-domaines non démontré »**

## 1. Objet

Après l'adoption de P5 (deux domaines : Famille, Organisation) et P4-R, la
question posée était : *un troisième domaine indépendant change-t-il la
conclusion selon laquelle le transfert structurel inter-domaines n'est pas
démontré ?* Ce document répond à cette question précise, par exécution
réelle, pas par supposition.

## 2. Le troisième domaine : chaîne d'approvisionnement

`corpus/supply_chain_facts_v0_1.json` — vocabulaire de relations disjoint des
deux autres domaines (`TRAVAILLE_DANS`, `RATTACHE_A`, `LIVRE_A`,
`DESTINEE_A`, `FABRIQUEE_PAR`), entités disjointes (ouvriers, ateliers,
usines, marchés, pièces).

Topologie **délibérément non isomorphe** à celle du corpus Organisation (pas
un simple renommage) : la branche `Atelier_A` a 3 ouvriers/3 usines/4 pièces,
la branche `Atelier_B` en a 1/1/0 — asymétrie vérifiée par
`tests/test_supply_chain_corpus_v0_1.py::test_supply_chain_topology_is_not_an_isomorphic_renaming_of_organization`.

`m6_corpus_from_supply_chain_v0_1.py` réutilise exactement le mécanisme déjà
validé (`m6_corpus_from_organization_v0_1.py`, séparation prédiction
structurelle / vérification indépendante) — seuls les fichiers de corpus et
le préfixe `record_id` (`supplyv1::`) changent.

Résultat réel (exécution directe, pas supposé) :

- 21 faits de découverte, 10 faits de preuve, 24 réclamations de
  vérification (17 accord, 7 `WRONG_ENDPOINT` délibéré) ;
- 28 motifs candidats considérés, 24 enregistrements réels, 16 exclus (aucun
  faussé/double-compté — vérifié) ;
- diversité d'issue réelle : **17 `SUPPORTED`, 7 `CONTRADICTED`** — non
  dégénéré ;
- 12 règles distinctes, profondeurs {1, 2} ;
- split par règle (graine 0) : 16 train / 4 validation / 4 holdout, aucune
  fuite de règle ;
- **Brier holdout = 0,375**, ECE = 0,0.

## 3. Pourquoi un transfert inter-domaines reste structurellement impossible à observer

Chaque domaine construit ses `PathPattern` à partir de son propre
vocabulaire de relations (`MEMBRE_DE` pour Famille, `TRAVAILLE_DANS` pour
Chaîne d'approvisionnement, etc.). La signature de règle
(`_rule_signature`, `m6_structural_learning_v0_1.py`) inclut ces identités
d'opérateur. Deux domaines ne peuvent donc jamais produire la même signature
de règle — `split_by_rule()` ne peut donc jamais placer une règle d'un
domaine en train et son « équivalent » d'un autre domaine en holdout, parce
qu'il n'existe aucun équivalent au sens de la signature. Ajouter un
troisième domaine ne peut donc **pas**, par construction, faire apparaître
un transfert qui n'existait pas avec deux domaines.

Vérifié directement (pas supposé) : sur le holdout du jeu combiné à trois
domaines (graine 0), **100 % des prédictions reposent sur
`BASIS_GLOBAL_PRIOR`** — exactement la même découverte transversale déjà
documentée dans `documentation/MetaHIA_M6_Structural_Learning_V0_1.md`
Sec. 11, maintenant reconfirmée sur un troisième domaine indépendant.

## 4. Ce qu'un troisième domaine PEUT changer : la stabilité de l'estimation combinée

Ce que la mise en commun de trois domaines peut réellement affecter, c'est
la stabilité statistique de l'estimation du prior global combiné (l'unique
base que ce projet a jamais utilisée en holdout). `p6_three_domain_regression_v0_1.py`
et `p6_three_domain_multiseed_v0_1.py` mesurent exactement cela.

### 4.1 Régression à graine fixe (graine 0)

| Domaine | Enregistrements | Règles | Holdout | Brier | ECE |
|---|---:|---:|---:|---:|---:|
| Famille | 26 | 20 | 5 | 0,48125 | 0,025 |
| Organisation | 24 | 12 | 4 | 0,6953125 | 0,3125 |
| Chaîne d'approvisionnement | 24 | 12 | 4 | 0,375 | 0,0 |
| **Combiné (3 domaines)** | 74 | 44 | 15 | **0,35556** | 0,13333 |

Round-trip JSON de l'interface v0.2 : `PASS` pour les quatre lignes, sans
aucune modification de `m1_m6_interface_v0_2.py` — l'interface gère un
troisième domaine sans changement de code.

### 4.2 Probe multi-graines (10 graines, 0 à 9)

| Domaine | Brier moyen | écart-type population | min | max |
|---|---:|---:|---:|---:|
| Famille | 0,535278 | 0,103619 | 0,406250 | 0,764444 |
| Organisation | 0,471875 | 0,215410 | 0,125000 | 0,695313 |
| Chaîne d'approvisionnement | 0,488281 | 0,289405 | 0,281250 | 1,320313 |
| Combiné (2 domaines, déjà documenté P5 Sec. 5) | 0,444565 | **0,107167** | 0,287774 | 0,680791 |
| **Combiné (3 domaines)** | 0,440232 | **0,056129** | 0,355556 | 0,558207 |

**Constat honnête, vérifié par exécution (pas hypothétique)** : l'écart-type
du Brier combiné passe de 0,107167 (deux domaines) à 0,056129 (trois
domaines) — une réduction d'environ moitié. La moyenne ne change presque
pas (0,444565 → 0,440232). Le domaine Chaîne d'approvisionnement pris seul
est lui-même le PLUS instable des trois (écart-type 0,289405, max 1,320313
sur un holdout de 2 à 4 enregistrements) — la stabilisation de l'ensemble
combiné vient donc de la taille du pool, pas de la qualité individuelle de
ce nouveau domaine.

**Interprétation, explicitement bornée** : ce résultat est cohérent avec
« plus de données pool stabilisent l'estimation du prior global », pas avec
« un transfert sémantique inter-domaines émerge ». Le test direct de la
Sec. 3 (100 % `BASIS_GLOBAL_PRIOR`) exclut cette seconde lecture. Aucune
affirmation de transfert n'est faite ici.

## 5. Tests

- `tests/test_supply_chain_corpus_v0_1.py` (9 tests) : indépendance du
  domaine, non-isomorphisme de la topologie, diversité d'issue réelle,
  répétabilité, comptabilité honnête, absence de collision de préfixe
  `record_id`, présence réelle d'accords et de désaccords dans les
  réclamations de vérification.
- `tests/test_p6_three_domain_regression_v0_1.py` (6 tests) : round-trip
  JSON pour les quatre lignes, non-régression des baselines Famille/
  Organisation déjà adoptées par P5, baseline Chaîne d'approvisionnement,
  disjonction de règles du combiné, absence de dépendance M7.
- `tests/test_p6_three_domain_multiseed_v0_1.py` (4 tests) : cinq tranches
  mesurées sur 10 graines chacune, non-régression du chiffre déjà documenté
  P5 (combiné à deux domaines), et vérification que les combinés à deux et
  trois domaines sont mesurés indépendamment (pas des alias).
- CLI (`cli_preprod_v0_1.py`) étendue avec `--domain supply_chain` (voir
  `documentation/MetaHIA_CLI_Preprod_M1_M6_V0_1.md`), 1 test ajouté.

## 6. Décision

**P6 = `PASS_THIRD_DOMAIN_STABILIZATION` — transfert toujours `NOT
DEMONSTRATED`, gain de stabilité statistique confirmé sur l'estimation
combinée.**

- M1/M6 inchangés.
- M7 exclu.
- Aucune revendication de transfert sémantique — le contraire est
  explicitement vérifié (100 % `BASIS_GLOBAL_PRIOR`).
- E20-D reste `OPEN`, sans lien avec ce chantier.
