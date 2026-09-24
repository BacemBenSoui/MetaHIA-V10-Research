# P4-U.2 — Calibration jetable, campagne 5 : validité du modèle nul de Gate H sous la procédure complète de sélection R1 (2026-09-24)

Répond à l'unique question méthodologique posée par le porteur du projet
après lecture de la campagne 4 (`P4U2_Calibration_Campaign4_2026-09-24.md`,
commit `32bb49d`) : le modèle nul utilisé dans cette campagne
ré-échantillonnait directement un sous-ensemble de taille `k` depuis un
pool, sans reproduire la procédure RÉELLE de sélection —
`corpus nul → mêmes traits gelés → même règle R1 → sélection
majorité/dissident → cohésion du dissident`. Si la procédure réelle
bénéficie d'une étape de sélection non reproduite dans le null, le taux
de faux positifs peut être sous-estimé. **Ce document construit et teste
directement le modèle nul corrigé**, plutôt que de supposer que la
correction fonctionne.

```text
32bb49d (campagne 4) -- null raccourci, risque de sous-estimation signalé
        ↓
campagne 5                            <- CE DOCUMENT
   null corrigé = reproduire TOUTE la procédure sous le null,
   pas seulement ré-échantillonner un sous-ensemble de taille k
        ↓
gel numérique (toujours pas fait)
```

## 1. Le défaut du modèle nul de la campagne 4

La campagne 4 ré-échantillonnait `k` éléments directement depuis
`all_sigs` du corpus jetable — un pool qui, par construction des corpus
`corpus_natural_noise`/`corpus_manifest_mix`, mélangeait les arêtes
« membres » du groupe candidat ET leurs arêtes de continuation
structurelle (jamais elles-mêmes des candidates réelles). Le null ne
reproduisait donc ni la vraie population de candidats éligibles, ni la
procédure de sélection R1 elle-même — il comparait la cohésion observée
à un ensemble de dissidents déjà pré-dimensionnés à la taille `k`, pas au
résultat d'une VRAIE application de R1 sur un groupe nul.

## 2. Modèle nul corrigé, construit et testé ici

```text
pool de fond RÉALISTE ET DIVERSIFIÉ (trois classes structurelles
    réellement différentes, dans des proportions qui ne favorisent
    aucune classe a priori : impasse (0,0), un saut (1,0), deux sauts
    (1,1) -- les seules classes atteignables par le vecteur de traits,
    puisqu'un chemin de profondeur 3 exige toujours un préfixe de
    profondeur 2)
        ↓
tirer un groupe nul de MÊME TAILLE que le groupe réel
        ↓
mêmes traits gelés (protocole Sec. 7)
        ↓
MÊME règle R1 (vote majoritaire, déterministe, jamais recherché)
        ↓
partition majorité/dissident ÉMERGEANT NATURELLEMENT de ce tirage nul
        ↓
cohésion de CE dissident émergent (si ≥2 membres, sinon réplicat écarté)
```

Pool de fond utilisé : 270 arêtes de type « membre » (80 impasses, 150 à
un saut, 40 à deux sauts) — aucune classe ne domine au point de fixer
d'avance quelle sera la majorité d'un tirage nul donné ; R1 doit
réellement s'exécuter sur chaque réplicat pour le savoir.

## 3. Balayage k ∈ {7, 8, 9, 10, 12, 15}, 20 graines par niveau, bruit
   naturel vs hétérogénéité manifeste

| k cible | Bruit — n utilisable | Bruit — percentile moyen | Bruit — percentile max | Bruit — taux de faux positifs (≥95 %) | Hétérogénéité — percentile |
|---|---|---|---|---|---|
| 7 | 20/20 | 19,0 | 100,0 | 5,0 % | **100,0** |
| 8 | 20/20 | 13,5 | 77,5 | 0,0 % | **100,0** |
| 9 | 20/20 | 12,5 | 88,5 | 0,0 % | **100,0** |
| 10 | 20/20 | 12,5 | 88,5 | 0,0 % | **100,0** |
| 12 | 20/20 | 12,7 | 95,0 | 10,0 % | **100,0** |
| 15 | 20/20 | 4,8 | 95,0 | 5,0 % | **100,0** |

## 4. Résultat — révise directement le résultat de la campagne 4

**Sous le modèle nul CORRIGÉ, le taux de faux positifs reste proche du
niveau nominal de 5 % sur TOUTE la plage testée (k=7 à k=15)** — 0 %,
5 % ou 10 % selon la cellule, sans tendance monotone claire, ce qui est
cohérent avec un simple bruit d'échantillonnage à 20 graines autour
d'un taux nominal de 5 % (l'intervalle attendu à cette taille
d'échantillon couvre grossièrement 0-15 %). **L'hétérogénéité manifeste
reste séparée de façon nette et parfaite à chaque niveau de k testé
(percentile 100,0 exactement, sans exception).**

**Ceci révise directement la recommandation de la campagne 4** (plancher
`k_min ≈ 9-10` nécessaire) : ce plancher provenait très probablement d'un
défaut du modèle nul RACCOURCI de la campagne 4 (pool mélangeant arêtes
membres et arêtes de continuation), pas d'une propriété fondamentale des
petits effectifs de dissidents. Une fois la procédure de sélection
correctement reproduite sous le null, contre un pool de fond réaliste,
**aucune dégradation systématique n'est observée entre k=7 et k=15.**

Réserve honnête, explicitement non résolue ici : la plage `k < 7`
(là où la campagne 4 avait trouvé sa coïncidence la plus nette, à
k≈5) n'a pas été retestée sous ce modèle nul corrigé — on ne peut donc
pas encore affirmer que la correction résout aussi ce cas le plus
extrême, seulement qu'elle résout la plage 7-15 explicitement demandée.
20 graines par cellule restent insuffisantes pour caractériser
précisément un taux proche de 5 % (le porteur du projet l'a lui-même
noté à l'avance) — les taux de 0 %/5 %/10 % rapportés ici sont indicatifs,
pas une calibration fine.

## 5. Réponse aux trois éléments à fixer simultanément

```text
1. procédure exacte du null Gate H
   -> RÉSOLUE : reproduire le pipeline complet (pool réaliste diversifié
      -> tirage de même taille -> mêmes traits -> même règle R1 ->
      dissident émergent -> sa cohésion), jamais un raccourci qui ne
      ré-échantillonne que la taille du dissident directement

2. floor k_min
   -> RÉVISÉ : aucune dégradation systématique trouvée entre k=7 et k=15
      sous le null corrigé -- le plancher ≈9-10 de la campagne 4 n'est
      pas confirmé, probablement un artefact du null raccourci. k<7 reste
      non testé sous cette procédure corrigée.

3. seuil statistique de Gate H
   -> PROPOSÉ, pas gelé : percentile ≥ 95 % (la même convention que
      Gate I), avec une marge de sécurité possible à 97,5-99 % étant
      donné que l'hétérogénéité atteint systématiquement 100,0 -- un
      seuil plus strict ne coûterait aucune sensibilité détectée sur
      cette grille tout en réduisant encore le risque de faux positif
      résiduel à 20 graines
```

## 6. Ce que cette campagne établit, et ce qu'elle n'établit pas

**Établi, par exécution directe** :
- Le modèle nul RACCOURCI de la campagne 4 souffrait bien du défaut
  méthodologique signalé (pool non représentatif de la vraie population
  de candidats, procédure de sélection non reproduite) — confirmé en
  observant que le modèle nul CORRIGÉ donne un tableau qualitativement
  différent (pas de plancher net) sur la même plage de k.
- Le modèle nul corrigé donne un taux de faux positifs proche du niveau
  nominal sur k=7 à k=15, avec une séparation parfaite et systématique
  de l'hétérogénéité manifeste à chaque niveau.

**Non établi, délibérément** :
- Le comportement du null corrigé pour `k < 7` (la plage la plus à
  risque trouvée en campagne 4) — non retesté ici.
- Un taux de faux positifs précisément calibré (20 graines insuffisantes,
  reconnu à l'avance par le porteur du projet).
- La composition exacte et les proportions du pool de fond réaliste
  restent un choix de conception (80/150/40 ici) — pas validées contre
  un corpus réel.
- Le seuil statistique de Gate H (95 % proposé) n'est pas gelé.

## 7. Prochaine étape

Cette campagne répond à la question centrale posée (validité du null
sous la procédure complète) et révise à la baisse le risque perçu en
campagne 4 (pas de plancher net entre 7 et 15). Avant tout gel :
retester `k < 7` sous ce même null corrigé pour savoir si la coïncidence
originale de la campagne 4 est elle aussi résolue ou si un plancher plus
bas (peut-être 5-6) suffit ; augmenter le nombre de graines pour une
calibration fine du taux de faux positifs si un seuil précis (pas
seulement « environ 95 % ») doit être gelé. Comme pour les campagnes
précédentes, la décision de poursuivre ou de geler revient explicitement
au porteur du projet.
