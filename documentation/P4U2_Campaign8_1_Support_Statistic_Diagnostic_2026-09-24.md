# P4-U.2 — Campagne 8.1 : calibration ciblée du support sous sélection complète (2026-09-24)

Exécute le protocole C8.1 pré-enregistré par le porteur du projet après
le rapport intermédiaire de la campagne 8 (`documentation/P4U2_Campaign8_CandidateGeneration_GateI_Interim_2026-09-24.md`,
commit `c8124a7`) : calibration resserrée, phase diagnostic seulement
(30-50 graines), de la statistique de **support** sous un **modèle nul
procédural complet avec correction de sélection globale** — jamais la
grille complète, jamais une correction du moteur sur la base d'un
résultat préliminaire. **Aucune modification de
`p4u2_autonomous_relation_discovery_v0_1.py`.**

```text
T = max_s |G_s|   -- taille du plus grand bucket produit par
                     group_by_signature(), comparée à la distribution
                     nulle de T lui-même (jamais aux distributions
                     individuelles des buckets) -- correction de
                     sélection globale, exigée explicitement
```

## 1. Protocole figé (repris exactement de la demande du porteur du projet)

```text
1. Production inchangée.
2. Null corrigé gelé : univers complet de nœuds (le bug de la campagne
   8 corrigé), mêmes contraintes de génération, même nombre d'arêtes.
3. Statistique : T = max_s |G_s|.
4. Par réplicat nul : graphe nul -> signatures -> group_by_signature ->
   maximum de support.
5. Comparaison de l'observé à la distribution nulle de T.
6. Puissance progressive : phase diagnostic (30-50 graines) avant toute
   confirmation à plus grande échelle.
```

## 2. Résultat — phase diagnostic, bruit pur (40 graines, N_null=50)

```text
percentiles (triés) :
4.0  5.0  6.0  6.0  8.0  9.0  19.0 24.0 25.0 26.0 27.0 29.0 31.0 31.0
31.0 33.0 35.0 38.0 41.0 57.0 58.0 58.0 59.0 61.0 61.0 65.0 67.0 69.0
80.0 80.0 80.0 83.0 83.0 84.0 86.0 87.0 91.0 91.0 95.0 99.0

moyenne = 50,5   -- proche de la valeur attendue (50) pour une
                    distribution de percentiles approximativement
                    uniforme sous une absence réelle de signal
FPR = 5,0 % (2/40)
IC de Wilson à 95 % = [1,4 % ; 16,5 %]
```

**La distribution des percentiles ressemble à une distribution
approximativement uniforme entre 0 et 100** — exactement ce qu'on
attend d'un test correctement calibré sous l'hypothèse nulle, pas une
concentration suspecte vers les valeurs hautes (contrairement à ce que
`Cohesion_B` aurait donné : 100,0 systématiquement). Le taux de faux
positifs (5,0 %) tombe exactement sur le niveau nominal, avec un
intervalle de confiance qui l'englobe confortablement.

**Ceci confirme directement la mise en garde statistique du porteur du
projet** sur les résultats à 10 graines de la campagne 8 (20 % et 10 %,
IC de Wilson [5,7-51,0 %] et [1,8-40,4 %], tous deux compatibles avec
5 %) : avec une résolution suffisante (40 graines, N_null=50), le signal
« au-dessus du nominal » ne se confirme PAS — c'était du bruit
d'échantillonnage à petite résolution, pas un défaut réel de l'Approche
A+B.

## 3. Résultat — phase diagnostic, signal injecté (25 graines, N_null=50)

Corpus : 15 chaînes à 2 sauts authentiques (signal réel), noyées dans un
fond de 80 arêtes aléatoires (60 nœuds).

```text
valeurs de T observées (triées) :
17 18 19 19 19 19 20 20 20 20 21 21 21 21 21 21 21 22 22 22 22 23 24 25 27

percentiles (triés) :
80.0 87.0 87.0 90.0 94.0 95.0 96.0 97.0 97.0 97.0 97.0 97.0 97.0 98.0
98.0 98.0 98.0 98.0 99.0 99.0 100.0 100.0 100.0 100.0 100.0

moyenne = 96,0
TPR = 80,0 % (20/25)
IC de Wilson à 95 % = [60,9 % ; 91,1 %]
```

**La distribution des percentiles est nettement concentrée vers les
valeurs hautes** (80 à 100, aucune valeur en dessous de 80) — clairement
distincte de la distribution quasi-uniforme obtenue sur le bruit pur
(Sec. 2). Le signal injecté est détecté dans 80 % des cas au seuil
conventionnel de 95 %, avec une marge statistique confortable.

## 4. Ce que cette phase diagnostic établit

**Établi, par exécution directe, à résolution diagnostic (30-50
graines, pas encore une calibration fine)** :
- Le couple **support (T=max_s|G_s|) + modèle nul procédural complet
  (univers de nœuds corrigé) + correction de sélection globale** répond
  correctement aux deux exigences du critère de succès fixé par le
  porteur du projet : des données sans structure injectée PEUVENT
  effectivement échouer (FPR≈5 %, distribution quasi-uniforme), et une
  structure injectée PEUT être distinguée (TPR=80 %, distribution
  nettement concentrée) — sans que la génération de candidats
  elle-même ne fournisse mécaniquement la réponse, contrairement à
  `Cohesion_B`.
- Le signal préoccupant de la campagne 8 (FPR 10-20 % sur seulement 10
  graines) ne se reproduit PAS à cette résolution — cohérent avec
  l'analyse de Wilson du porteur du projet : c'était du bruit
  d'échantillonnage, pas un défaut réel.

**Non établi, délibérément, à ce stade** :
- Une calibration fine du FPR/TPR (les IC de Wilson restent larges,
  particulièrement pour le TPR — une phase de confirmation à 100+
  graines, prévue par le protocole C8.1 lui-même, n'a pas encore été
  lancée, jugée non urgente étant donné la propreté de ce résultat
  diagnostic, mais reste une option ouverte).
- Le comportement à d'autres tailles de pool, d'autres tailles de
  signal, ou d'autres nombres de classes (la grille complète de la
  campagne 8, toujours différée).
- Aucune décision architecturale : `Cohesion_B` reste non modifiée dans
  le module de production, le support n'est PAS encore intégré comme
  remplacement -- ce diagnostic est un résultat de calibration, pas une
  décision de conception.

## 5. État après cette campagne

```text
C8 STATUS
────────────────────────────────────
Cohesion_B                     INVALIDÉE pour ce générateur de candidats
Support (T=max_s|G_s|)         DIAGNOSTIC POSITIF (FPR≈nominal,
                                TPR=80%, phase 30-50 graines)
Null procédural complet        VALIDÉ comme cadre de test
FPR calibré finement           PAS ENCORE (IC larges, confirmation 100+
                                possible mais non jugée urgente)
C8.1 diagnostic                FAIT -- résultat encourageant
C8.1 confirmation (100+)       OPTIONNELLE, PAS ENCORE LANCÉE
V1-V4                          TOUJOURS GELÉS
Production code                INCHANGÉ
Architecture                   AUCUNE décision prise
```

## 6. Prochaine étape

Décision explicite du porteur du projet : lancer la phase de
confirmation à plus grande échelle (100+ graines) pour resserrer les IC
de Wilson avant toute décision architecturale, ou considérer ce
diagnostic suffisamment probant pour passer à l'étape suivante
(intégration du support comme statistique candidate dans le module,
elle-même une décision architecturale distincte, non prise ici).
