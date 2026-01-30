# Générateur de Réseau Social Interactif

## Description
Ce script Python génère un graphique interactif HTML/JavaScript pour visualiser les relations entre personnes dans un groupe.

## Prérequis
```bash
pip install pandas networkx --break-system-packages
```

## Utilisation

### 1. Lancer le script
```bash
python social_network_generator.py
```

### 2. Interface utilisateur
L'interface Tkinter vous permet de :
- **Charger un fichier CSV** : Cliquez sur "Charger CSV" pour sélectionner votre fichier
- **Personnaliser les couleurs** :
  - Fond du graphique
  - Couleur des nodes (personnes)
  - Couleur de chaque type de relation (1-5)
- **Ajuster les poids** : Définir la distance entre les nodes (plus petit = plus proche)
- **Paramètres de physique** : Contrôler la flexibilité et l'élasticité du réseau
  - **Longueur ressort** : Distance de base entre les nodes
  - **Constante ressort** : Rigidité des connexions (plus petit = plus flexible)
  - **Amortissement** : Vitesse de stabilisation (plus petit = plus élastique)
  - **Gravité centrale** : Force vers le centre (plus petit = plus dispersé)
- **Edges droites ou courbes** : Case à cocher pour choisir le style des connexions
- **Générer** : Créer le fichier HTML
- **Ouvrir HTML** : Lancer le graphique dans votre navigateur

### 3. Format du fichier CSV
Le fichier CSV doit être une matrice triangulaire supérieure avec :
- La première colonne contenant les noms (index)
- La première ligne contenant les noms (en-têtes)
- Les valeurs de relation de 0 à 5 :
  - **0** : Ne connaît pas (pas d'edge affiché)
  - **1** : Déjà rencontré
  - **2** : Potes/Amies
  - **3** : Coloc
  - **4** : Famille
  - **5** : Amour

Exemple :
```csv
,Émi,Joy,Anne-Laure,Clem
Émi,n/a,3,0,2
Joy,,n/a,2,5
Anne-Laure,,,n/a,2
Clem,,,,n/a
```

### 4. Graphique interactif
Le fichier HTML généré (`network_graph.html`) utilise vis.js et permet :
- **Déplacer** les nodes en les glissant
- **Zoomer** avec la molette de la souris
- **Naviguer** avec les boutons de navigation
- **Physique interactive** : Les nodes s'attirent et se repoussent naturellement
- **Légende** : Affichée en haut à droite pour identifier les types de relations

## Fonctionnalités avancées

### Personnalisation des couleurs
- Chaque type de relation peut avoir sa propre couleur
- Les couleurs sont choisies via un sélecteur de couleur intuitif
- La saturation augmente avec l'intensité de la relation (de 1 à 5)

### Poids des edges
- Les poids définissent la **distance** entre les nodes connectées
- **Plus petit poids = nodes plus proches** (relation inversée)
- Par exemple : poids 0.5 = très proche, poids 2.5 = plus éloigné
- Affecte la disposition spatiale du graphique

### Paramètres de physique
Les paramètres de physique permettent de contrôler le comportement dynamique du réseau :

- **Longueur ressort (springLength)** : Distance naturelle entre les nodes (valeur par défaut : 200)
  - Plus grand = réseau plus étendu
  - Plus petit = réseau plus compact
  
- **Constante ressort (springConstant)** : Rigidité des connexions (valeur par défaut : 0.02)
  - Plus grand = connexions plus rigides
  - **Plus petit = plus flexible et élastique** (essayez 0.01 pour plus de flexibilité)
  
- **Amortissement (damping)** : Vitesse de stabilisation (valeur par défaut : 0.05)
  - Plus grand = stabilisation rapide
  - **Plus petit = plus élastique** (essayez 0.02 pour plus de rebond)
  
- **Gravité centrale (centralGravity)** : Force vers le centre (valeur par défaut : 0.1)
  - Plus grand = nodes attirées vers le centre
  - Plus petit = réseau plus dispersé

**Pour un réseau plus flexible et élastique**, diminuez ces valeurs :
- springConstant : 0.01 - 0.015
- damping : 0.02 - 0.03
- centralGravity : 0.05 - 0.08

### Edges droites ou courbes
- **Case décochée** (par défaut) : Edges courbes et fluides
- **Case cochée** : Edges parfaitement droites entre les nodes

### Log en temps réel
- Fenêtre de log intégrée pour suivre la génération
- Messages d'erreur clairs en cas de problème
- Statistiques sur le graphique généré

## Structure du projet
```
.
├── social_network_generator.py   # Script principal
├── exemple_relations.csv          # Fichier CSV d'exemple
└── network_graph.html             # Fichier HTML généré (après exécution)
```

## Technologies utilisées
- **Python** : Logique et traitement des données
  - tkinter : Interface graphique
  - pandas : Lecture et manipulation du CSV
  - networkx : Création du graphe
- **JavaScript** : Visualisation interactive
  - vis.js : Rendu du graphe avec physique
- **HTML/CSS** : Structure et style de la page

## Exemple de résultat
Le graphique généré affiche :
- Tous les noms comme des nodes grises avec labels
- Des edges colorées selon le type de relation
- Une physique qui organise automatiquement le graphique
- Une légende pour comprendre les couleurs

## Conseils
- **Distances** : Utilisez des poids entre 0.3 et 3.0 pour de meilleurs résultats visuels
  - Relations fortes (famille, amour) : 1.5 - 2.5 (plus éloignées)
  - Relations moyennes (potes, coloc) : 0.8 - 1.2 (distance moyenne)
  - Relations faibles (déjà rencontré) : 0.3 - 0.7 (très proches)
- **Physique flexible** : Pour un réseau plus élastique, réduisez springConstant (0.01) et damping (0.02-0.03)
- **Couleurs** : Les couleurs pastel fonctionnent mieux pour différencier les relations
- **Stabilisation** : Le graphique peut prendre quelques secondes à se stabiliser au chargement
- **Edges** : Les edges courbes sont plus esthétiques, les edges droites plus lisibles pour les réseaux complexes
