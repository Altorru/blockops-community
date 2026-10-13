# BlockOps — identité

**Your server. Less babysitting.** Une console calme, des opérations explicites et un chemin de retour visible.

## Logo : un monde et sa copie

Le symbole original superpose deux blocs : le monde actif et sa sauvegarde. Il relie l’univers Minecraft à la sauvegarde sans reprendre sa marque. Le wordmark Manrope est vectorisé ; aucun besoin d’installer une police pour utiliser les SVG.

| Asset | Usage |
|---|---|
| `assets/logo-dark.svg` | Logo horizontal sur graphite |
| `assets/logo-light.svg` | Logo horizontal sur fond clair |
| `assets/logo-monochrome.svg` | Impression ou usage une couleur sur fond clair |
| `assets/logo.svg` | Alias de la variante sombre |
| `assets/mark.svg` | Symbole seul, fond transparent |
| `assets/icon.svg`, `assets/icon-light.svg` | Icône d’application avec plateau et favicon |
| `assets/world-floating.png` | Monde et sauvegarde en PNG transparent, hero et connexion |
| `assets/world-hero.png` | Source originale avec fond conservée |
| `assets/system-map.svg` | Illustration originale : monde → copie locale |
| `assets/social-card.svg` | Carte de partage 1200 × 630 |

Respecter les proportions, prévoir au moins 16 px de dégagement pour le logo horizontal et éviter les effets, contours ou recolorations hors palette. Symbole seul sous 160 px de largeur disponible ; logo horizontal à partir de 160 px. La variante monochrome foncée est réservée aux fonds clairs.

## Deux thèmes assumés

| Rôle | Sombre | Clair |
|---|---|---|
| Fond | Graphite `#101713` | Minéral `#F4F5EF` |
| Surface | `#19211C` | `#FFFFFF` |
| Texte | `#F4F6F1` | `#18201C` |
| Texte secondaire | `#B3BEB0` | `#53604F` |
| Accent/action principale | Citron `#D1ED83` | Olive `#496C16` |
| Texte sur action | `#1B2612` | `#FFFFFF` |
| Erreur/arrêt | `#FFB4A5` | `#A63725` |
| À examiner | `#E8CF9B` | `#725320` |

Tokens complets : `assets/design-tokens.json`, appliqués via `web/style.css`. La couleur accompagne un libellé ou un pictogramme ; elle ne constitue jamais l’unique information. Rouge pour arrêter/erreur, ambre pour les avertissements et la fixture, accent pour l’action principale. Aucun sceau de confiance inventé.

Manrope variable 200–800, hébergée localement sous OFL. Chiffres tabulaires ; monospace réservé aux horaires, empreintes et repères techniques. Panels 16 px, boutons 9 px, commandes tactiles de 44 px de haut minimum. Les valeurs sont réelles et les données de fixture sont indiquées.

## Icônes et confiance

Les Lucide officielles accompagnent les actions ; le logo reste un dessin original. Voir `ICONOGRAPHY.md` pour chaque choix et les licences. Les boutons importants conservent leur texte, la restauration reste distincte du redémarrage et les mutations demandent confirmation. Les thèmes et la langue sont mémorisés localement ; aucun CDN ou service de police n’est requis.

Galerie locale : `/brand`. Console, connexion, landing et galerie partagent les mêmes couleurs, police et rythme visuel.

## Régénération des sources

Installer `requirements-dev.txt` dans le venv de développement puis :

```sh
python scripts/design_assets.py
mkdir -p dist/vendor
npm pack lucide-static@1.52.0 --pack-destination dist/vendor
python scripts/vendor_icons.py
```

Manrope source : https://github.com/google/fonts/tree/main/ofl/manrope ; licence conservée dans `assets/fonts/OFL.txt`. Les outils de génération ne sont pas nécessaires à l’exécution.

## Hero courant

« Gardez votre monde. L’esprit libre. » : promesse courte, CTA principal rempli, lien vers les usages et illustration 3D dédiée. Asset généré avec image_gen intégré, prompt dans `assets/world-hero.prompt.md`. Cette image est une illustration conceptuelle et ne représente aucun serveur réel. Layout vérifié à 360/768/1280 px.

## Hero flottant

Le monde détouré est posé directement à droite du texte, sans plateau de présentation, cadre ni légende. Édition image_gen intégrée, prompt dans `assets/world-floating.prompt.md`. PNG RGBA avec transparence vérifiée. Flottement CSS lent de 9 s (amplitude réduite sur mobile), lumières locales chaudes sur 7/11 s et reflet sur 13 s. Toutes les animations sont désactivées pour `prefers-reduced-motion: reduce`, vérifié dans le navigateur. Aucune dépendance ou boucle JavaScript ajoutée.
