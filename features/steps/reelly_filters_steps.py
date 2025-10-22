
from behave import given, then
from urllib.parse import urlparse, parse_qs

FILTER_URL = "https://find.reelly.io/?pricePer=unit&withDealBonus=false&handoverOnly=false&handoverMonths=1"

@given("I open the Reelly find page with filters URL")
def open_filter_url(context):
    context.app.open(FILTER_URL)

@then("The current URL should include the expected filter params")
def verify_filter_params(context):
    current = context.driver.current_url
    parsed = urlparse(current)
    qs = {k: v[0] for k, v in parse_qs(parsed.query).items()}

    # Host sanity
    assert "reelly.io" in parsed.netloc, f"Unexpected host: {parsed.netloc}"

    # Param assertions (string compare since URL query values are strings)
    expected = {
        "pricePer": "unit",
        "withDealBonus": "false",
        "handoverOnly": "false",
        "handoverMonths": "1",
    }
    for k, v in expected.items():
        assert qs.get(k) == v, f'Param {k} expected "{v}" but got "{qs.get(k)}" in URL: {current}'

