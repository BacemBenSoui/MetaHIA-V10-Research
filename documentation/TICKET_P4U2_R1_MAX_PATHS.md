# Ticket d'ingénierie P4-U.2-R1 — troncature de l'énumération de chemins (`MAX_PATHS`)

Nature : défaut de production déterministe. **Aucune campagne expérimentale associée**
(décision du porteur du projet, 2026-09-24). Hors de la branche C9.

## Défaut
`edge_signature()` (`p4u2_autonomous_relation_discovery_v0_1.py`) appelle
`discover_paths(graph, start=edge.source, max_paths=MAX_PATHS=1000)`, puis filtre les
chemins dont le premier pas est l'arête. Quand la source dépasse 1000 chemins
(profondeur ≤ 3, parcours inverse autorisé), l'énumération s'arrête selon l'ordre
d'insertion des arêtes. La signature d'une arête dépend alors de sa position, pas de la
structure. Les arêtes énumérées trop tard reçoivent `(0,0,0,∅)`, et
`group_by_signature()` les réunit en un bucket artificiel.

## Preuve (via `compute_signatures` de production, sur 20 graphes Zipf s = 1, 60 nœuds / 100 arêtes)
- 101 sources tronquées ;
- 819/2000 arêtes (41 %) issues d'une source tronquée ;
- 236 arêtes reçoivent `(0,0,0,∅)`, et toutes ont une source tronquée (assertion) ;
- aucune troncature sur les graphes uniformes 60/100 ni plus clairsemés.

## Critères d'acceptation (pour la future implémentation)
1. Signature **indépendante de l'ordre** : test de régression qui permute l'ordre des
   observations d'un graphe avec un nœud à forte connectivité (≥ 1000 chemins) et exige
   des signatures identiques arête par arête.
2. Option A, mode exhaustif (sans limite ou avec une limite très haute), avec un
   garde-fou de coût explicite. L'énumération à profondeur 3 croît comme degré³ : il faut
   un échec explicite et fermé, jamais une troncature silencieuse.
3. Option B, limite conservée, mais tout dépassement produit un marqueur explicite
   (par exemple `Signature.truncated = True`), exclu de `group_by_signature()` et
   compté ; jamais une signature partielle présentée comme valide.
4. Non-régression : les 7 tests existants de `tests/test_p4u2_autonomous_relation_discovery_v0_1.py`
   restent verts, et les signatures sont identiques bit à bit sur tout graphe sans
   troncature.
Le choix entre A et B est une décision de conception, non prise ici.
