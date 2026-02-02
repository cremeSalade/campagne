#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  type: ignore

import tkinter as tk
from tkinter import filedialog, colorchooser, ttk
import pandas as pd
import networkx as nx
import json
import os
from pathlib import Path

class SocialNetworkGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Générateur de Réseau Social")
        self.root.geometry("700x900")
        
        self.csv_path = None
        self.output_path = None
        
        # Couleurs par défaut
        self.bg_color = "#ffffff"
        self.node_color = "#97c2fc"
        self.relation_colors = {
            1: "#ffd700",  # Jaune pâle - déjà rencontré
            2: "#90ee90",  # Vert clair - potes/amies
            3: "#87ceeb",  # Bleu clair - coloc
            4: "#dda0dd",  # Violet clair - famille
            5: "#ff69b4"   # Rose - amour
        }
        
        # Poids par défaut (influence la distance)
        self.relation_weights = {
            1: 0.5,
            2: 1.0,
            3: 1.5,
            4: 2.0,
            5: 2.5
        }
        
        # Paramètres de physique par défaut
        self.physics_params = {
            'springLength': 200,
            'springConstant': 0.02,
            'damping': 0.05,
            'centralGravity': 0.1
        }
        
        # Option edges droites
        self.straight_edges = tk.BooleanVar(value=False)
        
        self.create_widgets()
    
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Section fichier CSV
        ttk.Label(main_frame, text="Fichier CSV:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        self.file_label = ttk.Label(file_frame, text="Aucun fichier sélectionné", relief=tk.SUNKEN, width=50)
        self.file_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(file_frame, text="Charger CSV", command=self.load_csv).pack(side=tk.LEFT)
        
        # Section couleurs
        ttk.Label(main_frame, text="Couleurs:", font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=(15, 5))
        
        # Couleur de fond
        ttk.Label(main_frame, text="Fond:").grid(row=3, column=0, sticky=tk.W, padx=20)
        self.bg_color_btn = tk.Button(main_frame, text="  ", bg=self.bg_color, width=3, command=lambda: self.choose_color('bg'))
        self.bg_color_btn.grid(row=3, column=1, sticky=tk.W)
        
        # Couleur des nodes
        ttk.Label(main_frame, text="Nodes:").grid(row=4, column=0, sticky=tk.W, padx=20)
        self.node_color_btn = tk.Button(main_frame, text="  ", bg=self.node_color, width=3, command=lambda: self.choose_color('node'))
        self.node_color_btn.grid(row=4, column=1, sticky=tk.W)
        
        # Couleurs des relations
        ttk.Label(main_frame, text="Relations:", font=('Arial', 9, 'bold')).grid(row=5, column=0, sticky=tk.W, padx=20, pady=(10, 5))
        
        relation_labels = {
            1: "Déjà rencontré",
            2: "Potes/Amies",
            3: "Coloc",
            4: "Famille",
            5: "Amour"
        }
        
        self.relation_color_btns = {}
        for i, (rel_id, label) in enumerate(relation_labels.items()):
            ttk.Label(main_frame, text=f"{rel_id}. {label}:").grid(row=6+i, column=0, sticky=tk.W, padx=40)
            btn = tk.Button(main_frame, text="  ", bg=self.relation_colors[rel_id], width=3, 
                          command=lambda r=rel_id: self.choose_color('relation', r))
            btn.grid(row=6+i, column=1, sticky=tk.W)
            self.relation_color_btns[rel_id] = btn
        
        # Section poids
        ttk.Label(main_frame, text="Poids des relations (distance):", font=('Arial', 10, 'bold')).grid(row=11, column=0, sticky=tk.W, pady=(15, 5))
        ttk.Label(main_frame, text="(plus petit = nodes plus proches)", font=('Arial', 8), foreground='gray').grid(row=11, column=1, sticky=tk.W, pady=(15, 5))
        
        self.weight_entries = {}
        for i, (rel_id, label) in enumerate(relation_labels.items()):
            ttk.Label(main_frame, text=f"{rel_id}. {label}:").grid(row=12+i, column=0, sticky=tk.W, padx=20)
            entry = ttk.Entry(main_frame, width=10)
            entry.insert(0, str(self.relation_weights[rel_id]))
            entry.grid(row=12+i, column=1, sticky=tk.W)
            self.weight_entries[rel_id] = entry
        
        # Section physique
        ttk.Label(main_frame, text="Paramètres de physique:", font=('Arial', 10, 'bold')).grid(row=17, column=0, sticky=tk.W, pady=(15, 5))
        
        physics_labels = [
            ('springLength', 'Longueur ressort:', 200),
            ('springConstant', 'Constante ressort:', 0.02),
            ('damping', 'Amortissement:', 0.05),
            ('centralGravity', 'Gravité centrale:', 0.1)
        ]
        
        self.physics_entries = {}
        for i, (param, label, default) in enumerate(physics_labels):
            ttk.Label(main_frame, text=label).grid(row=18+i, column=0, sticky=tk.W, padx=20)
            entry = ttk.Entry(main_frame, width=10)
            entry.insert(0, str(default))
            entry.grid(row=18+i, column=1, sticky=tk.W)
            self.physics_entries[param] = entry
        
        # Tooltip pour la physique
        ttk.Label(main_frame, text="Valeurs plus petites = plus flexible/élastique", 
                 font=('Arial', 8), foreground='gray').grid(row=22, column=0, columnspan=2, sticky=tk.W, padx=20)
        
        # Option edges droites
        ttk.Label(main_frame, text="Options d'affichage:", font=('Arial', 10, 'bold')).grid(row=23, column=0, sticky=tk.W, pady=(15, 5))
        ttk.Checkbutton(main_frame, text="Edges droites (sinon courbes)", 
                       variable=self.straight_edges).grid(row=24, column=0, columnspan=2, sticky=tk.W, padx=20)
        
        # Section log
        ttk.Label(main_frame, text="Log:", font=('Arial', 10, 'bold')).grid(row=25, column=0, sticky=tk.W, pady=(15, 5))
        
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=26, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        scrollbar = ttk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(log_frame, height=8, width=70, yscrollcommand=scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_text.yview)
        
        # Boutons d'action
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=27, column=0, columnspan=3, pady=15)
        
        ttk.Button(button_frame, text="Générer", command=self.generate, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Ouvrir HTML", command=self.open_html, width=15).pack(side=tk.LEFT, padx=5)
    
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def load_csv(self):
        filepath = filedialog.askopenfilename(
            title="Sélectionner un fichier CSV",
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")]
        )
        if filepath:
            self.csv_path = filepath
            self.file_label.config(text=os.path.basename(filepath))
            self.log(f"Fichier chargé: {os.path.basename(filepath)}")
    
    def choose_color(self, color_type, relation_id=None):
        if color_type == 'bg':
            color = colorchooser.askcolor(title="Choisir la couleur de fond", initialcolor=self.bg_color)
            if color[1]:
                self.bg_color = color[1]
                self.bg_color_btn.config(bg=self.bg_color)
        elif color_type == 'node':
            color = colorchooser.askcolor(title="Choisir la couleur des nodes", initialcolor=self.node_color)
            if color[1]:
                self.node_color = color[1]
                self.node_color_btn.config(bg=self.node_color)
        elif color_type == 'relation' and relation_id:
            color = colorchooser.askcolor(title=f"Choisir la couleur de la relation {relation_id}", 
                                         initialcolor=self.relation_colors[relation_id])
            if color[1]:
                self.relation_colors[relation_id] = color[1]
                self.relation_color_btns[relation_id].config(bg=self.relation_colors[relation_id])
    
    def generate(self):
        if not self.csv_path:
            self.log("❌ Erreur: Aucun fichier CSV sélectionné")
            return
        
        try:
            self.log("🔄 Lecture du fichier CSV...")
            
            # Lire le CSV
            df = pd.read_csv(self.csv_path, index_col=0)
            
            # Nettoyer les données
            df = df.replace('n/a', 0)
            df = df.fillna(0)
            
            # Convertir en int
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            
            self.log(f"✅ {len(df)} personnes trouvées")
            
            # Récupérer les poids
            for rel_id in range(1, 6):
                try:
                    self.relation_weights[rel_id] = float(self.weight_entries[rel_id].get())
                except ValueError:
                    self.log(f"⚠️  Poids invalide pour relation {rel_id}, utilisation de la valeur par défaut")
            
            # Récupérer les paramètres de physique
            for param in self.physics_params.keys():
                try:
                    self.physics_params[param] = float(self.physics_entries[param].get())
                except ValueError:
                    self.log(f"⚠️  Paramètre physique {param} invalide, utilisation de la valeur par défaut")
            
            # Créer le graphe NetworkX
            self.log("🔄 Création du graphe...")
            G = nx.Graph()
            
            # Ajouter les nodes
            for person in df.index:
                G.add_node(person)
            
            # Ajouter les edges
            edges_count = {i: 0 for i in range(1, 6)}
            for i, person1 in enumerate(df.index):
                for j, person2 in enumerate(df.columns):
                    if i < j:  # Éviter les doublons
                        rel = df.loc[person1, person2]
                        if rel > 0:
                            # Poids inversé pour la distance : plus petit poids = nodes plus proches
                            distance = self.physics_params['springLength'] / self.relation_weights[int(rel)]
                            G.add_edge(person1, person2, relation=int(rel), 
                                     weight=self.relation_weights[int(rel)],
                                     length=distance)
                            edges_count[int(rel)] += 1
            
            for rel_id, count in edges_count.items():
                if count > 0:
                    self.log(f"  - Type {rel_id}: {count} relations")
            
            # Générer le HTML
            self.log("🔄 Génération du fichier HTML...")
            html_content = self.generate_html(G)
            
            # Sauvegarder
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.output_path = os.path.join(script_dir, "network_graph.html")
            
            with open(self.output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.log(f"✅ Fichier généré: {os.path.basename(self.output_path)}")
            self.log("🎉 Génération terminée avec succès!")
            
        except Exception as e:
            self.log(f"❌ Erreur: {str(e)}")
    
    def generate_html(self, G):
        # Préparer les données pour vis.js
        nodes_data = []
        for i, node in enumerate(G.nodes()):
            nodes_data.append({
                'id': i,
                'label': node,
                'color': self.node_color,
                'font': {'color': '#000000'}
            })
        
        # Créer un mapping nom -> id
        node_mapping = {node: i for i, node in enumerate(G.nodes())}
        
        edges_data = []
        for person1, person2, data in G.edges(data=True):
            rel = data['relation']
            edge = {
                'from': node_mapping[person1],
                'to': node_mapping[person2],
                'color': self.relation_colors[rel],
                'width': data['weight'],
                'value': data['weight'],
                'length': data['length']
            }
            edges_data.append(edge)
        
        # Configuration des edges (droites ou courbes)
        if self.straight_edges.get():
            edge_smooth = 'false'
        else:
            edge_smooth = '{ type: "continuous", roundness: 0.5 }'
        
        html_template = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Réseau Social</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            background-color: {self.bg_color};
        }}
        #mynetwork {{
            width: 100%;
            height: 100vh;
            border: 1px solid lightgray;
        }}
        #legend {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            font-size: 14px;
        }}
        .legend-item {{
            margin: 5px 0;
            display: flex;
            align-items: center;
        }}
        .legend-color {{
            width: 30px;
            height: 3px;
            margin-right: 10px;
            display: inline-block;
        }}
    </style>
</head>
<body>
    <div id="mynetwork"></div>
    <div id="legend">
        <strong>Relations:</strong>
        <div class="legend-item">
            <span class="legend-color" style="background-color: {self.relation_colors[1]}; width: 40px;"></span>
            <span>1. Déjà rencontré</span>
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background-color: {self.relation_colors[2]}; width: 40px;"></span>
            <span>2. Potes/Amies</span>
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background-color: {self.relation_colors[3]}; width: 40px;"></span>
            <span>3. Coloc</span>
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background-color: {self.relation_colors[4]}; width: 40px;"></span>
            <span>4. Famille</span>
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background-color: {self.relation_colors[5]}; width: 40px;"></span>
            <span>5. Amour</span>
        </div>
    </div>

    <script type="text/javascript">
        // Données du réseau
        var nodes = new vis.DataSet({json.dumps(nodes_data, ensure_ascii=False)});
        var edges = new vis.DataSet({json.dumps(edges_data, ensure_ascii=False)});

        // Configuration du réseau
        var container = document.getElementById('mynetwork');
        var data = {{
            nodes: nodes,
            edges: edges
        }};
        
        var options = {{
            nodes: {{
                shape: 'dot',
                size: 20,
                font: {{
                    size: 14,
                    color: '#000000'
                }},
                borderWidth: 2,
                borderWidthSelected: 3
            }},
            edges: {{
                smooth: {edge_smooth},
                scaling: {{
                    min: 1,
                    max: 5
                }}
            }},
            physics: {{
                enabled: true,
                barnesHut: {{
                    gravitationalConstant: -8000,
                    centralGravity: {self.physics_params['centralGravity']},
                    springLength: {self.physics_params['springLength']},
                    springConstant: {self.physics_params['springConstant']},
                    damping: {self.physics_params['damping']},
                    avoidOverlap: 0.1
                }},
                stabilization: {{
                    iterations: 1000,
                    updateInterval: 25
                }}
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 200,
                navigationButtons: true,
                keyboard: true
            }}
        }};

        var network = new vis.Network(container, data, options);
        
        // Événements
        network.on("stabilizationIterationsDone", function () {{
            console.log("Stabilisation terminée");
        }});
    </script>
</body>
</html>"""
        
        return html_template
    
    def open_html(self):
        if self.output_path and os.path.exists(self.output_path):
            import webbrowser
            webbrowser.open('file://' + os.path.abspath(self.output_path))
            self.log("🌐 Ouverture du fichier HTML dans le navigateur...")
        else:
            self.log("❌ Erreur: Aucun fichier HTML généré")

def main():
    root = tk.Tk()
    app = SocialNetworkGenerator(root)
    root.mainloop()

if __name__ == "__main__":
    main()
