# BlockOps Community — présentation publique

BlockOps accompagne la supervision et les sauvegardes locales d’un petit serveur
Minecraft Java Docker. Community est gratuit sous licence MIT.

Ce dépôt contient le runtime gratuit Community : console locale, agent Docker
mono-cible, fixture simulée, tests et documentation. L’historique de développement,
les données et secrets ne sont pas inclus. Aucun service d’administration n’est
exposé par GitHub. Le dépôt public est séparé du dépôt de développement privé.

## Démonstration

Ouvrir `demo/index.html` dans un navigateur. La capture montre une fixture
**simulée** ; aucun bouton ne commande un serveur. Aucun réseau, compte, tracker
ou script n’est nécessaire pour cette démonstration.

## Essayer le candidat gratuit

[Téléchargement Community et checksum](https://blockops.altorru.fr/guide.html#telechargement).
Vérifier SHA256SUMS avant extraction dans un dossier neuf, puis suivre le README
de l’archive. Le code de ce dépôt reprend le runtime exact de ce candidat, avec documentation
actualisée et sans fichiers de déploiement internes.

La console et l’agent s’installent sur votre hôte privé. Les sauvegardes sont
locales et non chiffrées ; conserver une copie indépendante du monde. La socket
Docker reste un privilège élevé. Le candidat est destiné à un hôte privé de
confiance, pas au multitenant public.

## État de validation

Les recettes isolées utilisent un Engine simulé et un statut Java synthétique.
Elles vérifient des opérations de fichiers, l’authentification et les refus de
commandes. Elles ne prouvent pas une sauvegarde cohérente de Minecraft réel.
La recette Java réelle est différée par décision du propriétaire du 13 octobre
2026. Aucune cible ni intervention terrain n’est demandée. Le protocole est
conservé pour une éventuelle reprise explicite : [VALIDATION.md](VALIDATION.md).

Le cloud et le paiement ne sont pas disponibles. Aucun opérateur humain ni
revenu n’est annoncé. BlockOps ne fournit pas de serveur Minecraft et n’accepte
pas son EULA à votre place.

Support : contact@hugoviaud.fr. Ne transmettre ni secrets, mondes, ni logs
contenant des noms de joueurs. Aucun délai contractuel annoncé.

## Licences et attribution

Voir [LICENSE](LICENSE) et [NOTICE.md](NOTICE.md). Les fichiers publics sont
exportés individuellement ; aucun historique Git n’est inclus.

## Quickstart / English

This repository includes the free Community console, Docker agent, tests and
simulated fixture. GitHub does not expose an administration service. Open `demo/index.html`
directly, or serve this folder using Python 3:

```sh
python3 -m http.server 8080 --bind 127.0.0.1
```

Open http://127.0.0.1:8080/demo/ and stop the server with Ctrl-C. No installation,
credentials, Docker access or external requests are required for this preview.
The existing [public demo and download page](https://blockops.altorru.fr/guide.html)
clearly marks simulated data. Get the separate free MIT runtime candidate there,
verify its SHA256SUMS, then follow its included README in a fresh private folder.

Real Java backup/restore is not validated and was deferred by the owner on
13 October 2026. No target request or field test is active. A future explicitly
authorized restart would require an identified,
authorized disposable target and an EULA already accepted by its owner.
Local backups are unencrypted; keep an independent copy. No hosted plan or
payment is available. See VALIDATION.md, NOTICE.md and SECURITY.md.

## Premier essai du produit / Product quickstart

Prérequis : Git, Python 3.12+ et Docker Engine/Compose pour la fixture Docker.
Cloner dans un nouveau dossier, jamais un dossier monde existant :

```sh
git clone https://github.com/Altorru/blockops-community.git
cd blockops-community
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/seed_fixture.py
export BLOCKOPS_UID=$(id -u) BLOCKOPS_GID=$(id -g)
docker compose -f compose.fixture.yml up -d --build
.venv/bin/python scripts/verify_fixture.py
```

Ouvrir http://127.0.0.1:4218. Compte de test `qa`, mot de passe généré dans
`secrets/qa-password` ; ne pas le publier ni le réutiliser. Arrêter uniquement
cette stack avec `docker compose -f compose.fixture.yml down` ; les fichiers
de fixture restent locaux. Aucun serveur Minecraft ni EULA dans cet essai.

The Docker fixture is synthetic, not Minecraft. Use a fresh folder and the
generated local test credentials. The simulation recipe can also run without
Docker; see [INSTALLATION.md](INSTALLATION.md). Actual Java setup requires the
[validation gate](VALIDATION.md) and an already authorized disposable target.
The current Docker build and real Java compatibility remain unverified; the
standalone simulated Engine and file lifecycle recipe has passed.
