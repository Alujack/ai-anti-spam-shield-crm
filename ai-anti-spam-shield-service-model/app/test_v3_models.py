#!/usr/bin/env python3
"""
Test script for V3 Pre-trained Models

This script tests the new V3 predictor and ensemble predictor
to verify they work correctly before deployment.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def test_predictor_v3():
    """Test the V3 predictor with HuggingFace models"""
    print("\n" + "="*60)
    print("Testing V3 Pre-trained Predictor")
    print("="*60)

    try:
        from model.predictor_v3 import MultiModelPredictorV3

        predictor = MultiModelPredictorV3(model_dir='./trained_models_v3')

        # Test messages
        test_cases = [
            # Spam/Scam messages
            {
                "text": "Congratulations! You've won $1,000,000! Click here to claim your prize now!",
                "expected_spam": True,
                "description": "Prize scam"
            },
            {
                "text": "URGENT: Your bank account has been suspended. Verify immediately: http://fake-bank.xyz",
                "expected_spam": True,
                "description": "Bank phishing"
            },
            {
                "text": "Your Amazon order has been delayed. Confirm your address at http://amaz0n.tk/verify",
                "expected_spam": True,
                "description": "Impersonation phishing"
            },

            # Legitimate messages
            {
                "text": "Hey, are you coming to the meeting tomorrow?",
                "expected_spam": False,
                "description": "Normal message"
            },
            {
                "text": "Thanks for your help yesterday!",
                "expected_spam": False,
                "description": "Thank you message"
            },
            {
                "text": "Hi",
                "expected_spam": False,
                "description": "Simple greeting"
            },
        ]

        passed = 0
        failed = 0

        for test in test_cases:
            result = predictor.predict_auto(test["text"])
            is_correct = result["is_spam"] == test["expected_spam"]

            status = "PASS" if is_correct else "FAIL"
            if is_correct:
                passed += 1
            else:
                failed += 1

            print(f"\n[{status}] {test['description']}")
            print(f"  Text: {test['text'][:50]}...")
            print(f"  Expected: {'spam' if test['expected_spam'] else 'ham'}")
            print(f"  Got: {result['prediction']} (confidence: {result['confidence']:.2%})")
            print(f"  Model: {result['model_source']}")

        print(f"\n{'='*60}")
        print(f"Results: {passed}/{passed+failed} tests passed")
        print(f"{'='*60}")

        return failed == 0

    except Exception as e:
        print(f"Error testing V3 predictor: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ensemble_predictor():
    """Test the ensemble predictor"""
    print("\n" + "="*60)
    print("Testing Ensemble Predictor")
    print("="*60)

    try:
        from model.ensemble_predictor import EnsemblePredictor

        predictor = EnsemblePredictor(model_dir='./trained_models_v3')

        test_cases = [
            {
                "text": "URGENT: Your PayPal account has been limited. Click here to restore access: http://paypa1-verify.tk/login",
                "expected_threat": True,
                "description": "PayPal phishing"
            },
            {
                "text": "Hey, want to grab lunch today?",
                "expected_threat": False,
                "description": "Normal lunch invite"
            },
        ]

        for test in test_cases:
            result = predictor.predict(test["text"])

            status = "PASS" if result.is_threat == test["expected_threat"] else "FAIL"

            print(f"\n[{status}] {test['description']}")
            print(f"  Text: {test['text'][:50]}...")
            print(f"  Threat: {result.is_threat} (confidence: {result.confidence:.2%})")
            print(f"  Level: {result.threat_level}")
            print(f"  Scores - Transformer: {result.transformer_score:.2f}, "
                  f"Rules: {result.rule_score:.2f}, URLs: {result.url_score:.2f}")
            print(f"  Recommendation: {result.recommendation[:60]}...")

        return True

    except Exception as e:
        print(f"Error testing ensemble predictor: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_elder_mode():
    """Test elder-friendly warnings"""
    print("\n" + "="*60)
    print("Testing Elder-Friendly Mode")
    print("="*60)

    try:
        from model.predictor_v3 import MultiModelPredictorV3

        predictor = MultiModelPredictorV3(model_dir='./trained_models_v3')

        text = "ALERT: Your Social Security number has been suspended. Call 1-800-FAKE immediately or face arrest!"

        result = predictor.predict_with_elder_mode(text, "sms")

        print(f"\nText: {text}")
        print(f"Is spam: {result['is_spam']}")
        print(f"Confidence: {result['confidence']:.2%}")

        if "elder_warnings" in result:
            print(f"\nElder Warnings:")
            for warning in result['elder_warnings']:
                print(f"  - {warning}")

        return True

    except Exception as e:
        print(f"Error testing elder mode: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("V3 MODEL TEST SUITE")
    print("="*60)

    results = {
        "predictor_v3": test_predictor_v3(),
        "ensemble": test_ensemble_predictor(),
        "elder_mode": test_elder_mode()
    }

    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)

    all_passed = all(results.values())

    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")

    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")

    sys.exit(0 if all_passed else 1)
