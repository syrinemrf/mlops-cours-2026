Cette PR brouillon rassemble le pipeline IBM HR reproductible de Syrine et les
analyses train-only/ADR d’Aziz, adaptées sans modifier le champion pédagogique.
La validation personnelle antérieure est complétée par des contrôles propres à
cette intégration. Aucun merge global d’Aziz ; ses paramètres incompatibles restent
sur sa branche et sont documentés comme variantes.

## Contributions et provenance

- Syrine : ingestion Kaggle v1, contrat27features, préparation80/20 stratifiée42,
  quatre stages DVC, grille22runs, registre/Feast et preuves de reproductibilité ;
  adaptations d’intégration et tests avec assistance Codex.
- Aziz : sensibilité104cf5c et ADRea37452/39596be repris par cherry-picks -x,
  auteur conservé ; CV7f9d1ed extraite dans20bd582 avec auteur source conservé,
  puis adaptée séparément dans2fdc4f5. ADR0002/0003 renumérotés et contextualisés.
- Modules indépendants cross_validation/sensitivity : cinq plis train-only,
  preprocessing appris par pli, ROC AUC/AP et OOF partagées en cinq fits séquentiels.
  Aucun nouveau run MLflow, modèle sauvegardé ou seuil opérationnel modifié.

## Contrat et résultats

Conservés : Kaggle v1,27 prédicteurs, sensibles/ID hors modèle, split 80/20seed 42,
roc_auc/gate 0,70, trois groupes d’âge, LR C=1 sans poids, seuil 0,5, quatre stages et
Feast. AP/gate 0,32 et âge40 en deux groupes restent des alternatives proposées.

- 112 tests réussis ; un warning Feast/NumPy connu ; make lint réussi.
- make check-m1 réellement exécuté :18/18, code 0.
- DVC local à jour/cloud synchronisé ; repro ignore les quatre stages ; lock,
  données et modèle de référence préservés ;22 runs historiques inchangés.
- Registre :4versions, champion v4 run ef2d3f85ebe3432f9172275c34bbd6ac,
  challenger v3 run 139ae364aa6e4166b2bd19ef533f48e7, Dummy v2 failed.
  Signature et294probabilités local/distant identiques ;29 runs FINISHED.
- Champion test pédagogique : ROC AUC 0,8368507193, AP 0,6470361871, recall 0,425532,
  precision 0,714286, F1 0,533333, coût expérimental 35. Aucun nouveau champion.
- Nouvelle CV train : ROC AUC 0,854679982±0,029784770, AP 0,672947514±0,053510568 ;
  dispersion sur cinq plis, pas IC95%. Au seuil 0,5 : FP28/FN101, coût129 en OOF.
  Le scénario1:1 optimisé donne seuil 0,534894388 environ/coût128 sur ces mêmes OOF ;
  diagnostic optimiste, aucun seuil promu. Les valeurs exactes sont dans les preuves.
- Feast offline/online reconstruits et vérifiés dans le worktree isolé.

## Preuves à relire

[Rapport final](final-integration.md),
[tests](tests.log), [lint](lint.log),
[checker18/18](check-m1.log),
[diagnostics CV/OOF](train-diagnostics.json),
[préservation](preservation.json),
[registre](registry.json),
[Feast](feast.json), ADR0002/0003/0004 et journal.
Les rapports antérieurs et incidents initiaux sont conservés/contextualisés.

## Limites et points bloquant la fusion

- [ ] Revue humaine réelle d’Aziz sur le dernier SHA ; aucune approbation présumée.
- [ ] Reproduction indépendante §10.4 du contrat commun sur le cluster d’Aziz,
      ses vrais hashes/métriques/run IDs/registre/Feast et vérifications.
- [ ] Référence/date du courriel d’accord dataset à consigner.
- [ ] Capture réelle des18contrôles et vérification de la remise du professeur.
- [ ] Autorisation distincte de fusion puis décision du tag j0.

Scores de test exploratoires après comparaisons répétées ; ils ne sont pas une
estimation finale indépendante. Coûts RH hypothétiques et coût de seuil optimiste
sur les mêmes OOF ; pas de supériorité statistique, causalité ou innovation démontrée.
Jeu synthétique ; snapshot Feast technique. Aucun changement Jia B1/B2, XP-Cube,
dépendances verrouillées, branche personnelle ou infrastructure persistante.
Aucun nouveau grid search, promotion, M2, merge ou tag.
