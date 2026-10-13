# Contribuer / Contributing

Ce dépôt contient Community et une présentation statique. Les corrections de documentation,
accessibilité et traduction sont bienvenues. Vérifier les liens locaux et le
rendu à 360 px avant de proposer une modification ; conserver les mentions
« simulation » et les licences des éléments tiers.

Ne jamais ajouter un accès Docker public, un secret ou un monde client. Ne soumettre
aucun identifiant personnel, log de joueur, capture client ni archive de monde.
Les demandes d’évolution du runtime se discutent via le support sans publier
des données privées ici. Aucune nouvelle dépendance requise pour la démo.

Documentation and accessibility fixes are welcome. Keep simulated data labels
and third-party notices. Never submit credentials, private runtime code, customer
worlds, player logs or personal data. Check local links and the 360 px layout.

Runtime changes: run `python3 -m unittest discover -s tests -v` and validate
backup/restore on a fresh simulated fixture. Do not claim real Java validation
from synthetic tests. Include the regression evidence with your change.
