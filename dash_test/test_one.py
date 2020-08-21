from dash.testing.application_runners import import_app


def test_bbaaa001(dash_duo):
    """
    Dash documentation on this is here https://dash.plotly.com/testing, it's not very thorough.
    To install chromedriver, you download it from the website then copy it to PATH - on mac this meant moving it to
    /usr/local/bin. At time of writing it couldn't be version 85.
    To run this hit the below while in the project root directory.
    python -m pytest dash_test/
    """

    app = import_app("dash_test.app")
    dash_duo.start_server(app)

    dash_duo.wait_for_text_to_equal("h1", "About", timeout=10)

    assert dash_duo.find_element("em").text == "Sources"

    assert dash_duo.get_logs() == [], "Browser console should contain no error"

    return None
