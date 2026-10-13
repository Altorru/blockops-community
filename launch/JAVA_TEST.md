# Recette Java réelle — préparée, non exécutée

Gate : un environnement de test jetable exact fourni par le propriétaire, avec EULA déjà acceptée. Aucun EULA, nouveau contrat, téléchargement/exécution de serveur ou accès production n’est implicitement autorisé par ce document. Aucun conteneur ni monde tiers ne doit être utilisé. Voir README pour l’agent mono-cible et le montage exact.

## Préparation à valider avec le propriétaire

- Conteneur de test dédié (nom, image/runtime Java et version Minecraft documentés), volume monde dédié et copie indépendante. Le serveur fournit son réseau de statut à l’agent ; aucun port RCON/shell.
- EULA existante acceptée, version et SHA du jar/image enregistrés. Préférer réseau privé de test, aucun port de jeu publié si aucun joueur ne participe.
- UID/GID pouvant sauvegarder/restaurer, espace disponible pour archive + extraction + rollback + safety copy. Restart Docker désactivé. Au moins 30 s d’arrêt gracieux ; ne pas masquer un kill forcé.
- Compte admin de test et viewer ; aucune réutilisation de secrets de production.

## Recette (ne pas utiliser verify_fixture.py)

1. Mesurer boot et statut Server List Ping d’un **vrai** serveur : état Docker, version, nombre de joueurs retourné (0 est valide sans joueur de test). Capturer seulement des logs expurgés.
2. Créer une copie pendant que le serveur tourne. Inspecter les logs d’arrêt/enregistrement du monde et le code de sortie Docker ; pas de kill forcé 137. La console refuse une copie de serveur encore actif ou forcé 137. Constater reprise du serveur et apparition de la copie.
3. Arrêter volontairement. Confirmer arrêt et aucun auto-restart. Lire les empreintes des fichiers de l’archive ; noter le SHA de l’archive.
4. Modifier uniquement un fichier témoin créé pour ce drill dans le dossier de test. **Ne pas écrire du texte dans `level.dat`, region/*.mca ou un fichier NBT.** Sauvegarder indépendamment le monde avant toute mutation.
5. Restaurer via la console. Vérifier toutes les empreintes des fichiers contenus dans l’archive contre le monde restauré, avant redémarrage. Confirmer safety copy et serveur laissé arrêté. Un contrôle du seul `level.dat` ne suffit pas.
6. Redémarrer et attendre le statut Java ; vérifier absence d’erreur de chargement dans les logs. Si un joueur de test est explicitement désigné, se connecter et contrôler la zone témoin ; sinon signaler que cette preuve visuelle reste absente.
7. Rejouer refus viewer, CSRF invalide, bearer absent et routes Docker hors allowlist. Ne tester aucune route sur un proxy tiers.
8. Consigner système, version Java/Minecraft, durée boot/copie/restore, taille archives, durée indisponible, empreintes, résultats, incidents et minutes support dans `evidence/java-test-verification.json` et registre pilote local.

Critère : vraie sauvegarde après arrêt cohérent, empreintes restaurées exactes et redémarrage Java réussi. À ce jour ces preuves manquent. Ne jamais mélanger réponse Java synthétique et serveur réel.

## Dossier exécutable préparé le 8 octobre

Copier `launch/java-verification-template.json` dans `state/java-test/` pour
la saisie privée de la cible réellement autorisée. Tous les résultats restent
non exécutés tant que cette cible et son EULA existante ne sont pas établies.
L'espace VPS de vitrine ne constitue pas une autorisation de serveur Minecraft.

Après restauration, pendant que le serveur reste arrêté :

```sh
python3 scripts/check_java_restore.py /chemin/prive/copie.tar.gz /chemin/monde-test > state/java-test/hash-comparison.json
```

Cet outil lit uniquement les fichiers. Il compare tous les fichiers ordinaires,
détecte fichiers absents/modifiés/supplémentaires, et refuse chemins traversants,
liens et doublons. Il n'extrait rien, n'arrête et ne démarre aucun serveur.
Un code 0 prouve uniquement l'identité des fichiers à cet instant ; les logs
d'arrêt cohérent, la copie de sécurité et le redémarrage Java restent des preuves
séparées. Cinq tests couvrent ces contrôles sur données synthétiques, jamais sur
un monde propriétaire.

Environnement et gate exacte : `launch/JAVA_ENVIRONMENT.md`, modèle `launch/java-target-template.json`, contrôle read-only `scripts/preflight_java.py`. Autorisation générale donnée, référence technique encore absente.
