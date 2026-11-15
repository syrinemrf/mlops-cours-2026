# ADR-0005 — Data drift ≠ concept drift : ce que le gate de drift décide (et ne décide pas)

- **Statut :** mis en œuvre (Lab 3) ; revue du binôme (Aziz) en attente
- **Date :** 2026-11-08
- **Auteur(s) :** @syrinemrf
- **Relu par :** revue humaine GitHub à effectuer
- **Périmètre :** socle Lab M3, protocole pédagogique A
- **Liens :** src/detect_drift.py, src/simulate.py, params.yaml (section drift),
  pipelines/scoring_pipeline.py, pipelines/drift_demo.py, src/validate_model.py

## Contexte

Le pipeline de scoring IBM HR gagne trois gates au Lab 3 : contrat de données (Great
Expectations), drift, validation du modèle. Il faut décider ce que le gate de drift mesure
et ce qu'il a le droit de conclure.

Deux phénomènes différents portent le nom de « drift » :

- **data drift** (*covariate shift*) : la distribution des entrées P(X) change. Exemple
  simulé : une vague d'embauches plus jeunes, plus éloignées, moins payées, plus souvent en
  heures supplémentaires ;
- **concept drift** : la relation P(y | X) change. Exemple : à profil égal, les heures
  supplémentaires ne poussent plus au départ parce que la politique RH a changé.

Un test de distribution sur X ne voit que le premier. Le second ne se mesure qu'avec des
étiquettes, donc avec du retard : un départ n'est connu qu'après coup. Le dataset IBM HR est
de plus un instantané synthétique, sans dimension temporelle (fiche de données, §4) : aucun
concept drift réel n'y est observable.

Mesures locales du 2026-11-08 (31 colonnes du contrat, référence = train 1176 lignes) :

- train vs test (294 lignes, split stratifié) : **0/31** colonnes en drift. Deux colonnes ont
  une p-value < 0,05 (JobLevel 0,034, RelationshipSatisfaction 0,044) avec un PSI < 0,05,
  ce qu'on attend du hasard avec 31 tests à α = 0,05. Evidently, qui ne regarde que la
  p-value, en signale 3 ;
- test déplacé selon `params.yaml` (drift.simulation) : **4/31** (DistanceFromHome PSI 1,52,
  Age 0,52, MonthlyIncome 0,30, OverTime 0,28), soit 12,9 % ≥ 10 % : drift détecté. Le lot
  reste conforme au contrat GX : des données valides peuvent dériver.

## Options envisagées

| Option | Avantages | Inconvénients |
|---|---|---|
| p-value seule (KS / χ²), comme Evidently par défaut | Simple, standard | Avec 31 tests, fausses alertes attendues ; avec beaucoup de lignes, tout devient significatif |
| PSI seul | Mesure une ampleur, lisible métier | Instable sur petits lots, sans notion de hasard |
| **p-value ET PSI**, puis part de colonnes | Significatif ET important ; robuste aux deux tailles de lot | Deux seuils à justifier ; une seule colonne critique peut passer sous la part |
| Surveiller la performance (étiquettes) | Seule mesure directe du concept drift | Étiquettes en retard ; hors du périmètre d'un pipeline d'entraînement |

## Décision

1. Une colonne dérive si **p < 0,05** (KS numérique, χ² catégoriel et ordinal, le rôle venant
   du contrat) **et PSI ≥ 0,25** (déciles de la référence). Le lot dérive si au moins
   **10 %** des colonnes dérivent. Les seuils sont dans `params.yaml`, tracés par Git.
2. Dans `scoring-pipeline`, le gate compare **train et test** et bloque l'entraînement
   (`fail_on_drift=True`) : un split qui dérive signale un bug de préparation, pas une
   évolution du monde. Dans `scoring-drift-demo`, le drift est signalé sans bloquer.
3. Le gate de drift est nommé et documenté comme un détecteur de **data drift** uniquement.
   Il ne déclenche ni réentraînement ni promotion. Un drift détecté est une **alerte à
   instruire**, pas une preuve de dégradation du modèle.
4. Le **concept drift** est hors du périmètre du Lab 3 : il relève de la surveillance de la
   performance sur des étiquettes fraîches (Lab 7, monitoring), avec le gate ROC AUC 0,70 et
   les tests comportementaux de `src/validate_model.py` rejoués sur ces étiquettes.

## Conséquences

- **Positives :** les fausses alertes « p-value seule » sont filtrées (0/31 sur train vs test,
  contre 3 colonnes pour Evidently) ; le scénario simulé est détecté sur ses 4 colonnes
  exactement ; le rapport (JSON, Markdown, HTML Evidently) montre les deux verdicts.
- **Négatives :** la part de 10 % exige 4 colonnes sur 31. Une seule colonne très prédictive
  qui dérive (ex. OverTime) ne bloque pas seule : elle apparaît dans le rapport, à lire.
- **Limite de la simulation :** `src/simulate.py` déplace X sans régénérer y. Sur ce lot, la
  relation entre X et y est donc elle aussi modifiée artificiellement : la démo ne permet
  aucune conclusion sur la performance du modèle sous drift.
- **À revoir si :** des données horodatées réelles deviennent disponibles (seuils à recalibrer
  sur des périodes stables), ou si le monitoring du Lab 7 fournit des étiquettes (mesure
  directe du concept drift).
