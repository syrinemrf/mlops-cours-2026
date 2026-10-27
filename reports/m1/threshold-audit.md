# Audit du seuil — protocole A, avant grille

Pour une probabilité naturelle p=P(Yes|X), risque de décision positive C_FP(1-p),
risque négatif C_FN p. La règle de Bayes est p >= C_FP/(C_FP+C_FN), soit 0.5 avec
coûts expérimentaux 1:1 (aucune estimation économique RH).

Sous pondération constante w1/w0=k, la probabilité idéale de la population pondérée
q vérifie q/(1-q)=k p/(1-p), donc q=kp/(1-p+kp). Transposer le seuil naturel donne
q >= C_FP k/(C_FN+C_FP k). Avec balanced, sklearn pose w_c=N/(2 n_c), d'où
k=n0/n1=986/190 et seuil=986/(986+190)=0.8384353741496599.
C'est une correction théorique sous des hypothèses idéales, pas un optimum empirique
démontré pour nos estimateurs finis et régularisés. Aucun label test ne sert au calcul.

| Famille | Poids effectivement appliqués | Seuil A |
|---|---|---|
| LogisticRegression balanced | class_weight transmis au fit | 0.8384353741496599 |
| LogisticRegression None | non pondéré | 0.5 |
| RandomForest balanced | class_weight transmis ; partitions et fréquences des feuilles pondérées | 0.8384353741496599, heuristique dont l'équivalence exacte n'est pas garantie |
| GradientBoosting | pas de class_weight dans cette grille, aucun sample_weight ajouté | 0.5 |
| Dummy prior | non pondéré ; probabilité train 190/1176 | 0.5 |

Le script construit hyperparams uniquement à partir de MODELS[model]. Il ne transmet
pas le défaut balanced de params.yaml à GradientBoosting ni Dummy. Pour RF il ne
s'agit pas de balanced_subsample : le ratio global train correspond au mode utilisé.
LR régularisée, arbres, bootstrap et contraintes de profondeur ne garantissent pas
la relation idéale entre p et q. En particulier, les probabilités RF peuvent rester
loin de .838, même quand les rangs sont utiles : au smoke RF, TP=1 et FN=46.

ROC AUC mesure le classement sur tous les seuils ; elle n'impose ni calibration ni
rappel élevé à un seuil donné. Un modèle qui ordonne correctement les positifs mais
place presque toutes ses probabilités sous le seuil aura un rappel faible. La forte
prévalence négative rend aussi l'accuracy seule trompeuse. AP et confusion complètent
l'AUC ; le coût 1:1 est FP+FN et favorise souvent des décisions conservatrices.

Calibration : apprendre/évaluer l'accord entre probabilités et fréquences, par exemple
avec Brier/log-loss/fiabilité ; la formule de pondération ne calibre pas les modèles.
Optimisation empirique d'un seuil : comparer des décisions sur une validation interne,
avec objectif fixé ; ce travail n'est pas effectué ici. Aucun seuil changé à partir
du test, ni calibration apprise dans cet incrément.

La grille du cours conserve ces seuils pour sa comparabilité pédagogique. Pour une
sélection scientifique future : conserver le test fermé, CV stratifiée 5 folds sur
train uniquement, pipelines réajustés dans chaque fold, choix d'hyperparamètres sur
scores out-of-fold, seuil et éventuelle calibration dans une validation interne
supplémentaire/nestée. Refit sur train après gel. Le test A déjà consulté à répétition
ne pourra pas servir de confirmation indépendante de cette sélection ; une évaluation
nouvelle indépendante sera nécessaire pour une affirmation confirmatoire. B1/B2
restent isolés, inchangés et non exécutés.
