#!/usr/bin/python
# -*- coding: utf-8 -*-

from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import numpy as np
import os


base_path = os.path.dirname(__file__)
file_path = os.path.join(base_path, 'telecom_dataset_new.csv')

calls = pd.read_csv(file_path)

calls = calls.drop_duplicates()

calls['date'] = pd.to_datetime(calls['date']).dt.tz_localize(None)
calls['day'] = calls['date'].dt.date

# map() en lugar de astype(bool) — "False" como string se convierte a True con astype
calls['internal'] = calls['internal'].map({'True': True, 'False': False})

calls = calls.dropna(subset=['operator_id', 'internal'])

calls['wait_time'] = calls['total_call_duration'] - calls['call_duration']

# Calcular métricas por operador para el gráfico de eficiencia
operator_stats = calls.groupby('operator_id').agg({
    'calls_count': 'sum',
    'is_missed_call': 'mean',
    'wait_time': 'mean',
}).reset_index()
operator_stats = operator_stats.rename(columns={'is_missed_call': 'missed_rate'})
operator_stats = operator_stats.sort_values('missed_rate', ascending=False)


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = Dash(__name__, external_stylesheets=external_stylesheets)


app.layout = html.Div([

    html.H1("CallMeMaybe Dashboard", style={'textAlign': 'center'}),

    html.Div([
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

    html.Div([
        html.Div([
            html.H4("Duración de llamadas"),
            dcc.Graph(id='hist_duration')
        ], style={'width': '48%'}),

        html.Div([
            html.H4("Internas vs Externas"),
            dcc.Graph(id='pie_internal')
        ], style={'width': '48%'})

    ], style={'display': 'flex', 'gap': '20px'}),

    html.Br(),

    html.Div([
        html.H4("Llamadas por día"),
        dcc.Graph(id='calls_per_day')
    ]),

    html.Br(),

    html.Div([
        html.H4("Top 20 operadores por tasa de llamadas perdidas"),
        dcc.Graph(id='operator_efficiency')
    ])

], style={'width': '85%', 'margin': 'auto'})


@app.callback(
    [
        Output('hist_duration', 'figure'),
        Output('pie_internal', 'figure'),
        Output('calls_per_day', 'figure'),
        Output('operator_efficiency', 'figure'),
    ],
    [
        Input('call_type_filter', 'value'),
        Input('date_range', 'start_date'),
        Input('date_range', 'end_date')
    ]
)
def update_dashboard(call_type, start_date, end_date):

    if call_type == 'all':
        filtered = calls.copy()
    else:
        filtered = calls[calls['direction'] == call_type]

    start_date = pd.to_datetime(start_date).tz_localize(None)
    end_date = pd.to_datetime(end_date).tz_localize(None)

    filtered_dates = filtered[
        (filtered['date'] >= start_date) &
        (filtered['date'] <= end_date)
    ]

    # Gráfico 1: Duración de llamadas
    df = filtered_dates.copy()
    df['duration_min'] = df['call_duration'] / 60
    df = df[df['duration_min'] < 60]
    df['bin'] = pd.cut(df['duration_min'], bins=20)

    grouped = df.groupby(['bin', 'direction'])[
        'duration_min'].mean().reset_index()
    grouped['bin'] = grouped['bin'].astype(str)

    if call_type == 'all':
        fig1 = px.bar(
            grouped, x='bin', y='duration_min', color='direction',
            title='Duración promedio por rango de llamadas'
        )
    else:
        fig1 = px.bar(
            grouped[grouped['direction'] == call_type],
            x='bin', y='duration_min',
            title='Duración promedio por rango de llamadas',
            color_discrete_sequence=['#636EFA']
        )

    fig1.update_layout(
        xaxis_title="Rangos de duración (minutos)",
        yaxis_title="Duración promedio (minutos)",
        xaxis_tickangle=45
    )

    # Gráfico 2: Pie chart internas vs externas
    pie_data = filtered_dates['internal'].value_counts().reset_index()
    pie_data.columns = ['internal', 'count']
    pie_data['internal'] = pie_data['internal'].map({
        True: 'Interna', False: 'Externa'
    })

    fig2 = px.pie(
        pie_data, names='internal', values='count',
        title='Proporción internas vs externas'
    )

    # Gráfico 3: Llamadas por día
    calls_day = filtered_dates.groupby('day')['calls_count'].sum().reset_index()

    fig3 = px.bar(
        calls_day, x='day', y='calls_count',
        title='Número de llamadas por día'
    )

    # Gráfico 4: Eficiencia por operador
    op_stats = filtered_dates.groupby('operator_id').agg({
        'calls_count': 'sum',
        'is_missed_call': 'mean',
        'wait_time': 'mean',
    }).reset_index()
    op_stats = op_stats.rename(columns={'is_missed_call': 'missed_rate'})
    op_stats = op_stats.sort_values('missed_rate', ascending=False).head(20)

    fig4 = px.bar(
        op_stats, x='operator_id', y='missed_rate',
        color='wait_time',
        color_continuous_scale='RdYlGn_r',
        title='Top 20 operadores: tasa de llamadas perdidas (color = tiempo de espera)',
        labels={
            'operator_id': 'Operador',
            'missed_rate': 'Tasa de perdidas',
            'wait_time': 'Espera promedio (seg)'
        }
    )
    fig4.update_layout(xaxis_type='category')

    return fig1, fig2, fig3, fig4


if __name__ == '__main__':
    app.run(debug=True, port=8051, use_reloader=False)
