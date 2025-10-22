Feature: Reelly filter URL works
  As a QA Automation intern
  I want to confirm the filter URL loads correctly
  So I can rely on URL-based state for tests

  Scenario: Open saved filter URL and verify params
    Given I open the Reelly find page with filters URL
    Then The current URL should include the expected filter params
