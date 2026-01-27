@auth @user
Feature: User Authentication
  As a user of the AI Anti-Spam Shield
  I want to register, login, and manage my account
  So that I can access personalized features and save my scan history

  @registration
  Scenario: Successful user registration
    Given I am a new user
    When I register with the following details:
      | email    | test@example.com |
      | password | SecurePass123!   |
      | name     | Test User        |
      | phone    | +1234567890      |
    Then my account should be created successfully
    And I should receive an access token
    And I should receive a refresh token
    And my profile should be accessible

  @registration @validation
  Scenario Outline: Registration validation
    Given I am a new user
    When I try to register with invalid "<field>" value "<value>"
    Then I should receive a validation error
    And the error should mention "<field>"

    Examples:
      | field    | value          |
      | email    | invalid-email  |
      | email    |                |
      | password | 123            |
      | password |                |

  @registration @duplicate
  Scenario: Prevent duplicate email registration
    Given a user with email "existing@example.com" already exists
    When I try to register with email "existing@example.com"
    Then I should receive an error
    And the error should indicate email is already registered

  @login
  Scenario: Successful login
    Given I have a registered account with:
      | email    | user@example.com |
      | password | MyPassword123!   |
    When I login with email "user@example.com" and password "MyPassword123!"
    Then I should be logged in successfully
    And I should receive an access token
    And I should receive a refresh token

  @login @invalid
  Scenario: Login with invalid credentials
    Given I have a registered account with email "user@example.com"
    When I login with email "user@example.com" and password "WrongPassword!"
    Then I should receive an authentication error
    And I should not receive any tokens

  @login @nonexistent
  Scenario: Login with non-existent email
    When I login with email "nonexistent@example.com" and password "AnyPassword123!"
    Then I should receive an authentication error

  @profile
  Scenario: Access user profile
    Given I am logged in as "user@example.com"
    When I request my profile
    Then I should see my profile information
    And I should see my email
    And I should see my name
    And I should not see my password

  @profile @unauthorized
  Scenario: Profile requires authentication
    Given I am not logged in
    When I try to access my profile
    Then I should receive an unauthorized error

  @token @refresh
  Scenario: Refresh access token
    Given I am logged in and have a refresh token
    When my access token expires
    And I use my refresh token to get a new access token
    Then I should receive a new access token
    And I should be able to access protected endpoints

  @logout
  Scenario: Successful logout
    Given I am logged in as "user@example.com"
    When I logout
    Then my session should be terminated
    And I should not be able to access protected endpoints

  @security @password
  Scenario: Password is stored securely
    Given I register with password "SecurePass123!"
    Then my password should be hashed
    And the original password should not be stored

  @security @rate-limit
  Scenario: Rate limiting on login attempts
    Given I have a registered account with email "user@example.com"
    When I attempt to login 10 times with wrong password
    Then I should be rate limited
    And I should receive a rate limit error
