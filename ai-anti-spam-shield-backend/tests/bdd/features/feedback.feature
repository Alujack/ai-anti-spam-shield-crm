@feedback @continuous-learning
Feature: User Feedback and Continuous Learning
  As a user of the AI Anti-Spam Shield
  I want to provide feedback on scan results
  So that the AI model can improve over time

  Background:
    Given I am logged in as "user@example.com"

  @submit @false-positive
  Scenario: Submit false positive feedback
    Given I have a scan result that was incorrectly marked as spam
    When I submit feedback with type "false_positive"
    Then the feedback should be recorded
    And the original prediction should be stored
    And the corrected label should be "ham"
    And the feedback status should be "pending"

  @submit @false-negative
  Scenario: Submit false negative feedback
    Given I have a scan result that was incorrectly marked as safe
    When I submit feedback with type "false_negative"
    Then the feedback should be recorded
    And the corrected label should be "spam"

  @submit @confirmed
  Scenario: Confirm correct prediction
    Given I have a scan result that was correctly identified as spam
    When I submit feedback with type "confirmed"
    Then the feedback should be recorded
    And the corrected label should match the original prediction

  @submit @phishing
  Scenario: Submit phishing scan feedback
    Given I have a phishing scan result
    When I submit feedback for the phishing scan
    Then the feedback should be linked to the phishing history
    And the phishing scan ID should be stored

  @submit @duplicate
  Scenario: Prevent duplicate feedback
    Given I have already submitted feedback for scan "scan-123"
    When I try to submit another feedback for the same scan
    Then I should receive a conflict error
    And the error should indicate feedback already exists

  @submit @ownership
  Scenario: Cannot submit feedback for other users' scans
    Given another user has a scan with ID "other-scan-456"
    When I try to submit feedback for that scan
    Then I should receive a forbidden error

  @review @admin
  Scenario: Admin reviews pending feedback
    Given I am logged in as an admin
    And there is pending feedback with ID "feedback-123"
    When I approve the feedback
    Then the feedback status should be "approved"
    And the reviewer ID should be stored
    And the reviewed timestamp should be set

  @review @reject
  Scenario: Admin rejects feedback
    Given I am logged in as an admin
    And there is pending feedback with ID "feedback-123"
    When I reject the feedback
    Then the feedback status should be "rejected"

  @review @already-reviewed
  Scenario: Cannot review already reviewed feedback
    Given I am logged in as an admin
    And there is approved feedback with ID "feedback-123"
    When I try to approve the feedback again
    Then I should receive a bad request error
    And the error should indicate feedback already reviewed

  @list @pending
  Scenario: Admin views pending feedback
    Given I am logged in as an admin
    And there are 15 pending feedback items
    When I request pending feedback with page 1 and limit 10
    Then I should receive 10 feedback items
    And all items should have status "pending"
    And each item should include scan data

  @list @filter
  Scenario: Filter feedback by type
    Given I am logged in as an admin
    And there are feedback items of different types
    When I filter by type "false_positive"
    Then all returned feedback should be false positives

  @statistics
  Scenario: View feedback statistics
    Given I am logged in as an admin
    And there are feedback items:
      | type           | status   | count |
      | false_positive | pending  | 10    |
      | false_positive | approved | 20    |
      | false_negative | pending  | 5     |
      | false_negative | approved | 15    |
      | confirmed      | approved | 50    |
    When I request feedback statistics
    Then the total should be 100
    And the pending count should be 15
    And the approved count should be 85
    And false positive rate should be calculated

  @export
  Scenario: Export approved feedback for training
    Given there are 30 approved feedback items not yet used for training
    When I export approved feedback for training
    Then I should receive training data for 30 items
    And each item should have corrected label
    And each item should have original text
    And the feedback should be marked as included in training

  @export @csv
  Scenario: Export feedback as CSV
    Given there are approved feedback items
    When I export feedback in CSV format
    Then I should receive CSV data
    And the CSV should have proper headers
    And each row should have all required fields

  @retraining @threshold
  Scenario: Automatic retraining trigger
    Given the retraining threshold is 50 approved samples
    And there are 48 approved feedback not yet used for training
    When I approve 2 more feedback items
    Then a retraining job should be queued
    And the job should include sample count

  @user-history
  Scenario: View my feedback history
    Given I have submitted 5 feedback items
    When I request my feedback history
    Then I should see all 5 feedback items
    And each item should show status
    And each item should show feedback type

  @view
  Scenario: View specific feedback details
    Given I have submitted feedback with ID "feedback-123"
    When I request feedback "feedback-123"
    Then I should see the feedback details
    And I should see the original scan data
    And I should see the corrected label

  @view @forbidden
  Scenario: Cannot view other users' feedback
    Given another user has feedback with ID "other-feedback-456"
    And I am not an admin
    When I try to view feedback "other-feedback-456"
    Then I should receive a forbidden error
