@remote_hooks
Feature: To-Do Management
  As a user of the to-do application
  I want to manage my to-do items via remote step fixtures

  Scenario: Create generic to-do items
    Given I have "3" existing to-do items
    When I request the to-do list
    Then I should see 3 items

  Scenario: Create a specific to-do item
    Given a to-do item titled "Buy milk"
    And a to-do item titled "Walk the dog"
    When I request the to-do list
    Then I should see 2 items
    And the list should include "Buy milk"
    And the list should include "Walk the dog"

  Scenario: Create to-do items from a table
    Given the following to-do items exist
      | title         | priority |
      | Buy groceries | high     |
      | Clean house   | low      |
      | Fix bike      | medium   |
    When I request the to-do list
    Then I should see 3 items
    And the list should include "Buy groceries"

  Scenario: Create a to-do item with a description
    Given a to-do item titled "Write report" with description
      """
      Quarterly financial report for Q1.
      Include revenue, expenses, and projections.
      """
    When I request the to-do list
    Then I should see 1 items
    And the item "Write report" should have a description
