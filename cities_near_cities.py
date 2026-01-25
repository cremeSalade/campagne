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
        self.root.geometry("1100x1000")
        
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
        
        # Frame pour la liste et les infos
        list_info_frame = ttk.Frame(ref_frame)
        list_info_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        # Colonne gauche: liste des villes
        left_col = ttk.Frame(list_info_frame)
        left_col.grid(row=0, column=0, sticky=(tk.W, tk.N, tk.S), padx=5)
        
        ttk.Label(left_col, text="Villes sélectionnées:", font=('Arial', 9, 'bold')).pack(anchor=tk.W, pady=(0,5))
        
        self.cities_listbox = tk.Listbox(left_col, height=6, width=25)
        self.cities_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.cities_listbox.bind('<<ListboxSelect>>', self.on_city_select)
        
        cities_scroll = ttk.Scrollbar(left_col, orient='vertical', command=self.cities_listbox.yview)
        cities_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.cities_listbox.config(yscrollcommand=cities_scroll.set)
        
        # Colonne droite: infos de la ville sélectionnée
        right_col = ttk.LabelFrame(list_info_frame, text="Informations", padding="10")
        right_col.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        self.info_ville = tk.StringVar(value="Aucune ville sélectionnée")
        self.info_coords = tk.StringVar(value="")
        self.info_region = tk.StringVar(value="")
        
        ttk.Label(right_col, textvariable=self.info_ville, font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(right_col, textvariable=self.info_coords, foreground='#555').grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(right_col, textvariable=self.info_region, foreground='#555').grid(row=2, column=0, sticky=tk.W, pady=2)
        
        self.update_cities_listbox()
        
        # Frame pour les actions
        action_frame = ttk.Frame(ref_frame)
        action_frame.grid(row=1, column=0, columnspan=3, pady=(10, 0))
        
        # Méthode 1: Sélectionner depuis la liste prédéfinie
        select_frame = ttk.LabelFrame(action_frame, text="Ajouter depuis la liste", padding="5")
        select_frame.grid(row=0, column=0, padx=5, sticky=(tk.W, tk.E, tk.N))
        
        self.city_var = tk.StringVar()
        city_combo = ttk.Combobox(select_frame, textvariable=self.city_var, 
                                  values=sorted(list(self.city_coordinates.keys())), width=20)
        city_combo.grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(select_frame, text="➕ Ajouter", command=self.add_city).grid(row=0, column=1, padx=5, pady=5)
        
        # Méthode 2: Rechercher une ville
        search_frame = ttk.LabelFrame(action_frame, text="Rechercher une ville", padding="5")
        search_frame.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E, tk.N))
        
        self.search_city_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_city_var, width=20).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(search_frame, text="🔍 Rechercher", command=self.search_and_add_city).grid(row=0, column=1, padx=5, pady=5)
        
        # Méthode 3: Ajouter manuellement avec coordonnées
        manual_frame = ttk.LabelFrame(action_frame, text="Ajouter manuellement", padding="5")
        manual_frame.grid(row=0, column=2, padx=5, sticky=(tk.W, tk.E, tk.N))
        
        ttk.Button(manual_frame, text="✏️ Coordonnées GPS", command=self.add_city_with_coords).grid(row=0, column=0, padx=5, pady=5)
        
        # Bouton retirer
        ttk.Button(ref_frame, text="🗑️ Retirer la sélection", command=self.remove_city).grid(row=2, column=0, columnspan=3, pady=(10, 0))
        
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
        
        # Options de récupération de données
        options_frame = ttk.LabelFrame(main_frame, text="Options de données", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.fetch_altitude = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Récupérer l'altitude (API Open-Elevation)", 
                       variable=self.fetch_altitude).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.fetch_temperature = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Récupérer la température moyenne (API Open-Meteo)", 
                       variable=self.fetch_temperature).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.show_search_zones = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Afficher les zones de recherche sur la carte", 
                       variable=self.show_search_zones).grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        # Bouton rechercher
        search_btn = ttk.Button(main_frame, text="🔍 Rechercher", command=self.search_cities)
        search_btn.grid(row=4, column=0, columnspan=3, pady=10)
        
        # Boutons d'export
        export_frame = ttk.Frame(main_frame)
        export_frame.grid(row=5, column=0, columnspan=3, pady=5)
        
        export_csv_btn = ttk.Button(export_frame, text="💾 Exporter en CSV", command=self.export_csv)
        export_csv_btn.grid(row=0, column=0, padx=5)
        
        export_json_btn = ttk.Button(export_frame, text="💾 Exporter en JSON", command=self.export_json)
        export_json_btn.grid(row=0, column=1, padx=5)
        
        map_btn = ttk.Button(export_frame, text="🗺️ Voir sur la carte", command=self.open_map)
        map_btn.grid(row=0, column=2, padx=5)
        
        # Label résultats
        self.result_label = ttk.Label(main_frame, text="", font=('Arial', 10, 'bold'))
        self.result_label.grid(row=6, column=0, columnspan=3, pady=5)
        
        # Fenêtre de logs
        log_frame = ttk.LabelFrame(main_frame, text="Logs", padding="5")
        log_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        self.log_text = tk.Text(log_frame, height=5, wrap=tk.WORD, state='disabled')
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        log_scroll = ttk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_scroll.set)
        
        # Tableau des résultats
        result_frame = ttk.Frame(main_frame)
        result_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
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
        
        # Boutons d'édition du tableau
        edit_frame = ttk.Frame(main_frame)
        edit_frame.grid(row=9, column=0, columnspan=3, pady=5)
        
        ttk.Button(edit_frame, text="✏️ Modifier", command=self.edit_selected).grid(row=0, column=0, padx=5)
        ttk.Button(edit_frame, text="🗑️ Supprimer", command=self.delete_selected).grid(row=0, column=1, padx=5)
        ttk.Button(edit_frame, text="➕ Ajouter", command=self.add_city_manual).grid(row=0, column=2, padx=5)
        
        # Configuration du redimensionnement
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(8, weight=1)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
    
    def update_cities_listbox(self):
        self.cities_listbox.delete(0, tk.END)
        for city in self.reference_cities:
            self.cities_listbox.insert(tk.END, city)
    
    def on_city_select(self, event):
        """Afficher les infos de la ville sélectionnée"""
        selection = self.cities_listbox.curselection()
        if selection:
            city_name = self.cities_listbox.get(selection[0])
            coords = self.city_coordinates.get(city_name)
            if coords:
                self.info_ville.set(f"📍 {city_name}")
                self.info_coords.set(f"Coordonnées: {coords['lat']:.4f}°N, {coords['lon']:.4f}°E")
                
                # Déterminer la région approximative
                region = self.get_region_from_coords(coords['lat'], coords['lon'])
                self.info_region.set(f"Région: {region}")
            else:
                self.info_ville.set(f"📍 {city_name}")
                self.info_coords.set("Coordonnées non disponibles")
                self.info_region.set("")
    
    def get_region_from_coords(self, lat, lon):
        """Déterminer une région approximative depuis les coordonnées"""
        if lat > 48.5:
            if lon < 2:
                return "Nord-Ouest"
            elif lon < 5:
                return "Nord"
            else:
                return "Nord-Est"
        elif lat > 45.5:
            if lon < 0:
                return "Ouest"
            elif lon < 3:
                return "Centre-Ouest"
            elif lon < 6:
                return "Centre"
            else:
                return "Est"
        else:
            if lon < 0:
                return "Sud-Ouest"
            elif lon < 3:
                return "Sud-Ouest / Pyrénées"
            elif lon < 6:
                return "Sud / Méditerranée"
            else:
                return "Sud-Est / PACA"
    
    def log(self, message):
        """Ajoute un message dans la fenêtre de logs"""
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update()
    
    def add_city(self):
        city = self.city_var.get()
        if city and city not in self.reference_cities:
            self.reference_cities.append(city)
            self.update_cities_listbox()
            self.log(f"✓ Ville '{city}' ajoutée aux villes de référence")
        self.city_var.set('')
    
    def search_and_add_city(self):
        """Rechercher une ville via l'API et l'ajouter"""
        city_name = self.search_city_var.get().strip()
        if not city_name:
            messagebox.showwarning("Attention", "Veuillez saisir un nom de ville")
            return
        
        try:
            self.log(f"Recherche de '{city_name}'...")
            # Rechercher via l'API geo.gouv.fr
            url = f"https://geo.api.gouv.fr/communes?nom={city_name}&fields=nom,centre,population&limit=1"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    ville = data[0]
                    nom = ville['nom']
                    coords = ville.get('centre', {}).get('coordinates', [])
                    
                    if coords:
                        lon, lat = coords
                        # Ajouter aux coordonnées disponibles
                        self.city_coordinates[nom] = {'lat': lat, 'lon': lon}
                        
                        if nom not in self.reference_cities:
                            self.reference_cities.append(nom)
                            self.update_cities_listbox()
                            self.log(f"✓ Ville '{nom}' trouvée et ajoutée (Lat: {lat:.4f}, Lon: {lon:.4f})")
                            messagebox.showinfo("Succès", f"Ville '{nom}' ajoutée avec succès!")
                        else:
                            self.log(f"⚠ Ville '{nom}' déjà dans la liste")
                    else:
                        messagebox.showwarning("Erreur", "Coordonnées non disponibles pour cette ville")
                        self.log(f"❌ Coordonnées non disponibles pour '{city_name}'")
                else:
                    messagebox.showwarning("Non trouvé", f"Aucune ville trouvée pour '{city_name}'")
                    self.log(f"❌ Ville '{city_name}' non trouvée")
            
            self.search_city_var.set('')
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la recherche:\n{str(e)}")
            self.log(f"❌ Erreur recherche: {str(e)}")
    
    def add_city_with_coords(self):
        """Ajouter une ville manuellement avec coordonnées GPS"""
        coord_window = tk.Toplevel(self.root)
        coord_window.title("Ajouter une ville avec coordonnées")
        coord_window.geometry("400x200")
        
        ttk.Label(coord_window, text="Nom de la ville:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_var = tk.StringVar()
        ttk.Entry(coord_window, textvariable=name_var, width=30).grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(coord_window, text="Latitude (ex: 43.6108):").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        lat_var = tk.StringVar()
        ttk.Entry(coord_window, textvariable=lat_var, width=30).grid(row=1, column=1, padx=10, pady=10)
        
        ttk.Label(coord_window, text="Longitude (ex: 3.8767):").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        lon_var = tk.StringVar()
        ttk.Entry(coord_window, textvariable=lon_var, width=30).grid(row=2, column=1, padx=10, pady=10)
        
        def save_coords():
            try:
                nom = name_var.get().strip()
                lat = float(lat_var.get())
                lon = float(lon_var.get())
                
                if not nom:
                    messagebox.showwarning("Attention", "Veuillez saisir un nom de ville")
                    return
                
                # Valider les coordonnées
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    messagebox.showerror("Erreur", "Coordonnées invalides")
                    return
                
                # Ajouter la ville
                self.city_coordinates[nom] = {'lat': lat, 'lon': lon}
                if nom not in self.reference_cities:
                    self.reference_cities.append(nom)
                    self.update_cities_listbox()
                    self.log(f"✓ Ville '{nom}' ajoutée manuellement (Lat: {lat:.4f}, Lon: {lon:.4f})")
                    messagebox.showinfo("Succès", f"Ville '{nom}' ajoutée avec succès!")
                
                coord_window.destroy()
                
            except ValueError:
                messagebox.showerror("Erreur", "Latitude et Longitude doivent être des nombres")
        
        ttk.Button(coord_window, text="✅ Ajouter", command=save_coords).grid(row=3, column=0, columnspan=2, pady=20)
    
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
    
    def get_temperature(self, lat, lon):
        """Récupère la température moyenne annuelle via l'API Open-Meteo"""
        try:
            # API Open-Meteo pour obtenir les données climatiques historiques
            url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date=2023-01-01&end_date=2023-12-31&daily=temperature_2m_mean&timezone=auto"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                temps = data['daily']['temperature_2m_mean']
                # Calculer la moyenne annuelle
                valid_temps = [t for t in temps if t is not None]
                if valid_temps:
                    return round(sum(valid_temps) / len(valid_temps), 1)
        except:
            pass
        return None
    
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
        self.log("=== Début de la recherche ===")
        self.root.update()
        
        try:
            # Récupération des données
            self.log(f"Récupération des communes depuis l'API...")
            url = "https://geo.api.gouv.fr/communes"
            params = {
                'fields': 'nom,code,codesPostaux,population,centre',
                'format': 'json',
                'limit': 40000
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            communes = response.json()
            self.log(f"✓ {len(communes)} communes récupérées")
            
            results = {}
            min_pop = self.min_pop.get()
            max_pop = self.max_pop.get()
            min_dist = self.min_distance.get()
            max_dist = self.max_distance.get()
            
            self.log(f"Filtrage: pop {min_pop}-{max_pop}, dist {min_dist}-{max_dist} km")
            
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
            self.log(f"✓ {len(sorted_results)} villes correspondent aux critères")
            
            # Enrichir avec altitude et température si demandé
            if self.fetch_altitude.get() or self.fetch_temperature.get():
                total = len(sorted_results)
                self.log(f"Récupération des données supplémentaires...")
                
                for i, city in enumerate(sorted_results):
                    if i % 5 == 0:  # Mise à jour du statut tous les 5 villes
                        status = f"🔄 Récupération des données... ({i+1}/{total})"
                        self.result_label.config(text=status)
                        self.root.update()
                    
                    # Récupérer l'altitude si demandé
                    if self.fetch_altitude.get():
                        altitude = self.get_elevation(city['lat'], city['lon'])
                        city['altitude'] = altitude if altitude is not None else "N/A"
                        if i % 10 == 0:
                            self.log(f"  Altitude {i+1}/{total}...")
                    else:
                        city['altitude'] = "N/A"
                    
                    # Récupérer la température si demandé
                    if self.fetch_temperature.get():
                        temp = self.get_temperature(city['lat'], city['lon'])
                        city['temperature'] = temp if temp is not None else "N/A"
                        if i % 10 == 0:
                            self.log(f"  Température {i+1}/{total}...")
                    else:
                        city['temperature'] = "N/A"
                
                self.log(f"✓ Données supplémentaires récupérées")
            else:
                # Pas de récupération de données
                for city in sorted_results:
                    city['altitude'] = "N/A"
                    city['temperature'] = "N/A"
            
            # Stocker les résultats
            self.current_results = sorted_results
            
            # Affichage dans le tableau
            self.log(f"Affichage des résultats dans le tableau...")
            for city in sorted_results:
                alt_display = str(city['altitude']) if city['altitude'] != "N/A" else "N/A"
                temp_display = str(city['temperature']) if city['temperature'] != "N/A" else "N/A"
                
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
            self.log(f"✓ Recherche terminée avec succès!")
            self.log(f"=== Fin de la recherche ===\n")
            
            self.result_label.config(text=f"✅ {len(sorted_results)} villes trouvées")
            
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erreur", f"Erreur lors de la récupération des données:\n{str(e)}")
            self.result_label.config(text="❌ Erreur")
            self.log(f"❌ Erreur API: {str(e)}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue:\n{str(e)}")
            self.result_label.config(text="❌ Erreur")
            self.log(f"❌ Erreur: {str(e)}")
    
    def edit_selected(self):
        """Modifier l'élément sélectionné dans le tableau"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner une ville à modifier")
            return
        
        item = selection[0]
        values = self.tree.item(item, 'values')
        
        # Créer une fenêtre de dialogue
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Modifier la ville")
        edit_window.geometry("400x350")
        
        # Champs d'édition
        ttk.Label(edit_window, text="Ville:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ville_var = tk.StringVar(value=values[0])
        ttk.Entry(edit_window, textvariable=ville_var, width=30).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(edit_window, text="Code Postal:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        cp_var = tk.StringVar(value=values[1])
        ttk.Entry(edit_window, textvariable=cp_var, width=30).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(edit_window, text="Population:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        pop_var = tk.StringVar(value=values[2].replace(' ', ''))
        ttk.Entry(edit_window, textvariable=pop_var, width=30).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(edit_window, text="Distance (km):").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        dist_var = tk.StringVar(value=values[3])
        ttk.Entry(edit_window, textvariable=dist_var, width=30).grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(edit_window, text="Proche de:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        ref_var = tk.StringVar(value=values[4])
        ttk.Entry(edit_window, textvariable=ref_var, width=30).grid(row=4, column=1, padx=5, pady=5)
        
        ttk.Label(edit_window, text="Altitude (m):").grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
        alt_var = tk.StringVar(value=values[5])
        ttk.Entry(edit_window, textvariable=alt_var, width=30).grid(row=5, column=1, padx=5, pady=5)
        
        ttk.Label(edit_window, text="Temp. moy. (°C):").grid(row=6, column=0, padx=5, pady=5, sticky=tk.W)
        temp_var = tk.StringVar(value=values[6])
        ttk.Entry(edit_window, textvariable=temp_var, width=30).grid(row=6, column=1, padx=5, pady=5)
        
        def save_changes():
            try:
                new_values = (
                    ville_var.get(),
                    cp_var.get(),
                    pop_var.get(),
                    dist_var.get(),
                    ref_var.get(),
                    alt_var.get(),
                    temp_var.get()
                )
                self.tree.item(item, values=new_values)
                self.log(f"✓ Ville '{ville_var.get()}' modifiée")
                edit_window.destroy()
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la modification:\n{str(e)}")
        
        ttk.Button(edit_window, text="💾 Enregistrer", command=save_changes).grid(row=7, column=0, columnspan=2, pady=20)
    
    def delete_selected(self):
        """Supprimer l'élément sélectionné du tableau"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner une ville à supprimer")
            return
        
        item = selection[0]
        ville_nom = self.tree.item(item, 'values')[0]
        
        if messagebox.askyesno("Confirmation", f"Voulez-vous vraiment supprimer '{ville_nom}' ?"):
            self.tree.delete(item)
            self.log(f"✓ Ville '{ville_nom}' supprimée")
            
            # Mettre à jour le compteur
            count = len(self.tree.get_children())
            self.result_label.config(text=f"✅ {count} villes trouvées")
    
    def add_city_manual(self):
        """Ajouter manuellement une ville au tableau"""
        add_window = tk.Toplevel(self.root)
        add_window.title("Ajouter une ville")
        add_window.geometry("400x350")
        
        # Champs d'ajout
        ttk.Label(add_window, text="Ville:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ville_var = tk.StringVar()
        ttk.Entry(add_window, textvariable=ville_var, width=30).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(add_window, text="Code Postal:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        cp_var = tk.StringVar()
        ttk.Entry(add_window, textvariable=cp_var, width=30).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(add_window, text="Population:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        pop_var = tk.StringVar()
        ttk.Entry(add_window, textvariable=pop_var, width=30).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(add_window, text="Distance (km):").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        dist_var = tk.StringVar()
        ttk.Entry(add_window, textvariable=dist_var, width=30).grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(add_window, text="Proche de:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        ref_var = tk.StringVar()
        ttk.Entry(add_window, textvariable=ref_var, width=30).grid(row=4, column=1, padx=5, pady=5)
        
        ttk.Label(add_window, text="Altitude (m):").grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
        alt_var = tk.StringVar(value="N/A")
        ttk.Entry(add_window, textvariable=alt_var, width=30).grid(row=5, column=1, padx=5, pady=5)
        
        ttk.Label(add_window, text="Temp. moy. (°C):").grid(row=6, column=0, padx=5, pady=5, sticky=tk.W)
        temp_var = tk.StringVar(value="N/A")
        ttk.Entry(add_window, textvariable=temp_var, width=30).grid(row=6, column=1, padx=5, pady=5)
        
        def add_city():
            if not ville_var.get():
                messagebox.showwarning("Attention", "Veuillez saisir un nom de ville")
                return
            
            try:
                new_values = (
                    ville_var.get(),
                    cp_var.get(),
                    pop_var.get(),
                    dist_var.get(),
                    ref_var.get(),
                    alt_var.get(),
                    temp_var.get()
                )
                self.tree.insert('', tk.END, values=new_values)
                self.log(f"✓ Ville '{ville_var.get()}' ajoutée")
                
                # Mettre à jour le compteur
                count = len(self.tree.get_children())
                self.result_label.config(text=f"✅ {count} villes trouvées")
                
                add_window.destroy()
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'ajout:\n{str(e)}")
        
        ttk.Button(add_window, text="➕ Ajouter", command=add_city).grid(row=7, column=0, columnspan=2, pady=20)
    
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
                        alt_val = city['altitude'] if city['altitude'] != "N/A" else ''
                        temp_val = city['temperature'] if city['temperature'] != "N/A" else ''
                        
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
                            'ville_reference': city['ville_reference'],
                            'altitude_m': city['altitude'] if city['altitude'] != "N/A" else None,
                            'temperature_moyenne_c': city['temperature'] if city['temperature'] != "N/A" else None
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
            self.log("Génération de la carte HTML...")
            
            # Récupérer les données actuelles du tableau
            current_table_data = []
            for item in self.tree.get_children():
                values = self.tree.item(item, 'values')
                # Trouver les coordonnées dans current_results
                matching_city = None
                for city in self.current_results:
                    if city['nom'] == values[0]:
                        matching_city = city
                        break
                
                if matching_city:
                    current_table_data.append({
                        'nom': values[0],
                        'population': values[2],
                        'distance': values[3],
                        'ville_reference': values[4],
                        'altitude': values[5],
                        'temperature': values[6],
                        'lat': matching_city['lat'],
                        'lon': matching_city['lon']
                    })
            
            # Calculer le centre de la carte
            if current_table_data:
                avg_lat = sum(float(city['lat']) for city in current_table_data) / len(current_table_data)
                avg_lon = sum(float(city['lon']) for city in current_table_data) / len(current_table_data)
            else:
                avg_lat, avg_lon = 46.5, 2.5
            
            # Créer le fichier HTML
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
            
            # Ajouter les zones de recherche si demandé
            if self.show_search_zones.get():
                max_dist = self.max_distance.get() * 1000  # Convertir en mètres
                for ref_city in self.reference_cities:
                    coords = self.city_coordinates.get(ref_city)
                    if coords:
                        html_content += f"""
        // Zone de recherche pour {ref_city}
        L.circle([{coords['lat']}, {coords['lon']}], {{
            color: '#3498db',
            fillColor: '#3498db',
            fillOpacity: 0.1,
            radius: {max_dist},
            weight: 1
        }}).addTo(map);
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
            
            # Ajouter les résultats (limiter selon le paramètre)
            max_cities = self.max_cities_map.get()
            results_to_show = current_table_data[:max_cities]
            
            for city in results_to_show:
                city_name = city['nom'].replace("'", "\\'").replace('"', '\\"')
                alt_text = str(city['altitude']) + "m" if city['altitude'] != "N/A" else "N/A"
                temp_text = str(city['temperature']) + "°C" if city['temperature'] != "N/A" else "N/A"
                
                html_content += f"""
        L.marker([{city['lat']}, {city['lon']}], {{icon: blueIcon}})
            .bindPopup('<div class="city-popup"><h3>{city_name}</h3><p>Population: {city['population']}</p><p>Distance: {city['distance']} km</p><p>Proche de: {city['ville_reference']}</p><p>Altitude: {alt_text}</p><p>Temp. moy.: {temp_text}</p></div>')
            .addTo(map);
"""
                html_content += f"        markers.push(L.marker([{city['lat']}, {city['lon']}]));\n"
            
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
            
            # Sauvegarder le fichier à côté du script Python
            import os
            script_dir = os.path.dirname(os.path.abspath(__file__))
            map_file = os.path.join(script_dir, 'carte_villes.html')
            
            with open(map_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.log(f"✓ Carte générée: {map_file}")
            
            # Ouvrir dans le navigateur
            webbrowser.open('file://' + map_file)
            
            if len(current_table_data) > max_cities:
                messagebox.showinfo("Carte ouverte", 
                    f"La carte s'est ouverte dans votre navigateur.\n\n"
                    f"🔴 Marqueurs rouges = Villes de référence\n"
                    f"🔵 Marqueurs bleus = Villes trouvées\n\n"
                    f"Note: {max_cities} villes affichées sur {len(current_table_data)} résultats.\n"
                    f"Modifiez 'Villes max sur carte' pour en afficher plus.")
            else:
                messagebox.showinfo("Carte ouverte", 
                    "La carte s'est ouverte dans votre navigateur.\n\n"
                    "🔴 Marqueurs rouges = Villes de référence\n"
                    "🔵 Marqueurs bleus = Villes trouvées")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'ouverture de la carte:\n{str(e)}")
            self.log(f"❌ Erreur carte: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CitySearchApp(root)
    root.mainloop()