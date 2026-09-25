# GEL n°2 — P1-TEXT-STRUCT-A — note de constitution (2026-09-25)

## Décision du porteur du projet

Le porteur du projet a décidé de **considérer les annotations fournies comme conformes au
protocole et adéquates**, et de passer à l'étape suivante.

## Constats factuels, consignés tels quels

Ils ne sont pas interprétés : ils accompagnent la décision.

- Les deux annotations remises, `annotation_A.tsv` (Soumaya) et `annotation_B.tsv`
  (Karim), sont converties mécaniquement depuis les classeurs reçus, dont les empreintes
  figurent dans `RECEPTION_HELDOUT.sha256`. Elles sont **identiques octet pour octet**,
  avec la même empreinte, `c5b49b09…dc249`. C'est vrai de la colonne structure (40/40)
  comme de la colonne statut (40/40, dont les mêmes 10 « doute »). Seuls les commentaires
  diffèrent, sur 22 lignes sur 40.
- Les métadonnées des deux classeurs indiquent le même auteur et le même dernier
  modificateur (« Bacem Ben Soui »), avec des modifications à 15:54 et 16:00 UTC le
  2026-09-25.
- Les classeurs comportaient une colonne « Catégorie » visible des annotateurs.
- **L'indépendance des deux annotations n'est donc pas démontrée par les données.**
  L'accord entre annotateurs (1,00) ne mesure pas un accord entre jugements
  indépendants.
- Aucun désaccord ne restait à adjuger (GEL n°1-ter, T3) :
  `gold_adjudicated.tsv` est la copie de l'annotation commune.
- Écarts d'ordre, déjà consignés :
  - les fichiers ont été remis au développeur avant le GEL n°2 ;
  - les annotateurs sont deux tiers, au lieu du schéma « porteur = A, tiers = B »
    prévu par GEL n°1-ter.
- **La passerelle A était figée au GEL n°3 (`d2dd51a`) avant toute remise.** Elle n'a
  pas été modifiée, et elle n'a jamais été exécutée sur ces phrases avant ce GEL n°2.

## Conséquence pour l'interprétation

Les résultats de l'exécution unique seront rapportés **par rapport à une référence
issue d'une annotation commune**, et non d'une double annotation indépendante. Les
barrières de sûreté et les mesures descriptives restent calculées selon le protocole
figé.
