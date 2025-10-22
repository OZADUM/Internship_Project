from behave import given, then

REELLY_SIGNUP_URL = "https://soft.reelly.io/sign-up"

@given("I open the Reelly sign-up page")
def step_open_signup(context):
    context.app.open(REELLY_SIGNUP_URL)

@then('The page title should contain "Reelly"')
def step_verify_title(context):
    assert "reelly" in context.driver.title.lower(), f"Unexpected title: {context.driver.title}"