import pandas as pd
import numpy as np
import json
import os
from dataclasses import dataclass


@dataclass
class DashBLM:

    arrests_filename: str = "arrest-police-powers-procedures-mar19-hosb2519-tables.ods"
    pop_filename: str = "ukpopulationestimates18382018.xlsx"
    geojson_filename: str = "formatted_UK_LAD.geojson"
    ethnic_pops_data: str = "ethnic-population-by-local-authority.csv"
    stopsearch_filename: str = "2019stopsearchresults.json"
    sentence_length_filename: str = "acsl-by-ethnicity-and-sex-2009-2017.csv"
    custody_rate_filename: str = "custody-rate.csv"
    conviction_filename: str = "prosecutions-and-convictions.csv"

    @classmethod
    def make_arrests_dataframe(cls):
        """
        Combines population data and arrests data for graphing in plotly.
        Also creates values for arrests per 1,000 people and adjusted values expressing how many people in different
        ethnic groups would be arrested if they were arrested at the same rate as white people.
        The full urls for both data sources are:
        https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/841253/arrest-police-powers-procedures-mar19-hosb2519-tables.ods
        https://www.ons.gov.uk/file?uri=%2fpeoplepopulationandcommunity%2fpopulationandmigration%2fpopulationestimates%2fdatasets%2fpopulationestimatesforukenglandandwalesscotlandandnorthernireland%2fmid2001tomid2018detailedtimeseries/ukpopulationestimates18382018.xlsx
        Writes out correctly formatted dataframes to csv.
        """

        # Import arrests data

        path = os.getcwd()
        df = pd.read_excel(
            path + "/data/" + cls.arrests_filename, sheet_name=3, engine="odf"
        )

        columns = ["Year"]

        for x in range(1, len(df.columns)):
            columns.append(df.iloc[3][x])

        df.columns = columns

        # This slices the table so we get just the relevant data

        df_clean = df.loc[5:17]
        df_clean["Year"] = df_clean["Year"].str.extract(r"^(\d{4})")

        # Assign correct datatypes

        index = df_clean.columns.tolist()
        dtypes = {key: "int" for key in index[:]}
        df_clean = df_clean.astype(dtypes)

        # Prepare dataframe from graphing in plotly

        rows = [[i for i in row] for row in df_clean.itertuples()]
        rows_flat = [y for x in rows for y in x]

        arrests = []
        for x in rows:
            arrests.append(x[2:6])
        arrests = [y for x in arrests for y in x]

        dff = pd.DataFrame(
            {
                "Ethnicity": ["White", "Black Actual", "Asian Actual", "Mixed Actual"]
                * 13,
                "Arrests": arrests,
                "Year": rows_flat[1::9] * 4,
            }
        )

        # Import population data

        path = os.getcwd()
        df_pop = pd.read_excel(path + "/data/" + cls.pop_filename, sheet_name=3)
        df_pop = df_pop.iloc[4:17, :2]
        df_pop.columns = ["Year", "Population"]
        df_pop = df_pop.astype({"Year": "str", "Population": "int"})

        # Slightly restructure the population dataframe so it's usable for processing later

        df_pop = df_pop.loc[np.repeat(df_pop.index.values, 3)]
        df_pop.sort_values(by=["Year"], ascending=True, inplace=True)

        # Now create the proportional equivalents
        # i.e if everyone was arrested the same amount as white people, how many arrests would there be?

        ethnic_breakdown = {
            "Asian": 0.075,
            "Black": 0.033,
            "Mixed": 0.022,
            "White": 0.86,
        }
        white_arrests = arrests[0::4]
        counter = -1
        arrests_proportions = []

        for x in white_arrests:
            counter += 1
            whiteness = x / df_pop["Population"].iloc[counter]
            black_proportion = whiteness * ethnic_breakdown["Black"]
            asian_proportion = whiteness * ethnic_breakdown["Asian"]
            mixed_proportion = whiteness * ethnic_breakdown["Mixed"]
            black_value = black_proportion * df_pop["Population"].iloc[counter]
            asian_value = asian_proportion * df_pop["Population"].iloc[counter]
            mixed_value = mixed_proportion * df_pop["Population"].iloc[counter]
            arrests_proportions.append(black_value)
            arrests_proportions.append(asian_value)
            arrests_proportions.append(mixed_value)

        # Now work out arrests per 1k for the proportions data

        arrests_per_1k = []
        asian_arrests = arrests_proportions[1::3]
        black_arrests = arrests_proportions[0::3]
        mixed_arrests = arrests_proportions[2::3]
        counter = -1

        for x, y, z in zip(asian_arrests, black_arrests, mixed_arrests):
            counter += 1
            asian_per_1k = round(
                (x / (ethnic_breakdown["Asian"] * df_pop["Population"].iloc[counter]))
                * 1000,
                1,
            )
            arrests_per_1k.append(asian_per_1k)
            black_per_1k = round(
                (y / (ethnic_breakdown["Black"] * df_pop["Population"].iloc[counter]))
                * 1000,
                1,
            )
            arrests_per_1k.append(black_per_1k)
            mixed_per_1k = round(
                (z / (ethnic_breakdown["Mixed"] * df_pop["Population"].iloc[counter]))
                * 1000,
                1,
            )
            arrests_per_1k.append(mixed_per_1k)

        # Make a dataframe capturing all this proportional data

        ethnic_proportions = ["Black Adjusted", "Asian Adjusted", "Mixed Adjusted"] * 13
        years = [element for element in rows_flat[1::9] for _ in range(3)]
        df_proportions = pd.DataFrame(
            {
                "Ethnicity": ethnic_proportions,
                "Arrests": arrests_proportions,
                "Year": years,
                "Arrests per 1k": arrests_per_1k,
            }
        )

        # Now add values for arrests per 1,000 people in different ethnic groups

        dff.sort_values(by=["Year", "Ethnicity"], inplace=True)

        actual_arrests_per_1k = []
        counter = -1

        for index, group in dff.groupby(np.arange(len(dff)) // 4):

            asian_per_1k = round(
                (
                    group["Arrests"].iloc[0]
                    / (ethnic_breakdown["Asian"] * df_pop["Population"].iloc[counter])
                )
                * 1000,
                1,
            )
            actual_arrests_per_1k.append(asian_per_1k)
            black_per_1k = round(
                (
                    group["Arrests"].iloc[1]
                    / (ethnic_breakdown["Black"] * df_pop["Population"].iloc[counter])
                )
                * 1000,
                1,
            )
            actual_arrests_per_1k.append(black_per_1k)
            mixed_per_1k = round(
                (
                    group["Arrests"].iloc[2]
                    / (ethnic_breakdown["Mixed"] * df_pop["Population"].iloc[counter])
                )
                * 1000,
                1,
            )
            actual_arrests_per_1k.append(mixed_per_1k)
            white_per_1k = round(
                (
                    group["Arrests"].iloc[3]
                    / (ethnic_breakdown["White"] * df_pop["Population"].iloc[counter])
                )
                * 1000,
                1,
            )
            actual_arrests_per_1k.append(white_per_1k)

        dff["Arrests per 1k"] = actual_arrests_per_1k

        # Now combine this all into one dataframe that we will use to graph in plotly

        filtered_df = pd.concat([dff, df_proportions])
        filtered_df.sort_values(["Ethnicity", "Year"], inplace=True)

        # Write out dataframes to csv

        df_clean.to_csv("df_clean.csv")
        filtered_df.to_csv("filtered_df.csv")

        return None

    @classmethod
    def make_choropleth_inputs(cls):
        """
        This provides the input data required to make a choropleth map of the black population across LADs
        (Local Area Districts) in England and Wales.
        Data source - https://github.com/martinjc/UK-GeoJSON. See format-geojson.py script for more info.
        Writes out black population dataframe to csv and local area ids dataframe to csv (i.e. the local area names).
        :return: mapbox token, geojson data for districts in England and Wales.
        """

        # Get mapbox token

        token = open(".mapbox_token").read()

        # Get geojson

        path = os.getcwd()
        with open(path + "/data/" + cls.geojson_filename, "r") as f:
            geojson = json.load(f)

        # Get ethnic population breakdowns

        df = pd.read_csv(
            path + "/data/" + cls.ethnic_pops_data,
            usecols=["Measure", "Geography_name", "Ethnicity", "Value"],
        )
        df = df.astype({"Measure": "category", "Ethnicity": "category"})
        df = df.loc[df["Measure"] == "% of national ethnic population in this LA area"]
        df = df.loc[
            df["Ethnicity"].isin(
                ["Black", "Black African", "Black Caribbean", "Black Other"]
            )
        ]

        # Get the total percentage of black people per district

        df_blackpops = df.groupby("Geography_name")["Value"].sum()

        # Get all the districts

        ethnic_local_authorities = df["Geography_name"].unique().tolist()

        df_ids = pd.DataFrame({"ids": sorted(ethnic_local_authorities)})

        # Write out dataframes to csv

        df_blackpops.to_csv("df_blackpops.csv")
        df_ids.to_csv("df_ids.csv")

        return token, geojson

    def make_scattermapbox_inputs(cls):
        """
        This provides stop search data obtained from the UK Police public API for a scattermapbox that operates
        on top of the choropleth map.
        Data source - https://data.police.uk/.
        Writes out scattermapbox dataframe to csv.
        """

        with open(cls.stopsearch_filename, "r") as f:
            stopsearchdata = json.load(f)

        # Create arrays of the values to graph

        lats = [
            (date, stopsearch["location"]["latitude"])[1]
            for date in stopsearchdata["results"]
            for stopsearch in stopsearchdata["results"][date]
        ]

        longs = [
            (date, stopsearch["location"]["longitude"])[1]
            for date in stopsearchdata["results"]
            for stopsearch in stopsearchdata["results"][date]
        ]

        reason = [
            (date, stopsearch["object_of_search"])[1]
            for date in stopsearchdata["results"]
            for stopsearch in stopsearchdata["results"][date]
        ]

        ethnicity = [
            (date, stopsearch["self_defined_ethnicity"])[1]
            for date in stopsearchdata["results"]
            for stopsearch in stopsearchdata["results"][date]
        ]

        age_range = [
            (date, stopsearch["age_range"])[1]
            for date in stopsearchdata["results"]
            for stopsearch in stopsearchdata["results"][date]
        ]

        gender = [
            (date, stopsearch["gender"])[1]
            for date in stopsearchdata["results"]
            for stopsearch in stopsearchdata["results"][date]
        ]

        # Assigning numeric values to different ethnicity categories so they show up in different sizes
        # Setting None values to 21 which is the White value since this is the largest group
        # Unfortunately they can't be removed as this would require deletion for the stop/searches they correspond to

        ethnic_categories = set(
            [(group).split(" - ")[0] for group in set(ethnicity) if group != None]
        )
        ethnic_numbers = {
            key: value
            for key, value in zip(
                ethnic_categories, range(1, 1 + (len(ethnic_categories) * 10), 10)
            )
        }
        color = [
            ethnic_numbers[((ethnic_group).split(" - ")[0])]
            if ethnic_group != None
            else 21
            for ethnic_group in ethnicity
        ]

        # Taking the same approach now to age_ranges
        # Setting none values to the biggest group which I think is 18-24 since this is the largest group
        # Unfortunately they can't be removed as this would require deletion for the stop/searches they correspond to

        age_categories = sorted(set([age for age in set(age_range) if age != None]))[
            ::-1
        ]
        age_numbers = {
            key: value
            for key, value in zip(
                age_categories, range(4, 4 + (len(age_categories) * 4), 4)
            )
        }
        size = [
            age_numbers[age_group] if age_group != None else 12
            for age_group in age_range
        ]

        # Creating text for hover info

        text = []

        for w, x, y, z in zip(reason, ethnicity, age_range, gender):
            text.append(
                "Reason: {}".format(w)
                + "<br>"
                + "Ethnicity: {}".format(x)
                + "<br>"
                + "Age: {}".format(y)
                + "<br>"
                + "Gender: {}".format(z)
            )

        constructordict = {
            "lats": lats,
            "longs": longs,
            "text": text,
            "size": size,
            "color": color,
        }
        df = pd.DataFrame.from_dict(constructordict)

        # Write out dataframe to csv

        df.to_csv("df_scatter.csv")

        return None

    @classmethod
    def make_sunburst_input(cls):
        """
        This reads in data from several different department of justice sources to form a dataframe of the proper
        format for the px.sunburst graph type.
        Data source: https://www.ethnicity-facts-figures.service.gov.uk/crime-justice-and-the-law.
        Writes out sunburst dataframe to csv.
        """

        path = os.getcwd() + "/data/"

        # Read in data from all three datasets

        df_sentence_length = pd.read_csv(
            path + cls.sentence_length_filename,
            usecols=["Year", "Ethnicity", "ACSL (in months)"],
        )
        df_sentence_length.columns = ["Year", "Ethnicity", "Sentence Length"]
        df_custody_rate = pd.read_csv(
            path + cls.custody_rate_filename,
            usecols=["Year", "Ethnicity", "Sex", "Age group", "Value", "Offence group"],
        )
        df_custody_rate.columns = [
            "Year",
            "Ethnicity",
            "Sex",
            "Age group",
            "Offence group",
            "Custody Rate",
        ]
        df_conviction_rate = pd.read_csv(
            path + cls.conviction_filename,
            usecols=[
                "Time",
                "Sex",
                "Age group",
                "Offence group",
                "Ethnicity",
                "Police Force Area",
                "Value",
            ],
        )

        # Redact to data which is the same across all three datasets; i.e. for all black people in 2009 rather than
        # for black women in a particular police force area in 2009

        df_sentence_length = (
            df_sentence_length.groupby(["Year", "Ethnicity"])["Sentence Length"]
            .agg("mean")
            .reset_index()
        )
        df_sentence_length["Sentence Length"] = df_sentence_length[
            "Sentence Length"
        ].round(1)

        df_custody_rate = df_custody_rate[
            df_custody_rate["Sex"].str.contains("All")
            & df_custody_rate["Age group"].str.contains("All")
            & df_custody_rate["Offence group"].str.contains("All")
        ]
        df_custody_rate.drop(
            columns=["Sex", "Age group", "Offence group"], axis=1, inplace=True
        )

        df_conviction_rate = df_conviction_rate[
            df_conviction_rate["Sex"].str.contains("All")
            & df_conviction_rate["Age group"].str.contains("All")
            & df_conviction_rate["Offence group"].str.contains("All")
            & df_conviction_rate["Police Force Area"].str.contains("All")
        ]
        df_conviction_rate.drop(
            columns=["Sex", "Age group", "Offence group", "Police Force Area"],
            inplace=True,
        )
        df_conviction_rate.columns = ["Ethnicity", "Year", "Conviction Rate"]

        # Join the datasets together

        df_combined = pd.merge(
            df_sentence_length, df_custody_rate, on=["Year", "Ethnicity"]
        )
        df_sunburst = pd.merge(
            df_combined, df_conviction_rate, on=["Year", "Ethnicity"]
        )

        # Write out dataframe to csv

        df_sunburst["Ethnicity"] = np.where(
            df_sunburst["Ethnicity"] != "Other inc Chinese",
            df_sunburst["Ethnicity"],
            "Other",
        )
        df_sunburst.to_csv("df_sunburst.csv")

        return None


if __name__ == "__main__":

    DashBLM = DashBLM()
    # DashBLM.make_arrests_dataframe()
    # DashBLM.make_choropleth_inputs()
    # DashBLM.make_scattermapbox_inputs()
    DashBLM.make_sunburst_input()
