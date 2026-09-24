# P4-U.2 — Calibration jetable, campagne 3 : Gate H (bruit vs hétérogénéité), robustesse multi-graines, taille finale (2026-09-24)

Exécute la campagne ciblée en trois points explicitement demandée par le
porteur du projet après lecture de la campagne 2
(`P4U2_Calibration_Campaign2_2026-09-24.md`, commit `97981f0`) : Gate H
reste le principal verrou ; la robustesse multi-graines de la correction
multi-comparaisons manquait ; aucune taille de groupe n'était encore
choisie pour éviter que le futur cas V4 ne soit artificiellement sur la
frontière de puissance.

```text
97981f0 (campagne 2)
        ↓
campagne 3, trois points ciblés      <- CE DOCUMENT
   A. Gate H : bruit naturel vs hétérogénéité manifeste
   B. correction multi-comparaisons : mêmes scénarios, 20 graines
   C. taille finale : V1 et V4 loin de la frontière de puissance
        ↓
gel numérique (toujours pas fait)
```

**Toujours aucun code de production P4-U.2, aucune valeur numérique
gelée, aucun benchmark verrouillé.** Script jetable, non committé, même
discipline que les campagnes 1 et 2 ; réutilise leurs fonctions sans
modification.

## Partie A — Gate H : bruit naturel vs hétérogénéité manifeste

### Constat de départ, avant tout résultat

`contradiction_support` (campagnes 1-2) ne mesure qu'UNE fraction de
désaccord sur un seul trait binaire (`a un prolongement profondeur 2`).
Or le porteur du projet demande de distinguer deux CAUSES différentes
d'un même désaccord — bruit naturel vs vraie hétérogénéité — que cette
seule fraction ne peut, par construction, pas distinguer : la même
valeur numérique de `contradiction_support` peut provenir de l'une ou
de l'autre cause. Il fallait donc une seconde dimension, pas seulement
une résolution plus fine de la même dimension.

### Généralisation nécessaire : `contradiction_support_v2`

Le scénario d'hétérogénéité manifeste construit ci-dessous diffère de sa
majorité sur le trait `a un prolongement profondeur 3`, pas sur
`profondeur 2` — `contradiction_support` (v1, campagnes 1-2) ne
l'aurait donc pas du tout détecté. Généralisé ici en un vote majoritaire
sur le VECTEUR de traits `(a_profondeur_2, a_profondeur_3)`, plutôt que
sur un seul trait fixé à l'avance — un raffinement nécessaire, pas un
changement arbitraire.

### Deux corpus, deux causes réellement différentes

- **Bruit naturel** : UNE SEULE relation réelle (prolongement propre à
  un saut, `depth2=1, depth3=0`), avec une fraction `p_fail` (tirage de
  Bernoulli indépendant par membre, jamais un compte choisi à la main)
  d'échecs IDIOSYNCRASIQUES à observer ce motif propre (continuation
  manquante, ou un saut accidentel supplémentaire via un nœud partagé
  « occupé ») — délibérément PAS uniformes entre eux, pour imiter une
  imperfection réaliste de corpus, pas une seconde classe cachée.
  30 répétitions indépendantes par niveau de `p_fail`.
- **Hétérogénéité manifeste** : DEUX classes réellement différentes et
  chacune interne uniforme (majorité = prolongement à un saut,
  `depth2=1, depth3=0` ; minorité = prolongement à deux sauts,
  `depth2=1, depth3=1`) — un vrai second motif cohérent, pas du bruit.
  Construction déterministe, aucune répétition nécessaire.

### Résultats

| Bruit naturel `p_fail` | contradiction_support (moy./max sur 30 rép.) | Cohésion interne de la minorité (moy.) |
|---|---|---|
| 0.05 | 0.043 / 0.150 | 0.772 (n=6 répétitions avec ≥2 dissidents) |
| 0.10 | 0.105 / 0.250 | 0.537 (n=16) |
| 0.15 | 0.148 / 0.300 | 0.530 (n=25) |
| 0.20 | 0.193 / 0.350 | 0.497 (n=28) |
| 0.30 | 0.292 / 0.500 | 0.406 (n=29) |

| Hétérogénéité manifeste `minority_fraction` | contradiction_support | Cohésion interne de la minorité |
|---|---|---|
| 0.05 | 0.050 | n/a (< 2 dissidents) |
| 0.10 | 0.100 | **1.000** |
| 0.15 | 0.150 | **1.000** |
| 0.20 | 0.200 | **1.000** |
| 0.30 | 0.300 | **1.000** |
| 0.40 | 0.400 | **1.000** |
| 0.50 | 0.500 | **1.000** |

### Résultat décisif

**À un niveau de `contradiction_support` quasiment identique (~0,10),
les deux causes sont numériquement indiscernables sur `contradiction_support`
seul (0,105 vs 0,100) mais nettement séparées sur la cohésion interne de
la minorité (0,537 vs 1,000 exactement).** Le bruit naturel produit une
minorité dispersée, dont la cohésion se DÉGRADE encore à mesure que le
bruit augmente (0,772 → 0,406) — cohérent avec l'accumulation de modes
d'échec variés, pas un signal contradictoire. L'hétérogénéité manifeste
produit systématiquement une cohésion de minorité PARFAITE (1,000), quel
que soit le niveau de contamination testé, parce que la minorité est par
construction une vraie seconde classe uniforme.

**Conséquence directe pour Gate H, proposée ici pour la première fois,
PAS encore intégrée au protocole v0.1** : `contradiction_support` seul
est structurellement insuffisant pour distinguer bruit et hétérogénéité
— **Gate H devrait exiger conjointement (a) `contradiction_support`
au-dessus d'un seuil ET (b) une cohésion interne élevée du sous-groupe
dissident**, cette seconde condition étant la preuve qu'une seconde
classe réellement cohérente se cache dans le groupe, plutôt qu'un simple
bruit de mesure. Ceci est une PROPOSITION de raffinement issue de cette
calibration, à valider et endosser explicitement par le porteur du
projet avant toute écriture dans le protocole — pas une modification
silencieuse de Sec. 10.2.

Réserve honnête : la cohésion de minorité à `p_fail=0,05` repose sur
seulement 6 répétitions ayant ≥2 dissidents (échantillon réduit) ; le
modèle de bruit lui-même (trois modes d'échec équiprobables) est une
construction synthétique, pas un modèle de bruit de corpus réel calibré
sur des données observées.

## Partie B — Correction multi-comparaisons, robustesse sur 20 graines

Même scénario que la campagne 2 (1 vrai groupe à 90 % de prolongement +
9 candidats sans signal tirés d'un fond aléatoire), répété sur 20 graines
indépendantes (`N_null=200` par graine).

| Statistique | Taux moyen de faux positifs, corrigé (max-famille) | Taux moyen, non corrigé | Vrai signal détecté |
|---|---|---|---|
| Cohesion_A | **1.7 %** | 16.7 % | 20/20 |
| Cohesion_B | **0.6 %** | 1.7 % | 20/20 |
| Cohesion_C | **0.0 %** | 0.6 % | 20/20 |

**La correction par maximum de famille tient sur 20 graines, pas
seulement sur l'exécution unique de la campagne 2** : taux de faux
positifs corrigé toujours inférieur ou égal au taux non corrigé, et
toujours nettement sous le taux nominal individuel de 5 % pour les trois
statistiques — cohérent avec la conservativité attendue d'une correction
par maximum. `Cohesion_A` reste, sur 20 graines, la statistique la plus
vulnérable sans correction (16,7 % en moyenne, cohérent avec le 33 % à
une seule graine de la campagne 2 — même ordre de grandeur, pas un
hasard de graine). Le vrai signal franchit le seuil corrigé sur les 20
graines et les trois statistiques, sans exception : **la correction ne
coûte aucune sensibilité détectée sur cette configuration.**

## Partie C — Calibration finale de taille (V1 p=0,9 vs V4/PARTIAL p=0,8)

`N_null=300`, `group-resample-only`, `z` minimal sur les trois
statistiques rapporté comme le pire cas :

| Taille de groupe | V1 (p=0,9), pire z | V4/PARTIAL (p=0,8), pire z | Contrôle négatif (p=0,5), z |
|---|---|---|---|
| 20 | 2.90 | **1.72** (< 1.96, échoue) | -2.02 à -1.01 |
| 30 | 3.32 | **1.88** (< 1.96, échoue encore) | -2.30 à -1.27 |
| **40** | **3.79** | **2.18** (> 1.96, marge réelle) | -2.75 à -1.43 |
| 50 | 4.40 | 2.52 | -3.17 à -1.54 |
| 60 | 4.55 | 2.62 | -3.29 à -1.68 |

**`group_size=40` est la plus petite taille testée où le cas difficile
(V4/PARTIAL, 80/20) franchit le seuil conventionnel avec une marge
réelle (z=2,18, pas seulement 1,96) pour les TROIS statistiques
simultanément**, tandis que V1 (signal net) reste très largement
significatif (z≥3,79) et le contrôle négatif (p=0,5, aucun signal réel)
reste toujours et nettement du côté non significatif, sans dérive vers
un faux positif à mesure que la taille augmente. Les tailles 20 et 30 —
utilisées implicitement dans les campagnes 1 et 2 pour PARTIAL — sont
maintenant démontrées insuffisantes pour placer V4 loin de la frontière
de puissance ; 40 (ou davantage, au prix d'un corpus plus grand) est la
proposition concrète issue de cette calibration.

## Synthèse — état après cette campagne

```text
P4-U.2 = OPEN_RESEARCH

Gate H :
    contradiction_support seul -> confirmé INSUFFISANT pour distinguer
    bruit et hétérogénéité (même valeur, causes différentes, démontré)
    Raffinement proposé -> contradiction_support + cohésion interne de
    la minorité, PAS ENCORE endossé par le porteur du projet
    Seuils numériques (contradiction_support ET cohésion minorité) ->
    toujours non gelés

Correction multi-comparaisons :
    robustesse confirmée sur 20 graines, pas seulement 1 -> le principe
    peut raisonnablement être considéré comme établi

Taille du futur benchmark verrouillé :
    group_size=40 proposé, avec justification quantitative directe
    (marge réelle sur le cas difficile, pas seulement le seuil atteint)
    -> pas encore formellement décidé

Statistique de cohésion :
    toujours pas de gagnant unique choisi ; Cohesion_A confirmée la plus
    vulnérable sans correction sur 20 graines (pas un artefact d'une
    seule exécution)

Implémentation : NON COMMENCÉE
Benchmark verrouillé : NON CONSTRUIT
```

## Ce qui reste avant tout gel numérique

- **Endosser ou rejeter le raffinement de Gate H** (contradiction_support
  + cohésion de minorité) — c'est une proposition de cette calibration,
  pas une décision prise ici.
- **Geler les seuils numériques de Gate H** une fois le critère
  lui-même validé (quel seuil de `contradiction_support`, quel seuil de
  cohésion de minorité).
- **Geler formellement `group_size=40`** (ou une autre taille) pour le
  futur benchmark verrouillé.
- **Choix final de la statistique de cohésion** — toujours ouvert, bien
  que moins critique maintenant que la correction multi-comparaisons et
  la taille de groupe sont mieux établies.
- Le modèle de bruit naturel de la Partie A reste une construction
  synthétique ad hoc ; une validation contre un modèle de bruit dérivé
  de corpus réels renforcerait la proposition de raffinement de Gate H
  avant de la figer, mais n'est pas indispensable pour continuer.

Comme pour les campagnes précédentes, la décision de geler — ou de
prolonger encore la calibration sur l'un de ces points — revient
explicitement au porteur du projet.
