# MetaHIA — Organisation du code source v0.1

## Racine
- `kernel2.py` — baseline M1, gelée.
- `operator_space_v0_1.py` — espace structurel d’opérateurs.
- `e20d_*.py` — sous-capacités expérimentales E20-D.
- `m3_recursive_structural_closure_v0_1.py` — fermeture récursive.
- `m4_cold_start_evidence_v0_1.py` — acquisition d’évidence.
- `m5_metacognitive_dynamic_controller_v0_1.py` — politique dynamique.
- `engine.py` — façade d’orchestration sur entrée déjà structurée.
- `main.py` — point d’entrée CLI de démonstration.

## Ce qui est volontairement exclu
- sauvegardes `pre_*`, `latest_*` et snapshots historiques du kernel ;
- `__pycache__` et fichiers de cache ;
- résultats JSON générés par exécution de tests, lorsqu’ils ne sont pas requis au runtime ;
- intégration LLM live et parseur texte non implémentés.

## Reproduction
```bash
python -m pytest -q
python main.py --demo
```

Le package ne nécessite aucune dépendance Python tierce pour le cœur fourni ; `pytest` est requis pour les tests.
