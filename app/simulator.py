import random
import pandas as pd # type: ignore
import numpy as np # type: ignore
from datetime import datetime, timedelta

# Creazione di costanti che indicano la direzione del vento
WIND_DIRECTIONS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']

#Creo dizionario con mesi e relativi valori
dati_mensili = {
    1: {"temp_min": -1, "temp_max": 6.4, "umidita": 79, "pioggia": (40, 80), "radiazione": (7, 10), "vento": (0.5, 2)},
    2: {"temp_min": -0.1, "temp_max": 8, "umidita": 77, "pioggia": (30, 70), "radiazione": (8, 11), "vento": (0.5, 2.2)},
    3: {"temp_min": 2.7, "temp_max": 12.2, "umidita": 74, "pioggia": (50, 90), "radiazione": (10, 14), "vento": (0.7, 2.5)},
    4: {"temp_min": 6.3, "temp_max": 16.4, "umidita": 73, "pioggia": (70, 110), "radiazione": (14, 18), "vento": (1, 2.7)},
    5: {"temp_min": 10.6, "temp_max": 20.5, "umidita": 74, "pioggia": (60, 100), "radiazione": (16, 22), "vento": (1, 2.8)},
    6: {"temp_min": 14.7, "temp_max": 24.6, "umidita": 71, "pioggia": (50, 90), "radiazione": (18, 24), "vento": (1.2, 3)},
    7: {"temp_min": 16.8, "temp_max": 26.7, "umidita": 69, "pioggia": (40, 80), "radiazione": (18, 25), "vento": (1.5, 3.5)},
    8: {"temp_min": 16.8, "temp_max": 26.6, "umidita": 69, "pioggia": (50, 90), "radiazione": (16, 24), "vento": (1.3, 3.3)},
    9: {"temp_min": 13.0, "temp_max": 21.8, "umidita": 74, "pioggia": (70, 110), "radiazione": (12, 18), "vento": (1, 2.8)},
    10: {"temp_min": 9.4, "temp_max": 16.9, "umidita": 79, "pioggia": (90, 130), "radiazione": (10, 14), "vento": (0.8, 2.5)},
    11: {"temp_min": 4.7, "temp_max": 11.5, "umidita": 79, "pioggia": (80, 120), "radiazione": (6, 9), "vento": (0.7, 2.2)},
    12: {"temp_min": -0.1, "temp_max": 7.3, "umidita": 80, "pioggia": (50, 90), "radiazione": (4, 7), "vento": (0.5, 2)}
}

# Funzione che ritorna i tre appezzamenti
def appezzamenti_conosciuti():
    return {
        'A1': {'resa_kg_ha': 8000, 'lat': 45.898, 'lon': 12.308}, 
        'B2': {'resa_kg_ha': 9500, 'lat': 45.897, 'lon': 12.235}, 
        'C3': {'resa_kg_ha': 8700, 'lat': 45.925, 'lon': 12.303}
    }

def generate_trattamenti(rain, leaf_wetness):
    if rain > 5 or leaf_wetness > 6:
        return round(random.uniform(20, 50), 2) 
    else:
        return round(random.uniform(0, 10), 2)

 # Funzione che prende la lista di date e la ordina
def get_dates(n_days):
    start_date = datetime.today()
    return [start_date - timedelta(days=i) for i in range(n_days)] [::-1]

# Funzione che stabilisce in base al mese in quale fase si trova il vigneto
def get_fenological_stage(date):
    month = date.month
    if month in [3, 4]:
        return "germogliamento"
    elif month == 5:
        return "fioritura"
    elif month in [6, 7]:
        return "allegagione"
    elif month == 8:
        return "invaiatura"
    elif month == 9:
        return "maturazione"
    elif month == 10:
        return "vendemmia"
    else:
        return "riposo vegetativo"

def generate_resa_kg_ha(base_resa, gestione, pioggia, malattie):
                    penalty = 0
                    if gestione == 'biologica':
                        penalty += 0.1
                    if pioggia > 25:
                        penalty += 0.05
                    if malattie:  # flag booleano (es. alta bagnatura)
                        penalty += 0.1
                    variazione_random = np.random.uniform(0.95, 1.05)
                    resa_finale = base_resa * (1 - penalty) * variazione_random
                    return round(resa_finale, 2)
                
def generate_costi_ha(base_cost, gestione, trattamenti_euro):
    gestione_factor = 1.2 if gestione == 'biologica' else 1.0
    variabilita = np.random.uniform(0.9, 1.1)
    total_cost = (base_cost + trattamenti_euro) * gestione_factor * variabilita
    return round(total_cost, 2)

def generate_euro_kg(gestione, resa_kg_ha):
    base_price = 1.0
    if gestione == 'biologica':
        base_price += 0.1  # premium

    # penalizza prezzo se la resa è alta 
    if resa_kg_ha > 12000:
        base_price -= 0.05
    elif resa_kg_ha < 9000:
        base_price += 0.05
    return round(base_price * np.random.uniform(0.95, 1.05), 2)
     
def simulate_multi_plot_data(n_days, appezzamenti):
    # Crea lista di date per simulazione
    dates = get_dates(n_days)
    data = []
    for appezzamento, info in appezzamenti.items():
        base_resa = info["resa_kg_ha"]
        base_costo = 1200  # costo fisso di riferimento €/ha
        for gestione in ['convenzionale', 'biologica']:
            for date in dates:
                valori = dati_mensili[date.month]
                temp_min = valori["temp_min"]
                temp_max = valori["temp_max"]
                umidita = valori["umidita"]
                rain = random.uniform(*valori["pioggia"])
                solar_rad = random.uniform(*valori["radiazione"])
                wind_speed = random.uniform(*valori["vento"])
                wind_dir = random.choice(WIND_DIRECTIONS)
                leaf_wetness = random.uniform(0, 10)
                stage = get_fenological_stage(date)
                malattie = leaf_wetness > 8  # flag malattie alto con bagnatura fogliare alta
                trattamenti = generate_trattamenti(rain, leaf_wetness)
                # Simula costi ettaro, resa, euro al kg
                resa_kg_ha = generate_resa_kg_ha(base_resa, gestione, rain, malattie)
                costi_ha = generate_costi_ha(base_costo, gestione, trattamenti)
                prezzo = generate_euro_kg(gestione, resa_kg_ha)

                # Produzione uva stimata dal kg/ha (ipotizzando 1 ha per appezzamento)
                produzione_uva = round(resa_kg_ha * (0.8 + 0.2 * np.random.rand()), 2)  # variazione ±20%

                # Ricavi e costi
                ricavi = round(produzione_uva * prezzo, 2)
                costi_variabili = round(produzione_uva * (costi_ha/ resa_kg_ha), 2)  # costo variabile proporzionale
                costi_fissi = 150  # €/giorno, fisso

                # Se gestione biologica, modifica valori
                if gestione == 'biologica':
                    trattamenti *= 0.7
                    costi_variabili *= 0.95
                    produzione_uva *= 0.98

                data.append({
                   "data": date,
                    "temperatura_min": temp_min,
                    "temperatura_max": temp_max,
                    "precipitazioni": rain,
                    "umidità": umidita,
                    "radiazione_solare": solar_rad,
                    "vento_velocità": wind_speed,
                    "vento_direzione": wind_dir,
                    "bagnatura_fogliare": leaf_wetness,
                    "fase_fenologica": stage,
                    "produzione_uva_kg": round(produzione_uva, 2),
                    "ricavi": round(ricavi, 2),
                    "costi_variabili": round(costi_variabili, 2),
                    "costi_fissi": costi_fissi,
                    "trattamenti_euro": round(trattamenti, 2),
                    "resa_kg_ha": resa_kg_ha,
                    "costi_ha": costi_ha,
                    "prezzo_euro/kg": prezzo,
                    "appezzamento": appezzamento,
                    "lat": info['lat'],
                    "lon": info['lon'],
                    "gestione": gestione
                })


    df = pd.DataFrame(data)
    df['data'] = pd.to_datetime(df['data'])
    df.to_excel('dati.xlsx', index=False)

    return df


# Main della funzione che richiama la funzione simulate_multi_plot_data che genera il dataframe
if __name__ == "__main__":
    appezzamenti = appezzamenti_conosciuti()
    df = simulate_multi_plot_data(30, appezzamenti)
