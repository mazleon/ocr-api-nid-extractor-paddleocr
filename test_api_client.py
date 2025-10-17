"""
Sample API client for testing the NID extraction endpoint.
"""
import sys
import time
from pathlib import Path
import requests
from typing import Optional


class NIDExtractionClient:
    """Client for interacting with the NID Extraction API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
    
    def health_check(self) -> dict:
        """
        Check if the API is healthy and running.
        
        Returns:
            Health check response
        """
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def extract_nid(
        self,
        front_image_path: str,
        back_image_path: str
    ) -> dict:
        """
        Extract NID information from images.
        
        Args:
            front_image_path: Path to NID front image
            back_image_path: Path to NID back image
            
        Returns:
            Extraction response with NID data
        """
        front_path = Path(front_image_path)
        back_path = Path(back_image_path)
        
        if not front_path.exists():
            raise FileNotFoundError(f"Front image not found: {front_image_path}")
        
        if not back_path.exists():
            raise FileNotFoundError(f"Back image not found: {back_image_path}")
        
        files = {
            'nid_front': ('nid_front.jpg', open(front_path, 'rb'), 'image/jpeg'),
            'nid_back': ('nid_back.jpg', open(back_path, 'rb'), 'image/jpeg')
        }
        
        print(f"Uploading NID images...")
        print(f"  Front: {front_path.name} ({front_path.stat().st_size} bytes)")
        print(f"  Back: {back_path.name} ({back_path.stat().st_size} bytes)")
        
        response = self.session.post(
            f"{self.base_url}/api/v1/nid/extract",
            files=files
        )
        
        # Close files
        for file_tuple in files.values():
            file_tuple[1].close()
        
        response.raise_for_status()
        return response.json()
    
    def get_metrics(self) -> dict:
        """
        Get API metrics.
        
        Returns:
            Metrics data
        """
        response = self.session.get(f"{self.base_url}/metrics")
        response.raise_for_status()
        return response.json()
    
    def clear_cache(self) -> dict:
        """
        Clear OCR cache.
        
        Returns:
            Cache clear response
        """
        response = self.session.post(f"{self.base_url}/api/v1/cache/clear")
        response.raise_for_status()
        return response.json()


def print_result(result: dict) -> None:
    """Pretty print extraction result."""
    print("\n" + "="*60)
    print("NID EXTRACTION RESULT")
    print("="*60)
    
    print(f"\nStatus: {result['status']}")
    print(f"Message: {result['message']}")
    print(f"Processing Time: {result['processing_time_ms']:.2f}ms")
    
    if result.get('data'):
        data = result['data']
        
        # Front side
        print("\n--- NID Front ---")
        front = data.get('nid_front', {})
        print(f"  Name: {front.get('name') or 'Not found'}")
        print(f"  Date of Birth: {front.get('date_of_birth') or 'Not found'}")
        print(f"  NID Number: {front.get('nid_number') or 'Not found'}")
        
        # Back side
        print("\n--- NID Back ---")
        back = data.get('nid_back', {})
        print(f"  Address: {back.get('address') or 'Not found'}")
    
    print("\n" + "="*60)


def main():
    """Main function to test the API."""
    
    # Check if image paths provided
    if len(sys.argv) < 3:
        print("Usage: python test_api_client.py <front_image_path> <back_image_path>")
        print("\nExample:")
        print("  python test_api_client.py tests/sample_images/nid_front.jpg tests/sample_images/nid_back.jpg")
        print("\nOr use test images:")
        print("  python test_api_client.py tests/sample_images/test_leon_front.jpeg tests/sample_images/test_leon_front.jpeg")
        sys.exit(1)
    
    front_image = sys.argv[1]
    back_image = sys.argv[2]
    
    # Initialize client
    client = NIDExtractionClient()
    
    try:
        # Health check
        print("Checking API health...")
        health = client.health_check()
        print(f"✓ API is {health['status']}")
        print(f"  Version: {health['version']}")
        print(f"  Environment: {health['environment']}")
        
        # Extract NID information
        print("\nExtracting NID information...")
        start_time = time.time()
        result = client.extract_nid(front_image, back_image)
        elapsed_time = (time.time() - start_time) * 1000
        
        # Print result
        print_result(result)
        print(f"\nTotal Request Time: {elapsed_time:.2f}ms")
        
        # Get metrics
        print("\nFetching API metrics...")
        metrics = client.get_metrics()
        perf = metrics.get('performance', {})
        cache = metrics.get('cache', {})
        
        print(f"\nAPI Metrics:")
        print(f"  Total Requests: {perf.get('total_requests', 0)}")
        print(f"  Successful: {perf.get('successful_requests', 0)}")
        print(f"  Failed: {perf.get('failed_requests', 0)}")
        print(f"  Avg Processing Time: {perf.get('average_processing_time_ms', 0)}ms")
        print(f"\nCache Statistics:")
        print(f"  Enabled: {cache.get('cache_enabled', False)}")
        print(f"  Size: {cache.get('cache_size', 0)}/{cache.get('cache_max_size', 0)}")
        
        print("\n✓ Test completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("✗ Error: Cannot connect to API. Is the server running?")
        print("  Start the server with: python main.py")
        sys.exit(1)
        
    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP Error: {e}")
        if e.response is not None:
            try:
                error_data = e.response.json()
                print(f"\nError Details:")
                print(f"  Status: {error_data.get('status')}")
                print(f"  Message: {error_data.get('message')}")
                if error_data.get('errors'):
                    print(f"  Errors:")
                    for err in error_data['errors']:
                        print(f"    - {err.get('message')}")
            except:
                print(f"  Response: {e.response.text}")
        sys.exit(1)
        
    except FileNotFoundError as e:
        print(f"✗ File Error: {e}")
        sys.exit(1)
        
    except Exception as e:
        print(f"✗ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
