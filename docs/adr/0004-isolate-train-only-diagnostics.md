# ADR-0004 — Isoler les diagnostics CV et seuil du pipeline M1

- **Statut :** mis en œuvre sur autorisation de Syrine ; revue GitHub du binôme en attente
- **Date :** 2026-10-27
- **Auteur(s) :** @syrinemrf (intégration), depuis les contributions de @MohamedAzizKouch
- **Relu par :** revue humaine GitHub à effectuer
- **Périmètre :** socle Lab M1, protocole pédagogique A
- **Liens :** src/cross_validation.py, src/sensitivity.py, ADR-0002/0003,
  reports/m1/integration/final-integration.md

## Contexte

Les branches personnelles divergent sur le contrat, le typage ordinal, la gate,
le modèle et l’identifiant Feast. Le pipeline de référence de Syrine est reproduit.
Aziz apporte une CV train-only et une analyse OOF utiles sans remplacer ce pipeline.
Le test pédagogique a déjà été consulté à répétition : sa performance reste exploratoire.

## Options envisagées

| Option | Avantages | Inconvénients |
|---|---|---|
| Fusion globale / CV dans train.py | Intégration immédiate | Contrats incompatibles, invalidation DVC et nouveau modèle |
| Modules de diagnostic indépendants | Préserve modèle, hashes, registre ; ajoute CV/OOF | Diagnostics hors du DAG DVC, provenance à tracer explicitement |
| Ne pas intégrer les analyses | Aucun changement | Perte des contributions complémentaires |

## Décision

Ajouter les modules indépendants, cinq plis stratifiés seed 42 sur train seulement.
Chaque pli ajuste un clone du Pipeline complet ; une passe produit ROC-AUC, AP et
OOF, en cinq fits séquentiels avec BLAS limité à un thread. Moyenne et écart-type
(ddof=0) ne constituent pas un intervalle de confiance. Aucun test utilisé pour choisir.

Conserver Kaggle v1, 27 prédicteurs, audit sensible hors modèle, split 80/20 seed 42,
roc_auc/gate 0,70, LR C=1 sans poids, seuil 0,5, quatre stages DVC et Feast actuels.
Les seuils OOF pour coûts FN/FP hypothétiques1,2,3,5,10 restent diagnostiques ;
les coûts optimisés/évalués sur les mêmes OOF sont optimistes. Aucune calibration.
AP/0,32 et deux groupes d’âge restent des variantes proposées, pas des choix communs.

## Conséquences

- **Positives :** attribution Aziz conservée, analyses reproductibles, aucun refit
  du champion ni modification des anciens runs et alias.
- **Dette :** OOF conservées seulement en mémoire ; agrégats et hashes exportés.
  Une sélection scientifique nécessitera validation supplémentaire/nichée ; ajouter
  une CV ne rend pas indépendant un test antérieurement exploité.
- **Vérification :** tests d’isolation des plis, répétabilité, lecture train-only,
  coûts et seuil inchangé ; suite Python, lint, DVC, MLflow, Feast et check-m1.
