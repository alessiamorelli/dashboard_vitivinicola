from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from simulator import simulate_multi_plot_data  # importa la tua funz
from datetime import datetime, timedelta

appezzamenti = {
        'A1': {'resa_kg_ha': 8000, 'lat': 45.898, 'lon': 12.308}, #kg/ha kilogrammi per ettaro 
        'B2': {'resa_kg_ha': 9500, 'lat': 45.897, 'lon': 12.235}, #solitamente tra 8000 e 13000 kg/ha
        'C3': {'resa_kg_ha': 8700, 'lat': 45.925, 'lon': 12.303}
    }
NUMERO_GIORNI = 30

# Simula i dati
df = simulate_multi_plot_data(NUMERO_GIORNI, appezzamenti)

# Inizializza Dash
app = Dash()
app.title = "Dashboard Viticola"

# Layout
app.layout = html.Div([
    html.H1("Dashboard Viticola Conegliano", style={'textAlign': 'center', 'color': 'green', 'fontSize': 30}),
    html.Hr(),

   # Selettore metrica economica
    html.Div([
        html.Label("Seleziona metrica economica:",
            style={
                'textAlign': 'center',
                'fontSize': '20px',
                'display': 'block',
                'marginBottom': '10px'
            }
        ),
        dcc.RadioItems(
            options=[
                {'label': 'Costi Ettaro', 'value': 'costi_ha'},
                {'label': 'Resa (kg/ha)', 'value': 'resa_kg_ha'},
                {'label': 'Prezzo (€ / kg)', 'value': 'prezzo_euro/kg'}
            ],
            value='costi_ha',
            id='metric-selector',
            inline=True,
            style={
                'textAlign': 'center',
                'fontSize': '18px',
                'display': 'flex',
                'justifyContent': 'center',
                'gap': '20px'
            }
        )
    ], style={'marginBottom': 50}),

    # Date picker per selezionare giorno
    html.Div([
        html.Label("Seleziona data:", style={'fontSize': '18px', 'textAlign': 'center', 'display': 'block'}),
        dcc.DatePickerSingle(
            id='data-picker',
            min_date_allowed=(datetime.today() - timedelta(days=NUMERO_GIORNI)).date(),
            max_date_allowed=(datetime.today() + timedelta(days=NUMERO_GIORNI)).date(),
            initial_visible_month=datetime.today().date(),
            date=datetime.today().date(),
            display_format='DD/MM/YY',
            className='no-calendar-icon'
        )
    ], style={
    'marginBottom': 40,
    'textAlign': 'center'  # <-- centra il contenuto all’interno del div
    }),

    html.Div([
    html.Label("Tipo di gestione:", style={'fontSize': '18px'}),
    dcc.RadioItems(
        id='gestione-selector',
        options=[
            {'label': 'Convenzionale', 'value': 'convenzionale'},
            {'label': 'Biologica', 'value': 'biologica'}
        ],
        value='convenzionale',
        inline=True,
        style={'justifyContent': 'center', 'gap': '20px'}
    )
], style={'marginBottom': 40, 'textAlign': 'center'}),


    # grafico interattivo serve a collegarlo ai callback in modo dinamico: il grafico verrà aggiornato ogni volta che cambiano i dati o le metriche.
    dcc.Graph(id='map-graph'),
    

    html.Div([
    html.Label("Seleziona appezzamento:", style={'fontSize': '18px'}),
    dcc.Dropdown(
        id='appezzamento-selector',
        options=[{'label': k, 'value': k} for k in appezzamenti.keys()],
        value='A1',
        clearable=False,
        style={'width': '50%', 'margin': '0 auto'}
    )
], style={'marginBottom': 40, 'textAlign': 'center'}),

    # grafico temporale
    dcc.Graph(id='time-series-graph')

])

@callback(
    Output('map-graph', 'figure'),
    Input('metric-selector', 'value'),
    Input('data-picker', 'date'),
    Input('gestione-selector', 'value')
)


def update_map(metric, selected_date, gestione):
    # Data di filtro (solo giorno, senza orario)
    selected_date = pd.to_datetime(selected_date).date()  # ottengo solo la data

    # Creo una colonna temporanea con solo la data (senza orario)
    df['data_only'] = df['data'].dt.date

    # Filtro usando la colonna data_only
    filtered_df = df[df['data_only'] == selected_date].copy()

    if gestione != 'tutte':
            filtered_df = filtered_df[filtered_df['gestione'] == gestione]

    # Se il DataFrame è vuoto, mostra messaggio nel grafico
    if filtered_df.empty:
        formatted_date = selected_date.strftime('%d/%m/%Y')
        fig = px.scatter_mapbox(
            lat=[],
            lon=[],
            title=f"Nessun dato disponibile per {formatted_date}",
            mapbox_style="open-street-map"
        )
    
        return fig

    # Creare una nuova colonna chiamata 'size_metric' nel DataFrame filtered_df, basata su un'altra colonna identificata da metric, in modo che ogni valore sia almeno 1 e rappresenti il valore assoluto della metrica (o 1, se è più piccolo).
    filtered_df['size_metric'] = filtered_df[metric].apply(lambda x: max(abs(x), 1))

    # Costruzione mappa
    fig = px.scatter_mapbox(
        filtered_df,
        lat='lat',
        lon='lon',
        color=metric,
        size='size_metric',
        hover_name='appezzamento',
        hover_data={metric: ':.2f'},
        zoom=12,
        mapbox_style='open-street-map',
        title=f"{metric.upper()} al {selected_date.strftime('%d/%m/%Y')}"
    )
    fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})

    return fig

@callback(
    Output('time-series-graph', 'figure'),
    Input('metric-selector', 'value'),
    Input('appezzamento-selector', 'value')

)
def update_time_series(metric, appezzamento):
    # Raggruppa i dati per giorno (media o somma)
    df['data_only'] = df['data'].dt.date
    filtered_df = df.copy()

    # Applica filtro gestione, se selezionato
    if appezzamento != 'tutti':
        filtered_df = filtered_df[filtered_df['appezzamento'] == appezzamento]

    daily_data = filtered_df.groupby(['data_only', 'gestione'])[metric].sum().reset_index()

    fig = px.line(
        daily_data,
        x='data_only',
        y=metric,
        color='gestione',
        title=f"Andamento {metric.upper()} nel tempo per gestione ({appezzamento})",
        markers=True
    )

    fig.update_layout(
        xaxis_title="Data",
        yaxis_title=metric.upper(),
        margin={"r":0,"t":40,"l":0,"b":0}
    )

    return fig



# Avvio server
if __name__ == '__main__':
    app.run(debug=True)