#!/usr/bin/python
# -*- coding: utf-8 -*-

# ======================
# IMPORTACIONES
# ======================
# Dash → framework para dashboards interactivos
from dash import Dash, dcc, html, Input, Output

# Plotly → visualizaciones
import plotly.express as px

# Pandas → manejo de datos
import pandas as pd

# OS → manejo de rutas de archivos
import os


# ======================
# CARGA Y PREPARACIÓN DE DATOS
# ======================

# Obtener ruta del archivo
base_path = os.path.dirname(__file__)
file_path = os.path.join(base_path, 'telecom_dataset_new.csv')

# Leer dataset
calls = pd.read_csv(file_path)

# Convertir fechas y eliminar zona horaria (evita errores en filtros)
calls['date'] = pd.to_datetime(calls['date']).dt.tz_localize(None)

# Extraer solo la fecha (sin hora)
calls['day'] = calls['date'].dt.date

# Asegurar que la columna sea booleana
calls['internal'] = calls['internal'].astype(bool)


# ======================
# CREACIÓN DE LA APP
# ======================

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = Dash(__name__, external_stylesheets=external_stylesheets)


# ======================
# DISEÑO DEL DASHBOARD (LAYOUT)
# ======================

app.layout = html.Div([

    # Título principal
    html.H1("CallMeMaybe Dashboard", style={'textAlign': 'center'}),

    # ======================
    # FILTROS
    # ======================
    html.Div([

        # Dropdown para tipo de llamadas
        html.Div([
            html.Label("Tipo de llamadas"),
            dcc.Dropdown(
                id='call_type_filter',
                options=[
                    {'label': 'Todas', 'value': 'all'},
                    {'label': 'Entrantes', 'value': 'in'},
                    {'label': 'Salientes', 'value': 'out'}
                ],
                value='all',
                clearable=False
            )
        ], style={'width': '48%'}),

        # Selector de rango de fechas
        html.Div([
            html.Label("Rango de fechas"),
            dcc.DatePickerRange(
                id='date_range',
                start_date=calls['date'].min(),
                end_date=calls['date'].max(),
                display_format='YYYY-MM-DD'
            )
        ], style={'width': '48%'})

    ], style={'display': 'flex', 'gap': '20px'}),

    html.Br(),

    # ======================
    # GRÁFICOS PRINCIPALES
    # ======================
    html.Div([

        # Gráfico de duración de llamadas
        html.Div([
            html.H4("Duración de llamadas (análisis real)"),
            dcc.Graph(id='hist_duration')
        ], style={'width': '48%'}),

        # Gráfico de proporción internas vs externas
        html.Div([
            html.H4("Internas vs Externas"),
            dcc.Graph(id='pie_internal')
        ], style={'width': '48%'})

    ], style={'display': 'flex', 'gap': '20px'}),

    html.Br(),

    # Gráfico de llamadas por día
    html.Div([
        html.H4("Llamadas por día"),
        dcc.Graph(id='calls_per_day')
    ])

], style={'width': '85%', 'margin': 'auto'})


# ======================
# CALLBACK (LÓGICA DEL DASHBOARD)
# ======================

@app.callback(
    [
        Output('hist_duration', 'figure'),
        Output('pie_internal', 'figure'),
        Output('calls_per_day', 'figure'),
    ],
    [
        Input('call_type_filter', 'value'),
        Input('date_range', 'start_date'),
        Input('date_range', 'end_date')
    ]
)
def update_dashboard(call_type, start_date, end_date):

    # ======================
    # FILTRO POR TIPO DE LLAMADA
    # ======================
    if call_type == 'all':
        filtered = calls.copy()
    else:
        filtered = calls[calls['direction'] == call_type]

    # ======================
    # FILTRO POR FECHAS
    # ======================
    start_date = pd.to_datetime(start_date).tz_localize(None)
    end_date = pd.to_datetime(end_date).tz_localize(None)

    filtered_dates = calls[
        (calls['date'] >= start_date) &
        (calls['date'] <= end_date)
    ]

    # ======================
    # GRÁFICO 1: DURACIÓN DE LLAMADAS
    # ======================

    df = filtered.copy()

    # Convertir duración de segundos a minutos
    df['duration_min'] = df['call_duration'] / 60

    # Eliminar outliers extremos (>60 min) para mejorar visualización
    df = df[df['duration_min'] < 60]

    # Crear rangos (bins) de duración
    df['bin'] = pd.cut(df['duration_min'], bins=20)

    # Calcular duración promedio por rango
    grouped = df.groupby(['bin', 'direction'])[
        'duration_min'].mean().reset_index()

    # Convertir bins a string para visualización
    grouped['bin'] = grouped['bin'].astype(str)

    # Crear gráfico dependiendo del filtro
    if call_type == 'all':
        fig1 = px.bar(
            grouped,
            x='bin',
            y='duration_min',
            color='direction',
            title='Duración promedio por rango de llamadas'
        )
    else:
        fig1 = px.bar(
            grouped[grouped['direction'] == call_type],
            x='bin',
            y='duration_min',
            title='Duración promedio por rango de llamadas',
            color_discrete_sequence=['#636EFA']
        )

    # Etiquetas del gráfico
    fig1.update_layout(
        xaxis_title="Rangos de duración de llamada (minutos)",
        yaxis_title="Duración promedio (minutos)",
        xaxis_tickangle=45
    )

    # ======================
    # GRÁFICO 2: PIE CHART
    # ======================

    # Conteo de llamadas internas vs externas
    pie_data = filtered_dates['internal'].value_counts().reset_index()
    pie_data.columns = ['internal', 'count']

    # Renombrar valores para mejor interpretación
    pie_data['internal'] = pie_data['internal'].map({
        True: 'Interna',
        False: 'Externa'
    })

    fig2 = px.pie(
        pie_data,
        names='internal',
        values='count',
        title='Proporción internas vs externas'
    )

    # ======================
    # GRÁFICO 3: LLAMADAS POR DÍA
    # ======================

    # Agrupar número de llamadas por día
    calls_day = filtered_dates.groupby(
        'day')['calls_count'].sum().reset_index()

    fig3 = px.bar(
        calls_day,
        x='day',
        y='calls_count',
        title='Número de llamadas por día'
    )

    # Retornar los tres gráficos
    return fig1, fig2, fig3


# ======================
# EJECUCIÓN DE LA APP
# ======================

if __name__ == '__main__':
    app.run(debug=True, port=8051, use_reloader=False)
