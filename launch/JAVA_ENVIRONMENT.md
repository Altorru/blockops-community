# Environnement exact de recette Java

L'autorisation générale de test jetable est donnée. La référence technique de
cible et son EULA existante ne sont pas fournies dans ce repo. Aucun serveur
Java n'est créé ni téléchargé, aucun eula.txt écrit. Ne pas réutiliser le VPS
de vitrine, une fixture synthétique ou un conteneur existant non désigné.

## Entrée exacte et gate en lecture seule

Dans une copie privée fraîche du candidat, sur l'hôte du monde de test :

```sh
mkdir -p state/java-test
cp -n launch/java-target-template.json state/java-test/target.json
python3 scripts/preflight_java.py state/java-test/target.json > state/java-test/preflight.json
```

Renseigner `disposable: true`, nom du conteneur dédié préfixé
`blockops-java-drill`, chemin bind des données, sous-dossier monde, réseau privé
exact et référence de l'autorisation. Le script vérifie en lecture seule le
eula.txt déjà accepté, le bind Docker, réseau et restart désactivé, et refuse
les ports publics. Le modèle vide retourne code 2 avant toute commande Docker.
Un résultat ready n'est jamais une preuve backup/restore ou Java.

## Installation BlockOps sur cette cible seulement

Configurer `.env` de la copie fraîche : `BLOCKOPS_CONTAINER` = nom validé,
`WORLD_PATH` = chemin monde validé, `MC_HOST` = nom validé,
`MC_PORT` = port privé de statut du serveur, UID/GID de l'opérateur autorisé.
Copier `.env.example` sans écraser un fichier existant. Garder une copie
indépendante du monde, espace pour archive/extraction/rollback/safety.
Créer les seuls comptes de test avec `python3 scripts/setup.py`.

Créer `state/java-test/compose.network.yml` avec le réseau exact :

```yaml
services:
  agent:
    networks: [private, java_test]
networks:
  java_test:
    external: true
    name: NOM_RESEAU_VALIDE_DANS_PREFLIGHT
```

```sh
docker compose -p blockops-java-drill -f compose.yml -f state/java-test/compose.network.yml config --quiet
# Seulement après gate locale >=8 Gio, mutex et port 4218 libre :
docker compose -p blockops-java-drill -f compose.yml -f state/java-test/compose.network.yml up -d --build
```

Ces commandes construisent console/agent, pas un serveur Minecraft. Aucun
EULA accepté par ces commandes. Suivre `launch/JAVA_TEST.md`, puis contrôle
lecture seule :

```sh
python3 scripts/check_java_restore.py backups/ARCHIVE_VALIDEE.tar.gz CHEMIN_MONDE_VALIDE > state/java-test/restored-files.json
docker compose -p blockops-java-drill -f compose.yml -f state/java-test/compose.network.yml stop
```

Ne pas exécuter `verify_fixture.py` sur Java. Ne pas faire down/prune globaux.
Après restore vérifier toutes les empreintes avant boot, logs save/stop sans 137,
copie safety, statut Java après boot. Copier le modèle de résultat en privé,
noter versions/image, durées et incidents, conserver les logs expurgés seulement.

Sources officielles relues le 8 octobre : documentation Docker (inspect et
compose config) via Context7 `/docker/docs`, et
https://www.minecraft.net/en-us/download/server (Java Edition et exigence EULA).
La version/image Java reste celle de la cible propriétaire, aucun téléchargement
ou remplacement implicite.
