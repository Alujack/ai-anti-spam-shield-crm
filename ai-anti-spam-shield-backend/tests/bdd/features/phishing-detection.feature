@phishing @detection
Feature: Phishing Detection
  As a user of the AI Anti-Spam Shield
  I want to scan messages and URLs for phishing content
  So that I can protect myself from credential theft and fraud

  Background:
    Given the phishing detection service is available
    And the phishing detection threshold is set to 65%

  @text @critical
  Scenario: Detect critical phishing email
    Given I have a text "Your PayPal account has been suspended! Click here to verify: http://paypa1-secure.com/verify"
    When I scan the text for phishing
    Then the result should indicate phishing
    And the threat level should be "CRITICAL"
    And the phishing type should be "EMAIL"
    And brand impersonation should be detected
    And the impersonated brand should be "PayPal"
    And the danger causes should include "brand_impersonation"

  @text @high
  Scenario: Detect high-risk phishing SMS
    Given I have a text "Your bank account is locked. Call 1-800-SCAM now or click http://bank-verify.tk"
    When I scan the text for phishing with type "sms"
    Then the result should indicate phishing
    And the threat level should be "HIGH" or "CRITICAL"
    And the danger causes should include "suspicious_urls"

  @text @safe
  Scenario: Detect safe text message
    Given I have a text "Don't forget to pick up groceries on your way home. Mom"
    When I scan the text for phishing
    Then the result should indicate safe
    And the is_safe flag should be true
    And the threat level should be "NONE"

  @url @suspicious
  Scenario: Detect suspicious URL
    Given I have a URL "http://paypa1-login-secure.tk/signin"
    When I scan the URL for phishing
    Then the result should indicate phishing
    And the URL should be analyzed
    And suspicious patterns should be detected
    And the danger causes should include "suspicious_tld"

  @url @ip-address
  Scenario: Detect IP address based phishing URL
    Given I have a URL "http://192.168.1.1/banking/login"
    When I scan the URL for phishing
    Then the result should indicate phishing
    And the danger causes should include "ip_address_url"
    And the severity should be "critical"

  @url @brand-spoofing
  Scenario: Detect brand spoofing in URL
    Given I have a URL "http://amazon-deals-verify.com/account"
    When I scan the URL for phishing
    Then brand impersonation should be detected
    And the danger causes should include "brand_spoofing"

  @url @safe
  Scenario: Detect safe URL
    Given I have a URL "https://www.google.com/search?q=weather"
    When I scan the URL for phishing
    Then the result should indicate safe
    And the URL should be marked as not suspicious

  @batch
  Scenario: Batch scan multiple items
    Given I have the following items to scan:
      | item                                          |
      | Your account has been compromised! Click here |
      | Meeting at 2pm tomorrow                       |
      | http://scam-site.tk/login                     |
    When I perform a batch phishing scan
    Then I should receive results for all 3 items
    And the summary should show 2 phishing detected
    And the summary should show 1 safe

  @indicators
  Scenario: Detailed phishing indicators
    Given I have a text containing multiple phishing indicators
    When I scan the text for phishing
    Then the indicators list should not be empty
    And each indicator should have a description
    And high severity indicators should be highlighted

  @recommendation
  Scenario Outline: Appropriate recommendations based on threat level
    Given I have content with "<threat_level>" threat level
    When I scan for phishing
    Then the recommendation should contain "<keyword>"

    Examples:
      | threat_level | keyword          |
      | CRITICAL     | DANGER           |
      | HIGH         | WARNING          |
      | MEDIUM       | CAUTION          |
      | NONE         | appears to be safe |

  @history
  Scenario: Phishing scan history tracking
    Given I am logged in as "user@example.com"
    And I have a URL "http://suspicious-site.com"
    When I scan the URL for phishing
    Then the scan should be saved to my phishing history
    And I should be able to retrieve the scan by ID
    And I should be able to delete the scan from history

  @statistics
  Scenario: User phishing statistics
    Given I am logged in as "user@example.com"
    And I have performed 10 phishing scans
    And 3 of them detected phishing
    When I request my phishing statistics
    Then the total scans should be 10
    And the phishing detected count should be 3
    And the phishing percentage should be 30%
