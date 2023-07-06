from flask import Flask
from dash import Dash, html, dcc, callback, Output, Input
import pandas  as pd
import re
import plotly.express as px
from plotly.offline import plot
import plotly.graph_objects as go 
from plotly.subplots import make_subplots
from app_config import *
import numpy as np
from flask import Flask, render_template
# Initialisation de Flask
server = Flask(__name__)


external_stylesheets = ['https://cdn.jsdelivr.net/npm/tailwindcss/dist/tailwind.min.css',
                        'https://cdn.jsdelivr.net/npm/font-awesome@4.7.0/css/font-awesome.min.css'
                    ]
app = Dash(__name__, server=server,external_stylesheets=external_stylesheets)
app.title = 'GlobalWarming'
#### DATASET GES #####
df_ges = pd.read_csv(f"csv/data_ges.csv",sep=",")
df_ges=df_ges[df_ges.year>=1800]
df_ges["types"]=df_ges.iso_code.apply(lambda x:"country" if x is not np.nan else "other")



#### DATASERT EMISSION BY SECTOR #####





##### LISTE DES PAYS ##### 

country_name=df_ges.country.unique().tolist()
country_name.append("World")
liste_region_by_rich = df_ges[df_ges.types=='region_by_rich'].country.unique()
other=df_ges[(df_ges.types=='other') & (~df_ges.country.str.contains('Panama Canal Zone'))].country.unique()

colors = px.colors.sequential.YlGnBu_r 


liste_col=['country','year','population','co2','methane','nitrous_oxide','other_industry_co2','co2_per_capita','trade_co2','trade_co2_share','total_ghg','total_ghg_excluding_lucf']
liste_world =['year','population','co2','methane','nitrous_oxide','other_industry_co2','co2_per_capita','trade_co2','trade_co2_share','total_ghg','total_ghg_excluding_lucf']
liste_include =['cement_co2_per_capita','coal_co2_per_capita','flaring_co2_per_capita','gas_co2_per_capita','methane_per_capita', 'nitrous_oxide_per_capita','oil_co2_per_capita', 'other_co2_per_capita']




# Initialisation de Dash


def empreinte_carbone_fill(df,liste_col,method=None):

    df = df.loc[:,liste_col].fillna(method="ffill")
    df = df.fillna(method="bfill")
    df = df.fillna(0)
    

    df['total']=df['co2']
    if "country"  in liste_col:
        df['total_net_emission']=df.total+df.trade_co2
    else:
          df['total_net_emission']=df.total
    df['ghg_net_per_capita']=df['total_net_emission']/(df['population']/1000000)
    return df

def get_div(title,value):
        return html.Div(children=[
                        html.H3(children=title,className="p-3 m-2 "),
                        html.P(children=value,className="p-3 m-2  ")
        ],className="")

def graph_energy(df,year,visualisation,pattern,title,energy_see):
    low_carbon = ["nuclear","biofuel"]
    renew_energy=["wind", "solar", "hydro"]
    fossil_energy=[ "coal", "gas", "oil"]
    bloc_energy=['fossil','nuclear','renewables']
    if energy_see == "Par type":
        liste_energy=low_carbon+renew_energy+fossil_energy
    else:
        liste_energy=bloc_energy


    if visualisation == "sunburst":
        df=df[df.year==year].drop("year",axis=1).reset_index().T.rename(columns={0:"values"}).reset_index().iloc[1:,]
        print(df)
        df["index"]=df["index"].apply(lambda x:"".join(re.findall(pattern,x)[0]))


        df['groupe']=df['index'].apply(lambda x: 'low_carbon' if x in low_carbon else ('renewables' if x in renew_energy else ('bloc' if x in bloc_energy else 'fossil_energy')))
        df =df.groupby(['groupe','index'])['values'].sum().reset_index()[2:]
        fig = px.sunburst(df[df['index']!='renewables'], path=['groupe','index'], values='values',color="groupe",color_discrete_sequence=colors)
        fig.update_traces( hovertemplate=None)
        get_templates_histo(fig)


    elif visualisation == "barmod":
        df=df[df.year==year]
        df=df.rename(columns=({i:re.findall(pattern,i)[0] for i in df.columns if len(re.findall(pattern,i))>0  }))
        df=df.loc[:,["year",*[col for col in liste_energy]]]
        fig = px.bar(data_frame=df,x=df.drop("year",axis=1).columns,color_discrete_sequence=colors,text_auto=True)
        fig.update_layout(yaxis_showticklabels=False)
        fig.update_traces( hovertemplate=None)

    else:

        df=df.rename(columns=({i:re.findall(pattern,i)[0] for i in df.columns if len(re.findall(pattern,i))>0  }))
     
        df=df.loc[:,["year",*[col for col in liste_energy]]]
        fig = px.bar(data_frame=df,x="year",y=df.drop("year",axis=1).columns,color_discrete_sequence=colors)
        fig.update_traces( hovertemplate=None)

    get_templates_histo(fig)

    fig.update_layout(title=f"{title} - {year}")

    return html.Div(
        children=[
            dcc.Graph(figure=fig)
        ]
    )  
        

@app.callback(Output("ges_global","children"),[Input('country','value'),Input("year","value")])
def get_number_ges(country,year):
    df_world = df_ges[~df_ges.iso_code.isna()].copy()

    if country == "World":
        df = df_world
        df=df.groupby("year").agg("sum",numeric_only="True").reset_index()
        liste=liste_world

    else:
        df = df_ges[df_ges.country==country]
        liste=liste_col
   
    
    
    df=empreinte_carbone_fill(df,liste)
    df=df[df.year==year]
    df_world= empreinte_carbone_fill(df_world.groupby("year").agg("sum",numeric_only="True").reset_index(),liste_world)
    df_world=df_world[df_world.year==year]
    
    total_world=df_world.total.values[0]

    return html.Div(id="",
                    children=[
                        html.Div(children=get_div("Emission globale eq C02 (Mt)",'{:,.0f}'.format(df.total_net_emission.values[0])),className="p-3 m-2 bg-white rounded-2xl w-full xl:w-1/4 text-3xl"),
                        html.Div(children=get_div("Population",'{:,.0f}'.format(df.population.values[0])),className="p-3 m-2 bg-white rounded-2xl w-full xl:w-1/4 text-3xl"),
                        html.Div(children=get_div("Eq T CO2 par habitant",round(df.ghg_net_per_capita.values[0],2)),className="p-3 m-2 bg-white rounded-2xl w-full xl:w-1/4 text-3xl"),
                        html.Div(children=get_div("Représentation des Emissions",f'{round((round(df.total_net_emission.values[0],2)/total_world)*100,2)}%'),className="p-3 m-2 bg-white rounded-2xlw-full xl:w-1/4 text-3xl")
                    ],className="flex flex-col xl:flex-row xl:flex-nowrap w-full p-3 m-2")


@app.callback(Output("ges_per_hab","children"),[Input("country","value"),Input("year","value"),Input("visualisation","value")])
def graph_ges(country,year,visualisation):
    name=country

    if name == "World":
        df=df_ges[df_ges.types=="country"].groupby("year").agg("mean",numeric_only="True").reset_index()
  

    else:   
        df = df_ges[df_ges.country==name]
       
    # creation graphique C02 per capita 
    pattern='[a-z\_\d]*(?=\_per_capita)'
    df_graph = df.loc[:,['year',*liste_include]].reset_index()
    df_graph=df_graph.rename(columns={col: "".join(re.findall(pattern, col)) for col in liste_include})

    if visualisation=="sunburst":
        x=""
        y=""
        df_graph=df_graph[df_graph.year==year].drop("year",axis=1)
        df_graph=df_graph.drop("index",axis=1).reset_index().T.drop("index",axis=0).rename(columns={0:"values"}).reset_index()
        fig = px.sunburst(data_frame=df_graph,path=["index"],values="values",color_discrete_sequence=colors)
        get_templates_histo(fig)
    elif visualisation =="barmod":
        x="T Eq CO2/ habitant"
        y=""
        df_graph=df_graph[df_graph.year==year].drop("year",axis=1)

        fig=px.bar(data_frame = df_graph,x=df_graph.iloc[:,1:].columns,color_discrete_sequence=colors,text_auto=True)
        get_templates_histo(fig)
        fig.update_layout(legend=dict(title=""),yaxis_showgrid=False,yaxis_showticklabels=False)
        

    else:
        x="year"
        y="T Eq C02 / habitant"
        fig = px.bar(data_frame = df_graph,x="year",y=df_graph.iloc[:,1:].columns,color_discrete_sequence=colors)
        get_templates_histo(fig)
        


    fig.update_layout(xaxis_title=x,yaxis_title=y,xaxis=dict(dtick=5, tickangle=45))
    fig.update_traces( hovertemplate=None)
    fig.update_layout(title=f"Représentation des Tonne Eq C02 par type - {year}")
    return html.Div(
          children=[
             dcc.Graph(id="",figure=fig)
          ]
    )




@app.callback(Output("emission_sector","children"),[Input("country","value"),Input("year","value"),Input("visualisation","value")])

def get_emission_sector(country,year,visualisation):
   # colors = px.colors.sequential.YlGnBu_r 
    df_emission_sector = pd.read_csv(f"csv/df_emission_sector.csv",sep=";")
    df_emission_sector.columns = df_emission_sector.columns.str.lower().str.replace("-","_").str.replace(" ","_")
    df_emission_sector=df_emission_sector[(df_emission_sector.entity==country)]
    
    #color=px.colors.cyclical.Edge

    #pattern="^(?!.*share).*"

    colors = px.colors.sequential.YlGnBu_r 
    pattern = '((?=share_)[a-z\d\_]*)'
    cols=[",".join(re.findall(pattern,i)) for i in df_emission_sector if len(re.findall(pattern,i)) > 0]
    df_graph = df_emission_sector.loc[:,['year',*cols]][df_emission_sector.entity==country]
    pattern_graph = '((?<=share_)[a-z\d\_]*)'
    df_graph=df_graph.rename(columns=({col : re.findall(pattern_graph,col)[0] for col in cols}))  

    if visualisation == "evolution":
        year=year
    else:
        if year > 2019:
            year=2019
        else:
            year=year
    if visualisation=="sunburst":

        df_graph=df_graph[df_graph.year==year].reset_index().T.loc["land_use_change_and_forestry":"aviation_and_shipping",:].rename(columns={0:"values"}).reset_index()
        colors = px.colors.sequential.YlGnBu_r 
        fig = px.sunburst(data_frame=df_graph,path=["index"],values="values",color_discrete_sequence=colors)
        get_templates_histo(fig)
        
    elif visualisation =="barmod":

        x=""
        y=""
        df_graph=df_graph[df_graph.year==year].drop("year",axis=1)
        fig=px.bar(data_frame = df_graph,x=df_graph.iloc[:,1:].columns,color_discrete_sequence=colors,text_auto=True)
        get_templates_histo(fig)
        fig.update_layout(legend=dict(title=""),yaxis_showgrid=False,yaxis_showticklabels=False)


    else:
  
        fig = px.bar(data_frame=df_graph,x="year",y=df_graph.iloc[:,1:].columns,color_discrete_sequence=colors)
    
        get_templates_histo(fig)
        fig.update_layout(barmode="relative",xaxis_title="year",yaxis_title="percentages")

    fig.update_layout(title=f"Représentation des secteurs par emission - {year}")
    fig.update_traces( hovertemplate=None)

    return html.Div(
          children=[
              dcc.Graph(figure=fig)
          ]
    ) 



@app.callback(Output("energie_consumption","children"),[Input("country","value"),Input("year","value"),Input("visualisation","value"),Input("value_see","value"),Input("energie_see","value")])


def get_energy_consumption(country,year,visualisation,value_see,energie_see):
    df = pd.read_csv("csv/df_energie.csv",sep=",")

    df=df.rename(columns={"fossil_fuel_consumption":"fossil_consumption"})


    pattern = '[a-z\_]*consumption'
    twh_consumption=[i for i in df.columns if re.fullmatch(pattern,i) ]

    pattern = '[a-z\_]*energy'
    col_consumption_share=[i for i in df.columns if re.fullmatch(pattern,i) ]
    if value_see == "valeur en pourcentage":
        col_see = col_consumption_share
        pattern = '([a-z\_]*(?=\_share))'
        df = df[df.country==country].loc[:,["year",*col_see]]
    else:
        col_see = twh_consumption
        pattern='([a-z\_]*(?=\_consumption))'
        df = df[df.country==country].loc[:,["year",*col_see]].rename(columns={"fossil_fuel":"fossil"})


    df=df.fillna(method="ffill")
    df=df.dropna()

    return  graph_energy(df,year,visualisation,pattern,"Représentation de la consommation énergétique",energie_see)


@app.callback(Output("energie_electrique","children"),[Input("country","value"),Input("year","value"),Input("visualisation","value"),Input("value_see","value"),Input("energie_see","value")])
def get_energy_electrique(country,year,visualisation,value_see,energie_see):
    df = pd.read_csv("csv/df_energie.csv",sep=",")

    pattern = '[a-z\_]*share(\_elec)'
    col_consumption_share=[i for i in df.columns if re.fullmatch(pattern,i) ]

    pattern = '[a-z\_]*electricity'
    eletricite=[i for i in df.columns if re.fullmatch(pattern,i) ]

    if value_see == "valeur en pourcentage":
        col_see = col_consumption_share
        pattern = '([a-z\_]*(?=\_share))'
    else:
        col_see = eletricite
        pattern = '([a-z\_]*(?=_electricity))'

    df = df[df.country==country].loc[:,["year",*col_see]]
    df=df.fillna(method="ffill")
    df=df.dropna()
    return  graph_energy(df,year,visualisation,pattern,"Représentation de la production Electrique",energie_see)




app.layout = html.Div(
    children=[
        html.Div(children=[
        html.Div(
              children=[
                    html.H3(children="Pays",className="text-5xl p-3 m-2 text-center"),
                    dcc.Dropdown(

                            id="country",
                            multi=False,
                            options=[{"label":row,"value":row } for  row in country_name],
                            value="World",
                            className="flex flex-col  p-3 m-2 items-center w-full"
                            ),
              ],className="w-full xl:w-1/2 bg-white p-3 m-2 rounded-2xl shadow-lg"
        ),
        html.Div(
              children=[
                    html.H3(children="Année",className="text-5xl p-3 m-2 text-center"),
                    dcc.Dropdown(

                            id="year",
                            multi=False,
                            options=[{"label":row,"value":row } for  row in sorted(df_ges.year.unique())],
                            value=2021,
                            className="flex flex-col  p-3 m-2 items-center w-full"
                            ),
              ],className="w-full xl:w-1/2 bg-white p-3 m-2 rounded-2xl shadow-lg"
        ),
        html.Div(
              children=[
                    html.H3(children="Type visualisation",className="text-5xl p-3 m-2 text-center"),
                    dcc.Dropdown(

                            id="visualisation",
                            multi=False,
                            options=[{"label":row,"value":index } for  index,row in {"sunburst":"secteurs","barmod":"bar empilées","evolution":"evolution"}.items()],
                            value=2021,
                            className="flex flex-col  p-3 m-2 items-center w-full"
                            ),
              ],className="w-full xl:w-1/2 bg-white p-3 m-2 rounded-2xl shadow-lg"
        ),
        ],className="flex flex-col xl:flex-row p-3 m-2 xl:flex-nowrap w-full"),
        html.Div(id="ges_global",children=[]),

        html.Div(
            children=[
   
        html.Div(id="ges_per_hab",children=[],className=className.get("graph-full")),
        html.Div(id="emission_sector",children=[],className=className.get("graph-full")),
            ],className="flex flex-col xl:flex-row xl:flex-nowrap justify-between p-3 m-2"
        ),

        html.Div(
            children=[
                dcc.RadioItems(id="value_see",options=["valeur en pourcentage","valeur en TWh"],value="valeur en pourcentage",inline=True,className="p-3 m-2 rounded-2xl bg-white"),
                dcc.RadioItems(id="energie_see",options=["Par famille","Par type"],value="Par type",inline=True,className="p-3 m-2 rounded-2xl bg-white"),

                html.Div(
                    children=[
                        html.Div(id="energie_consumption",children=[],className=className.get("graph-full")),
                        html.Div(id="energie_electrique",children=[],className=className.get("graph-full"))
                    ],className="flex flex-col xl:flex-row xl:flex-nowrap p-3 m-2"
                )
            ],
        )
    ],className="p-5 mx-4 bg-gray-100 font-semibold")

