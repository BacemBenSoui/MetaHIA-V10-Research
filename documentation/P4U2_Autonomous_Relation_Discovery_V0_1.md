# MetaHIA V10 — P4-U.2 : cadrage (découverte autonome de relations INCONNUES) — aucun code, aucun protocole verrouillé

> **SUPERSEDED (2026-09-23).** Une revue méthodologique du porteur du
> projet a identifié une faille de non-identifiabilité dans le cadrage
> ci-dessous (Sec. 4 : « comparer des arêtes après avoir ignoré leur
> opérateur » collapse naïvement toutes les relations binaires
> ensemble). Remplacé intégralement par
> `documentation/P4U2_Autonomous_Relation_Discovery_V0_2.md`. Ce
> document reste l'historique exact de la revue initiale (inventaire
> réutilisable toujours valide) — non implémentable tel quel au-delà de
> son propre inventaire (Sec. 3).

## 0. Statut

```text
P4-U.2 = OPEN_RESEARCH, CADRAGE UNIQUEMENT
scope  = AUTONOMOUS DISCOVERY OF UNKNOWN RELATIONS
         (jamais raccourci en « unsupervised discovery », même règle
          de nommage que P4-U.1 — Sec. 17 de sa v0.3)
```

Ce document n'écrit aucun protocole verrouillé et aucun code. Il fait
exactement ce que P4-U.1 avait lui-même fait avant son propre protocole
v0.1 : une revue directe de ce qui existe déjà dans ce dépôt (K3
research kernel line, zéro couplage avec le dépôt de production),
suivie d'un cadrage proposé, à valider ou à corriger par le porteur du
projet avant tout protocole v0.1 formel — même discipline « protocole
avant implémentation », appliquée ici un cran plus tôt.

Déclencheur : la clôture du gate de validation tierce P4-U.1
(`documentation/P4U1_Unsupervised_Compositional_Pattern_Discovery_V0_3.md`
Sec. 22, 2026-09-23) — chaque document P4-U.1, depuis sa toute première
version, avait explicitement différé P4-U.2 « à définir seulement après
avoir vu les résultats réels de P4-U.1 ». C'est fait ; ce document
commence ce cadrage, sans présumer qu'il doive aboutir à une
implémentation immédiate.

## 1. Distinction avec ce qui existe déjà — pourquoi P4-U.2 est réellement différent

```text
P4-T    : induction de transformation à partir de COUPLES
          (source, cible) FOURNIS à l'entraînement — jamais de
          découverte de l'existence même d'une relation.

P4-U.1  : découverte non supervisée de COMPOSITIONS de relations
          DÉJÀ ÉTIQUETÉES (ex. MERE_DE puis TRAVAILLE_DANS) — le
          graphe est déjà « nommé », seule la combinaison est
          découverte.

P4-U.2  : proposer qu'un GROUPE d'arêtes, dont l'opérateur (la
          référence opaque qui joue le rôle d'étiquette de relation)
          n'est PAS déjà partagé de façon exploitable, instancie
          malgré tout UNE SEULE relation sous-jacente non encore
          nommée — puis la réifier comme candidat de relation
          nouvelle, avec un statut épistémique par défaut UNKNOWN,
          jamais auto-affirmé.
```

C'est la distinction que P4-T lui-même pose depuis toujours
(`STRUCTURAL_TRANSFORMATION_INDUCTION` vs
`AUTONOMOUS_DISCOVERY_GENERAL`, E20-D resté `OPEN`), et que P4-U.1 a
explicitement refusé de revendiquer.

## 2. Ce que « découvrir une relation inconnue » signifie ici, précisément

Revue directe du modèle K3 avant toute proposition (confirmée par
lecture directe de `kernel2.py`, pas supposée) :

- Un `GraphEdge`/une `OBSERVATION` porte un `operator` **opaque** —
  typiquement un `NodeRef` (`kernel2.py:1410-1425`, `1552-1573`).
- `reference_equal` compare deux `NodeRef` **uniquement par
  `ref_id`** (`kernel2.py:179-190`). `structural_equal`, pour deux
  `NodeRef`, **retombe sur `reference_equal`** (`kernel2.py:252-253`)
  — jamais de comparaison « structurellement similaire mais
  référence différente ».
- Conséquence directe, vérifiée : **aucune fonction de kernel2.py ne
  peut aujourd'hui décider que deux arêtes portant des `NodeRef`
  d'opérateur DIFFÉRENTS instancient « la même relation »** — ni par
  égalité de référence, ni par égalité structurelle. `group_by_skeleton`
  de P4-U.1 (`p4u1_unsupervised_pattern_discovery_v0_1.py:61-68`)
  regroupe lui aussi par `ref_id` exact — un regroupement par
  étiquette EXACTE, jamais par similarité.

**C'est précisément ce vide que P4-U.2 doit combler** — pas
« découvrir une composition » (déjà fait), mais « décider que
plusieurs arêtes à opérateurs distincts (ou dépourvus d'étiquette
stable) sont probablement des occurrences d'UNE relation commune, pas
encore nommée ».

## 3. Ce qui existe déjà et peut être réutilisé sans modification — inventaire direct (2026-09-23)

| Pièce existante | Fichier | État | Rôle possible pour P4-U.2 |
|---|---|---|---|
| `reify_path_link` | `kernel2.py:2146-2155` | vivant, mais 0 appelant hors `m3_recursive_structural_closure_v0_1.py` | réifie UN chemin découvert en objet référencé « encore sémantiquement anonyme » — la brique de base pour transformer une composition candidate en objet manipulable |
| `materialize_reified_link` / `reinject_reified_links` | `kernel2.py:1599-1683` | idem | réinjecte un lien réifié comme arête ordinaire, réutilisable dans un nouveau `discover_paths()` |
| `Hypothesis.status` | `kernel2.py:1272-1296` | vivant | `UNKNOWN` par défaut sauf preuve `supporting_ids`/`contradicting_ids` — **contrat épistémique déjà existant, à réutiliser tel quel**, jamais à réinventer |
| `ref_jaccard` / `structural_similarity` | `e20d_rationalization_v0_1.py:39-81` | **vivant** (appelé par `p4t_structural_transformation_induction_v0_1.py:75,652`) | seul moteur de similarité réel du dépôt — Jaccard sur les ensembles de `NodeRef` opaques recueillis récursivement ; conçu aujourd'hui pour une comparaison UN-candidat-contre-un-pool, pas un regroupement multi-arêtes |
| `e20d_operation_synthesis_v0_1.py` | dossier racine | **mort** (0 appelant hors ses propres tests) | contrat `IDENTIFIED_EXISTING` / `CREATED_NEW` / `AMBIGUOUS` — la forme exacte de décision qu'il faudrait UNE FOIS un candidat de relation regroupé ; réactivation envisageable mais **jamais silencieuse** (voir Sec. 7) |
| `m3_recursive_structural_closure_v0_1.py:13` | dossier racine | vivant | seul énoncé de principe déjà écrit dans CE dépôt proche de « une dérivation ne peut pas être sa propre preuve » : *« DERIVED structures are never treated as epistemic evidence »* — à ériger en contrainte non négociable de tout protocole P4-U.2 |

**Les 4 autres fichiers `e20d_*` morts** (`operator_relation`,
`operator_behavior`, `property_discovery`, `emergent_structure`) ont
été relus directement : tous opèrent sur des opérateurs **déjà
distincts et déjà identifiés** (ils relient ou caractérisent des
`NodeRef` connus), jamais sur un regroupement d'arêtes à opérateurs
non partagés. **Aucun n'est le chaînon manquant** — confirmé par
lecture directe, pas supposé par leur nom.

## 4. Le vide réel à combler — une seule pièce manquante, pas plusieurs

Une seule capacité nouvelle est requise, et une seule : **regrouper un
ensemble d'arêtes structurellement similaires malgré des `NodeRef`
d'opérateur distincts**, avant même de parler de composition ou de
réification. Tout le reste (réification, statut épistémique par
défaut, décision identifié-vs-nouveau) existe déjà ou a un contrat
déjà écrit (mort, mais réutilisable après décision explicite).

Cette pièce manquante ressemble structurellement à
`group_by_skeleton` de P4-U.1, mais remplace son critère d'égalité
EXACTE (`op.ref_id`) par un critère de similarité (a priori
`structural_similarity`/`ref_jaccard`, déjà vivants, appliqués non
plus à UN candidat contre un pool mais à une clusterisation par
paires sur l'ensemble des arêtes).

## 5. Squelette d'architecture proposé (à valider, pas à coder)

```text
G (graphe, arêtes à opérateurs NON tous partagés/exploitables)
        │
   Sélection du pool de candidats
   (ex. : arêtes dont l'opérateur n'apparaît qu'une fois — jamais
    republié — donc jamais regroupable par group_by_skeleton)
        │
   NOUVEAU : clustering par similarité structurelle
   (ref_jaccard / structural_similarity, e20d_rationalization_v0_1.py,
    INCHANGÉ -- seule la boucle d'agrégation multi-paires est nouvelle)
        │
   Chaque cluster retenu -> reify_path_link (kernel2.py, INCHANGÉ)
   -> candidat de relation, encore « sémantiquement anonyme »
        │
   Contrôle négatif -- OBLIGATOIRE, à spécifier avant tout benchmark
   (un cluster de similarité ne doit jamais être accepté sans preuve
    qu'il dépasse un regroupement de hasard -- même discipline que le
    modèle nul de Gate B en P4-U.1, probablement plus stricte encore
    ici, voir Sec. 6)
        │
   IDENTIFIED_EXISTING / CREATED_NEW / AMBIGUOUS
   (contrat de e20d_operation_synthesis_v0_1.py -- réactivation
    délibérée à décider explicitement, jamais automatique)
        │
   Hypothesis.status = UNKNOWN par défaut (kernel2.py, INCHANGÉ)
   -- jamais SUPPORTED sans preuve indépendante du regroupement
      lui-même (principe de m3_recursive_structural_closure_v0_1.py:13)
```

## 6. Risque méthodologique central — plus sévère qu'en P4-U.1

P4-U.1 devait distinguer « découvert » de « simplement fréquent »
(Gate B, modèle nul, correction multi-comparaisons). P4-U.2 doit
distinguer un degré supplémentaire de risque : **une similarité
structurelle mesurée (Jaccard sur des références opaques) peut être
élevée par pur hasard combinatoire**, surtout si le pool de candidats
est grand — le même type de piège que le modèle nul de Gate B, mais
appliqué à une statistique de PAIRE (similarité), pas à un COMPTE
(support). Un protocole v0.1 pour P4-U.2 devra donc définir, avant
tout code :

1. un modèle nul spécifique à la similarité (quelle distribution de
   `ref_jaccard`/`structural_similarity` obtient-on entre arêtes
   authentiquement sans relation commune ?) ;
2. une correction pour comparaisons multiples adaptée au nombre de
   PAIRES considérées (`O(n²)` sur le pool de candidats, pas `O(n)`
   comme pour les squelettes de P4-U.1 — un risque de faux positifs
   structurellement plus grand, à quantifier avant tout seuil) ;
3. le même type de trio U1/U2/U3 (regroupement réel, regroupement
   accidentel présent seulement en train, contrôle nul pur) — mais
   conçu pour la clusterisation par similarité, pas pour un squelette
   de composition.

**Ce point n'est pas résolu ici.** Il définit la charge de preuve
qu'un futur protocole v0.1 devra remplir avant tout benchmark
verrouillé — exactement le rôle qu'avait joué la revue méthodologique
du porteur du projet avant l'écriture de P4-U.1 v0.2.

## 7. Décisions déjà prises, à ne pas rouvrir silencieusement

- **`kernel2.py` reste non modifié** — même règle que pour tout le
  reste du projet ; le clustering par similarité est un nouveau
  module, jamais une modification de `reference_equal`/
  `structural_equal`.
- **Aucune réactivation silencieuse des fichiers `e20d_*` morts** —
  si `e20d_operation_synthesis_v0_1.py` est effectivement réutilisé
  pour l'étape IDENTIFIED/CREATED/AMBIGUOUS, ce sera une décision
  explicite, documentée ici même, jamais un import discret.
- **Aucun dictionnaire sémantique, aucun nom de relation deviné** — la
  relation proposée reste, comme en P4-U.1, un objet référencé
  « anonyme » (Sec. 3) ; nommer une relation découverte n'est pas dans
  le périmètre de P4-U.2 (ni de ce dépôt en général).
- **Statut épistémique** : toute relation proposée par P4-U.2 est
  `UNKNOWN` par défaut (`Hypothesis.status`, inchangé) — jamais
  `SUPPORTED` du seul fait d'avoir été découverte, conformément au
  principe déjà écrit dans `m3_recursive_structural_closure_v0_1.py:13`.

## 8. Hors périmètre explicite pour ce premier cadrage

- Où proviennent, dans un premier benchmark, les arêtes à opérateur
  « non exploitable » (masquage délibéré d'étiquettes existantes ?
  génération d'observations à opérateur unique par construction ?
  autre ?) — **question ouverte, Sec. 9, point A**.
- L'intégration avec M7 (proposition de faits par LLM) — volontairement
  hors sujet : P4-U.2 reste, comme tout le reste de la lignée K3, sans
  dépendance sémantique/LLM à ce stade.
- Toute extension au-delà d'un premier increment « regrouper, puis
  décider identifié-vs-nouveau » — l'boucle complète de
  `m3_recursive_structural_closure_v0_1.py` (réinjection récursive et
  ré-exploration) reste un sujet distinct, à ne considérer qu'après un
  premier increment validé.

## 9. Questions ouvertes nécessitant une décision explicite du porteur du projet, avant tout protocole v0.1

**A. Comment simuler « relation inconnue » dans le premier corpus ?**
Trois options envisagées, aucune tranchée ici :
   1. Masquer délibérément l'étiquette de certaines arêtes d'un corpus
      par ailleurs déjà utilisé (ex. réutiliser la structure des
      corpus P4-U.1, mais retirer l'identité partagée de l'opérateur
      pour un sous-ensemble d'arêtes) — la simulation la plus fidèle à
      l'idée « on ne sait pas encore que c'est la même relation ».
   2. Construire un corpus où CHAQUE arête porte un opérateur UNIQUE
      (jamais republié) — plus réaliste d'un flux d'observations brut,
      mais plus difficile à concevoir de façon contrôlée pour un
      premier test.
   3. Une autre source, à proposer.

**B. Portée du premier increment** : se limiter strictement à
« regrouper un pool de candidats déjà réduit » (déférant la question
« d'où vient ce pool » à une étape ultérieure), ou inclure dès le
premier protocole une étape de sélection du pool candidat elle-même ?

**C. Réutilisation de `e20d_operation_synthesis_v0_1.py`** : réactiver
son contrat IDENTIFIED_EXISTING/CREATED_NEW/AMBIGUOUS tel quel pour
l'étape finale, ou écrire un mécanisme minimal dédié à P4-U.2 sans
toucher à ce fichier mort (cohérent avec la discipline « ne rien
réactiver sans raison démontrée », mais au prix d'une possible
duplication) ?

## 10. Ce que ce document ne fait pas

Aucun protocole verrouillé, aucun seuil numérique, aucun code, aucun
cas de test. Il propose un cadrage et pose les questions nécessaires à
un protocole v0.1 formel — même étape que celle qu'avait traversée
P4-U.1 avant l'écriture de sa propre v0.1, avant toute revue du
porteur du projet.
