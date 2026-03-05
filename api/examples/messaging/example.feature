@remote_hooks
Feature: Messaging between users
  As a user of the messaging platform
  I want to send and receive messages
  So that I can communicate with others

  Scenario: User sends a message in a conversation
    Given a user "alice" exists
    And a user "bob" exists
    And a conversation between "alice" and "bob"
    And "alice" has sent a message to "bob" with body
      """
      Hey Bob, are we still on for lunch tomorrow?
      Let me know what time works for you.
      """
    When "bob" opens the conversation with "alice"
    Then "bob" should see 1 message
    And the message body should contain "lunch tomorrow"

  Scenario: Multiple messages in a conversation
    Given a user "carol" exists
    And a user "dave" exists
    And a conversation between "carol" and "dave"
    And "carol" has sent a message to "dave" with body
      """
      Hi Dave,

      I wanted to follow up on the project proposal.
      Here are the key points:
      - Timeline: 3 months
      - Budget: $50,000
      - Team size: 4 people

      Let me know your thoughts.
      """
    And "dave" has sent a message to "carol" with body
      """
      Thanks Carol, I'll review and get back to you by Friday.
      """
    When "carol" opens the conversation with "dave"
    Then "carol" should see 2 messages
