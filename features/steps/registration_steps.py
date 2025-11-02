from behave import when, then

FULL_NAME = "test+ozan careerist"
PHONE     = "+971555123456"
EMAIL     = "test.ozan.careerist+qa@example.com"
PASSWORD  = "TestPassword!123"

@when("I fill the registration form with valid test data")
def fill_form(context):
    # Use the POM
    context.app.sign_up_page.fill_form(
        full_name=FULL_NAME,
        phone=PHONE,
        email=EMAIL,
        password=PASSWORD
    )

@then("Each registration field shows the entered value")
def verify_values(context):
    context.app.sign_up_page.assert_form_values(
        full_name=FULL_NAME,
        phone_part="+971",
        email=EMAIL,
        password=PASSWORD
    )