# P4-U.2 — C9-C : signal relationnel découplé des degrés et des doublons — pré-enregistrement

Rédigé et gelé AVANT tout run de C9-2 et de C9-C, 2026-09-24. Aucun résultat de C9-2 ne
peut modifier ces paramètres. Base : MetaHIA-V10-Research `2631252`, production
inchangée.

## Objectif
Tester si une régularité relationnelle reste détectable quand elle n'est expliquée ni
par (1) les degrés entrants/sortants, ni par (2) les arêtes répétées, ni par (3) la
troncature.

## Graphe de fond
Digraphe SIMPLE uniforme : N nœuds, E arêtes distinctes, sans boucle ni doublon (tirage
de paires ordonnées distinctes sans remise).

## Motif
Boucle d'anticipation (feed-forward loop, FFL) : A → B, B → C, A → C.

## Injection à degrés invariants (procédure gelée)
Pour k = 1..m : tirer aléatoirement un chemin A → B → C existant (A, B, C distincts,
A → C absent, aucun des trois nœuds déjà utilisé par un motif planté), puis une arête
A → x (x ∉ {B, C}) et une arête y → C (y ∉ {A, B}), non plantées, avec y ≠ x et
y → x absent. Remplacer {A → x, y → C} par {A → C, y → x}.
Invariants : mêmes nœuds, même nombre d'arêtes, chaque degré sortant et entrant
identique, aucune boucle, aucun doublon. Les arêtes des motifs plantés ne sont jamais
retirées par les injections suivantes. Plafond de 10 000 tentatives par motif ; un
échec est consigné et la graine est invalidée (jamais remplacée silencieusement).

## Null (simple, à degrés préservés)
Chaîne de Markov depuis le graphe observé, avec deux mouvements :
(a) échange : A → B, C → D ↦ A → D, C → B, si A ≠ D, C ≠ B et les deux nouvelles arêtes
    sont absentes ;
(b) inversion d'un triangle orienté A → B → C → A ↦ A → C → B → A, si les inversées
    sont absentes.
Le mouvement (b) est nécessaire à l'irréductibilité sur les digraphes simples. Chaque
réplicat repart de l'observé avec sa propre graine : 100·E tentatives de mouvement,
dont 10 % de tentatives de type (b).
Contrôle de mélange (gelé) : sur les 5 premières graines de C9C-M0, la moyenne nulle de
T′ et du nombre de FFL, à 30·E et à 100·E tentatives, doit différer de moins de 5 %.
Sinon, rapporté comme sous-mélange, avec un null conservateur.

## Contrôles automatiques (chaque graphe observé et chaque réplicat, avant la statistique)
degree_in(observé) == degree_in(null) ; degree_out(observé) == degree_out(null) ;
nombre d'arêtes constant ; duplicate_count == 0 ; self_loop_count == 0 ;
truncation_count == 0 (aucune source à ≥ MAX_PATHS chemins).
Tout écart invalide la graine concernée (consigné, compté, jamais remplacé).

## Configurations (100 graines neuves, N_null = 200)
- C9C-M0 : N = 100, E = 150, m = 0 (calibration exacte : test d'implémentation du null)
- C9C-M10 : N = 100, E = 150, m = 10
- C9C-M25 : N = 100, E = 150, m = 25
- C9C-S10 : N = 150, E = 150, m = 10 (plus clairsemé : voisinage des motifs plus pauvre)
- C9C-S25 : N = 150, E = 150, m = 25

## Statistiques (toutes calculées, sélection globale sur le null de chacune)
1. T = max_s |G_s| ; 2. T′ (définition C9-2) ; 3. signature et famille arg-max ;
4. taille de la famille non triviale (nombre d'arêtes à signature non triviale) ;
5. excès de motif, DESCRIPTIF : pour l'ensemble S_m des signatures portées par les
   arêtes plantées, Σ_{s ∈ S_m} |G_s| observé contre null ;
6. contrôle de manipulation : nombre de FFL (triades A → B, B → C, A → C) observé
   contre null.

## Critères (gelés)
Contrôle : 0 graine invalidée attendue ; toute invalidation est rapportée.
Manipulation (m > 0) : FFL observé > moyenne nulle pour ≥ 95 % des graines valides ;
sinon le motif n'a pas été injecté efficacement et la config n'est pas interprétée.
Calibration (M0 ; T et T′, Bonferroni 0,05/2 = 0,025) : binomial bilatéral contre
α_eff, p ≥ 0,025 ; KS et χ² sur le PIT, p ≥ 0,025.
Détection (M10, M25, S10, S25), pour T′ puis T — mesures, sans seuil de puissance :
taux de rejet, Wilson, binomial unilatéral > α_eff (seuil 0,05/4 = 0,0125) ;
attribution. Hypothèse falsifiable : « le motif est capté par les signatures » ⇔ le
taux de rejet de T′ excède significativement α_eff (p < 0,0125) dans au moins les
configurations m = 25. Un rejet de cette hypothèse est un résultat valide, pas un échec
du protocole.

## Issues possibles déclarées à l'avance
(i) T′ détecte → la famille non triviale capte une régularité non expliquée par degrés et
doublons ; (ii) T′ ne détecte pas, mais la manipulation est réussie et l'excès de motif
est dispersé dans de nombreux buckets → limite de GRANULARITÉ de l'égalité exacte de
signature, pas absence de signal ; (iii) manipulation ratée → config non interprétée.
L'issue (ii) est plausible a priori : plongé dans un fond connecté, un motif ne produit
pas de signature unique.
