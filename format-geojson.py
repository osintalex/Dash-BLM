import pandas as pd
import json
import pathlib


def format_geojson():
    """
    :param: the geojson file to format; you will be prompted for info on this when the script executes.
    This is how I formatted a particular geojson file for graphing in plotly. 
    There is a very good article on what to be aware of here https://archive.is/wip/6X0Pm.
    :return: None but it writes out a correctly formatted file.
    """

    # Geojson source I used https://github.com/martinjc/UK-GeoJSON of all the local authorities in the UK
    # This source file is in the data file of this repository

    with open(filename, "r") as f:
        data = json.load(f)

    # Get a list of all the local authorities

    local_authorities = []

    for x in data["features"]:

        local_authorities.append(x["properties"]["LAD13NM"])

    # Now get a list of all the local authorities we have data for

    path = str(pathlib.Path.cwd())
    df = pd.read_csv(
        path + "/data/" + "ethnic-population-by-local-authority.csv",
        usecols=["Measure", "Geography_name", "Ethnicity", "Value"],
    )
    ethnic_local_authorities = df["Geography_name"].unique().tolist()

    # Remove Scottish values from the geojson file as we have no data for them

    difference = list(set(local_authorities) - set(ethnic_local_authorities))
    positions_of_local_authorities_to_remove = []
    counter = 0
    another_counter = 0

    for x in data["features"]:
        if x["properties"]["LAD13NM"] in difference:
            positions_of_local_authorities_to_remove.append(counter)
        counter += 1

    for x in positions_of_local_authorities_to_remove:
        x = x - another_counter
        del data["features"][x]
        another_counter += 1

    # Format this file for use in plotly; see the archive url in the docstring for more information on this section.

    del data["crs"]
    for x in data["features"]:
        value = x["properties"]["LAD13NM"]
        x["id"] = value

    for x in data["features"]:
        del x["properties"]

    # Write out the correctly formatted geojson file

    with open("formatted_UK_LAD.geojson", "w") as f:
        json.dump(data, f)

        return None


if __name__ == "__main__":

    filename = input("Enter your filename here including the extension.")
    format_geojson()
