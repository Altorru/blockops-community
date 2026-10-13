# BlockOps — kit opérateur / operator kit

**Cinq places prévues ; aucun participant recruté, aucune installation humaine validée.** Distribution en attente de destinataires et canal explicitement autorisés. Pack gratuit MIT ; aucun achat, compte cloud ou abonnement.

## Remise du pack

Donner le tar.gz et son SHA256SUMS, la version/commit, README, ce protocole et les limites du rapport de livraison. Conserver la preuve de la version remise à chaque participant. Le candidat reste en validation ; ne pas présenter une fixture comme une recette Minecraft réelle. Pas de données ou de monde de production dans le pilote.

## Parcours FR (15–20 minutes prévus, durée à mesurer)

1. Choisir un hôte Docker de test et un dossier frais ; vérifier 4218 libre. Chronométrer depuis la première commande jusqu’au premier écran utile. Lire README avant de démarrer.
2. Vérifier le checksum et extraire le pack. Lancer la fixture isolée selon README. Noter version Docker, système/architecture, réussite ou message précis. Ne pas fournir le mot de passe, le bearer, les logs contenant des joueurs ou le monde au mainteneur.
3. Créer une copie depuis la console. Arrêter, modifier uniquement le `level.dat` texte de **la fixture sans Minecraft**, puis restaurer la copie. Constater serveur laissé arrêté et checksum original ; redémarrer. `scripts/verify_fixture.py` réalise ce drill seulement sur la cible jetable `blockops-fixture` et jamais sur un monde Java réel.
4. Tester le compte viewer : état visible, commandes interdites. Noter tout incident ou délai. Arrêter uniquement la stack BlockOps test ; conserver les fichiers voulus.
5. Après validation de la fixture et accord sur un vrai serveur Java jetable/EULA existante, suivre `launch/JAVA_TEST.md`. Le vrai `level.dat` binaire ne doit jamais être modifié comme un fichier texte.
6. Reporter installation, première copie, restauration, durée, incidents, minutes d’assistance et besoin cloud explicite dans `state/pilot-results.csv` (copie privée du modèle). Les créneaux « not_enrolled » ne comptent pas comme utilisateurs.

## English drill

Verify the archive hash; extract into a fresh directory on an authorized test Docker host. Follow README's disposable fixture setup. Measure time to useful UI, first backup and exact restore; check viewer denial. Never run the fixture mutation script against a real Minecraft world. Record incidents, support minutes and an explicit cloud request, if any. Keep passwords, player logs and worlds private. Stop only the owned test stack. Real Java testing uses the separately authorized protocol below.

## Questions après utilisation

- Avez-vous installé et restauré sans aide ? Où avez-vous hésité ?
- Quelle erreur ou procédure avez-vous rencontrée, et combien de minutes d’assistance ?
- Le self-hosted suffit-il ? Sinon, quelle opération voulez-vous réellement confier au cloud ?
- Si un cloud sans CPU Minecraft était proposé à 4,99 EUR/mois, le souhaiteriez-vous et pourquoi ? Une réponse positive ne vaut pas achat.

Codes anonymes, accord de participation, aucune adresse personnelle dans le Git public/privé. Ne pas enregistrer les logs bruts. L’opérateur conserve ses fichiers ; exporter seulement les mesures consenties. Après décision, supprimer les mesures nominatives éventuelles du registre local.

## Mesure et décision

```sh
mkdir -p state
cp -n launch/pilot-template.csv state/pilot-results.csv
python3 scripts/summarize_pilot.py state/pilot-results.csv
```

Objectif : cinq installations avec copie et restauration exactes, incidents documentés et support mesuré. Aucun pourcentage de conversion statistique à partir de cinq personnes. Le coût de support utilise une hypothèse explicite de 40 EUR/h ; les minutes doivent être observées. Garder le self-hosted tant que demande cloud et coûts restent inconnus ; aucune infrastructure payante à ouvrir.

Guide public : https://blockops.altorru.fr/guide.html. Kit remise/acquisition sans envoi : `launch/ACQUISITION_KIT.md`. Outils Java complémentaires livrés séparément du candidat applicatif historique ; vérifier leurs SHA avant usage.
