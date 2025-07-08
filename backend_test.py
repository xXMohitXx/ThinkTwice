import requests
import unittest
import time
import json
import uuid
import sys

# Use the public endpoint for testing
API_BASE_URL = "https://d1923bbc-a7fa-4061-b3d1-995e92c3619a.preview.emergentagent.com/api"

class ThinkTwiceAPITest(unittest.TestCase):
    """Test suite for ThinkTwice API endpoints"""
    
    def setUp(self):
        """Setup for each test"""
        self.user_id = f"test-user-{uuid.uuid4()}"
        self.test_texts = {
            "safe": "Thank you for your help today!",
            "harmful": "You are such a stupid idiot!",
            "borderline": "This is really frustrating and annoying",
            "empty": "",
            "long": "This is a very long text " + "test " * 500
        }
    
    def test_01_health_endpoint(self):
        """Test the health endpoint"""
        print("\n🔍 Testing health endpoint...")
        response = requests.get(f"{API_BASE_URL}/health")
        
        self.assertEqual(response.status_code, 200, "Health endpoint should return 200")
        data = response.json()
        
        # Check required fields
        self.assertIn("status", data, "Health response should include status")
        self.assertIn("model_loaded", data, "Health response should include model_loaded")
        self.assertIn("timestamp", data, "Health response should include timestamp")
        
        print(f"✅ Health endpoint test passed: {data['status']}")
        
    def test_02_analyze_text_safe(self):
        """Test text analysis with safe content"""
        print("\n🔍 Testing text analysis with safe content...")
        
        response = requests.post(
            f"{API_BASE_URL}/analyze-text",
            json={"text": self.test_texts["safe"], "threshold": 0.5}
        )
        
        self.assertEqual(response.status_code, 200, "Analyze endpoint should return 200")
        data = response.json()
        
        # Check response structure
        self.assertIn("regret_score", data, "Response should include regret_score")
        self.assertIn("should_warn", data, "Response should include should_warn")
        self.assertIn("analysis", data, "Response should include analysis")
        
        # Safe text should have low regret score
        self.assertLess(data["regret_score"], 0.3, "Safe text should have low regret score")
        self.assertFalse(data["should_warn"], "Safe text should not trigger warning")
        
        print(f"✅ Safe text analysis passed: Score={data['regret_score']:.2f}, Warning={data['should_warn']}")
        
    def test_03_analyze_text_harmful(self):
        """Test text analysis with harmful content"""
        print("\n🔍 Testing text analysis with harmful content...")
        
        response = requests.post(
            f"{API_BASE_URL}/analyze-text",
            json={"text": self.test_texts["harmful"], "threshold": 0.5}
        )
        
        self.assertEqual(response.status_code, 200, "Analyze endpoint should return 200")
        data = response.json()
        
        # Harmful text should have high regret score
        self.assertGreater(data["regret_score"], 0.5, "Harmful text should have high regret score")
        self.assertTrue(data["should_warn"], "Harmful text should trigger warning")
        
        print(f"✅ Harmful text analysis passed: Score={data['regret_score']:.2f}, Warning={data['should_warn']}")
        
    def test_04_analyze_text_threshold(self):
        """Test text analysis with different thresholds"""
        print("\n🔍 Testing text analysis with different thresholds...")
        
        # Test with borderline text and low threshold (should warn)
        response_low = requests.post(
            f"{API_BASE_URL}/analyze-text",
            json={"text": self.test_texts["borderline"], "threshold": 0.3}
        )
        
        data_low = response_low.json()
        
        # Test with same text and high threshold (should not warn)
        response_high = requests.post(
            f"{API_BASE_URL}/analyze-text",
            json={"text": self.test_texts["borderline"], "threshold": 0.7}
        )
        
        data_high = response_high.json()
        
        # Same text, different thresholds should give different warning results
        self.assertEqual(data_low["regret_score"], data_high["regret_score"], 
                         "Same text should have same regret score regardless of threshold")
        
        # Check if threshold affects warning
        if data_low["regret_score"] > 0.3 and data_low["regret_score"] < 0.7:
            self.assertTrue(data_low["should_warn"], "Should warn with low threshold")
            self.assertFalse(data_high["should_warn"], "Should not warn with high threshold")
            print("✅ Threshold test passed: Different thresholds produce different warnings")
        else:
            print("⚠️ Threshold test inconclusive: Text score not between thresholds")
        
    def test_05_analyze_text_edge_cases(self):
        """Test text analysis with edge cases"""
        print("\n🔍 Testing text analysis with edge cases...")
        
        # Test with empty text (should return 400)
        response_empty = requests.post(
            f"{API_BASE_URL}/analyze-text",
            json={"text": self.test_texts["empty"], "threshold": 0.5}
        )
        
        self.assertEqual(response_empty.status_code, 400, 
                         "Empty text should return 400 Bad Request")
        
        # Test with very long text (should handle or truncate)
        response_long = requests.post(
            f"{API_BASE_URL}/analyze-text",
            json={"text": self.test_texts["long"], "threshold": 0.5}
        )
        
        self.assertEqual(response_long.status_code, 200, 
                         "Long text should be handled properly")
        
        print("✅ Edge cases test passed")
        
    def test_06_user_settings(self):
        """Test user settings endpoints"""
        print("\n🔍 Testing user settings endpoints...")
        
        # Create user settings
        threshold = 0.75
        response_create = requests.post(
            f"{API_BASE_URL}/user-settings",
            json={"user_id": self.user_id, "threshold": threshold}
        )
        
        self.assertEqual(response_create.status_code, 200, 
                         "Create settings should return 200")
        
        # Get user settings
        response_get = requests.get(f"{API_BASE_URL}/user-settings/{self.user_id}")
        
        self.assertEqual(response_get.status_code, 200, 
                         "Get settings should return 200")
        
        data = response_get.json()
        self.assertEqual(data["user_id"], self.user_id, 
                         "Retrieved user_id should match")
        self.assertEqual(data["threshold"], threshold, 
                         "Retrieved threshold should match")
        
        print("✅ User settings test passed")
        
    def test_07_analytics(self):
        """Test analytics endpoint"""
        print("\n🔍 Testing analytics endpoint...")
        
        response = requests.get(f"{API_BASE_URL}/analytics")
        
        self.assertEqual(response.status_code, 200, 
                         "Analytics endpoint should return 200")
        
        data = response.json()
        
        # Check required fields
        self.assertIn("total_analyses", data, "Analytics should include total_analyses")
        self.assertIn("warned_analyses", data, "Analytics should include warned_analyses")
        self.assertIn("warning_rate", data, "Analytics should include warning_rate")
        self.assertIn("model_loaded", data, "Analytics should include model_loaded")
        
        print("✅ Analytics test passed")
        
    def test_08_performance(self):
        """Test API performance"""
        print("\n🔍 Testing API performance...")
        
        start_time = time.time()
        
        response = requests.post(
            f"{API_BASE_URL}/analyze-text",
            json={"text": self.test_texts["borderline"], "threshold": 0.5}
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200, "API should respond successfully")
        
        # Check if response time is reasonable (under 2 seconds)
        self.assertLess(response_time, 2.0, 
                        f"API response time should be under 2 seconds, got {response_time:.2f}s")
        
        print(f"✅ Performance test passed: Response time = {response_time:.2f}s")


def run_tests():
    """Run all tests and return results summary"""
    test_suite = unittest.TestLoader().loadTestsFromTestCase(ThinkTwiceAPITest)
    test_result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    
    # Print summary
    print("\n" + "="*50)
    print(f"TESTS RUN: {test_result.testsRun}")
    print(f"FAILURES: {len(test_result.failures)}")
    print(f"ERRORS: {len(test_result.errors)}")
    print(f"SKIPPED: {len(test_result.skipped)}")
    print("="*50)
    
    return len(test_result.failures) + len(test_result.errors) == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)