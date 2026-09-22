# MetaHIA V10 — P4-T : induction de transformation structurelle (Gates A-G) v0.1

Date : 2026-09-21
Statut : **`STRONG_MICROSTRUCTURAL_CANDIDATE` — E20-D reste `OPEN`**

## 1. Contexte et origine

Ce chantier remplace **P4-R** (transfert inter-domaines avec endpoint cible,
`documentation/P4R_Non_Circular_Structural_Transfer_V0_2.md`) comme voie
principale vers E20-D, sur la base d'une revue externe qui a audité
`e20d_protocol.py` — un fichier **déjà présent dans ce dépôt** depuis le
commit `92d396d`, antérieur à ce document. Cette revue proposait un
protocole formel en sept portes (A-G) ; ce document l'implémente et en
vérifie chaque affirmation par exécution directe, jamais par lecture seule
du récit.

**Vérification indépendante des affirmations de la revue**, avant toute
adoption :

- Suite E20-D existante rejouée : **99 tests, 0 échec** (périmètre
  légèrement plus large que les « 69 tests » cités, probablement un
  sous-ensemble de fichiers différent — aucune contradiction).
- `tests/test_e20d_v03_recursive_transform.py::test_recursive_transformation_replays_on_unseen_rows`
  inspecté ligne à ligne : le replay utilise des entités fraîches
  (`fresh_src1/2/3`, `f{i}x`/`f{i}y`) totalement disjointes des entités
  d'entraînement — confirmé non circulaire, à la différence du bug trouvé
  dans P4.4/P4.5 (`documentation/P4_Transfer_Review_and_Rejection_2026-09-19.md`).
- Sondes adversariales exécutées indépendamment (pas celles de la revue) :
  cible constante → rejetée ; many-to-one → rejeté. Confirmées.

## 2. Ce que `e20d_protocol.py` faisait déjà (réutilisé, non modifié)

- `REFERENCE_EQUALITY` : même référence NodeRef en source et cible sur
  toutes les lignes.
- `COMPARE_PERMUTATION` : réordonnancement de colonnes découvert via
  `kernel2.compare_candidates()`.
- `COMPARE_RECURSIVE` : permutation imbriquée découverte récursivement.
- Échec fermé sur ambiguïté (`compare_candidates()` ne devine jamais entre
  plusieurs permutations également valides).

`p4t_structural_transformation_induction_v0_1.py` **ne modifie ni
`e20d_protocol.py` ni `kernel2.py`** — il délègue à `discover_cross_slot_candidates`/
`replay_candidate` pour ces trois familles.

## 3. La limite réelle trouvée, et la capacité réellement nouvelle ajoutée ici

`kernel2.compare()`/`compare_candidates()` exigent
`len(a.children) == len(b.children)` — **la comparaison générique ne peut
donc jamais exprimer une transformation qui change l'arité** entre source
et cible (projection, duplication). C'est exactement la limite identifiée
par la revue (« il ne sait pas identifier génériquement `f(x,y)=x`,
`f(x)=(x,x)` »).

`discover_selection_mapping()` (nouveau, dans ce fichier uniquement) ajoute
cette capacité manquante par un mécanisme unique et général : pour chaque
position cible `j`, il cherche la position source `i` telle que
`reference_equal(cible[j], source[i])` est vraie sur **toutes** les lignes.

- **Une seule position source correspond** → résolu, `sigma[j] = i`.
- **Zéro position ne correspond** → rejeté (pas deviné).
- **Plusieurs positions correspondent également** → ambigu (pas deviné).

Ce mécanisme unifie, sans code dupliqué :

| Famille | Condition sur sigma |
|---|---|
| Permutation | bijective, arité égale |
| Projection | injective, arité cible < arité source |
| Duplication | non injective (une position source réutilisée) |

## 4. Portes A-D : pipeline complet, vérifié par exécution

```text
Gate A  discover(train_rows)          -- train uniquement
Gate B  freeze(candidate)             -- opaque, aucune référence aux Node d'entraînement
Gate C  blind_replay(frozen, source)  -- source seule, cible jamais consultée
Gate D  verify(predicted, truth)      -- seulement après la prédiction
```

Vérifié réellement (pas simulé) pour **quatre familles**, chacune avec des
entités totalement fraîches côté holdout :

- `COMPARE_RECURSIVE` (réutilisé) : `test_discover_reuses_e20d_protocol_for_recursive_permutation_and_replays_blind_on_fresh_entities`.
- `PROJECTION` : `test_projection_is_discovered_and_replays_blind_on_fresh_entities`.
- `DUPLICATION` : `test_duplication_is_discovered_and_replays_blind_on_fresh_entities`.
- **Composition de deux transformations indépendamment gelées** :
  `test_two_independently_discovered_mappings_compose_and_replay_blind` —
  `compose_frozen(outer, inner)` chaîne deux `FrozenTransformation`
  séparées (`sigma_composé[j] = inner.sigma[outer.sigma[j]]`), sans
  ré-exécuter la découverte sur des données pré-composées. C'est la lecture
  la plus littérale de « composition » proposée par la revue.

## 5. Porte E : anti-triche, vérifiée par sondes adversariales

Quatre propriétés testées directement dans
`tests/test_p4t_structural_transformation_induction_v0_1.py`, chacune sur
des données construites pour ce fichier (pas réutilisées d'ailleurs) :

1. **Ambiguïté exposée, pas devinée** : deux positions source partageant la
   même référence sur toutes les lignes → `OUTCOME_AMBIGUOUS`.
2. **Contradiction rejetée** : une cible qui correspond à la position 0 sur
   deux lignes mais à la position 2 sur la troisième → `OUTCOME_REJECTED`.
3. **Cible constante rejetée** : une référence indépendante, jamais issue
   de la source → `OUTCOME_REJECTED`.
4. **Cible non structurelle rejetée** : une référence qui varie à chaque
   ligne mais n'est jamais égale par référence à aucune position source →
   `OUTCOME_REJECTED`. C'est la garantie que le mécanisme ne « hallucine »
   jamais une fonction sémantique arbitraire.

## 6. Porte B, vérifiée : aucune fuite de provenance d'entraînement

`test_frozen_transformation_does_not_leak_training_node_refs` inspecte
chaque champ de `FrozenTransformation` (hors le hash SHA-256 lui-même,
exclu du test car un hash de 64 caractères hexadécimaux peut contenir
n'importe quelle sous-chaîne courte par coïncidence — ceci a été trouvé et
corrigé comme un faux positif du test lui-même, pas du mécanisme, pendant
l'écriture de ce document) et confirme qu'aucun identifiant NodeRef
d'entraînement n'y apparaît : `sigma` ne contient que des entiers de
position.

### 6.1 Durcissement P4-T.1 (2026-09-21, revue externe, deux bugs réels confirmés par exécution)

Une revue externe a identifié deux défauts réels dans la branche
PERMUTATION/RECURSIVE de `freeze()` (celle testée en Sec. 6 ci-dessus ne
couvrait que la branche SELECTION_MAPPING) — **confirmés par exécution
directe avant correction**, pas acceptés sur récit :

- **Fuite de provenance réelle** : `freeze()` stockait le `CrossSlotCandidate`
  brut, dont les champs `evidence_rows`/`source_target_provenance`
  contiennent littéralement les identifiants de lignes d'entraînement
  (`"row1"`, `"row2"`, ...). Pire : même le `Node` PATTERN produit par
  `e20d_protocol.py` embarque ces identifiants dans ses propres champs
  `node_id`/`provenance` (ex. `"pattern::column::1::row1::row2::row3::..."`).
  Vérifié : `"row1" in repr(frozen)` → `True` avant correction.
- **Digest trop faible** : le hash ne dépendait que de `(family,
  relation_kind)` — constant pour toute une famille. Deux permutations
  structurellement différentes de la même famille produisaient le **même**
  digest. Vérifié par construction de deux permutations différentes :
  digests identiques avant correction.

**Correction** : `freeze()` reconstruit désormais une copie anonymisée du
`Node` PATTERN (`_anonymize_pattern`, remplace `node_id`/`provenance` par
des labels canoniques — `apply()`/le replay n'utilisent jamais ces champs
pour leur logique, seulement `kind`/`children`) et calcule le digest via
`kernel2.structural_signature()`, déjà utilisé ailleurs dans ce projet
(`_rule_signature` de M6) pour la même fonction : un fingerprint canonique
et sans référence d'entraînement. `blind_replay()` applique directement
cette copie anonymisée via `kernel2.apply()`, sans plus jamais appeler
`replay_candidate()`.

Deux nouveaux tests de régression permanents :
`test_frozen_recursive_transformation_does_not_leak_training_row_ids`,
`test_structural_digest_distinguishes_two_different_permutations_of_the_same_family`
— tous deux exécutés et vérifiés après correction (avant, ils auraient
échoué, confirmant que le bug était réel et pas seulement théorique).

## 7. Porte G : mesure de coût, honnêtement bornée

`run_costed_pipeline()` mesure réellement (jamais estimé) : temps de
découverte, nombre de lignes d'entraînement, nombre de paires de positions
essayées, temps de replay, nombre de lignes de holdout, temps de
vérification — voir `P4TCostReport`.

**Ce que cette porte ne fait PAS encore, déclaré explicitement** : ces
chiffres ne sont pas encore branchés sur `e20d_cognitive_control_v0_1.py`
(E20-D.19, `score_candidate`/ROI). Cette fonction est couplée à
`PathCandidate`/`PathRecord` (issus de l'exploration de chemins), pas à un
candidat de transformation — les y connecter exigerait un adaptateur
supplémentaire, non construit ici. La revue elle-même présentait ceci comme
un objectif final (« pour pouvoir finalement connecter »), pas comme déjà
fait ; ce document ne le revendique pas non plus.

## 8. Ce qui N'EST PAS démontré — lecture honnête, pas optimiste

- **Découverte non supervisée générale** : le mécanisme reçoit des paires
  `(source, cible)` appariées à l'entraînement. C'est une **induction de
  transformation à partir d'exemples appariés**, pas une découverte de
  relation dans un graphe sans structure cible — exactement la distinction
  posée par la revue (`STRUCTURAL_TRANSFORMATION_INDUCTION`, pas
  `AUTONOMOUS_DISCOVERY_GENERAL`).
- **Holdout scientifique formel avec corpus verrouillé séparément** : les
  tests de ce fichier construisent leurs propres données synthétiques dans
  le même fichier que l'assertion — c'est une preuve de mécanisme
  unitaire, pas un protocole avec un corpus gelé et remis par un tiers
  avant exécution. Aucun paquet de validation tierce n'est préparé ici.
- **Langage général de fonctions structurelles** : seules les familles
  RÉFÉRENCE-ÉGALITÉ / PERMUTATION / RÉCURSIVE / SÉLECTION (projection,
  duplication, composition de sélections) sont couvertes. Une fonction
  authentiquement sémantique (ex. calcul arithmétique sur des valeurs
  opaques) reste, par construction, rejetée — vérifié, pas supposé.
- **Sélection automatique entre plusieurs hypothèses candidates** : quand
  `discover_cross_slot_candidates()` renvoie plusieurs paires
  source/cible candidates à des positions différentes, ce module ne
  choisit pas laquelle retenir — l'appelant doit préciser
  `source_position`/`target_position`. Il n'y a pas encore d'étape
  « hypothèses → sélection/rationalisation → transformation retenue »
  proposée par la revue (Sec. 7 du rapport).

### 8.1 P4-T.3 — sélection d'hypothèses (2026-09-21, FAIT)

`discover_all_hypotheses()` énumère désormais tous les couples
`(source_position, target_position)` ordonnés et collecte chaque candidat
non rejeté/non ambigu comme une hypothèse structurelle distincte — la
découverte ne décide toujours pas laquelle retenir. `select_hypothesis()`
classe les hypothèses par **complexité structurelle uniquement** (rasoir
d'Occam, aucun dictionnaire sémantique) :

```text
REFERENCE_EQUALITY (rang 0) < COMPARE_PERMUTATION (rang 1)
  < SELECTION_MAPPING (rang 2) < COMPARE_RECURSIVE (rang 3)
```

et retient l'unique hypothèse de rang minimal — une égalité au rang
minimal est exposée comme `AMBIGUOUS_SELECTION`, jamais choisie
arbitrairement.

**Constat vérifié par exécution, pas supposé** : `REFERENCE_EQUALITY` et
`COMPARE_PERMUTATION` sont des relations **intrinsèquement non
orientées** — si la colonne *i* égale toujours la colonne *j* par
référence, `(i,j)` et `(j,i)` sont tous deux des hypothèses valides. Ce
n'est pas un bug de ce module : c'est une propriété réelle de ces deux
familles, et `select_hypothesis()` l'expose honnêtement comme une
ambiguïté plutôt que de choisir une direction arbitraire. Vérifié par 4
constructions différentes avant d'écrire les tests correspondants (pas
après) : deux paires symétriques → ambigu ; une hypothèse `SELECTION_MAPPING`
unique → retenue ; une hypothèse de rang 2 en présence d'une alternative
de rang 3 (elle-même symétrique) → la rang 2 gagne, la symétrie du rang 3
n'entre jamais en jeu puisque seul le meilleur rang est comparé ; aucune
hypothèse découvrable → `NO_HYPOTHESES`.

**Corroboration optionnelle via E20-D.6** (`rationalize_retained_hypothesis`) :
réutilise `e20d_rationalization_v0_1.rationalize()` **sans aucune
modification**, en comparant le `pattern_ref` (déjà anonymisé par le
durcissement Sec. 6.1) de l'hypothèse retenue à des transformations déjà
gelées précédemment. Deux transformations récursives découvertes
indépendamment à partir de données totalement disjointes (aucun
identifiant partagé) et structurellement identiques donnent
`similarity=1.0`, `SUPPORTED_HISTORICAL` — vérifié par exécution directe,
pas suggéré par construction du test. **Frontière de portée explicite,
pas une lacune cachée** : pour `SELECTION_MAPPING`, `sigma` est un simple
tuple d'entiers sans `RefObject` à comparer — la fonction renvoie `None`
plutôt que de forcer une comparaison qui ne correspond pas au mécanisme
d'E20-D.6.

8 nouveaux tests (23 au total sur P4-T) : 1 énumération/symétrie, 4
sélection (ambiguïté, unicité, priorité de rang, aucune hypothèse), 3
rationalisation (correspondance exacte, frontière `SELECTION_MAPPING`,
absence d'historique).

## 9. Décision

**P4-T = `STRONG_MICROSTRUCTURAL_CANDIDATE`.** Remplace P4-R comme voie
principale vers E20-D. **E20-D reste `OPEN`** — ce document ne le
prétend pas fermer, il ferme seulement la question de savoir si le
mécanisme de génération d'une nouvelle structure à partir d'une
transformation découverte est réel et non circulaire (il l'est,
maintenant vérifié pour quatre familles et leur composition, et gelé sans
fuite de provenance depuis le durcissement Sec. 6.1).

Aucune modification de `kernel2.py`/`e20d_protocol.py` : architecture
compatible avec la trajectoire M1 v0.4 (« M1 reste minimal ; la richesse
vit dans les objets structurels dérivés »).

### 9.1 Matrice de clôture E20-D (mise à jour après durcissement)

| Critère E20-D | Ce que P4-T apporte | Ce qui manque |
|---|---|---|
| Relation non fournie | 🟠 partiel | découverte sans paire cible explicitement donnée |
| Holdout aveugle | 🟢 mécanisme + verrouillage structurel auto-administré (P4-T.2, `documentation/P4T2_Locked_Benchmark_V0_1.md`) | verrouillage par un tiers externe (aucun disponible dans cette session) |
| Relation → opération → structure | 🟢 fort pour transformations structurelles | généralisation au-delà du langage actuel (projection/duplication/composition) |
| Coût/ROI | 🟠 mesure réelle (Porte G) | intégration à `e20d_cognitive_control_v0_1.py` (E20-D.19) |
| Non-circularité | 🟢 forte | validation tierce formelle |
| Provenance (gel) | 🟢 maintenant réellement vérifié (Sec. 6.1) | — |
| Sélection d'hypothèses | 🟢 FAIT (Sec. 8.1) — rasoir d'Occam + corroboration E20-D.6 optionnelle | sélection encore purement structurelle (aucune pondération par coût/ROI, en attente de P4-T.6) |

### 9.2 Séquence de suite proposée (P4-T.1 → P4-T.7)

Remplace l'ancienne liste plate d'options ouvertes par une progression
explicite :

1. **P4-T.1 — durcissement du gel.** **FAIT (2026-09-21, Sec. 6.1)** :
   provenance d'entraînement supprimée de `FrozenTransformation`, digest
   canonique via `structural_signature()`, 2 tests de régression permanents.
2. **P4-T.2 — vrai benchmark séparé.** **FAIT (2026-09-21)** : trois
   fichiers distincts (cas/train+holdout-source, témoin, exécuteur),
   verrouillage vérifié statiquement (texte + AST) et dynamiquement
   (`sys.modules`), 7 cas couvrant toutes les familles + les deux issues
   fermées, 7/7 correspondent au témoin. Deux bugs réels trouvés et
   corrigés pendant la construction (comparaison par `repr()` au lieu de
   `structural_equal`, `frozen_id` non déterministe). Protocole
   **auto-administré**, pas verrouillé par un tiers — voir
   `documentation/P4T2_Locked_Benchmark_V0_1.md` pour la portée exacte.
3. **P4-T.3 — sélection d'hypothèses.** **FAIT (2026-09-21, Sec. 8.1)** :
   `discover_all_hypotheses()`/`select_hypothesis()` (rasoir d'Occam,
   ambiguïté exposée sur égalité de rang) + corroboration optionnelle via
   E20-D.6 réutilisé sans modification. 8 tests de régression.
4. **P4-T.4 — nouvelles familles de transformation** au-delà de
   permutation/récursif/projection/duplication/composition — pas encore
   fait.
5. **P4-T.5 — structure émergente** (opération figée appliquée à de
   nouveaux opérandes, structure absente du graphe, vérification
   indépendante) — recouvre partiellement E20-D.17, à relier explicitement.
6. **P4-T.6 — ROI** (adaptateur vers `e20d_cognitive_control_v0_1.py`,
   E20-D.19) — pas encore fait.
7. **P4-T.7 — validation indépendante** (paquet tiers, comme M4-M7) — pas
   encore fait.

Aucune étape au-delà de P4-T.1 n'est urgente ; à décider explicitement
avant de commencer, comme pour chaque étape précédente de ce chantier.
P6/P7 (diversité de corpus M6) et JEV/Kev (M7) restent **explicitement
séparés** de cette trajectoire — ni preuve de clôture E20-D, ni substitut
à P4-T.2-P4-T.7.

## 10. Tests

`tests/test_p4t_structural_transformation_induction_v0_1.py` (23 tests,
après P4-T.1 et P4-T.3) : 2 réutilisation (permutation, récursif + replay
aveugle), 3 nouvelles familles (projection, duplication, composition)
chacune avec replay aveugle et vérification, 4 anti-triche, 4 gel (fuite
SELECTION_MAPPING, fuite RECURSIVE, digest canonique, refus sur
non-candidat), 2 coût, 1 énumération/symétrie, 4 sélection d'hypothèses
(ambiguïté, unicité, priorité de rang, aucune hypothèse), 3 rationalisation
E20-D.6 (correspondance exacte, frontière SELECTION_MAPPING, absence
d'historique). Tous exécutés réellement, aucun résultat inventé.
