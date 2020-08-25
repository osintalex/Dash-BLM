import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import os
import pandas as pd
from processing import DashBLM


# ----------------------------------------------------------------------------#
# Basic dash configuration
# ----------------------------------------------------------------------------#

app = dash.Dash(__name__)
app.title = "UK BLM App"

# ----------------------------------------------------------------------------#
# Import data
# ----------------------------------------------------------------------------#

path = os.getcwd() + "/data/"

# Read in dataframes for graphing

df_clean = pd.read_csv(path + "df_clean.csv")
filtered_df = pd.read_csv(path + "filtered_df.csv")
df_blackpops = pd.read_csv(path + "df_blackpops.csv")
df_ids = pd.read_csv(path + "df_ids.csv")
df_scatter = pd.read_csv(path + "df_scatter.csv")
df_sunburst = pd.read_csv(path + "df_sunburst.csv")

# Read in mapbox token and geojson for choroplethmapbox graph used in 'Stop and Search' section

DashBLM = DashBLM()

token = DashBLM.make_choropleth_inputs()[0]
geojson = DashBLM.make_choropleth_inputs()[1]

# ----------------------------------------------------------------------------#
# Draw figures
# ----------------------------------------------------------------------------#

# Scatter mapbox on top of choropleth mapbox for 'Stop and Search' section

choro = go.Choroplethmapbox(
    geojson=geojson,
    locations=df_ids.ids,
    z=df_blackpops["Value"],
    colorscale="Reds",
    text=df_ids.ids,
    hovertemplate="""Black Population: %{z}% <br> Area: %{text} <extra></extra>""",
    # extra tags removes trace name
    hoverlabel={"bgcolor": "white"},
    showscale=False,
)

scatt = go.Scattermapbox(
    lat=df_scatter.lats,
    lon=df_scatter.longs,
    mode="markers",
    text=df_scatter["text"],
    textposition="top left",
    marker={
        "size": df_scatter["size"],
        "color": df_scatter["color"],
        "sizemin": 1,
        "colorscale": "Icefire",
    },
    hovertemplate="%{text} <extra></extra>",
)

layout = go.Layout(
    mapbox=dict(
        center=dict(lat=52.370216, lon=-1), accesstoken=token, zoom=6, style="dark"
    )
)

ethnicity_map = go.Figure(data=[choro, scatt], layout=layout)
ethnicity_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
ethnicity_map["layout"]["titlefont"] = {"family": "Roboto", "size": 14}
ethnicity_map.layout.font.family = "Roboto"

# The arrests by race and justice graph sections contain interactive graphs so the code for that is in callbacks below

# ----------------------------------------------------------------------------#
# Application Layout
# ----------------------------------------------------------------------------#

app.layout = html.Div(
    [
        dcc.Tabs(
            [
                dcc.Tab(
                    label="Mission Statement",
                    children=[
                        html.H1(
                            "About",
                            style={
                                "width": "100%",
                                "text-align": "center",
                                "padding-top": "5%",
                            },
                        ),
                        html.Div(
                            dcc.Markdown(
                                """
                
                This app has been made in response to the UK government's disappointing reaction to recent Black Lives
                Matter protests in Britain. 
                
                The government's principal response to protests was to set up a UK race inequality commission.
                
                
                However the head of the commission has previously doubted the existence of institutional racism in the 
                UK.
                
                This app tries to use to data to show how mistaken this is. You can view the source code [here](https://github.com/osintalex/Dash-BLM).
                
                *Sources*:
                
                [Police Data](https://data.police.uk)

                [UK Government Ethnicity Facts and Figures](https://www.ethnicity-facts-figures.service.gov.uk)
                
                [UK Government Arrests Data](https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/841253/arrest-police-powers-procedures-mar19-hosb2519-tables.ods)
                
                [Office of National Statistics Population Data](https://www.ons.gov.uk/file?uri=%2fpeoplepopulationandcommunity%2fpopulationandmigration%2fpopulationestimates%2fdatasets%2fpopulationestimatesforukenglandandwalesscotlandandnorthernireland%2fmid2001tomid2018detailedtimeseries/ukpopulationestimates18382018.xlsx)
                
                [UK Local Area District Co-Ordinates](https://github.com/martinjc/UK-GeoJSON)
                """
                            ),
                            style={
                                "width": "80%",
                                "margin": "0 10% 0 10%",
                                "text-align": "center",
                            },
                        ),
                    ],
                ),
                dcc.Tab(
                    label="Arrests by Race",
                    children=[
                        html.Div(
                            [
                                html.H3(
                                    "Number and Proportion of Arrests by Ethnicity",
                                    style={"width": "100%", "text-align": "center"},
                                ),
                                html.P(
                                    "Data for England and Wales only",
                                    style={"width": "100%", "text-align": "center"},
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                dcc.Markdown(
                                    id="times-more-likely",
                                    style={
                                        "backgroundColor": "#B5D7E7",
                                        "text-align": "center",
                                    },
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                dcc.Graph(
                                    id="arrests-graph", config={"displayModeBar": False}
                                ),
                            ]
                        ),
                        dcc.Slider(
                            id="year-slider",
                            min=df_clean["Year"].min(),
                            max=df_clean["Year"].max(),
                            value=df_clean["Year"].min(),
                            marks={
                                str(year): str(year)
                                for year in df_clean["Year"].unique()
                            },
                            step=None,
                        ),
                    ],
                ),
                dcc.Tab(
                    label="Stop and Search",
                    children=[
                        html.H3(
                            "Map of Searches Made",
                            style={"width": "100%", "text-align": "center"},
                        ),
                        html.P(
                            "Data for England and Wales and 2019 only.",
                            style={"width": "100%", "text-align": "center"},
                        ),
                        html.P(
                            """Bubble colour represents ethnicity. Bigger bubbles mean younger suspects. The redder a map section, 
               the more black people live in the area.""",
                            style={"width": "100%", "text-align": "center"},
                        ),
                        html.Div(
                            [
                                dcc.Markdown(
                                    """In 2019 black people were **9.5** times more likely to be stopped and searched 
        than white people, asian and mixedpeople were 2.75 times more likely.  
        """,
                                    style={
                                        "backgroundColor": "#B5D7E7",
                                        "text-align": "center",
                                    },
                                )
                            ]
                        ),
                        html.Div(
                            [
                                dcc.Graph(
                                    figure=ethnicity_map,
                                    config={"displayModeBar": False},
                                ),
                            ]
                        ),
                    ],
                ),
                dcc.Tab(
                    label="Department of Justice",
                    children=[
                        html.Div(
                            [
                                dcc.Markdown(
                                    """
                        ## Sentence Length by Ethnicity
                        #### Data for England and Wales only
                        *Hover over the graph for more information*""",
                                    style={"width": "100%", "text-align": "center"},
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                dcc.Graph(
                                    id="justice-graph", config={"displayModeBar": False}
                                ),
                            ]
                        ),
                        dcc.Slider(
                            id="year-slider-justice",
                            min=df_sunburst["Year"].min(),
                            max=df_sunburst["Year"].max(),
                            value=df_sunburst["Year"].min(),
                            marks={
                                str(year): str(year)
                                for year in df_sunburst["Year"].unique()
                            },
                            step=None,
                        ),
                    ],
                ),
                dcc.Tab(
                    label="Take Action",
                    children=[
                        html.H1(
                            "What You Can Do",
                            style={
                                "width": "100%",
                                "text-align": "center",
                                "padding-top": "5%",
                            },
                        ),
                        html.Div(
                            dcc.Markdown(
                                """
                You can add your signature to existing petitions [here.](https://petition.parliament.uk/petitions?state=open&topic=race-and-equality)
                
                You can write to your MP. Find them [here.](https://members.parliament.uk/members/Commons)
                
                Sign the [petition](https://www.change.org/p/govia-thameslink-justice-for-belly-mujinga?recruiter=false&utm_source=share_petition&utm_medium=twitter&utm_campaign=psf_combo_share_initial&utm_term=psf_combo_share_initial&recruited_by_id=ffad40c0-a0c4-11ea-ac15-4118e05249bd) 
                to get justice for Belly Mujinga, who likely died after being spat at by an individual with COVID-19.
                
                [Donate](https://greenandblackcross.org/get-involved/donate/) to give legal support to protesters.
                
                [Support](https://supportgrenfell.co.uk/) the justice for grenfell movement.
                
                Keep learning and [read more!](https://blackinbritain.uk/resources)
                """
                            ),
                            style={
                                "width": "100%",
                                "text-align": "center",
                                "padding-top": "5%",
                            },
                        ),
                    ],
                ),
            ]
        )
    ]
)

# ----------------------------------------------------------------------------#
# Callbacks for interactive graph components
# ----------------------------------------------------------------------------#

# Create arrests graph


@app.callback(Output("arrests-graph", "figure"), [Input("year-slider", "value")])
def update_figure(selected_year):
    """
    Updates the arrests graph based on user input for the year.
    :param selected_year: int or float, user input.
    :return: a plotly express graph object.
    """

    # Add year slider and prep data

    df_temp = filtered_df[~filtered_df.Ethnicity.str.contains("White")]
    df_temp = df_temp[df_temp["Year"] == selected_year]

    # Draw figure. There was a glitch with the x axis title so I removed it here before drawing it on later

    fig = px.bar(
        df_temp,
        y="Ethnicity",
        x="Arrests",
        text="Arrests",
        color="Arrests per 1k",
        orientation="h",
        color_continuous_scale="sunsetdark",
        title="Adjusted = if arrested at white arrest rate.",
        hover_data={"Arrests": False, "Ethnicity": False},
    )

    # Format figure

    fig.update_traces(
        texttemplate="%{text:.2s}", textposition="outside",
    )

    fig.update_layout(
        xaxis_tickangle=-45,
        yaxis={"categoryorder": "category descending"},
        yaxis_title=None,
        xaxis_title="Number of Arrests",
        hovermode="x",
    )

    # Add annotations to show offset compared to white arrests

    fig.add_annotation(
        x=df_temp["Arrests"].iloc[0],
        y="Asian Actual",
        text="{}{}%".format(
            "+"
            if (
                (df_temp["Arrests"].iloc[0] - df_temp["Arrests"].iloc[1])
                / df_temp["Arrests"].iloc[0]
                * 100
            )
            > 0
            else "",
            int(
                round(
                    (df_temp["Arrests"].iloc[0] - df_temp["Arrests"].iloc[1])
                    / df_temp["Arrests"].iloc[1],
                    2,
                )
                * 100
            ),
        ),
        font=dict(color="white", size=12),
        arrowcolor="#ffffff",
    )
    fig.add_annotation(
        x=df_temp["Arrests"].iloc[2],
        y="Black Actual",
        text="{}{}%".format(
            "+",
            int(
                round(
                    (df_temp["Arrests"].iloc[2] - df_temp["Arrests"].iloc[3])
                    / df_temp["Arrests"].iloc[3],
                    2,
                )
                * 100
            ),
        ),
        font=dict(color="white", size=12,),
        arrowcolor="#ffffff",
    )
    fig.add_annotation(
        x=(df_temp["Arrests"].iloc[4]),
        y="Mixed Actual",
        text="{}{}%".format(
            "+",
            int(
                round(
                    (df_temp["Arrests"].iloc[4] - df_temp["Arrests"].iloc[5])
                    / df_temp["Arrests"].iloc[5],
                    2,
                )
                * 100
            ),
        ),
        font=dict(color="white", size=12,),
        arrowcolor="#ffffff",
    )
    fig.update_annotations(
        dict(xref="x", yref="y", showarrow=True, arrowhead=7, ax=-100, ay=0,)
    )

    # Make all fonts in graph Roboto

    fig["layout"]["titlefont"] = {"family": "Roboto", "size": 14}
    fig.layout.font.family = "Roboto"

    return fig


# Create justice graph


@app.callback(
    Output("justice-graph", "figure"), [Input("year-slider-justice", "value")]
)
def update_justice_figure(selected_justice_year):
    """
    Updates the justice graph based on user input for the year.
    :param selected_year: int or float, user input.
    :return: a plotly express graph object.
    """
    df_sunburst_graph = df_sunburst[df_sunburst["Year"] == selected_justice_year]
    justice_graph = px.sunburst(
        df_sunburst_graph,
        path=["Ethnicity", "Sentence Length"],
        values="Conviction Rate",
        color="Sentence Length",
        hover_data=[
            "Year",
            "Ethnicity",
            "Sentence Length",
            "Conviction Rate",
            "Custody Rate",
        ],
        color_continuous_scale="RdBu_r",
        color_continuous_midpoint=np.average(
            df_sunburst_graph["Sentence Length"],
            weights=df_sunburst_graph["Conviction Rate"],
        ),
    )

    justice_graph.update_traces(
        go.Sunburst(
            hovertemplate="""Year: %{customdata[0]} <br>Ethnicity:%{customdata[1]}
    <br>Sentence Length: %{customdata[2]} months <br>Conviction Rate %{customdata[3]}% 
    <br>Custody Rate: %{customdata[4]}%""",
            insidetextorientation="radial",
        )
    )

    justice_graph.update_layout(
        margin=dict(t=10, l=0, r=0, b=0),
        uniformtext=dict(minsize=10, mode="show"),
        paper_bgcolor="whitesmoke",
    )

    # Make all fonts in graph Roboto

    justice_graph["layout"]["titlefont"] = {"family": "Roboto", "size": 14}
    justice_graph.layout.font.family = "Roboto"

    return justice_graph


# Update markdown stats too


@app.callback(Output("times-more-likely", "children"), [Input("year-slider", "value")])
def update_text(selected_year):
    """
    This updates a text box below the graph that says how many times more likely black people are to be arrested.
    :param selected_year: int or float, user input.
    :return: string.
    """

    filtered_df.sort_values(by=["Year", "Ethnicity"], inplace=True)
    df_markdown = filtered_df[filtered_df["Year"] == selected_year]
    text = """
    This year Black, Asian, and Mixed people were respectively **{}**, **{}** and **{}** times as likely as white 
    people to be arrested.""".format(
        round(
            (
                df_markdown["Arrests per 1k"].iloc[2]
                / df_markdown["Arrests per 1k"].iloc[6]
            ),
            1,
        ),
        round(
            (
                df_markdown["Arrests per 1k"].iloc[0]
                / df_markdown["Arrests per 1k"].iloc[6]
            ),
            1,
        ),
        round(
            (
                df_markdown["Arrests per 1k"].iloc[4]
                / df_markdown["Arrests per 1k"].iloc[6]
            ),
            1,
        ),
    )

    return text


# ----------------------------------------------------------------------------#
# Launch
# ----------------------------------------------------------------------------#

if __name__ == "__main__":
    app.run_server(debug=True)
