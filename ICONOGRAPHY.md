# BlockOps — Lucide par usage

Sous-ensemble officiel de **lucide-static 1.52.0**, conservé dans `assets/lucide/`. Chaque SVG original et la licence ISC avec attribution Feather sont inclus. Provenance et liste : `assets/lucide/provenance.json`. Documentation officielle : https://lucide.dev/guide/packages/lucide-static.

| Icône | Usage | Justification |
|---|---|---|
| Server | Serveur cible | Identifie le service supervisé |
| Play | Démarrer | Lance le processus |
| Square | Arrêter | Convention explicite stop |
| RotateCw | Redémarrer | Nouveau cycle du processus |
| HardDriveDownload | Créer une copie | Écriture sur le stockage local |
| Archive | Copies et état vide | Archives conservées |
| ArchiveRestore | Restaurer | Récupère une archive, distinct du restart |
| Users | Joueurs | Personnes connectées déclarées par le serveur |
| SquareTerminal | Journal | Sortie de console en lecture seule |
| Clock3 | Actualisation | Cadence de lecture, pas une promesse de temps réel |
| Bell | Activité | Événements à consulter localement |
| SlidersHorizontal | Règles | Réglage intervalle, rétention, automatisation |
| ShieldCheck | Restart prudent | Garde-fous de relance, aucun label de certification |
| KeyRound | Rôle | Niveau d’accès du compte local |
| LockKeyhole | Connexion | Authentification locale |
| CircleCheck / CirclePause | État | En marche / arrêté, toujours avec libellé |
| CircleAlert | Incident/confirmation | Opération à examiner |
| FlaskConical | Fixture | Signale les données de test |
| Sun / Moon | Thème | Indique le thème à activer, avec nom accessible FR/EN |
| Globe | Langue | Changement FR/EN |
| LogOut | Quitter | Fin de session |
| ArrowRight / ArrowUpRight | Liens | Continuation/navigation |
| Check / X | Confirmer/annuler | Décision explicite dans le dialogue |
| Layers / FileCheck2 | Copie/vérification | Repères de la connexion, sans résultat fabriqué |

Grille 24 × 24, trait UI 1,8 px, extrémités arrondies, `currentColor`. Sprite local unique ; aucune dépendance JS ni requête CDN. Le SVG décoratif porte `aria-hidden="true"` et `focusable="false"`. Les boutons portent leur texte ; thème et logout mobile gardent leur nom accessible. La traduction modifie les libellés sans supprimer les icônes.

Le symbole de marque et l’illustration sont des géométries originales, pas des icônes Lucide recolorées.
