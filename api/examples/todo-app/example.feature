@remote_hooks
Feature: To-Do list management
  As a user of the to-do application
  I want to manage my to-do items
  So that I can stay organized

  Scenario: User views a pre-populated to-do list
    Given I have "5" existing to-do items
    When I open the to-do list
    Then I should see 5 items

  Scenario: User has specific to-do items
    Given the following to-do items exist
      | title            | priority | completed |
      | Buy groceries    | high     | false     |
      | Walk the dog     | medium   | false     |
      | Read a book      | low      | true      |
    When I open the to-do list
    Then I should see 3 items
    And I should see 1 completed item
