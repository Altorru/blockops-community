# BlockOps 0.1.0

**Your server. Less babysitting.** Une console locale pour un petit serveur Minecraft Java Docker existant : état, joueurs via Server List Ping, logs, start/stop/restart confirmés, sauvegardes cohérentes, restauration, rétention et alertes locales. Self-hosted gratuit sous MIT ; cloud envisagé à 4,99 €/serveur/mois, non disponible et non encaissable.

Candidat exécuté sur une fixture Docker jetable, **sans binaire Minecraft ni acceptation d’EULA**. La compatibilité avec un vrai serveur autorisé reste à valider. La recette de fixture prouve des opérations isolées ; elle ne valide pas Java réel.

## Premier essai isolé (FR)

Prérequis : Docker Engine/Compose, Python 3.12+ pour les scripts locaux, port 4218 libre. Depuis une copie fraîche de ce dossier :

```sh
python3 scripts/seed_fixture.py
export BLOCKOPS_UID=$(id -u) BLOCKOPS_GID=$(id -g)
docker compose -f compose.fixture.yml up -d --build
python3 scripts/verify_fixture.py
```

Ouvrir http://127.0.0.1:4218 : utilisateur `qa`, mot de passe dans le fichier local `secrets/qa-password` (ou `viewer` pour la lecture seule). La recette remplace uniquement `world/level.dat` de la fixture nommée `blockops-fixture`. Elle vérifie un SHA-256 exact après restauration, une copie de sécurité et le serveur laissé arrêté, puis redémarre la fixture. Ne pas utiliser ces comptes jetables en production.

Arrêter uniquement cette stack : `docker compose -f compose.fixture.yml down`. Les répertoires bind-mounted restent conservés. Ne pas lancer la stack fixture et la stack réelle sur le même port ou dans le même dossier.

## Installation sur un serveur existant autorisé

1. Faire une copie séparée du pack, et garder une sauvegarde indépendante de votre monde avant connexion. BlockOps ne fournit ni image ni installation Minecraft.
2. `cp .env.example .env`, puis renseigner le **nom exact** du conteneur autorisé, le dossier de données de ce conteneur (montage bind, pas le chemin du conteneur), et UID/GID ayant droit de lecture/écriture sur ce dossier. Ne jamais viser un dossier parent ou partagé avec d’autres services.
3. `mkdir -p backups`, puis `python3 scripts/setup.py` pour créer votre admin. Réexécuter ce script pour ajouter un `viewer`. Secrets en 0600 et dossier en 0700 : leurs propriétaires doivent correspondre à l’UID de la console ; l’agent est root pour accéder à la socket, la console n’est pas root. Sur Linux, préparer droits/groupe du dossier monde et backups explicitement. Ne pas appliquer un chmod récursif général aux autres services.
4. Configurer `MC_HOST` et `MC_PORT` pour compter les joueurs via Server List Ping. L’agent doit rejoindre le réseau existant du serveur. Exemple d’override `compose.minecraft.yml` :

```yaml
services:
  agent:
    networks: [private, minecraft]
networks:
  minecraft:
    external: true
    name: NOM_DU_RESEAU_EXISTANT
```

5. `docker compose -f compose.yml -f compose.minecraft.yml up -d --build`. Si le comptage joueurs n’est pas configuré, l’état Docker, les backups et les logs fonctionnent ; le nombre en direct apparaît indisponible. Les événements des logs ne constituent pas une liste fiable des joueurs connectés. Le protocole de statut Java peut lui-même être modifié par des plugins.
6. La console est sur localhost:4218, l’agent **sans port publié**. Accès distant via votre tunnel SSH existant ou reverse proxy HTTPS contrôlé par vous ; avec HTTPS, `COOKIE_SECURE=true`. Ne pas exposer un port Docker ou le proxy agent. Le serveur cible doit avoir sa règle Docker de restart désactivée pour éviter un conflit avec BlockOps, et aucun autre outil ne doit le relancer pendant un backup.
7. Créer une copie manuelle, restaurer sur un monde de test, contrôler les fichiers puis démarrer. Adapter intervalle/rétention après cette preuve. L’intervalle par défaut est de 24 h et la première copie automatique intervient au prochain tick (~20 s) si aucune copie n’existe. Une sauvegarde n’est déclenchée que lorsque le conteneur tourne. La prochaine copie est relative à la dernière copie terminée ; pas de cron calendaire.

## Règles opérationnelles

- Backups **avec arrêt** : les joueurs sont déconnectés, le serveur est relancé seulement s’il tournait avant la copie. Pas de RCON, pas de shell, pas d’exec Docker.
- Une copie inclut les fichiers ordinaires du dossier monde, sans liens symboliques. Les chemins d’archives, liens et entrées autres que fichiers sont rejetés en restauration.
- Rétention 2–30 copies, sauvegardes locales gzip non chiffrées. Pas de stockage hors machine : une perte de l’hôte peut perdre le monde et ses copies. Exporter indépendamment les archives vers votre stockage existant.
- Restauration : arrêt volontaire persistant, copie de sécurité, extraction de validation, copie de rollback, remplacement des fichiers ; serveur laissé arrêté. Espace libre requis : archive + monde extrait + copie de rollback + copie de sécurité. Le rollback précédent reste local jusqu’à la prochaine restauration.
- Restart : **off par défaut**, uniquement après sortie non zéro, 3 observations (~60 s), maximum 2 tentatives/heure, budget persistant. Arrêt volontaire persistant jamais relancé ; sortie zéro jamais relancée. Pas de détection de freeze/TPS ni réparation automatique de corruption. Une tentative ratée compte dans le budget.
- Alertes locales persistantes (30 dernières), visibles dans la console ; aucun email/webhook distant dans v0.1. Backup planifié en échec : attente d’au moins une heure avant nouvel essai. L’agent indisponible est affiché avec instruction de reprise.
- Comptes admin/viewer, mots de passe PBKDF2-SHA256 300 000 itérations avec sel aléatoire, sessions mémoire 8 h, cookies HttpOnly/SameSite Strict, jeton CSRF. Limite 10 tentatives de connexion/5 min/IP. Redémarrer la console après modification d’un utilisateur : révoque également les sessions existantes.
- Le proxy vérifie son bearer secret et n’accepte que `/status`, `/players`, `/logs`, `/start`, `/stop`, `/restart` sur **un seul nom** fixé au démarrage. Aucune URL Docker fournie par le navigateur. L’inspection est réduite à l’état, sans environnement ni secrets.
- La socket Docker dans l’agent reste un privilège élevé : un montage `:ro` ne rend **pas** l’API Docker en lecture seule. Le proxy est la frontière applicative ; une compromission du processus agent reste un risque pour l’hôte. v0.1 destiné à un petit hôte privé de confiance, pas au multitenant public.

## Upgrade et rollback

Arrêter la console et l’agent (sans supprimer les fichiers monde/archives), exporter les backups et `secrets/` en privé, conserver le pack et les images précédents. Remplacer les sources, rebuild, puis reprendre le même `.env` et les mêmes chemins. v0.1 utilise JSON sans migration destructrice. Vérifier login, état et backup sur fixture avant application à votre serveur. Retour arrière : relancer les images/sources précédentes avec les mêmes fichiers. Une restauration monde est une opération distincte, toujours confirmée.

## Tests et architecture

```sh
python3 -m unittest discover -s tests -v
# Recette Docker uniquement dans le dossier fixture préparé :
python3 scripts/verify_fixture.py
```

Python standard library pour HTTP, authentification et domaine ; frontend HTML/CSS/JS sans build. Un seul ajout fonctionnel : mcstatus pour le protocole de statut Java (dépendances épinglées). Ce choix réduit dépendances et maintenance comparé à Go + Nuxt pour ce MVP mono-serveur. `blockops/core.py` porte les règles sans UI ; `agent.py` est le proxy Docker ; `server.py` assure permissions/session ; `web/` rend la console. API interne, pas de contrat SaaS stable.

## Identité et assets

Logo original « monde + snapshot », variantes sombre/claire/monochrome, symbole, icône et carte de partage SVG. Console et landing : Manrope locale sous OFL, deux thèmes graphite/citron et minéral/olive, 29 icônes Lucide officielles locales avec licence ISC. Hero moderne avec monde en PNG transparent `assets/world-floating.png`, flottement et lumières CSS lentes. Mode réduction des mouvements respecté ; simulation explicitement identifiée. Galerie `/brand`, charte `BRAND.md`, usages justifiés `ICONOGRAPHY.md`. Aucun CDN ou chargement de police externe. Les captures montrent uniquement une fixture simulée.

## Privacy, support and English quick start

No external analytics, trackers, telemetry, mailing list or payment SDK. Player names may appear in container logs; world backups contain your server data. Alerts hold operational messages only. Users are local and removable from `secrets/users.json`; restart the console to apply/revoke sessions. Remove the local secrets/backups/world only after exporting what you want to retain. Support: contact@hugoviaud.fr (owner-confirmed), with version, operation and redacted logs. No contractual support SLA; never send credentials, player names or world archives.

For an isolated trial: run `scripts/seed_fixture.py` in a fresh copy, export your UID/GID, run `docker compose -f compose.fixture.yml up -d --build`, then `python3 scripts/verify_fixture.py`. Sign in on localhost:4218 using the generated local credentials. Switch the console to EN and choose light/dark. For a real existing authorized server, configure the exact container, data path and network as described above; BlockOps never installs Minecraft or accepts its EULA.

The local landing is at `/landing`. Cloud, checkout, remote notifications, multi-server control and offsite backups are outside this candidate. Monetization is not verified. No cloud service or payment is available.

## Recette locale indépendante du daemon (dev uniquement)

Lorsque Docker est indisponible, `scripts/local_fixture.py` simule explicitement les endpoints Engine dans une socket privée. Cela **n’est pas une preuve Docker**. Le protocole Server List Ping utilise une réponse Java synthétique ; aucun vrai serveur Minecraft.

Après préparation des secrets jetables et d’un venv avec `requirements.txt`, lancer trois terminaux dans ce dossier :

```sh
.venv/bin/python scripts/local_fixture.py
```

```sh
DOCKER_SOCKET=state/local-fixture/engine.sock MC_HOST=127.0.0.1 MC_PORT=12518 \
  .venv/bin/python -m blockops.agent
```

```sh
PORT=42180 WORLD_PATH=state/local-fixture/world BACKUP_PATH=state/local-fixture/backups \
  FIXTURE=true FIXTURE_TRANSPORT=local .venv/bin/python -m blockops.server
```

La console alternative est sur http://127.0.0.1:42180, l’agent sur localhost:8218 ; le TCP de statut synthétique est sur 12518. Vérifier ces ports avant de lancer. Arrêter ses trois processus avec Ctrl-C. Si une interruption non propre laisse `state/local-fixture/engine.sock`, ne la supprimer qu’après confirmation que le processus fixture propriétaire est arrêté.

```sh
VERIFY_BASE_URL=http://127.0.0.1:42180 VERIFY_WORLD_PATH=state/local-fixture/world \
VERIFY_REPORT=evidence/local-fixture-verification.json FIXTURE_TRANSPORT=local \
  .venv/bin/python scripts/verify_fixture.py
```

Les captures `current-*` correspondent à cette recette locale signalée dans l’interface. Les captures `desktop-*` et `fixture-verification.json` documentent le premier candidat testé dans les conteneurs Docker. La preuve du rebuild Docker **final** reste en attente de disponibilité du daemon partagé.

Pour les contrôles de développement : installer `requirements-dev.txt` dans le venv, puis `.venv/bin/mypy --strict blockops`. Les cinq modules applicatifs passent le typage strict ; `Any` reste explicite aux frontières JSON dont les champs sensibles sont validés. Les scripts de recette ne font pas partie du runtime applicatif.

## Recette de livraison et pilote

Le backup vérifie maintenant que l’arrêt est effectif et refuse un code 137 (kill forcé), sans relancer automatiquement la cible après ce refus. Inspecter les logs et la gestion de l’arrêt avant nouvel essai. Cela ne remplace pas la validation de sauvegarde sur un vrai serveur Java.

```sh
# Après génération du pack : installation fraîche, transport simulé privé,
# ports éphémères et arrêt uniquement des processus créés par ce script.
.venv/bin/python scripts/verify_archive.py
```

Cette recette mesure le démarrage automatisé de QA et la restauration ; elle ne mesure pas le temps d’installation d’un opérateur et ne valide ni Docker ni Minecraft. Les fichiers jetables restent dans `state/archive-check/`, ignorés par Git.

Dans ce workspace coordonné, `scripts/verify_docker_release.py` refuse le rebuild tant que DockStart n’a pas déclaré l’infrastructure `ready`, autorisé les builds et laissé au moins 8 Gio libres. Il prend le verrou partagé, rebuilde uniquement `blockops-qa`, contrôle lifecycle/restauration, proxy et présence du PNG courant. Un utilisateur hors orchestration utilise les commandes Docker du premier essai ci-dessus.

Le protocole opérateur est dans `launch/PILOT.md` et le protocole Java réel dans `launch/JAVA_TEST.md`. Modèle de cinq places non recrutées : `launch/pilot-template.csv`. Conserver les résultats remplis dans `state/`, pas dans Git. Coûts de support = minutes observées × taux horaire hypothétique ; aucune demande cloud ou vente n’est déduite des fixtures.

## Domaine et contact confirmés

Support : `contact@hugoviaud.fr`. Domaine prévu : `blockops.altorru.fr` sur l’apex propriétaire `altorru.fr` (Cloudflare). Le compte dédié VPS est vérifié et la vitrine statique avec éditeur confirmé est activée dans sa seule racine web, avec placeholder sauvegardé en privé. Vitrine publique https://blockops.altorru.fr vérifiée en HTTPS après DNS/TLS centralisés : neuf SHA exacts, chemins sensibles refusés, rendu responsive contrôlé. Console et agent restent privés. Voir `launch/DOMAIN_PLAN.md` et `launch/STATIC_RELEASE.md`. La console et l’agent restent privés ; ce domaine ne constitue pas un service cloud disponible. Aucun email de test ou message externe envoyé.

La vitrine est exportée sans build par `scripts/package_static.py`, avec un
manifeste SHA-256 et sans fichiers de contrôle applicatif. La comparaison
complète en lecture seule pour une future recette Java est préparée dans
`scripts/check_java_restore.py` et `launch/java-verification-template.json`.

## Guide public et préparation Java

Le guide /guide.html publie un aperçu explicitement simulé et le protocole de copie/restauration ; aucun contrôle serveur en ligne. Sitemap/robots et canonical ajoutés, aucun tracker. La référence technique de la cible Java autorisée reste à fournir : launch/JAVA_ENVIRONMENT.md et scripts/preflight_java.py vérifient bind/réseau/EULA existante en lecture seule, sans démarrage ni acceptation. Kit pilote et brouillons sans envoi : launch/ACQUISITION_KIT.md.

## Distribution Community

Point d’entrée : `launch/COMMUNITY.md`. Le paquet privé réunit runtime, installation, fixture, préflight et protocoles Java ; aucun recrutement pilote requis pour le préparer. `scripts/package_community.py` produit une archive immuable au commit exact et une liste SHA de tous les fichiers, sans secrets/monde/backups/preuves historiques. Le logiciel reste candidat, gratuit MIT et sans validation Minecraft réelle.
