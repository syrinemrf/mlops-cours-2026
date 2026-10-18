# Journal de bord du binôme

<!--
Mode d'emploi (à garder en tête du fichier) :
- Une entrée par séance (et par session de travail importante hors séance), la plus récente en bas.
- 3 à 5 lignes : qui a piloté, ce qui a été fait, ce qui a bloqué ou ce qui a été appris,
  la prochaine étape. Pas de roman : c'est un outil de pilotage, pas un rapport.
- Titre d'entrée au format exact « ## S<n> — AAAA-MM-JJ — <sujet> » (date réelle) :
  le pré-contrôle de rendu (make check-m10) compte les entrées datées.
- Liez les PR, issues et ADR (#12, docs/adr/0003-...). Les problèmes non résolus restent
  visibles : c'est précisément ce qui aide l'enseignant à vous débloquer.
- L'entrée d'exemple ci-dessous (date AAAA-MM-JJ) n'est pas comptée ; supprimez-la
  quand vous aurez écrit la vôtre.
-->

**Binôme :** Syrine (@syrinemrf) et Aziz (collaborateur ; pseudo à renseigner)
**Repo :** https://github.com/syrinemrf/mlops-cours-2026
**Dataset :** IBM HR Analytics Employee Attrition (validé par le professeur selon Syrine ; lien de l’issue à renseigner)
**Extensions :** [À compléter à la S8 : @pseudo-1 → ext/<nom> · @pseudo-2 → ext/<nom>]

<!-- Vos entrées commencent ici. Modèle :

## S1 — AAAA-MM-JJ — Lab 0 : setup

- **Pilote / copilote :**
- **Fait :**
- **Bloqué / appris :**
- **Prochaine étape :**

-->

## S1 — 2026-10-18 — Lab 0 : restauration et setup personnel

- **Pilote :** Syrine (@syrinemrf), avec assistance Codex ; travail sur `work/syrine/m0`, à comparer avec Aziz.
- **Fait :** trois conteneurs kind redémarrés sans recréation ; registry, SeaweedFS et MLflow déployés ; environnement uv/Python 3.12 vérifié hors ligne ; test DVC poussé et relu dans S3 (12 octets identiques).
- **Bloqué / appris :** le kubeconfig était correct, mais les nœuds étaient arrêtés ; scripts non exécutables corrigés ; ancien MinIO conservé ; collision S3_PORT corrigée par enableServiceLinks=false ; make pf corrigé pour ne plus tuer son shell.
- **Prochaine étape :** checklist 18/19 (seul commit/push restant), tests MLflow et DVC réussis ; publier après accord de Syrine, relancer la validation, capturer le résultat puis comparer et faire relire la PR par Aziz.

## S2 — 2026-10-19 — Lab 0 : publication et validation finale

- **Pilote :** Syrine (@syrinemrf), avec assistance Codex.
- **Fait :** branche personnelle publiée ; `make check-m0` exécuté avec succès, **19/19** ; preuve dans `reports/m0/check-m0-final.log`.
- **Bloqué / appris :** le push nécessitait un agent SSH avec clé déverrouillée ; Syrine l’a chargé dans son terminal, sans partager sa phrase secrète.
- **Prochaine étape :** capturer le résultat, déposer le livrable, comparer avec Aziz et préparer la PR `lab/m0-setup` relue ; aucune fusion automatique.
