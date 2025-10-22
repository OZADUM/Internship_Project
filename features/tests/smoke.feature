Feature: Smoke sanity for Reelly
  As a QA Automation intern
  I want to confirm my framework launches and can open the app
  So I can start taking Jira tickets

  Scenario: Open Reelly sign-up page
    Given I open the Reelly sign-up page
    Then The page title should contain "Reelly"