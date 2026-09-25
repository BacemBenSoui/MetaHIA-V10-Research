# P4-U.2 — Clôture de la branche C9 : C9-2 et C9-C (2026-09-24)

Pré-enregistrements : `PREREGISTRATION_C9_2.md` et `PREREGISTRATION_C9_C.md`, gelés
ensemble avant tout run (sha256 `13f52c7c…035f6` et `391311…7f7`), plus l'addendum de
faisabilité `ADDENDUM_C9C_M_FEASIBILITY.md` (m passe de {10, 25} à {5, 12}, rédigé avant
tout run C9-C et sans aucune statistique vue). **Production inchangée. Aucune
modification d'architecture.** Même réserve de reconstruction du harnais que pour
C8.1 et C9-1.

**Statut : BRANCHE C9 CLOSE, diagnostic suffisant.**

## 1. C9-2 — T′ = max sur les signatures non triviales, même null que C9-1

Statut méthodologique : **hypothèse générée par C9-1**, exécutée de façon prospective
sur des graines neuves, **non présentée comme une validation indépendante**.

Spécificité (critères P1/P2, Bonferroni 0,0125) :

| config | T′ rejets / α_eff | binomial | KS | χ² | verdict | T apparié |
|---|---|---|---|---|---|---|
| A0 | 6/100 / 4,7 % | 0,48 | 0,42 | 0,48 | PASS | 1/100 |
| A1 | 4/100 / 4,1 % | 1,00 | 0,54 | 0,38 | PASS | 1/100 |
| A2 | 3/100 / 4,2 % | 0,80 | 0,47 | **0,011** | **FAIL (P2)**, enregistré, non répliqué | 8/100 |
| SBM | 3/100 / 4,6 % | 0,63 | 0,24 | 0,90 | **PASS** | **18/100, PIT non uniforme (p < 10⁻³)** |
| A-bis | 6/100 | — | — | — | non jugeable (95/100 tronqués) | 5/100 |

Détection :

| config | T′ | T | arg-max de T′ | part d'arêtes de chaîne |
|---|---|---|---|---|
| B2 (8) | 100/100 | 5/100 | `(1,1,0,{F,FF})` 100/100 | 0,94 |
| B1 (15) | 100/100 | 2/100 | idem | 0,97 |
| B3 (25) | 100/100 | 6/100 | idem | 0,98 |

McNemar T contre T′ : p ≈ 10⁻²⁹ sur B1–B3. Le test de tendance est dégénéré (plafond
à 100 %). Lecture, selon la règle d'interprétation pré-enregistrée : preuve
**descriptive** d'une meilleure focalisation. T′ élimine la domination des impasses et
la fuite SBM, qui passait par les impasses et les doublons. Ce n'est **pas** une preuve
de spécificité relationnelle.

## 2. C9-C — signal relationnel découplé des degrés, des doublons et de la troncature

Fond : digraphe simple uniforme. Motif : FFL (A→B, B→C, A→C) injecté par échanges à
degrés invariants. Null : chaîne de Markov simple à degrés préservés (échanges et
inversions de triangles).

Contrôles automatiques (degrés, doublons, boucles, troncature, sur chaque graphe et
chaque réplicat) : **0 invalidation**, sauf 1 échec d'injection sur S12 (consigné, non
remplacé, 99 graines valides).

Mélange : T′ stable, écart de moins de 3 % entre 30·E et 100·E sur 5/5 graines. Le
nombre de FFL dépasse le seuil de 5 % sur 2 graines sur 5 (7,9 % et 11,0 %).
**Sous-mélange partiel** : le null est conservateur, rapporté selon la règle.

Manipulation : FFL observés supérieurs à la moyenne nulle sur 100 % des graines avec
motifs (M12 : 15,3 contre 3,4 ; S12 : 12,9 contre 1,0). **Injection efficace.**

Calibration M0 : T 5/100 (α_eff 4,1 %, p = 0,61) ; T′ 5/100 (α_eff 4,4 %, p = 0,63).
PIT uniformes. **PASS.**

Détection :

| config | T′ | Wilson | binom. > α_eff | T | excès de motif obs / null (descriptif, biaisé vers le haut) | signatures du motif | part plantée de l'arg-max de T′ |
|---|---|---|---|---|---|---|---|
| M5 | 4/100 | [1,6 ; 9,8] | 0,64 | 3/100 | 24,5 / 11,5 | 14 | 0,18 |
| **M12** | **4/100** | [1,6 ; 9,8] | **0,59** | 4/100 | 53,4 / 23,5 | 32 | 0,27 |
| S5 | 5/100 | [2,2 ; 11,2] | 0,46 | 6/100 | 26,0 / 12,8 | 14 | 0,11 |
| **S12** | **12/99** | [7,1 ; 20,0] | **0,003** | 2/99 | 56,8 / 27,7 | 31 | 0,30 |

**Verdict pré-enregistré : l'hypothèse « le motif est capté par les signatures » est
REJETÉE.** Elle exigeait une détection dans les configurations m = 12 : M12 échoue,
S12 ne passe que faiblement. C'est l'**issue (ii) déclarée d'avance** : la manipulation
réussit et le motif est en excès, mais cet excès est **dispersé sur environ 31
signatures distinctes d'environ 1,7 arête chacune**. Plongée dans un fond connecté,
chaque arête du motif reçoit en plus les chemins de son voisinage. L'égalité exacte
des signatures ne rassemble jamais les arêtes du motif, et aucun maximum de bucket, T
ou T′, ne peut les voir. Le faible signal de S12 est cohérent avec cette lecture : en
régime plus clairsemé, les voisinages sont plus pauvres et les signatures se dispersent
moins.

## 3. Chaîne expérimentale complète

```text
C8.1   null uniforme          T « détecte » → en fait les degrés (A-bis 88 %)
C9-1   null à degrés           T aveugle : max saturé par le bucket d'impasses
C9-2   T′ non triviale         motif ISOLÉ (nœuds dédiés) : 100 % ; SBM calibré
C9-C   motif ENCASTRÉ          T′ ~ α sauf S12 (12 %) : excès dispersé
```

**Ce que P4-U.2 (signature exacte + `group_by_signature` + support maximal) mesure
réellement** : la répétition d'une **topologie locale identique à profondeur 3**. Il
détecte un motif quand les arêtes qui le portent ont des voisinages identiques, c'est-à-
dire des motifs isolés. Il ne détecte **pas** une régularité relationnelle encastrée
dans un contexte hétérogène. La limite ne se situe ni dans le null (corrigé par C9-1),
ni dans la statistique (corrigée par C9-2), mais dans la **génération de candidats par
égalité exacte de signature**.

## 4. Conséquences pour la road map (aucune décision d'architecture prise ici)

1. **Ne pas intégrer T′ dans Gate I** comme statistique de découverte relationnelle :
   il ne satisfait pas le test discriminant C9-C.
2. **V1–V4 restent gelés.** Un benchmark construit sur ce mécanisme mesurerait
   l'identité topologique locale, pas la découverte de relations.
3. Toute suite exigerait un **changement de génération de candidats** (regroupement par
   similarité ou par motif, et non par égalité exacte) : c'est une nouvelle conception,
   pas un raffinement de C9.
4. **R1 (`MAX_PATHS`)** : ticket d'ingénierie séparé (`TICKET_P4U2_R1_MAX_PATHS.md`),
   sans campagne.

## 5. Garde-fou road map (adopté par le porteur du projet)

> Après C9-2 et C9-C, aucune nouvelle expérience de caractérisation de cette branche
> ne doit être lancée sans démontrer qu'elle change une décision de la road map.

La branche C9 est **close**. Les résultats FAIL enregistrés (C9-A2/N3 en C9-1, A2/P2 en
C9-2) restent notés tels quels.

## Fichiers

`c9_2_nontrivial.py`, `analyze_c92.py`, `c9c_decoupled.py`, `raw_C92*.json`,
`raw_C9C-*.json`, `c9c_mixcheck.json`, `summary_c92.json`.
