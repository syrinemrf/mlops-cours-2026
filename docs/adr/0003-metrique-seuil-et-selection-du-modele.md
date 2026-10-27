# ADR-0003 — Métrique, seuils et sélection du modèle

> **Intégration du 2026-10-27 : variante historique proposée.**
> Texte d’Aziz conservé, ancien ADR-0002, commit source `39596be9db5bef8c5b6b2ae08197307c3f4d0ca5`.
> Renumérotation et encadré par Syrine avec assistance Codex ; aucune approbation
> GitHub du binôme n’est présumée. Les liens du texte original décrivent sa branche.
> Le contrat commun reste roc_auc, gate 0,70, LR C=1 sans poids et seuil 0,5. AP/0,32 et one-SE restent des propositions alternatives. Les chiffres/versions ci-dessous sont ceux déclarés par Aziz sur son pipeline et son cluster, pas ceux du champion commun. La sensibilité est désormais un diagnostic indépendant, sans promotion.


- **Statut :** proposé
- **Date :** 2026-10-21
- **Auteur(s) :** @MohamedAzizKouch
- **Relu par :** en attente de la relecture de @syrinemrf (pull request)
- **Périmètre :** socle (Lab 1)
- **Liens :** `dataset.yaml`, `src/train.py`, `src/promote.py`, `src/sensitivity.py`, `params.yaml`

## Contexte

Seuls 16,1 % des employés partent (237 sur 1 470). Un modèle qui prédit « personne ne part »
a donc 83,9 % d'accuracy : cette métrique ne dit rien ici. Le jeu de test ne contient que 294
lignes dont 47 départs, ce qui rend ses chiffres très variables : deux modèles avec le même
score de validation croisée (0,632) ont eu 0,574 et 0,612 au test. Enfin, le jeu ne fournit
aucune matrice de coûts, et je ne veux pas en inventer une.

## Options envisagées

| Option | Avantages | Inconvénients |
|---|---|---|
| Métrique `roc_auc` | Simple, indépendante du seuil | Peu sensible aux positifs rares |
| Métrique `average_precision` | Adaptée aux classes déséquilibrées | Se lit moins directement |
| Choisir le modèle sur le jeu de test (comme le code du cours) | Rapide | 22 essais sur 47 positifs : on choisit du bruit |
| Choisir sur la validation croisée du train | Plus de données, test préservé | Plus de calcul |

## Décision

1. La métrique primaire est `average_precision` (`dataset.yaml`).
2. Les modèles sont comparés par validation croisée stratifiée en 5 plis sur le train. Parmi
   les modèles à moins d'une erreur-type du meilleur, on prend le plus simple (règle de
   `src/promote.py`). Le jeu de test sert seulement de barrière.
3. Le seuil de promotion vaut **0,32**. C'est **deux fois la prévalence** (2 × 0,161), un
   plancher provisoire : le modèle naïf obtient 0,160 au test, donc il n'est jamais promu.
   Il reste à confirmer, il ne mesure pas la qualité d'un modèle.
4. Les coûts restent à 1 / 1, faute de données. Le seuil de décision vient de la formule du
   cours (`cost_threshold`).

Résultat : la version 3 du registre (`@champion`) est une régression logistique (`C=0.01`,
`class_weight=balanced`), `cv_average_precision` 0,617 et `average_precision` 0,598 au test,
tracée par `dvc repro` (le `data_md5` du run est celui de `dvc.lock`).

## Analyse de sensibilité du seuil

Calculée par `python -m src.sensitivity` sur les prédictions hors-pli du train (1 176 lignes,
190 départs). Ce sont des **scénarios hypothétiques** : aucun coût réel n'est connu.

| Scénario | Seuil | Rappel | Précision | Alertes | Coût / « personne » |
|---|---|---|---|---|---|
| Seuil actuel (coûts 1/1) | 0,838 | 0,032 | 1,000 | 6 | 0,968 |
| Coût FN = 1 × FP | 0,665 | 0,442 | 0,724 | 116 | 0,726 |
| Coût FN = 2 × FP | 0,665 | 0,442 | 0,724 | 116 | 0,642 |
| Coût FN = 3 × FP | 0,583 | 0,642 | 0,506 | 241 | 0,567 |
| Coût FN = 5 × FP | 0,566 | 0,674 | 0,471 | 272 | 0,478 |
| Coût FN = 10 × FP | 0,455 | 0,811 | 0,312 | 494 | 0,368 |

Les seuils sont optimisés sur ces mêmes prédictions, donc les coûts sont optimistes.

## Conséquences

- **Positives :** le choix du modèle ne dépend plus du petit jeu de test ; aucun coût inventé ;
  le modèle naïf est bloqué par la barrière.
- **Négatives / dette acceptée :** avec la formule du cours, le seuil de 0,838 ne signale que
  6 employés sur 1 176 (rappel 0,032), presque comme ne signaler personne. Même avec les
  coûts 1 / 1, un seuil de 0,665 ferait mieux (0,726 contre 0,968). La formule suppose des
  probabilités calibrées, ce qui n'est pas le cas ici (forte régularisation, poids de classes).
  `check-m1` ne voit pas ce défaut : il ne vérifie que `average_precision` ≥ 0,32.
  Une correction (seuil choisi sur les prédictions hors-pli) est envisagée mais **pas
  décidée** : elle fera l'objet d'un ADR séparé. Le seuil de promotion 0,32 reste à revoir.
- **Vérification :** `tests/test_promote.py` (règle de sélection), `tests/test_train.py`
  (seuil, validation croisée, pas de fuite), `tests/test_sensitivity.py` et `check-m1`.
