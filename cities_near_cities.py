import requests
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from math import radians, sin, cos, sqrt, atan2
import json
import csv
import webbrowser
import urllib.parse

class CitySearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Recherche de villes à proximité")
        self.root.geometry("900x700")
        
        # Coordonnées des villes prédéfinies
        self.city_coordinates = {
            'Paris': {'lat': 48.8566, 'lon': 2.3522},
            'Marseille': {'lat': 43.2965, 'lon': 5.3698},
            'Lyon': {'lat': 45.7640, 'lon': 4.8357},
            'Toulouse': {'lat': 43.6047, 'lon': 1.4442},
            'Nice': {'lat': 43.7102, 'lon': 7.2620},
            'Nantes': {'lat': 47.2184, 'lon': -1.5536},
            'Montpellier': {'lat': 43.6108, 'lon': 3.8767},
            'Strasbourg': {'lat': 48.5734, 'lon': 7.7521},
            'Bordeaux': {'lat': 44.8378, 'lon': -0.5792},
            'Lille': {'lat': 50.6292, 'lon': 3.0573},
            'Rennes': {'lat': 48.1173, 'lon': -1.6778},
            'Reims': {'lat': 49.2583, 'lon': 4.0317},
            'Saint-Étienne': {'lat': 45.4397, 'lon': 4.3872},
            'Toulon': {'lat': 43.1242, 'lon': 5.9280},
            'Grenoble': {'lat': 45.1885, 'lon': 5.7245},
            'Dijon': {'lat': 47.3220, 'lon': 5.0415},
            'Angers': {'lat': 47.4784, 'lon': -0.5632},
            'Nîmes': {'lat': 43.8367, 'lon': 4.3601},
            'Villeurbanne': {'lat': 45.7662, 'lon': 4.8794},
            'Le Mans': {'lat': 48.0077, 'lon': 0.1984},
            'Clermont-Ferrand': {'lat': 45.7772, 'lon': 3.0870},
            'Aix-en-Provence': {'lat': 43.5297, 'lon': 5.4474},
            'Brest': {'lat': 48.3905, 'lon': -4.4861},
            'Tours': {'lat': 47.3941, 'lon': 0.6848},
            'Amiens': {'lat': 49.8941, 'lon': 2.2958},
            'Limoges': {'lat': 45.8336, 'lon': 1.2611},
            'Annecy': {'lat': 45.8992, 'lon': 6.1294},
            'Boulogne-Billancourt': {'lat': 48.8350, 'lon': 2.2397},
            'Perpignan': {'lat': 42.6886, 'lon': 2.8948},
            'Besançon': {'lat': 47.2380, 'lon': 6.0243},
            'Orléans': {'lat': 47.9029, 'lon': 1.9093},
            'Metz': {'lat': 49.1193, 'lon': 6.1757},
            'Rouen': {'lat': 49.4432, 'lon': 1.0993},
            'Mulhouse': {'lat': 47.7508, 'lon': 7.3359},
            'Caen': {'lat': 49.1829, 'lon': -0.3707},
            'Nancy': {'lat': 48.6921, 'lon': 6.1844},
            'Argenteuil': {'lat': 48.9474, 'lon': 2.2466},
            'Saint-Denis': {'lat': 48.9362, 'lon': 2.3574},
            'Roubaix': {'lat': 50.6942, 'lon': 3.1746},
            'Tourcoing': {'lat': 50.7236, 'lon': 3.1609},
            'Nanterre': {'lat': 48.8925, 'lon': 2.2069},
            'Avignon': {'lat': 43.9493, 'lon': 4.8055},
            'Poitiers': {'lat': 46.5802, 'lon': 0.3404},
            'Versailles': {'lat': 48.8048, 'lon': 2.1203},
            'Courbevoie': {'lat': 48.8977, 'lon': 2.2531},
            'Créteil': {'lat': 48.7903, 'lon': 2.4555},
            'Pau': {'lat': 43.2951, 'lon': -0.3708},
            'La Rochelle': {'lat': 46.1603, 'lon': -1.1511},
            'Béziers': {'lat': 43.3442, 'lon': 3.2150},
            'Narbonne': {'lat': 43.1839, 'lon': 3.0044}
        }
        
        self.reference_cities = ['Montpellier', 'Béziers', 'Toulouse']
        self.current_results = []  # Stocker les résultats actuels
        self.current_communes_data = {}  # Stocker les données complètes des communes
        
        self.setup_ui()
    
    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Titre
        title = ttk.Label(main_frame, text="🗺️ Recherche de villes à proximité", 
                         font=('Arial', 16, 'bold'))
        title.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Section villes de référence
        ref_frame = ttk.LabelFrame(main_frame, text="Villes de référence", padding="10")
        ref_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Liste des villes de référence
        self.cities_listbox = tk.Listbox(ref_frame, height=4)
        self.cities_listbox.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5)
        self.update_cities_listbox()
        
        # Dropdown pour ajouter une ville
        self.city_var = tk.StringVar()
        city_combo = ttk.Combobox(ref_frame, textvariable=self.city_var, 
                                  values=list(self.city_coordinates.keys()), width=20)
        city_combo.grid(row=1, column=0, padx=5, pady=5)
        
        add_btn = ttk.Button(ref_frame, text="Ajouter", command=self.add_city)
        add_btn.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        remove_btn = ttk.Button(ref_frame, text="Retirer sélection", command=self.remove_city)
        remove_btn.grid(row=1, column=2, padx=5, pady=5)
        
        # Section paramètres
        param_frame = ttk.LabelFrame(main_frame, text="Paramètres de recherche", padding="10")
        param_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Population minimale
        ttk.Label(param_frame, text="Population minimale:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.min_pop = tk.IntVar(value=8000)
        ttk.Entry(param_frame, textvariable=self.min_pop, width=15).grid(row=0, column=1, padx=5, pady=5)
        
        # Population maximale
        ttk.Label(param_frame, text="Population maximale:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.max_pop = tk.IntVar(value=30000)
        ttk.Entry(param_frame, textvariable=self.max_pop, width=15).grid(row=1, column=1, padx=5, pady=5)
        
        # Distance minimale
        ttk.Label(param_frame, text="Distance min (km):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.min_distance = tk.IntVar(value=10)
        ttk.Entry(param_frame, textvariable=self.min_distance, width=15).grid(row=2, column=1, padx=5, pady=5)
        
        # Distance maximale
        ttk.Label(param_frame, text="Distance max (km):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.max_distance = tk.IntVar(value=300)
        ttk.Entry(param_frame, textvariable=self.max_distance, width=15).grid(row=3, column=1, padx=5, pady=5)
        
        # Nombre max de villes sur la carte
        ttk.Label(param_frame, text="Villes max sur carte:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.max_cities_map = tk.IntVar(value=200)
        ttk.Entry(param_frame, textvariable=self.max_cities_map, width=15).grid(row=4, column=1, padx=5, pady=5)
        
        # Bouton rechercher
        search_btn = ttk.Button(main_frame, text="🔍 Rechercher", command=self.search_cities)
        search_btn.grid(row=3, column=0, columnspan=3, pady=10)
        
        # Boutons d'export
        export_frame = ttk.Frame(main_frame)
        export_frame.grid(row=4, column=0, columnspan=3, pady=5)
        
        export_csv_btn = ttk.Button(export_frame, text="💾 Exporter en CSV", command=self.export_csv)
        export_csv_btn.grid(row=0, column=0, padx=5)
        
        export_json_btn = ttk.Button(export_frame, text="💾 Exporter en JSON", command=self.export_json)
        export_json_btn.grid(row=0, column=1, padx=5)
        
        map_btn = ttk.Button(export_frame, text="🗺️ Voir sur la carte", command=self.open_map)
        map_btn.grid(row=0, column=2, padx=5)
        
        # Label résultats
        self.result_label = ttk.Label(main_frame, text="", font=('Arial', 10, 'bold'))
        self.result_label.grid(row=5, column=0, columnspan=3, pady=5)
        
        # Tableau des résultats
        result_frame = ttk.Frame(main_frame)
        result_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Scrollbars
        vsb = ttk.Scrollbar(result_frame, orient="vertical")
        hsb = ttk.Scrollbar(result_frame, orient="horizontal")
        
        # Treeview
        self.tree = ttk.Treeview(result_frame, columns=('ville', 'cp', 'population', 'distance', 'reference', 'altitude', 'temperature'),
                                show='headings', yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Colonnes
        self.tree.heading('ville', text='Ville')
        self.tree.heading('cp', text='CP')
        self.tree.heading('population', text='Population')
        self.tree.heading('distance', text='Distance (km)')
        self.tree.heading('reference', text='Proche de')
        self.tree.heading('altitude', text='Altitude (m)')
        self.tree.heading('temperature', text='Temp. moy. (°C)')
        
        self.tree.column('ville', width=200)
        self.tree.column('cp', width=70)
        self.tree.column('population', width=100)
        self.tree.column('distance', width=100)
        self.tree.column('reference', width=150)
        self.tree.column('altitude', width=100)
        self.tree.column('temperature', width=120)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Configuration du redimensionnement
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
    
    def update_cities_listbox(self):
        self.cities_listbox.delete(0, tk.END)
        for city in self.reference_cities:
            self.cities_listbox.insert(tk.END, city)
    
    def add_city(self):
        city = self.city_var.get()
        if city and city not in self.reference_cities:
            self.reference_cities.append(city)
            self.update_cities_listbox()
        self.city_var.set('')
    
    def remove_city(self):
        selection = self.cities_listbox.curselection()
        if selection:
            city = self.cities_listbox.get(selection[0])
            self.reference_cities.remove(city)
            self.update_cities_listbox()
    
    def get_elevation(self, lat, lon):
        """Récupère l'altitude via l'API open-elevation"""
        try:
            url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data['results'][0]['elevation']
        except:
            pass
        return None
    
    def estimate_temperature(self, lat, altitude):
        """Estime la température moyenne annuelle basée sur la latitude et l'altitude"""
        # Formule simplifiée basée sur le gradient thermique
        # Température de référence à latitude 45° et altitude 0m : environ 12°C
        base_temp = 12.0
        
        # Effet de la latitude (environ -0.6°C par degré de latitude vers le nord)
        lat_effect = (45 - lat) * 0.6
        
        # Effet de l'altitude (environ -0.65°C par 100m)
        if altitude:
            alt_effect = -(altitude / 100) * 0.65
        else:
            alt_effect = 0
        
        temp = base_temp + lat_effect + alt_effect
        return round(temp, 1)
    
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        R = 6371  # Rayon de la Terre en km
        
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def search_cities(self):
        if not self.reference_cities:
            messagebox.showwarning("Attention", "Veuillez ajouter au moins une ville de référence")
            return
        
        # Vider le tableau
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.result_label.config(text="🔄 Recherche en cours...")
        self.root.update()
        
        try:
            # Récupération des données
            url = "https://geo.api.gouv.fr/communes"
            params = {
                'fields': 'nom,code,codesPostaux,population,centre',
                'format': 'json',
                'limit': 40000
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            communes = response.json()
            
            results = {}
            min_pop = self.min_pop.get()
            max_pop = self.max_pop.get()
            min_dist = self.min_distance.get()
            max_dist = self.max_distance.get()
            
            for commune in communes:
                pop = commune.get('population', 0)
                
                if min_pop <= pop <= max_pop:
                    centre = commune.get('centre', {})
                    if 'coordinates' in centre:
                        lon, lat = centre['coordinates']
                        
                        min_distance_to_ref = float('inf')
                        closest_city = ''
                        
                        for ref_city in self.reference_cities:
                            coords = self.city_coordinates.get(ref_city)
                            if coords:
                                distance = self.haversine_distance(
                                    coords['lat'], coords['lon'], lat, lon
                                )
                                if distance < min_distance_to_ref:
                                    min_distance_to_ref = distance
                                    closest_city = ref_city
                        
                        if min_dist <= min_distance_to_ref <= max_dist:
                            key = commune['code']
                            if key not in results or results[key]['distance'] > min_distance_to_ref:
                                results[key] = {
                                    'nom': commune['nom'],
                                    'population': pop,
                                    'distance': round(min_distance_to_ref, 1),
                                    'code_postal': commune.get('codesPostaux', [''])[0],
                                    'ville_reference': closest_city,
                                    'lat': lat,
                                    'lon': lon
                                }
            
            # Tri par distance
            sorted_results = sorted(results.values(), key=lambda x: x['distance'])
            
            # Enrichir avec altitude et température
            self.result_label.config(text="🔄 Récupération des altitudes...")
            self.root.update()
            
            for i, city in enumerate(sorted_results):
                if i % 10 == 0:  # Mise à jour du statut tous les 10 villes
                    self.result_label.config(text=f"🔄 Récupération des altitudes... ({i+1}/{len(sorted_results)})")
                    self.root.update()
                
                altitude = self.get_elevation(city['lat'], city['lon'])
                city['altitude'] = altitude if altitude is not None else "N/A"
                
                if altitude is not None:
                    city['temperature'] = self.estimate_temperature(city['lat'], altitude)
                else:
                    city['temperature'] = self.estimate_temperature(city['lat'], 0)
            
            # Stocker les résultats
            self.current_results = sorted_results
            
            # Affichage dans le tableau
            for city in sorted_results:
                alt_display = f"{city['altitude']}" if isinstance(city['altitude'], int) else city['altitude']
                temp_display = f"{city['temperature']}" if city['temperature'] else "N/A"
                
                self.tree.insert('', tk.END, values=(
                    city['nom'],
                    city['code_postal'],
                    f"{city['population']:,}".replace(',', ' '),
                    city['distance'],
                    city['ville_reference'],
                    alt_display,
                    temp_display
                ))
            
            self.result_label.config(text=f"✅ {len(sorted_results)} villes trouvées")
            
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erreur", f"Erreur lors de la récupération des données:\n{str(e)}")
            self.result_label.config(text="❌ Erreur")
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue:\n{str(e)}")
            self.result_label.config(text="❌ Erreur")
    
    def export_csv(self):
        if not self.current_results:
            messagebox.showwarning("Attention", "Aucun résultat à exporter. Veuillez d'abord effectuer une recherche.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")],
            initialfile="resultats_villes.csv"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['Ville', 'Code Postal', 'Population', 'Distance (km)', 'Proche de', 'Altitude (m)', 'Temperature moyenne (°C)']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for city in self.current_results:
                        alt_val = city['altitude'] if isinstance(city['altitude'], int) else ''
                        temp_val = city['temperature'] if city['temperature'] else ''
                        
                        writer.writerow({
                            'Ville': city['nom'],
                            'Code Postal': city['code_postal'],
                            'Population': city['population'],
                            'Distance (km)': city['distance'],
                            'Proche de': city['ville_reference'],
                            'Altitude (m)': alt_val,
                            'Temperature moyenne (°C)': temp_val
                        })
                
                messagebox.showinfo("Succès", f"Données exportées avec succès dans:\n{filename}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'export CSV:\n{str(e)}")
    
    def export_json(self):
        if not self.current_results:
            messagebox.showwarning("Attention", "Aucun résultat à exporter. Veuillez d'abord effectuer une recherche.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")],
            initialfile="resultats_villes.json"
        )
        
        if filename:
            try:
                export_data = {
                    'parametres': {
                        'villes_reference': self.reference_cities,
                        'population_min': self.min_pop.get(),
                        'population_max': self.max_pop.get(),
                        'distance_min': self.min_distance.get(),
                        'distance_max': self.max_distance.get()
                    },
                    'nombre_resultats': len(self.current_results),
                    'resultats': [
                        {
                            'ville': city['nom'],
                            'code_postal': city['code_postal'],
                            'population': city['population'],
                            'distance_km': city['distance'],
                            'ville_reference': city['ville_reference']
                        }
                        for city in self.current_results
                    ]
                }
                
                with open(filename, 'w', encoding='utf-8') as jsonfile:
                    json.dump(export_data, jsonfile, ensure_ascii=False, indent=2)
                
                messagebox.showinfo("Succès", f"Données exportées avec succès dans:\n{filename}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'export JSON:\n{str(e)}")
    
    def open_map(self):
        if not self.current_results:
            messagebox.showwarning("Attention", "Aucun résultat à afficher. Veuillez d'abord effectuer une recherche.")
            return
        
        try:
            # Calculer le centre de la carte (moyenne des coordonnées)
            if self.current_results:
                avg_lat = sum(city['lat'] for city in self.current_results) / len(self.current_results)
                avg_lon = sum(city['lon'] for city in self.current_results) / len(self.current_results)
            else:
                avg_lat, avg_lon = 46.5, 2.5
            
            # Créer un fichier HTML avec Leaflet
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Carte des villes</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
        integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
        crossorigin=""/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
        integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
        crossorigin=""></script>
    <style>
        body {{ margin: 0; padding: 0; }}
        #map {{ height: 100vh; width: 100%; }}
        .city-popup {{ font-family: Arial, sans-serif; }}
        .city-popup h3 {{ margin: 0 0 10px 0; color: #2c3e50; font-size: 16px; }}
        .city-popup p {{ margin: 5px 0; font-size: 14px; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        // Initialiser la carte
        var map = L.map('map').setView([{avg_lat}, {avg_lon}], 8);
        
        // Ajouter la couche de tuiles OpenStreetMap
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19
        }}).addTo(map);
        
        // Créer des icônes personnalisées
        var redIcon = new L.Icon({{
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        }});
        
        var blueIcon = new L.Icon({{
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        }});
        
        // Groupe de marqueurs pour ajuster la vue
        var markers = [];
        
"""
            
            # Ajouter les villes de référence
            for ref_city in self.reference_cities:
                coords = self.city_coordinates.get(ref_city)
                if coords:
                    html_content += f"""
        var marker = L.marker([{coords['lat']}, {coords['lon']}], {{icon: redIcon}})
            .bindPopup('<div class="city-popup"><h3>{ref_city}</h3><p><strong>Ville de référence</strong></p></div>')
            .addTo(map);
        markers.push(marker);
"""
            
            # Ajouter les résultats (limiter selon le paramètre utilisateur)
            max_cities = self.max_cities_map.get()
            results_to_show = self.current_results[:max_cities]
            for city in results_to_show:
                city_name = city['nom'].replace("'", "\\'")
                html_content += f"""
        var marker = L.marker([{city['lat']}, {city['lon']}], {{icon: blueIcon}})
            .bindPopup('<div class="city-popup"><h3>{city_name}</h3><p>Population: {city['population']:,}</p><p>Distance: {city['distance']} km</p><p>Proche de: {city['ville_reference']}</p></div>')
            .addTo(map);
        markers.push(marker);
"""
            
            html_content += """
        // Ajuster la vue pour afficher tous les marqueurs
        if (markers.length > 0) {
            var group = new L.featureGroup(markers);
            map.fitBounds(group.getBounds().pad(0.1));
        }
    </script>
</body>
</html>
"""
            
            # Sauvegarder le fichier
            import tempfile
            import os
            
            # Créer un fichier dans le dossier temporaire
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, 'carte_villes.html')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Ouvrir dans le navigateur
            webbrowser.open('file://' + temp_file)
            
            if len(self.current_results) > max_cities:
                messagebox.showinfo("Carte ouverte", 
                    f"La carte s'est ouverte dans votre navigateur.\n\n"
                    f"🔴 Marqueurs rouges = Villes de référence\n"
                    f"🔵 Marqueurs bleus = Villes trouvées\n\n"
                    f"Note: {max_cities} villes affichées sur {len(self.current_results)} résultats.\n"
                    f"Modifiez 'Villes max sur carte' pour en afficher plus.")
            else:
                messagebox.showinfo("Carte ouverte", 
                    "La carte s'est ouverte dans votre navigateur.\n\n"
                    "🔴 Marqueurs rouges = Villes de référence\n"
                    "🔵 Marqueurs bleus = Villes trouvées")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'ouverture de la carte:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CitySearchApp(root)
    root.mainloop()