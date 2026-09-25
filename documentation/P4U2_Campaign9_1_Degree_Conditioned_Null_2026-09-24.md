# P4-U.2 — Campagne 9-1 : null conditionnel aux degrés, statistique T inchangée (2026-09-24)

C9-1 = nouveau null + `T = max_s |G_s|` actuel. Pré-enregistrement :
`PREREGISTRATION_C9_1.md` (sha256 `7a9dc131…352aef4`), rédigé avant tout run.
Addendum de réplication : `ADDENDUM_C9A2_REPLICATION.md`, rédigé après lecture de
C9-A2 et avant la réplication. **Production inchangée. Aucune décision d'architecture.
C9-2 (T′) et C9-C non lancés. P4-U.2-R1 (MAX_PATHS) hors périmètre.**
Harnais : `c9_degree_null.py`, sur la même base reconstruite que C8.1-confirmation
(même réserve de reconstruction, voir le rapport C8.1-confirmation, Sec. 0).

## 1. Null C9

Chaque réplicat conserve les sources observées dans l'ordre et permute uniformément la
liste des cibles. Toute permutation contenant une boucle est rejetée. Les degrés
entrants et sortants sont donc préservés exactement (vérifié), les multi-arêtes sont
autorisées comme dans le générateur observé, et le tirage est exact et indépendant, sans
chaîne de Markov. Pour un générateur produit P(s,t) ∝ w_s·w_t, ce null est exact par
construction : C9-A0/A1/A2 testent donc l'**implémentation**, pas l'adéquation à un
corpus réel. Les bras non tautologiques sont SBM et, dans une moindre mesure, A-bis.

## 2. C9-A — calibration (100 graines, N_null = 200, 100 nœuds / 100 arêtes)

| config | hétérog. (s ; CV degrés) | FPR | Wilson 95 % | α_eff | binom. bilat. | KS | χ² | tronq. |
|---|---|---|---|---|---|---|---|---|
| A0 | 0 ; 0,69 | 3/100 | [1,0 ; 8,5] | 4,76 % | 0,64 | 0,14 | 0,18 | 0 |
| A1 | 0,5 ; 0,99 | 6/100 | [2,8 ; 12,5] | 3,94 % | 0,29 | 0,11 | 0,15 | 0 |
| **A2** | 0,75 ; 1,48 | **10/100** | [5,5 ; 17,4] | 4,18 % | **0,0093** | 0,35 | 0,53 | 0 |
| A2-rép. (300 graines neuves) | 0,75 ; 1,48 | 18/300 = 6,0 % | [3,8 ; 9,3] | 4,23 % | 0,148 | 0,66 | 0,70 | 0 obs / 1 nul sur 60 000 |

Verdicts pré-enregistrés, **enregistrés tels quels** :
```text
N1  A0 PASS   A1 PASS   A2 FAIL (p = 0,0093 < 0,0167)
N2  A0/A1/A2 PASS
N3  tendance Cochran-Armitage z = 1,96, p(croissant) = 0,025 < 0,05   FAIL
N4  aucune troncature                                                PASS
```
**Interprétation, selon la règle pré-déclarée de l'addendum** : la réplication
indépendante est compatible avec α_eff (p = 0,148 ≥ 0,05). Le FAIL de A2, et le FAIL
N3 qui en dépend, s'interprètent donc comme une fluctuation, cohérente avec l'exactitude
mathématique du null pour ce générateur. Deux points de vigilance restent ouverts, sans
être tranchés :
- le taux répliqué, 6,0 %, reste au-dessus de α_eff, même si c'est compatible ;
- le cumul A2 + réplication (28/400, p = 0,009) **n'est pas une inférence valide**, car
  il inclut l'échantillon qui a déclenché la réplication. Il ne peut ni confirmer ni
  infirmer.
Si une future campagne retrouve une inflation systématique à forte hétérogénéité, la
piste H2 (défaut subtil) sera à rouvrir en priorité.

## 3. C9-B — falsification du signal C8.1 (graphes observés identiques à C8.1-confirmation)

| config | TPR, null uniforme | TPR, null degrés | Wilson (degrés) | α_eff | McNemar apparié | perdus / gagnés |
|---|---|---|---|---|---|---|
| B2 (8 chaînes) | 32 % | 4 % | [1,6 ; 9,8] | 5,0 % | 5,8×10⁻⁸ | 29 / 1 |
| B1 (15) | 72 % | 11 % | [6,3 ; 18,6] | 5,1 % | 6,8×10⁻¹⁶ | 64 / 3 |
| B3 (25) | 100 % | 6 % | [2,8 ; 12,5] | 5,0 % | 1,0×10⁻²⁸ | 94 / 0 |

**Prédiction pré-enregistrée confirmée.** Le bucket d'impasses `(1,0,0,{F})` est fixé
par les degrés, aux multi-arêtes près : 13,7 / 20,9 / 30,7 observés contre 13,8 / 20,8 /
30,7 sous le null. Il porte l'arg-max dans 100 % des cas, et T devient quasi aveugle.

**La domination n'est pas un effet de seuil : elle est structurelle dans ce plan de
signal.** Chaque chaîne ajoute exactement une tête `(1,1,0,{F,FF})` et une impasse
`(1,0,0,{F})`. Le bucket d'impasses est donc toujours au moins égal au bucket de tête,
plus environ 6 impasses de fond. Le scénario « la signature relationnelle finit par
dépasser les impasses » est **impossible** avec les chaînes B, quelle que soit leur
taille. B ne pouvait pas départager les deux branches de l'hypothèse H_T.

**Le signal relationnel existe pourtant, et T choisit le mauvais représentant :**

| config | tête de chaîne observée | tête sous null degrés |
|---|---|---|
| B2 | 8,6 | 2,3 |
| B1 | 15,5 | 4,2 |
| B3 | 25,7 | 7,7 |

## 4. Bras supplémentaires (hors critère)

**A-bis** (exactement les graphes A-bis de C8.1-confirmation, 60 / 100, Zipf s = 1) :
FPR 88 % → **4 %** (α_eff 4,9 %, binomial p = 1,0, KS 0,95). McNemar apparié
p = 1×10⁻²⁵, 84 rejets perdus, 0 gagné. **Spécificité rétablie** : ce que T
« détectait » sur A-bis est entièrement expliqué par les degrés. Réserve : ce bras est
**confondu avec R1**. 92/100 observés et 18 917/20 000 nuls sont tronqués, et l'artefact
`(0,0,0,∅)` porte encore l'arg-max dans 60 % des cas. Il disparaît du test parce que le
null reproduit les mêmes hubs, donc la même troncature, pas parce qu'il est corrigé. La
signature tronquée reste dépendante de l'ordre, et le null garde l'ordre des sources :
l'échangeabilité n'est donc qu'approchée dans ce bras.

**SBM** (100 nœuds, 2 blocs, rapport intra/inter 9:1, aucune régularité injectée) :
FPR 10/100 contre α_eff 4,5 % (binomial p = 0,015), **PIT non uniforme** (KS p = 0,006,
χ² p = 0,002, 23 graines dans le dernier décile). Le null conditionnel aux degrés
n'absorbe donc pas entièrement une structure mésoscopique. L'attribution localise le
mécanisme :
- l'arg-max est le bucket d'impasses dans 99 cas sur 100, en léger excès (14,35 contre
  14,08) ;
- l'excès passe par les **arêtes répétées** : 0,91 doublon par graphe contre 0,50 sous le
  null ;
- les graines rejetées ont un excès moyen de 1,79 doublon, contre 0,26 pour les autres ;
- la corrélation entre excès de doublons et excès d'impasses vaut 0,40.
Un doublon A→B produit une signature d'impasse, puisque le retour vers A est déjà
visité. C'est une propriété dyadique, pas une régularité relationnelle. Ce mécanisme
n'explique que partiellement l'inflation (corrélation 0,40), le reste n'est pas attribué.

## 5. Attribution par famille (DESCRIPTIVE, a posteriori, 50 réplicats nuls, aucune décision)

| config | impasses obs / null | max non trivial (d2>0 ∨ d3>0) obs / null |
|---|---|---|
| A0 | 13,9 / 14,0 | 4,7 / 4,6 |
| SBM | 14,4 / 14,1 | 4,7 / 4,6 |
| B1 | 20,9 / 20,8 | **15,5 / 5,8**, porté par `(1,1,0,{F,FF})` dans 100/100 |

La famille non triviale est muette sur le bruit et sur les communautés, et fortement
réactive à la chaîne. **C'est une observation faite après avoir vu les données** : elle
motive T′, elle ne le valide pas. T′ doit être pré-enregistré comme hypothèse
indépendante, avec ses propres étages A, A-bis, SBM et B, et sur des graines neuves.

## 6. Ce que C9-1 établit

```text
C8.1 « signal »                  expliqué à 85-94 % par les degrés (McNemar, B1-B3)
T = max|G_s| sous null degrés    calibré (A0/A1, A2 après réplication), spécifique
                                  sur A-bis, légère fuite sur SBM (doublons)
H_T : max dominé par les         CONFIRMÉE sur B1-B3 ; domination structurelle
      classes induites par        dans ce plan de signal (tête ≤ impasse),
      les degrés                  donc non généralisable sans signal découplé
Signal relationnel               PRÉSENT dans (1,1,0,{F,FF}), masqué par le max
Verdict pré-enregistré C9-A      FAIL (N1 sur A2, N3), interprété comme fluctuation
                                  après réplication pré-déclarée ; FAIL conservé
```

## 7. Conséquences pour la suite (proposées, rien de lancé)

1. **C9-2, T′ = max sur signatures non triviales, même null.** À pré-enregistrer
   maintenant, en sachant que la Sec. 5 a été vue. Graines neuves, mêmes bras.
   Critères de spécificité explicites :
   - SBM : doit rester calibré, vu que l'excès SBM passe par les impasses, que T′
     exclut ;
   - A-bis : seulement après R1, car les hubs y tronquent les signatures.
2. **C9-C, signal découplé.** Le plan B lie mécaniquement tête et impasse. C9-C doit
   injecter une régularité relationnelle **sans nœuds dédiés de degré 1**. Piste : des
   chaînes, ou des boucles d'anticipation (A→B→C avec A→C), plantées par des échanges
   d'arêtes qui préservent exactement la séquence de degrés d'un graphe de fond. La
   régularité serait alors invisible aux degrés par construction. À concevoir et
   pré-enregistrer séparément.
3. **Multi-arêtes** (constat SBM). Il faut décider si une observation répétée A→B est
   une régularité ou une nuisance. Si c'est une nuisance, le null peut conditionner
   aussi sur la multiplicité des paires, ou la signature peut dédoublonner. C'est une
   décision de modélisation, pas un réglage.
4. **Attribution obligatoire** dans tout futur Gate I : signature arg-max, famille
   (impasse / non triviale / tronquée), taille observée contre null, par candidat.
5. **R1 (MAX_PATHS)** reste un verrou indépendant. A-bis ne sera interprétable
   proprement qu'après R1.

## 8. État

```text
C8.1                     PASS conditionnel (null uniforme) ; spécificité NON démontrée
C9-1                     FAIT
  ├─ C9-A                FAIL enregistré (A2/N3) → fluctuation après réplication
  ├─ C9-B                puissance de T effondrée (85-94 % du signal = degrés)
  ├─ A-bis               spécificité rétablie (88 % → 4 %), confondu avec R1
  └─ SBM                 fuite légère via multi-arêtes
C9-2 (T′)                À PRÉ-ENREGISTRER
C9-C (signal découplé)   À CONCEVOIR
P4-U.2-R1 (MAX_PATHS)    OUVERT
V1–V4                    GELÉS
Production / Archi       INCHANGÉE / GELÉE
```

## Fichiers

`PREREGISTRATION_C9_1.md` (+ `.sha256`), `ADDENDUM_C9A2_REPLICATION.md` (+ `.sha256`),
`c9_degree_null.py`, `analyze_c9.py`, `attribution_families.py`, `raw_C9*.json`,
`summary_c9.json`, `attribution_families.json`.
