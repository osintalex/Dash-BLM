import requests
import pathlib
import glob
import json
import logging
import time
import random
from dataclasses import dataclass
from argparse import ArgumentParser
import pandas as pd
import tenacity


@dataclass
class PoliceAPI:
    @staticmethod
    def flatten(bad):
        """
        Flattenst a list no matter how many sublists.
        :param bad: the bad list of sublists you want to flatten.
        :return: flat list.
        """

        good = []

        while bad:
            e = bad.pop()
            if isinstance(e, list):
                bad.extend(e)
            else:
                good.append(e)

        return good[::-1]

    @staticmethod
    def swap_pairs(poly):
        """
        Turns a list like this [1, 2, 3, 4] into [2, 1, 4, 3]
        :param poly: list
        :return: list
        """

        for i in range(0, len(poly) - 1, 2):
            poly[i], poly[i + 1] = poly[i + 1], poly[i]

        return poly

    @staticmethod
    def format_geojson_for_api(poly=None):
        """
        Turns geojson co-ordinates into the format requried by the UK police API; example format below:
         https://data.police.uk/api/stops-street?poly=52.2,0.5:52.8,0.2:52.1,0.88&date=2018-06.
        :param poly: list of sublists containing lat/long co-ordinate pairs.
        :return: string in the right format for the API.
        """

        poly = PoliceAPI.flatten(poly)
        poly = PoliceAPI.swap_pairs(poly)
        polys_formatted = [
            str(x) + "," + str(y) + ":" for x, y in zip(poly[0::2], poly[1::2])
        ]
        polys_formatted[-1] = polys_formatted[-1].replace(":", "")
        poly_as_string = "".join(x for x in polys_formatted)

        return poly_as_string

    @staticmethod
    @tenacity.retry(stop=tenacity.stop_after_attempt(10))
    def get_stop_search_data(poly, date):
        """
        Makes an API call to the UK Police API for stop search data.
        :param poly: string; the area you want want to find stop and searches in
        :param date: string; you have to specify a year and a month
        :return: the response as a string.
        """

        api_endpoint = "https://data.police.uk/api/stops-street?"
        data = {"poly": poly, "date": date}
        response = requests.post(url=api_endpoint, data=data)
        if response.status_code == 200:
            logging.info("[*] Successful API call, saving data...")
        else:
            logging.info(
                "[*] API call failed - {}{}".format(
                    response.status_code, response.reason
                )
            )
        time.sleep(random.uniform(1, 2))

        return response.text

    @staticmethod
    def write_results(result):
        """
        Writes the API response to a json file.
        :param result: list of json dicts.
        :return: None.
        """

        logging.info("[*] Writing data...")
        with open("stopsearchresults.json", "a") as f:
            json.dump(result, f)

        return None


if __name__ == "__main__":

    logging.basicConfig(
        filename="Police API Calls.log",
        filemode="a",
        format="%(asctime)s-%(message)s",
        level=logging.DEBUG,
    )
    path = str(pathlib.Path.cwd()) + "/data/"

    with open(path + "formatted_UK_LAD.geojson", "r") as original_file:
        geojson = json.load(original_file)

    parser = ArgumentParser()
    parser.add_argument(
        "--lad",
        action="store_true",
        help="For stop and searches in one local area district.",
    )
    parser.add_argument(
        "--date",
        action="store_true",
        help="""For stop and searches in all local area districts on the 
                                                            same date.""",
    )
    parser.add_argument(
        "--range",
        action="store_true",
        help="For stop and searches in all local area districts on a range of dates.",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="""Join results from differen months together. Only works
                                                            with output from the --range argument.""",
    )

    args = parser.parse_args()
    PoliceAPI = PoliceAPI()

    data = []

    if args.lad:

        input_date = input("Enter your date here in a YYYY-MM format")
        input_LAD = input(
            "Enter the name of your target local area district. First letter must be capitalized."
        )

        counter = 0
        for LAD in geojson["features"]:

            counter += 1

            if LAD["id"] == input_LAD:
                original_poly = geojson["features"][0]["geometry"]["coordinates"]
                formatted_poly = PoliceAPI.format_geojson_for_api(poly=original_poly)
                output = PoliceAPI.get_stop_search_data(
                    poly=formatted_poly, date=input_date
                )
                value_to_write = json.loads(output)
                if output:
                    result = {"results": value_to_write[0]}
                    PoliceAPI.write_results(result=result)

        if len(geojson["features"]) == counter:
            logging.info(
                "This LAD is incorrect. Check the spelling/formatting and try again."
            )

    if args.date:

        input_date = input("Enter your date here in a YYYY-MM format")
        results = []

        for LAD in geojson["features"]:
            original_poly = LAD["geometry"]["coordinates"]
            logging.info(
                "Trying to get stop and search data for LAD {}.".format(LAD["id"])
            )
            formatted_poly = PoliceAPI.format_geojson_for_api(poly=original_poly)
            output = PoliceAPI.get_stop_search_data(
                poly=formatted_poly, date=input_date
            )
            value_to_write = json.loads(output)
            if value_to_write:
                results.append(value_to_write[0])

        result = {"results": {input_date: results}}
        with open("stopsearch-{}.json".format(input_date), "w") as f:
            json.dump(result, f)

    if args.range:

        start_date = input("Enter desired start date in YYYY-MM format.")
        end_date = input("Enter desired end date in YYYY-MM format.")
        input_dates = (
            pd.date_range(start_date, end_date, freq="MS").strftime("%Y-%m").tolist()
        )
        input_dates = input_dates[
            ::-1
        ]  # it's unclear when the police data begins so best to go through in reverse
        results = []

        for target_date in input_dates:
            # Written the below to fix an error where original_poly a few lines below kept coming back as an empty list
            with open(path + "formatted_UK_LAD.geojson", "r") as original_file:
                geojson = json.load(original_file)
            for item in geojson["features"]:
                original_poly = item["geometry"]["coordinates"]
                logging.info(
                    "Trying to get stop and search data for LAD {} on date {}.".format(
                        item["id"], target_date
                    )
                )
                formatted_poly = PoliceAPI.format_geojson_for_api(poly=original_poly)
                output = PoliceAPI.get_stop_search_data(
                    poly=formatted_poly, date=target_date
                )
                value_to_write = json.loads(output)
                if value_to_write:
                    results.append(value_to_write[0])

            if target_date == input_dates[0]:
                result = {"results": {target_date: results}}
                with open("stopsearch-{}.json".format(target_date), "w") as f:
                    json.dump(result, f)
            else:
                result["results"][target_date] = results
                with open("stopsearch-{}.json".format(target_date), "w") as f:
                    json.dump(result, f)

    if args.merge:

        target_year = input("Which year are you merging different json data for?")

        root_path = str(pathlib.Path.cwd())
        json_files = glob.glob(root_path + "/*.json")

        stopsearchdata = {"results": {}}

        for json_month in json_files:

            with open(json_month.split(root_path)[1].replace("/", ""), "r") as f:
                that_months_data = json.load(f)
                stopsearchdata["results"] = that_months_data["results"]

        with open("{}stopsearchresults.json".format(target_year), "w") as f_to_write:
            json.dump(stopsearchdata, f_to_write)
