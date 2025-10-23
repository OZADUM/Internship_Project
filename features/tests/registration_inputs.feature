Feature: Registration input fields accept user data
  As a prospective user
  I want to enter information into registration inputs
  So that I can proceed with verification later

  Scenario: The user can enter the information into the input fields on the registration page
    Given I open the Reelly sign-up page
    When I fill the registration form with valid test data
    Then Each registration field shows the entered value
