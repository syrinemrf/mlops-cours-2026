# ADR-0001 — Épingler l’ingestion IBM HR et séparer identifiant, audit et prédiction

- **Statut :** proposé
- **Date :** 2026-10-19
- **Auteur(s) :** @syrinemrf (avec assistance Codex)
- **Relu par :** personne à ce stade ; revue à solliciter auprès de @MohamedAzizKouch
- **Périmètre :** socle (Lab 1), premier incrément données uniquement
- **Liens :** [dataset card](../dataset-card.md), [contrat](../../dataset.yaml), M0 PR #1 fusionnée

## Contexte

Le dataset IBM HR est validé par le professeur selon Syrine. Il faut conserver
l’interface du cours sur un poste à RAM limitée, avec source reproductible et sans
entraîner de modèle. Kaggle décrit des profils synthétiques, sans historique réel.
La version 1 téléchargée contient 1 470 × 35, 237 Yes, zéro valeur manquante et zéro
doublon exact ; l’identifiant est unique et trois colonnes sont constantes.

## Options envisagées

| Option | Avantages | Inconvénients |
|---|---|---|
| Kaggle version 1 + empreinte CSV + validation stricte | Provenance explicite, dérive bloquée, petit volume | Dépend du service ; empreinte initiale non indépendante |
| URL Kaggle latest sans empreinte | Simple | Mise à jour silencieuse, reproduction incertaine |
| Miroir tiers ou CSV manuel non vérifié | Disponibilité possible | Provenance/version non garanties, contraire à la demande |

## Décision

Utiliser exclusivement Kaggle version 1, épingler son membre CSV par SHA-256 et
vérifier le schéma avant export. L’ancre SHA-256 provient du premier téléchargement,
pas d’une signature indépendante. Conserver EmployeeNumber hors prédicteurs, retirer
les constantes et conserver Age/Gender/MaritalStatus pour audit hors modèle.
Exporter 32 colonnes (27 prédicteurs). Traiter 9 ordinales en catégories one-hot,
avec libellés à rang explicite ; aucune distance arbitraire ni apprentissage à l’ingestion.
Garder le lecteur et check.sh inchangés ; rendre le test sensible hors features
indépendant de German Credit avec une fixture synthétique, autorisation du 2026-10-20. Split 80/20 stratifié,
graine 42 ; apprentissage des transformations sur le train uniquement.
Proposer ROC AUC ≥ 0.70, gate inchangée, avec AP/rappel/précision/F1 en complément.
Sans coûts RH fournis, utiliser 1:1 comme hypothèse expérimentale neutre validée par Syrine le 2026-10-20, pas 5:1.

## Conséquences

- **Positives :** données reproductibles, identifiant conservé, audit compatible avec
  `extra_sensitive`, source et licences ODbL/DbCL documentées ; aucun entraînement requis.
- **Négatives / dette acceptée :** perte de l’ordre dans le modèle one-hot ; exclusion
  des sensibles n’éliminant pas leurs proxys ; disponibilité Kaggle ; aucune généralisation
  RH/causalité démontrée. Revoir coûts, gate et groupes avant entraînement avec Syrine,
  sans les ajuster pour obtenir un résultat vert. DVC download/prepare est implémenté dans l’incrément suivant.
- **Vérification :** téléchargement et relecture, empreintes source/export, contrôles
  de types et domaines, tests ciblés, simulation stratifiée 1 176/294 (190/47 Yes).
  Le test auparavant spécifique à personal_status est rendu générique sans skip ni suppression.
