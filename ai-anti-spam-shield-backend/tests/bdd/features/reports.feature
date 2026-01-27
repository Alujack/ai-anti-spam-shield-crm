@reports
Feature: Report Submission and Management
  As a user of the AI Anti-Spam Shield
  I want to report suspicious messages and threats
  So that I can help improve detection and protect others

  Background:
    Given I am logged in as "user@example.com"

  @create @spam
  Scenario: Submit a spam report
    Given I have detected a spam message
    When I create a report with:
      | messageText | URGENT! You won $1,000,000! Call now! |
      | reportType  | SPAM                                   |
      | description | This is clearly spam                   |
      | phoneNumber | +1-800-SCAM                            |
    Then the report should be created successfully
    And the report status should be "PENDING"
    And I should receive the report ID

  @create @phishing
  Scenario: Submit a phishing report
    Given I have detected a phishing attempt
    When I create a report with:
      | messageText | Your account is compromised!           |
      | reportType  | PHISHING                               |
      | description | Fake bank email with suspicious link   |
      | url         | http://fake-bank.tk/login              |
    Then the report should be created successfully
    And the report type should be "phishing"

  @create @scam
  Scenario: Submit a scam report
    When I create a report with:
      | messageText | Investment opportunity! 1000% returns! |
      | reportType  | SCAM                                   |
      | description | Investment scam targeting elderly      |
      | senderInfo  | scammer@fake.com                       |
    Then the report should be created successfully
    And the report type should be "scam"

  @create @validation
  Scenario: Report type validation
    When I try to create a report with:
      | messageText | Some message      |
      | reportType  | INVALID_TYPE      |
      | description | Test description  |
    Then I should receive a validation error
    And the error should mention "Invalid report type"

  @create @required-fields
  Scenario Outline: Required field validation
    When I try to create a report without "<field>"
    Then I should receive a validation error

    Examples:
      | field       |
      | messageText |
      | reportType  |
      | description |

  @list
  Scenario: View my reports
    Given I have submitted 5 reports
    When I request my reports list
    Then I should see all 5 reports
    And the reports should be ordered by creation date descending
    And each report should have a status

  @list @pagination
  Scenario: Paginated reports list
    Given I have submitted 50 reports
    When I request page 1 with limit 20
    Then I should receive 20 reports
    And the pagination should indicate 50 total
    And the pagination should indicate 3 total pages

  @list @filter
  Scenario Outline: Filter reports by status
    Given I have reports with different statuses
    When I filter reports by status "<status>"
    Then all returned reports should have status "<status>"

    Examples:
      | status   |
      | PENDING  |
      | REVIEWED |
      | RESOLVED |
      | REJECTED |

  @view
  Scenario: View specific report
    Given I have submitted a report with ID "report-123"
    When I request report "report-123"
    Then I should see the report details
    And I should see the message text
    And I should see the report type
    And I should see the status

  @view @not-found
  Scenario: View non-existent report
    When I request report "non-existent-id"
    Then I should receive a not found error

  @update @user
  Scenario: User can update own report description
    Given I have submitted a report with ID "report-123"
    When I update the report description to "Updated description"
    Then the report description should be updated

  @update @admin
  Scenario: Admin can update report status
    Given I am logged in as an admin
    And there is a pending report with ID "report-456"
    When I update the report status to "RESOLVED"
    Then the report status should be "RESOLVED"

  @update @forbidden
  Scenario: Regular user cannot update report status
    Given I have submitted a report with ID "report-123"
    When I try to update the report status to "RESOLVED"
    Then I should receive a forbidden error

  @delete
  Scenario: Delete own report
    Given I have submitted a report with ID "report-123"
    When I delete report "report-123"
    Then the report should be deleted successfully
    And the report should no longer be accessible

  @delete @not-found
  Scenario: Delete non-existent report
    When I try to delete report "non-existent-id"
    Then I should receive a not found error

  @statistics
  Scenario: View report statistics
    Given I have submitted reports:
      | type     | status   | count |
      | SPAM     | PENDING  | 10    |
      | SPAM     | RESOLVED | 5     |
      | PHISHING | PENDING  | 8     |
      | PHISHING | RESOLVED | 3     |
      | SCAM     | REJECTED | 2     |
    When I request my report statistics
    Then the total reports should be 28
    And the pending count should be 18
    And the resolved count should be 8
    And the spam reports should be 15
    And the phishing reports should be 11

  @workflow
  Scenario: Report workflow from submission to resolution
    Given I submit a new spam report
    Then the report status should be "PENDING"
    When an admin reviews the report
    Then the report status should be "REVIEWED"
    When the admin resolves the report
    Then the report status should be "RESOLVED"
    And the resolved timestamp should be set

  @anonymous
  Scenario: Anonymous users cannot submit reports
    Given I am not logged in
    When I try to create a report
    Then I should receive an unauthorized error
