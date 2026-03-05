@remote_hooks
Feature: E-Commerce shopping flow
  As an online shopper
  I want to browse products and manage my cart
  So that I can purchase items

  Scenario: User adds a product to their cart
    Given a user "alice" with account balance 500
    And the product catalog contains 10 items
    And user "alice" has item "Wireless Mouse" in their cart
    When user "alice" views their cart
    Then the cart should contain 1 item
    And the cart total should be less than 500

  Scenario: Multiple users shopping concurrently
    Given a user "bob" with account balance 1000
    And a user "carol" with account balance 250
    And the product catalog contains 50 items
    And user "bob" has item "Mechanical Keyboard" in their cart
    And user "carol" has item "USB-C Hub" in their cart
    When user "bob" checks out
    Then user "bob" account balance should be reduced
