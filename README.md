# BlockOps Community — présentation publique

BlockOps accompagne la supervision et les sauvegardes locales d’un petit serveur
Minecraft Java Docker. Community est gratuit sous licence MIT.

Ce dépôt préparé contient uniquement une présentation, une capture de démonstration
et le protocole de validation. Il ne contient ni console exécutable, ni agent,
ni accès Docker, ni historique du dépôt de développement. Le dépôt GitHub public est séparé du dépôt de développement privé.

## Démonstration

Ouvrir `demo/index.html` dans un navigateur. La capture montre une fixture
**simulée** ; aucun bouton ne commande un serveur. Aucun réseau, compte, tracker
ou script n’est nécessaire pour cette démonstration.

## Essayer le candidat gratuit

[Téléchargement Community et checksum](https://blockops.altorru.fr/guide.html#telechargement).
Vérifier SHA256SUMS avant extraction dans un dossier neuf, puis suivre le README
de l’archive. Cette archive applicative distincte contient le runtime local ;
elle n’est pas incluse dans cet export GitHub de présentation.

La console et l’agent s’installent sur votre hôte privé. Les sauvegardes sont
locales et non chiffrées ; conserver une copie indépendante du monde. La socket
Docker reste un privilège élevé. Le candidat est destiné à un hôte privé de
confiance, pas au multitenant public.

## État de validation

Les recettes isolées utilisent un Engine simulé et un statut Java synthétique.
Elles vérifient des opérations de fichiers, l’authentification et les refus de
commandes. Elles ne prouvent pas une sauvegarde cohérente de Minecraft réel.
La recette Java réelle reste à exécuter sur une cible jetable autorisée avec EULA
acceptée préalablement par son propriétaire : voir [VALIDATION.md](VALIDATION.md).

Le cloud et le paiement ne sont pas disponibles. Aucun opérateur humain ni
revenu n’est annoncé. BlockOps ne fournit pas de serveur Minecraft et n’accepte
pas son EULA à votre place.

Support : contact@hugoviaud.fr. Ne transmettre ni secrets, mondes, ni logs
contenant des noms de joueurs. Aucun délai contractuel annoncé.

## Licences et attribution

Voir [LICENSE](LICENSE) et [NOTICE.md](NOTICE.md). Les fichiers publics sont
exportés individuellement ; aucun historique Git n’est inclus.

## Quickstart / English

This repository is a static Community presentation and simulated screenshot,
not the executable management console or Docker agent. Open `demo/index.html`
directly, or serve this folder using Python 3:

```sh
python3 -m http.server 8080 --bind 127.0.0.1
```

Open http://127.0.0.1:8080/demo/ and stop the server with Ctrl-C. No installation,
credentials, Docker access or external requests are required for this preview.
The existing [public demo and download page](https://blockops.altorru.fr/guide.html)
clearly marks simulated data. Get the separate free MIT runtime candidate there,
verify its SHA256SUMS, then follow its included README in a fresh private folder.

Real Java backup/restore is not validated yet. It requires an identified,
authorized disposable target and an EULA already accepted by its owner.
Local backups are unencrypted; keep an independent copy. No hosted plan or
payment is available. See VALIDATION.md, NOTICE.md and SECURITY.md.
