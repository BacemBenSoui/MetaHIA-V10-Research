# P4-U.2 — Calibration jetable, campagne 4 (mini-campagne Gate H exclusivement) (2026-09-24)

Exécute la mini-campagne Gate H demandée explicitement par le porteur du
projet après lecture de la campagne 3 (`P4U2_Calibration_Campaign3_2026-09-24.md`,
commit `38b1f74`) : la campagne 3 a montré que `contradiction_support`
seul est insuffisant et que la cohésion du sous-groupe dissident est une
piste prometteuse, mais a laissé un risque méthodologique explicite non
résolu — la **circularité** : si le sous-groupe dissident était choisi en
CHERCHANT la partition qui maximise sa propre cohésion, une minorité
artificiellement cohérente pourrait être fabriquée même à partir de pur
bruit. Le porteur du projet a demandé trois décisions précises, à obtenir
sans choisir arbitrairement des seuils ronds (0,10/0,15 et 0,8/0,9).

```text
38b1f74 (campagne 3)
        ↓
mini-campagne Gate H seule           <- CE DOCUMENT
   1. règle de sélection du sous-groupe -- pré-enregistrée, déterministe
   2. seuil de contradiction nécessaire
   3. seuil de cohésion distinguant bruit et vraie sous-classe
        ↓
gel numérique (toujours pas fait)
```

**Résultat par anticipation, pour cadrer la lecture** : cette campagne
répond complètement à la décision 1, mais montre que les décisions 2 et
3 telles que formulées (deux SEUILS FIXES) ne sont PAS la bonne réponse
— un résultat négatif honnête, pas un échec de calibration. Un
diagnostic plus profond et une meilleure architecture pour Gate H en
ressortent à la place.

## 1. Règle pré-enregistrée de sélection du sous-groupe (Règle R1)

```text
R1 : partitionner le groupe par VOTE MAJORITAIRE sur le vecteur de
     traits (a_profondeur_2, a_profondeur_3) -- une dimension déjà
     fixée par la signature structurelle gelée (protocole Sec. 7),
     jamais choisie ni recherchée pour cette campagne. Le sous-groupe
     dissident est l'ensemble des membres en désaccord avec le vecteur
     majoritaire. Aucune autre partition n'est jamais considérée ni
     comparée pour un même groupe -- il n'y a ici aucune étape
     d'optimisation susceptible d'introduire une circularité.
```

Cette règle est utilisée identiquement partout dans cette campagne, sans
exception, ce qui répond directement à la décision 1 demandée.

## 2. Balayage systématique (règle R1, 7 niveaux de contamination × 3
   tailles de groupe × deux causes)

20 répétitions par cellule pour le bruit naturel (même modèle
idiosyncrasique que la campagne 3) ; construction déterministe pour
l'hétérogénéité manifeste (deux classes réellement différentes et
uniformes).

### Résultat inattendu, trouvé avant toute conclusion

Avec de petits effectifs de dissidents (2 à 6 environ), le bruit naturel
peut **occasionnellement** atteindre une cohésion de minorité parfaite
(1,000) par pure coïncidence — le modèle de bruit synthétique n'a que
trois modes d'échec discrets, donc plusieurs dissidents peuvent, par
hasard, tomber dans le même mode et partager ainsi une signature
identique, sans qu'aucune vraie seconde classe n'existe. Exemple
concret : `size=40, frac=0,15`, sur 20 répétitions, 1 atteint une
cohésion de minorité de 1,000 avec seulement 5 dissidents.

**Conséquence directe et vérifiée par exécution** : `max(cohésion sous
bruit) = 1,0000` sur l'ensemble de la grille touche exactement
`min(cohésion sous hétérogénéité) = 1,0000` — **aucun seuil fixe unique
ne sépare proprement les deux causes sur cette grille.** C'est
précisément le type de piège que le porteur du projet redoutait, bien
qu'il provienne ici d'une coïncidence de petit échantillon plutôt que
d'une recherche explicite de partition.

## 3. Une comparaison à un modèle nul (à la Gate I) résout-elle le
   problème ? Testé directement, pas supposé

Proposition testée : au lieu d'un seuil fixe sur la cohésion de
minorité, comparer cette cohésion à un modèle nul — ré-échantillonner
aléatoirement, dans le pool complet du corpus, un sous-ensemble de même
taille que le sous-groupe dissident (même mécanique que
`group-resample-only`, déjà validée pour Gate I), et calculer un
percentile/z.

### Test 1 — petits effectifs (k≈5-6), où la coïncidence a été trouvée

| Cas | k | cohésion observée | percentile (modèle nul) | z |
|---|---|---|---|---|
| Bruit (coïncidence trouvée) | 5 | 1,000 | 97,2 | 3,45 |
| Hétérogénéité | 6 | 1,000 | 99,0 | 4,61 |

**La comparaison au modèle nul NE RÉSOUT PAS le problème à ces
effectifs** : la coïncidence de bruit obtient un percentile (97,2)
presque aussi extrême que le vrai cas d'hétérogénéité (99,0) — les deux
franchiraient un seuil conventionnel de 95 %.

### Test 2 — grands effectifs (k≈18)

| Cas | k | cohésion observée | percentile | z |
|---|---|---|---|---|
| Bruit (20 répétitions) | 18 | — | moyenne 4,9 %, max 25,7 % | moyenne -1,73 |
| Hétérogénéité | 18 | 1,000 | 100,0 | 14,83 |

**À ce niveau, la comparaison au modèle nul fonctionne parfaitement** :
aucune des 20 répétitions de bruit ne dépasse 95 % (0 % de faux
positifs), tandis que l'hétérogénéité atteint un percentile de 100 %
avec un z énorme (14,8) — séparation nette et large.

### Localisation de la frontière de fiabilité

| Taille effective du sous-groupe dissident (k moyen) | Taux de faux positifs (percentile ≥ 95 %) sur 15 répétitions |
|---|---|
| ≈5,5 | 7,1 % |
| ≈6,9 | 6,7 % |
| ≈9,7 | **0,0 %** |
| ≈11,7 | **0,0 %** |

**La comparaison au modèle nul devient fiable (taux de faux positifs
conforme au seuil nominal) à partir d'un sous-groupe dissident d'environ
9-10 membres**, et reste mesurablement peu fiable en-dessous (~7 % à
k≈5,5-6,9, au-dessus du taux nominal de 5 %).

## 4. Réponse réelle aux trois décisions demandées

```text
1. règle de sélection du sous-groupe
   -> RÉSOLUE : Règle R1 (vote majoritaire sur un vecteur de traits déjà
      gelé, jamais recherché) -- utilisée partout, sans exception

2. seuil de contradiction nécessaire
   -> REFORMULÉE : pas un seuil de FRACTION, mais un plancher sur le
      NOMBRE ABSOLU de dissidents (~9-10), condition pour que le
      diagnostic structurel soit fiable du tout -- une fraction fixe
      (ex. 10 %) donne un nombre de dissidents différent selon la
      taille du groupe, donc une fraction seule ne suffit pas

3. seuil de cohésion distinguant bruit et vraie sous-classe
   -> REFORMULÉE : pas un seuil fixe sur la valeur de cohésion (prouvé
      dangereux, Sec. 2) -- mais une comparaison à un modèle nul
      (percentile/z), qui fonctionne de façon fiable UNE FOIS le
      plancher de la décision 2 atteint
```

**Aucune des deux dernières décisions n'est un nombre isolé** : ce sont
des propriétés de conception (modèle nul + plancher d'effectif), pas des
seuils à choisir arbitrairement — exactement ce que le porteur du projet
demandait d'éviter.

## 5. Conséquence pour l'architecture de Gate H

Gate H devrait être restructurée pour ÉCHOUER PROPREMENT
(`INSUFFICIENT_STRUCTURAL_INFORMATION`, jamais un faux verdict) quand le
sous-groupe dissident est trop petit pour permettre un diagnostic
fiable, et sinon comparer sa cohésion à un modèle nul plutôt qu'à un
seuil fixe — **la même architecture statistique que Gate I**
(statistique de groupe contre modèle nul), pas une mécanique différente.
C'est une proposition d'architecture issue de cette calibration, pas
encore endossée ni intégrée au protocole.

## 6. Ce que cette campagne établit, et ce qu'elle n'établit pas

**Établi, par exécution directe** :
- La règle de partition R1 est bien spécifiée, déterministe, sans
  recherche — la décision 1 est résolue.
- Un seuil FIXE sur la cohésion de minorité est démontré dangereux
  (chevauchement exact bruit/hétérogénéité sur la grille testée), pas
  seulement risqué en théorie.
- Une comparaison à un modèle nul RÉSOUT le problème, mais seulement
  au-delà d'un plancher d'effectif dissident empiriquement localisé
  entre k≈7 et k≈10.

**Non établi, délibérément** :
- La valeur EXACTE du plancher d'effectif (quelque part entre 7 et 10,
  pas plus précisément localisée ici).
- Le protocole exact du modèle nul pour ce sous-test (celui utilisé ici
  ré-échantillonne dans le pool COMPLET du corpus — pourrait devoir être
  affiné).
- Si `Cohesion_B` reste la bonne statistique pour ce sous-test
  spécifiquement (seule testée ici).
- Le modèle de bruit synthétique (trois modes discrets) reste une
  construction ad hoc, pas calibrée sur un corpus réel — la conclusion
  qualitative (petits effectifs = risque de coïncidence) est un principe
  statistique général, probablement robuste au choix exact du modèle de
  bruit, mais pas vérifié au-delà de ce modèle précis.

## 7. Prochaine étape

Ni Gate H ni sa version raffinée ne peuvent être gelées maintenant.
L'architecture proposée (modèle nul + plancher d'effectif ~9-10) est une
avancée réelle par rapport aux campagnes 1-3, mais nécessite encore :
localiser précisément le plancher, choisir/valider le protocole de
modèle nul pour ce sous-test, et vérifier la robustesse sur d'autres
modèles de bruit avant tout gel. Comme pour les campagnes précédentes,
la décision de poursuivre ou de geler revient explicitement au porteur
du projet.
