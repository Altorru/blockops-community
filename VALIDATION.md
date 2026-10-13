# Validation Java réelle — plan, non exécuté

Cette présentation ne contient pas les outils runtime. Les commandes ci-dessous
s’exécutent dans une copie privée fraîche du candidat Community téléchargé,
sur l’hôte d’une cible **jetable déjà autorisée**. Aucun serveur à créer et aucun
EULA à accepter automatiquement.

## Entrée propriétaire unique

Renseigner `state/java-test/target.json` à partir de
`launch/java-target-template.json` dans le candidat : disposable=true, nom exact
du conteneur dédié `blockops-java-drill…`, chemins absolus du bind données et
sous-dossier monde, réseau privé exact, référence d’autorisation de cette cible.
Le fichier `eula.txt` doit déjà avoir été accepté par son propriétaire.
Ne pas transmettre les secrets ou le monde.

```sh
python3 scripts/preflight_java.py state/java-test/target.json
```

Le préflight lit uniquement : EULA existante, montage, cible, restart désactivé
et absence de ports publics. Code 2 avec un modèle vide, avant tout appel Docker.
Un code 0 valide la préparation, pas la sauvegarde ni la restauration.

## Conditions avant mutation

Version Java/Minecraft et empreinte image/jar enregistrées ; copie indépendante,
droits du compte de test, place pour archive/extraction/rollback/safety copy,
aucun autre relanceur et arrêt gracieux configuré. Console sur localhost/tunnel
existant, agent sans port public. Ne jamais viser un monde de production.

## Critères de passage

1. Statut d’un vrai serveur Java avant la copie et version enregistrée.
2. Sauvegarde : logs d’enregistrement/arrêt gracieux et absence de kill 137,
   archive identifiée par SHA-256, reprise cohérente.
3. Arrêt volontaire persistant ; mutation du seul fichier témoin du drill,
   jamais de texte dans level.dat, NBT ou région.
4. Restauration confirmée, safety copy présente, serveur laissé arrêté.
5. Tous les fichiers restaurés identiques, aucun fichier absent ou supplémentaire :
   `python3 scripts/check_java_restore.py ARCHIVE.tar.gz CHEMIN_MONDE_TEST`.
6. Redémarrage Java, statut réel et absence d’erreur de chargement du monde.
7. Refus viewer/CSRF/bearer/route hors allowlist sur le seul proxy du drill.

Suivre `launch/JAVA_ENVIRONMENT.md` et `launch/JAVA_TEST.md` du candidat.
Consigner résultats expurgés et durées dans le modèle de résultat fourni.
Une connexion de joueur ne compte que si un joueur de test est explicitement
autorisé ; sinon indiquer « non effectuée ». En cas d’échec, arrêter le drill,
conserver les preuves et la copie indépendante ; aucun nettoyage global Docker.

La recette simulée déjà vérifiée ne remplace aucun de ces critères. Tant que
la cible exacte et les preuves ci-dessus manquent, statut : Java réel non validé.
