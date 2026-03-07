@remote_hooks
Feature: Retail Product Catalog
  As a retail site operator
  I want to manage my product catalog via remote fixtures
  So that BDD tests can verify catalog behavior

  Scenario: Stock the catalog with generic products
    Given the catalog has "5" products
    When I browse the product catalog
    Then I should see 5 products

  Scenario: Add named products with prices
    Given a product named "Wireless Mouse" at $29.99
    And a product named "USB Keyboard" at $49.99
    When I browse the product catalog
    Then I should see 2 products
    And the catalog should include "Wireless Mouse"
    And "Wireless Mouse" should cost $29.99
    And the catalog should include "USB Keyboard"

  Scenario: Add products from a table
    Given the following products exist
      | name           | price | category    |
      | HDMI Cable     | 12.99 | accessories |
      | Monitor Stand  | 34.99 | furniture   |
      | Webcam         | 59.99 | electronics |
    When I browse the product catalog
    Then I should see 3 products
    And the catalog should include "HDMI Cable"

  Scenario: Add a category with a description
    Given a category "Electronics" with description
      """
      Consumer electronics including computers,
      peripherals, and mobile devices.
      """
    When I browse the categories
    Then I should see 1 categories
    And the category "Electronics" should have a description

  Scenario: Verify lifecycle hooks fired
    Given the catalog has "1" products
    When I check the hooks log
    Then the hooks log should include a "before_scenario" entry
    And the hooks log should include a "before_step" entry
    And the hooks log should include a "after_step" entry
