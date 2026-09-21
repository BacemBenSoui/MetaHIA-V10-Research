# MetaHIA V10 — P7 : quatrième domaine indépendant (bibliothèque) v0.1

Date : 2026-09-21
Statut : **implémenté, vérifié par exécution réelle — confirme que le
transfert reste non démontré ; la tendance de stabilisation n'est PAS
monotone**

## 1. Objet

Après P6 (trois domaines : Famille, Organisation, Chaîne d'approvisionnement),
la question posée explicitement était : *le motif de stabilisation observé
en passant de deux à trois domaines (écart-type 0,107167 → 0,056129)
se poursuit-il avec un quatrième domaine ?* Réponse par exécution réelle,
pas par extrapolation.

## 2. Le quatrième domaine : bibliothèque

`corpus/library_facts_v0_1.json` — vocabulaire de relations disjoint des
trois autres domaines (`ECRIT_PAR`, `PUBLIE_CHEZ`, `SITUE_A`,
`APPARTIENT_A`), entités disjointes (livres, auteurs, éditeurs, villes,
collections).

Topologie **délibérément différente des trois précédentes**, pas un
renommage : 3 auteurs avec des nombres de livres inégaux (2/1/3), 2 éditeurs
servant des groupes d'auteurs de tailles différentes (2/1) — vérifié par
`tests/test_library_corpus_v0_1.py::test_library_topology_is_not_an_isomorphic_renaming_of_any_prior_domain`.

`m6_corpus_from_library_v0_1.py` réutilise exactement le mécanisme déjà
validé (séparation prédiction structurelle / vérification indépendante) —
seuls les fichiers de corpus et le préfixe `record_id` (`libraryv1::`)
changent.

Résultat réel (exécution directe) :

- 17 faits de découverte, 8 faits de preuve, 20 réclamations de vérification
  (15 accord, 5 `WRONG_ENDPOINT` délibéré) ;
- 17 motifs candidats considérés, 20 enregistrements réels, 7 exclus
  (comptabilité vérifiée honnête) ;
- diversité d'issue réelle : **15 `SUPPORTED`, 5 `CONTRADICTED`** — non
  dégénéré ;
- 10 règles distinctes, profondeurs {1, 2} ;
- split par règle (graine 0) : 12 train / 4 validation / 4 holdout, aucune
  fuite de règle ;
- **Brier holdout = 0,375**, ECE = 0,0.

## 3. La conclusion « transfert non démontré » reste inchangée

Même raison structurelle que P6 Sec. 3 : chaque domaine construit ses
`PathPattern` à partir de son propre vocabulaire de relations, donc deux
domaines ne peuvent jamais produire la même signature de règle.

Vérifié directement sur le holdout du jeu combiné à quatre domaines (graine
0) : **100 % des prédictions reposent sur `BASIS_GLOBAL_PRIOR`** —
exactement la même découverte transversale, maintenant reconfirmée une
troisième fois (deux, puis trois, puis quatre domaines).

## 4. Le motif de stabilisation N'EST PAS monotone — constat honnête

C'est le résultat le plus important de ce document, et il contredit
l'hypothèse implicite qui motivait la question.

### 4.1 Régression à graine fixe (graine 0)

| Domaine | Enregistrements | Règles | Holdout | Brier | ECE |
|---|---:|---:|---:|---:|---:|
| Famille | 26 | 20 | 5 | 0,48125 | 0,025 |
| Organisation | 24 | 12 | 4 | 0,6953125 | 0,3125 |
| Chaîne d'approvisionnement | 24 | 12 | 4 | 0,375 | 0,0 |
| Bibliothèque | 20 | 10 | 4 | 0,375 | 0,0 |
| **Combiné (4 domaines)** | 94 | 54 | 20 | **0,37540** | 0,01415 |

Round-trip JSON de l'interface v0.2 : `PASS` pour les cinq lignes, sans
aucune modification de `m1_m6_interface_v0_2.py`.

### 4.2 Probe multi-graines (10 graines, 0 à 9)

| Domaine | Brier moyen | écart-type population | min | max |
|---|---:|---:|---:|---:|
| Famille | 0,535278 | 0,103619 | 0,406250 | 0,764444 |
| Organisation | 0,471875 | 0,215410 | 0,125000 | 0,695313 |
| Chaîne d'approvisionnement | 0,488281 | 0,289405 | 0,281250 | 1,320313 |
| Bibliothèque | 0,504167 | 0,294893 | 0,125000 | 1,263889 |
| Combiné (2 domaines, P5 Sec.5) | 0,444565 | 0,107167 | 0,287774 | 0,680791 |
| Combiné (3 domaines, P6 Sec.4) | 0,440232 | **0,056129** | 0,355556 | 0,558207 |
| **Combiné (4 domaines)** | 0,418103 | **0,066963** | 0,326531 | 0,540263 |

**Constat honnête, vérifié par exécution (pas supposé)** : l'écart-type du
Brier combiné **remonte légèrement** en passant de trois à quatre domaines
(0,056129 → 0,066963), au lieu de continuer à descendre. Il reste bien
inférieur au chiffre à deux domaines (0,107167), mais la trajectoire n'est
**pas monotone** — trois domaines constituaient un minimum local sur cette
plage, pas le début d'une tendance strictement décroissante.

Le domaine Bibliothèque pris seul reste, comme les deux précédents domaines
ajoutés, plus instable individuellement (écart-type 0,294893, comparable à
la Chaîne d'approvisionnement 0,289405) que les deux premiers domaines —
cohérent avec le fait que chaque nouveau domaine testé jusqu'ici a un
holdout de seulement 2 à 4 enregistrements par graine, donc une variance
intrinsèquement élevée à ce stade.

**Interprétation, explicitement bornée** : ce résultat ne réfute ni ne
confirme une hypothèse plus fine (par exemple : la stabilisation pourrait
suivre une courbe non linéaire, ou dépendre de la composition relative des
issues `SUPPORTED`/`CONTRADICTED` de chaque nouveau domaine plutôt que de
son seul nombre). Aucune de ces hypothèses plus fines n'est testée ici —
seul le fait empirique (non-monotonie observée) est rapporté. La lecture
« plus de domaines pool = stabilisation systématique » que P6 aurait pu
suggérer par extrapolation est donc explicitement **infirmée** par ce
quatrième point de données.

## 5. Tests

- `tests/test_library_corpus_v0_1.py` (9 tests) : indépendance du domaine,
  non-isomorphisme de la topologie, diversité d'issue réelle, répétabilité,
  comptabilité honnête, absence de collision de préfixe `record_id`,
  présence réelle d'accords et de désaccords.
- `tests/test_p7_four_domain_regression_v0_1.py` (6 tests) : round-trip
  JSON pour les cinq lignes, non-régression des baselines Famille/
  Organisation/Chaîne déjà adoptées, baseline Bibliothèque, disjonction de
  règles du combiné, absence de dépendance M7.
- `tests/test_p7_four_domain_multiseed_v0_1.py` (4 tests) : sept tranches
  mesurées sur 10 graines chacune, non-régression des chiffres déjà
  documentés P5/P6, et **assertion explicite de la non-monotonie**
  (`three_std < four_std < two_std`) — pas juste observée en passant, mais
  gelée comme régression permanente vérifiée.
- CLI (`cli_preprod_v0_1.py`) étendue avec `--domain library` ; `--domain
  combined` évolue pour pool désormais les quatre domaines réels (74 → 94
  enregistrements) — documenté explicitement comme un comportement d'outil
  qui évolue avec le nombre de domaines connus, pas un résultat scientifique
  gelé. Le test CLI qui vérifiait auparavant les chiffres à trois domaines a
  été mis à jour vers les chiffres à quatre domaines, avec une note
  explicite dans le test lui-même expliquant pourquoi.

## 6. Décision

**P7 = `PASS_FOURTH_DOMAIN_NONMONOTONIC_STABILIZATION` — transfert toujours
`NOT DEMONSTRATED`, la tendance de stabilisation observée P5→P6 ne se
poursuit PAS de façon monotone à quatre domaines.**

- M1/M6 inchangés.
- M7 exclu.
- Aucune revendication de transfert sémantique — vérifiée absente (100 %
  `BASIS_GLOBAL_PRIOR`).
- E20-D reste `OPEN`, sans lien avec ce chantier.
- Recommandation explicite pour un futur cinquième domaine (si jamais
  entrepris) : ne pas présumer que l'écart-type continuera de baisser —
  cette hypothèse est maintenant explicitement infirmée par ce document.
