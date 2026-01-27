@spam @detection
Feature: Spam/Scam Detection
  As a user of the AI Anti-Spam Shield
  I want to scan messages for spam/scam content
  So that I can protect myself from malicious messages

  Background:
    Given the AI service is available
    And the detection threshold is set to 80%

  @positive @high-risk
  Scenario: Detect high-risk spam message
    Given I have a message "URGENT! You won $10,000! Click http://claim-prize.com NOW to collect!"
    When I scan the message for spam
    Then the result should indicate spam
    And the confidence should be greater than 80%
    And the risk level should be "CRITICAL" or "HIGH"
    And the danger causes should include "urgency_language"
    And the danger causes should include "spam_keywords"
    And the danger causes should include "contains_url"

  @positive @medium-risk
  Scenario: Detect medium-risk spam message
    Given I have a message "Special offer just for you! Limited time deal on amazing products"
    When I scan the message for spam
    Then the result should indicate spam
    And the risk level should be "MEDIUM" or "HIGH"

  @negative @safe
  Scenario: Detect safe message
    Given I have a message "Meeting tomorrow at 3pm in conference room A. Please bring your laptop."
    When I scan the message for spam
    Then the result should indicate safe
    And the is_safe flag should be true
    And the risk level should be "NONE"
    And the confidence label should be "Safety Confidence"

  @negative @greeting
  Scenario Outline: Safe greetings should bypass spam detection
    Given I have a message "<greeting>"
    When I scan the message for spam
    Then the result should indicate safe
    And the AI service should not be called
    And the bypass reason should be "safe_greeting_pattern"

    Examples:
      | greeting                    |
      | Hi                          |
      | Hello                       |
      | Hey there                   |
      | How are you                 |
      | Good morning                |
      | Hi, how are you?            |
      | Hello friend                |
      | What's up                   |

  @edge-case @short-message
  Scenario: Short messages get penalty applied
    Given I have a short message "ok thanks"
    And the AI returns a confidence of 75%
    When I scan the message for spam
    Then the short message penalty should be applied
    And the result should indicate safe
    And the adjusted confidence should be below threshold

  @authenticated
  Scenario: Scan history is saved for authenticated users
    Given I am logged in as "user@example.com"
    And I have a message "Test message for scanning"
    When I scan the message for spam
    Then the scan result should be saved to my history
    And I should be able to view the scan in my history

  @unauthenticated
  Scenario: Scan works without authentication
    Given I am not logged in
    And I have a message "Test message without auth"
    When I scan the message for spam
    Then the scan should complete successfully
    And the scan should not be saved to history

  @voice
  Scenario: Voice message spam detection
    Given I have an audio file containing spam content
    When I submit the audio for voice scanning
    Then the voice should be transcribed
    And the transcription should be analyzed for spam
    And the result should indicate spam

  @error-handling
  Scenario: Handle AI service unavailable
    Given the AI service is unavailable
    And I have a message "Test message"
    When I scan the message for spam
    Then I should receive an error message
    And the error should indicate service unavailability

  @performance
  Scenario: Response time within acceptable limits
    Given I have a message "Performance test message"
    When I scan the message for spam
    Then the response should be received within 5 seconds
