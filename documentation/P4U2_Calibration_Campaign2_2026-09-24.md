# P4-U.2 — Calibration jetable, campagne 2 : puissance de Gate I, correction multi-comparaisons, seuil Gate H (2026-09-24)

Suite directe de la campagne 1 (`P4U2_Calibration_Experiment_2026-09-23.md`,
commit `854b32e`). Le porteur du projet a jugé ce premier résultat
correct mais insuffisant pour un gel numérique : il isole
`group-resample-only` sur UN SEUL corpus (TWIN) et laisse ouverte la
question centrale — le résultat limite du cas PARTIAL (juste sous le
seuil conventionnel) vient-il d'une statistique de cohésion
insuffisante, d'un échantillon insuffisant, ou d'un modèle nul trop
conservateur ? La correction multi-comparaisons (protocole Sec. 13,
point 6) restait par ailleurs entièrement non testée.

```text
854b32e (campagne 1)
        ↓
critique du porteur du projet : résultat correct mais pas suffisant
        ↓
campagne 2                          <- CE DOCUMENT
   1. group-resample-only : validé sur TWIN seul -> à revalider sur
      plusieurs niveaux de signal, pas une seule fois
   2. puissance de Gate I : signal x taille x N_null, séparément
   3. correction multi-comparaisons : jamais testée -> testée ici
   4. Gate H : sweep fin, deux frontières à distinguer
        ↓
gel numérique (toujours pas fait)
```

**Toujours aucun code de production P4-U.2, aucune valeur numérique
gelée, aucun benchmark verrouillé.** Script jetable, non committé,
exécuté depuis le scratchpad — même discipline que la campagne 1.
Réutilise sans modification toutes les fonctions de la campagne 1
(signature, trois statistiques de cohésion, `group-resample-only`).
`topology-only` n'est pas retesté ici : la campagne 1 l'a déjà éliminé
sur TWIN de façon décisive (Sec. 3.2 de ce document précédent).

## 1. Partie 1+2A — Balayage de force de signal (group_size=20,
   bg_size=20, N_null=300)

Généralisation continue de SEP (`p_group=1.0`) et PARTIAL
(`p_group=0.8`) de la campagne 1 : groupe candidat avec fraction
`p_group` d'arêtes à prolongement, fond de corpus avec la fraction
miroir `1 - p_group`.

| p_group | Cohesion_A (pct / z) | Cohesion_B (pct / z) | Cohesion_C (pct / z) |
|---|---|---|---|
| 0.5 | 1.0 / **-2.17** | 1.0 / -1.07 | 1.0 / **-2.17** |
| 0.6 | 19.8 / -0.94 | 19.8 / -0.86 | 19.8 / -0.94 |
| 0.7 | 64.2 / 0.38 | 64.2 / 0.10 | 64.2 / 0.38 |
| 0.8 | 93.8 / 1.65 | 93.8 / **1.92** | 93.8 / 1.65 |
| 0.9 | 100.0 / 3.01 | 100.0 / 5.50 | 100.0 / 3.01 |
| 1.0 | 100.0 / 4.32 | 100.0 / 12.62 | 100.0 / 4.32 |

**Résultat propre : les trois statistiques croissent de façon
STRICTEMENT MONOTONE avec la force du signal**, sous `group-resample-only`
— aucune irrégularité, aucune inversion. `p_group=0.5` (groupe construit
EXACTEMENT à 10/20, la configuration la moins cohérente possible pour un
trait binaire) donne un z négatif : le groupe observé est, à dessein,
moins homogène qu'un ré-échantillon aléatoire typique du même pool
50/50 (qui atterrit rarement exactement sur un partage 10/10). Ce n'est
pas une anomalie, c'est la conséquence directe et attendue de la
construction. Le seuil conventionnel (z=1,96 / percentile 95) est
franchi quelque part entre `p_group=0.8` et `p_group=0.9` pour les trois
statistiques — **le cas PARTIAL (80/20) de la campagne 1 se situe presque
exactement à la frontière naturelle de détectabilité pour cette taille
d'échantillon**, ce qui n'était pas su au moment de la campagne 1 et
répond directement à sa question ouverte.

## 2. Partie 2B — Balayage de taille d'échantillon (p_group=0.8,
   N_null=300)

| group_size | Cohesion_A (pct / z) | Cohesion_B (pct / z) | Cohesion_C (pct / z) |
|---|---|---|---|
| 10 | 85.5 / 1.15 | 85.5 / 0.82 | 85.5 / 1.15 |
| 20 | 93.7 / 1.56 | 93.7 / 1.91 | 93.7 / 1.56 |
| 40 | 99.7 / 2.32 | 99.7 / 3.36 | 99.7 / 2.32 |
| 80 | 100.0 / 2.90 | 100.0 / 4.34 | 100.0 / 2.90 |

**Résultat décisif** : à force de signal FIXE (80/20), augmenter
uniquement la taille de l'échantillon augmente la puissance de façon
nette et monotone pour les trois statistiques — dès `group_size=40`, le
signal 80/20 franchit largement le seuil conventionnel. **Ce n'est donc
pas la statistique de cohésion qui est insuffisante** : le même signal,
avec plus d'observations, devient clairement détectable par les trois
candidats sans qu'aucun changement de formule ne soit nécessaire.

## 3. Partie 2C — Balayage de N_null (p_group=0.8, group_size=20 fixe)

| N_null | Cohesion_A (pct / z) | Cohesion_B (pct / z) | Cohesion_C (pct / z) |
|---|---|---|---|
| 200 | 94.2 / 1.66 | 94.2 / 2.03 | 94.2 / 1.66 |
| 500 | 94.1 / 1.68 | 94.1 / 1.97 | 94.1 / 1.68 |
| 1000 | 93.6 / 1.62 | 93.6 / 1.86 | 93.6 / 1.62 |
| 2000 | 93.6 / 1.60 | 93.6 / 1.82 | 93.6 / 1.60 |

**Résultat clair : le percentile/z est stable, à des fluctuations
d'échantillonnage près, de `N_null=200` à `N_null=2000`.** Le modèle nul
n'est pas sous-échantillonné à `N_null=200-300` — l'hypothèse « modèle
nul trop conservateur par manque de réplicats » est donc écartée par
exécution directe, pas par supposition.

### Synthèse 1-3 : réponse à la question posée par le porteur du projet

```text
Le résultat limite de PARTIAL (campagne 1) est causé par :
    échantillon insuffisant   -> OUI, démontré (Sec. 2, monotone et net)
    statistique insuffisante  -> NON, exclu (les 3 réagissent pareil au signal ET à la taille)
    null trop conservateur    -> NON, exclu (Sec. 3, stable de 200 à 2000)
```

## 4. Partie 3 — Correction multi-comparaisons (1 vrai groupe + 9
   candidats sans signal)

Corpus : un groupe réel `T` (20 arêtes, 90 % de prolongement) noyé dans
un fond de 200 arêtes tirées au hasard (aucune structure intentionnelle,
seed fixe) ; 9 « candidats nuls » = sous-ensembles aléatoires disjoints
de 20 arêtes tirés de ce fond. Modèle nul par maximum (discipline déjà
retenue par P4-U.1, testée ici plutôt que supposée acquise) : pour
chaque réplicat, tirer 10 sous-groupes aléatoires indépendants du pool
entier et retenir le maximum de la statistique parmi les 10 — seuil de
correction = 95ᵉ percentile de cette distribution du maximum,
**partagé** par les 10 candidats. Comparé à une approche non corrigée où
chaque candidat est jugé contre son propre seuil individuel.

| Statistique | Seuil corrigé (famille) | Faux positifs corrigés (/9) | Faux positifs non corrigés (/9) |
|---|---|---|---|
| Cohesion_A | 0.8000 | **0/9** | **3/9** |
| Cohesion_B | 0.3498 | 0/9 | 0/9 |
| Cohesion_C | 0.6000 | 0/9 | 0/9 |

Le vrai groupe (`TRUE_SIGNAL`, observé 0.95/0.7787/0.90 selon la
statistique) franchit correctement le seuil corrigé pour les trois
statistiques. **Sans correction, Cohesion_A laisse passer 3 candidats
sur 9 qui n'ont aucun signal réel — un taux de fausse découverte de
33 % sur cette exécution.** Avec correction (maximum de famille), les
trois statistiques donnent 0/9 faux positifs tout en détectant
correctement le vrai signal. **Résultat démontré, pas supposé : la
correction multi-comparaisons de type P4-U.1 (statistique du maximum)
est nécessaire et suffisante ici**, et son absence est concrètement
dangereuse pour au moins une des trois statistiques candidates.

Réserve honnête : une seule graine aléatoire, un seul tirage de 9
candidats nuls — le "3/9" illustre un risque réel et démontré, ce n'est
pas un taux de faux positifs calibré (il faudrait de nombreuses
répétitions indépendantes pour cela, non faites ici).

## 5. Partie 4 — Gate H, balayage fin

Remplacement progressif des membres cohérents du groupe SEP par des
leurres contradictoires, de 0 % à 50 % par pas de 5 % (sauf 45 %, omis) :

```text
0% -> 0.000   5% -> 0.050   10% -> 0.100   15% -> 0.150   20% -> 0.200
25% -> 0.250  30% -> 0.300  35% -> 0.350   40% -> 0.400   50% -> 0.500
```

Confirme, à résolution plus fine, la linéarité déjà observée en
campagne 1 — aucune irrégularité. **Ce balayage ne règle cependant PAS
la question posée par le porteur du projet** : il fait varier une seule
dimension (fraction injectée), donc ne distingue pas deux régimes
réellement différents — (a) un groupe véritablement cohérent avec du
bruit de mesure naturel (couverture de corpus incomplète, plafond
`max_paths`, effets de bord) et (b) un groupe manifestement hétérogène
par construction. Les deux frontières que le porteur du projet demande
de déterminer séparément restent donc **non résolues** : il faudrait un
corpus construit pour produire du bruit naturel (pas un remplacement
contrôlé et discret) pour établir la frontière d'acceptation, distincte
de la frontière de rejet observée ici. Reporté explicitement comme
ouvert, pas comme résolu par ce balayage plus fin.

## 6. État scientifique après cette campagne

```text
P4-U.2 = OPEN_RESEARCH

Modèle nul :
    group-resample-only -> CONFIRMÉ sur un balayage de force de signal
    ET de taille d'échantillon (pas seulement sur TWIN) -- toujours pas
    formellement gelé, mais l'évidence en sa faveur s'est élargie, pas
    répétée à l'identique

Puissance de Gate I :
    ÉTABLIE -- monotone en force de signal et en taille d'échantillon,
    stable en N_null. La limite du cas 80/20 est un effet de TAILLE
    D'ÉCHANTILLON, démontré, pas un défaut de statistique ni de modèle nul

Statistique de cohésion :
    toujours pas de gagnant unique sur les corpus synthétiques gradués
    (A et C coïncident numériquement sur ces corpus à 2 classes -- un
    artefact de cette famille de corpus, pas une propriété générale) ;
    MAIS Cohesion_A s'est montrée seule vulnérable (3/9 faux positifs)
    sans correction multi-comparaisons sur le corpus à fond aléatoire de
    la Partie 3 -- argument supplémentaire pour ne jamais sauter la
    correction

Correction multi-comparaisons :
    NÉCESSAIRE ET SUFFISANTE, démontrée (0/9 faux positifs corrigés vs
    jusqu'à 3/9 non corrigés) -- pas encore calibrée sur plusieurs graines

Gate H :
    comportement confirmé linéaire et prévisible à résolution fine ;
    SEUIL TOUJOURS NON GELÉ ; les deux frontières (bruit naturel vs
    hétérogénéité manifeste) restent à distinguer par un corpus dédié,
    non construit ici

Implémentation :
    NON COMMENCÉE

Benchmark verrouillé :
    NON CONSTRUIT
```

## 7. Ce qui reste avant tout gel numérique

- **Taille du futur benchmark verrouillé** : la Partie 2 montre qu'une
  taille de groupe plus grande donne une puissance strictement
  meilleure — mais choisir une taille uniquement pour maximiser la
  puissance irait à l'encontre de l'objectif (tester des conditions
  réalistes, pas les conditions les plus favorables). Décision de
  conception à prendre explicitement, pas une pure optimisation
  statistique.
- **`N_null`/percentile à geler** : la Partie 3 suggère `N_null=200-300`
  déjà stable ; reste à décider formellement.
- **Frontière d'acceptation de Gate H face au bruit naturel** :
  entièrement ouverte, nécessite un corpus dédié non construit ici.
- **Calibration multi-graines de la correction multi-comparaisons** :
  la Partie 3 démontre le principe sur UNE exécution ; une calibration
  plus poussée voudrait plusieurs graines avant de figer le percentile
  de correction.
- **Choix final de la statistique de cohésion** : toujours ouvert,
  quoique moins critique maintenant que la correction multi-comparaisons
  est établie comme non-négociable indépendamment du choix.

Comme pour la campagne 1, la décision de geler ces valeurs — ou de
prolonger encore la calibration sur l'un des points ci-dessus — revient
explicitement au porteur du projet.
