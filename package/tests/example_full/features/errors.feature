@remote_hooks
Feature: Error Handling
  Verify that the library surfaces remote errors correctly

  Scenario: Server returns 500 (infrastructure error)
    Given the server has an internal error

  Scenario: Server returns 422 (validation error)
    Given the server rejects the request

  Scenario: Server returns 200 with status error (logical error)
    Given the server reports a logical error
