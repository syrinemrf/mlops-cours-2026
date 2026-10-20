# Brouillon de PR M1 — résultats locaux validés, intégration à préparer

Titre proposé : `lab/m1-versioning : pipeline DVC, registre et Feast pour IBM HR`.
Base future main, branche future lab/m1-versioning. **PR non ouverte.**

Le socle M1 adapte le contrat du cours à IBM HR Attrition et rend reproductibles
l’ingestion, la préparation, l’entraînement A et l’évaluation par DVC. Le modèle
DVC est désormais celui promu dans scoring-model ; Feast fournit les27 features
offline et online.

## Preuves réelles de la branche personnelle

- 18/18 contrôles officiels,85 tests réussis, lint validé ; rapports dans reports/m1.
- Split80/20 stratifié seed 42 ; ID et sensibles hors prédicteurs ; version1/hash
  source Kaggle ; source 35 colonnes, export 32,27 features. Données inchangées.
- Les 22 configurations historiques sont conservées, sans relance de la grille.
  Le poids balanced des neuf RF est explicite, indépendant des defaults DVC.
- LR DVC C=1 sans poids, run ef2d3f85ebe3432f9172275c34bbd6ac,
  ROC AUC 0,8368507193, seuil 0,5. Gate 0,70 inchangée et passée.
- Nouvelle v4 champion, v3 challenger préservée, v1/v2 conservées ; idempotence,
  rejet réel de Dummy, signature/paramètres/métriques et294 probabilités distant/local vérifiés.
- §8.5 réalisé dans un clone : modification d’un seul paramètre, diffs et retour
  train/evaluate au cache ; §10.3 rejoue les quatre stages, données et probabilités
  identiques, métriques inchangées. Même cluster et Python existant réutilisés.
- DVC synchronisé, trois objets nouveaux poussés et dix objets S3 vérifiés.
  Feast offline/online conforme, horodatage technique synthétique.
- 29 runs FINISHED :25 antérieurs +4 fits de reproduction/référence clairement taggés.

## Points restant avant fusion/remise

- [ ] Replay indépendant d’Aziz sur son propre cluster (§10.4), preuves réelles.
- [ ] Référence minimale de l’accord dataset par courriel consignée ; aucune issue inventée.
- [ ] Comparaison et intégration du travail réel d’Aziz ; SHA final d’intégration validé.
- [ ] Capture réelle de make check-m1 entièrement vert sur le commit publié.
- [ ] Revue réelle de @MohamedAzizKouch sur le dernier commit de la PR.
- [ ] Autorisation de fusion de Syrine ; aucune fusion automatique.

## Correctifs et limites à relire

Le test initial spécifique à personal_status utilise une fixture générique
conservant la vérification des sensibles hors features ; aucun skip ajouté.
Le checker M1 a seulement changé de mode644→755 pendant la phase antérieure :
contenu et critères du cours inchangés.

Les archives skops locales/distantes ont des hashes différents ; payloads des
tableaux et schéma normalisé sont identiques. IDs d’objets et timestamps ZIP sont
distingués des paramètres/prédictions, sans prétendre à une identité binaire.

Les candidats A ont été choisis après comparaison répétée sur le test du cours :
aucune performance finale indépendante ni supériorité statistique revendiquée.
Coûts 1:1 neutres expérimentaux ; gate 0,70 provisoire, pas de coût RH démontré.
A/B1/B2 restent distincts, sans reproduction Jia ni innovation XP-Cube démontrée.
Données/modèles/credentials/venv/bases locales exclus de Git ; uv.lock inchangé.

## Vérification

Suivre NOTES pour le cluster existant, l’environnement verrouillé, les credentials
locaux et Feast. Vérifier make test, make lint, dvc status, dvc status --cloud,
la filiation champion/DVC, puis make check-m1 sur le SHA retenu.
Utiliser les IDs du serveur concerné, pas ceux d’un autre membre.

Voir [les résultats d’alignement](alignment-validation.md),
[l’audit initial historique](pre-publication-audit.md) et
[la checklist de revue/publication](binome-review-publication.md).
