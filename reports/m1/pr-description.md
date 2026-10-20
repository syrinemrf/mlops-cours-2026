# Brouillon de PR M1 — à actualiser après les décisions de l’audit

Titre proposé : `lab/m1-versioning : pipeline DVC, registre et Feast pour IBM HR`.
Base future `main`, branche future `lab/m1-versioning`. **PR non ouverte.**

Le socle M1 adapte le contrat du cours à IBM HR Attrition et rend reproductibles
l’ingestion, la préparation, l’entraînement A et l’évaluation par DVC. MLflow trace
les runs/versions/gates ; Feast fournit les27 features offline et online.

## Preuves acquises au snapshot personnel d2ea3ca

- 18/18 contrôles officiels, 77 tests réussis, lint validé ; rapports dans reports/m1.
- Split80/20 stratifié seed 42 ; ID et sensibles hors prédicteurs ; version 1/hash
  source Kaggle ; source35 colonnes, export32,27 features.
- 2 smoke +22 configurations +1 run DVC FINISHED ; trois versions, Dummy failed,
  champion LR C=1 sans poids et challenger LR C=0,1 sans poids.
- Quatre stages DVC, cache/remote synchronisés ; clone même cluster vérifié par
  pull/repro avec Python existant. Recalcul intégral et autre cluster non encore prouvés.
- Feast offline/online vérifié ; timestamp technique synthétique, pas de preuve
  de validité temporelle RH en production.

## Points à résoudre avant publication de cette description

- [ ] Décision et exécution8.4 : alignement DVC/champion autorisé, nouveau run et
  nouvelle version à consigner, challenger vérifié. À d2ea3ca, DVC reste C=0,1 balanced.
- [ ] Preuves8.5 et10.3, portabilité du diagnostic registre, replay réel d’Aziz10.4.
- [ ] Poids balanced des neuf RF explicite dans la grille si les defaults DVC
  deviennent sans poids ; conservation des conditions des22 configurations historiques.
- [ ] Référence de l’accord dataset par courriel consignée ; aucun numéro d’issue inventé.
- [ ] Commits intégrés, SHA de validation, résultats réels renouvelés et capture joints.
- [ ] Revue réelle de @MohamedAzizKouch sur le dernier commit.

## Correctifs et limites à relire

Le test initial spécifique à personal_status utilise désormais une fixture
générique conservant la vérification des sensibles hors features ; aucun skip.
Le checker M1 a seulement changé de mode 644→755, son contenu reste celui du cours.
La gate 0,70 est conservée, distincte des seuils de décision. Les coûts 1:1 sont une
hypothèse neutre expérimentale, sans justification économique RH démontrée.

Les candidats ont été choisis après comparaison répétée sur le test du cours :
aucune performance finale indépendante ni supériorité statistique revendiquée.
A/B1/B2 sont documentés séparément ; aucune reproduction Jia ni innovation XP-Cube
n’est déclarée réalisée. Données/modèles/credentials/venv/bases locales exclus de Git.

## Vérification

Suivre NOTES pour le cluster existant, l’environnement verrouillé, les credentials
locaux et Feast. Vérifier `make test`, `make lint`, `dvc status`,
`dvc status --cloud`, filiation champion/DVC, puis `make check-m1` sur le SHA retenu.
Les run IDs de Syrine ne sont pas ceux d’un autre serveur MLflow.

Voir [l’audit](pre-publication-audit.md) et
[la checklist de revue/publication](binome-review-publication.md).
