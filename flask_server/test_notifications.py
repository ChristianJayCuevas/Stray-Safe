#!/usr/bin/env python3
# Test script to verify notifications are working properly

import requests
import time
import json
import os
import sys
import random

# Set the base URL for the API - change if needed
API_BASE = "http://localhost:5000/api2"

def test_notifications():
    """Test the notifications system to ensure it's recording and updating properly"""
    print("Testing notifications system...")
    
    # First check if API is running
    try:
        response = requests.get(f"{API_BASE}/streams", timeout=3)
        if response.status_code != 200:
            print(f"Error: API returned status code {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"Error: Could not connect to API at {API_BASE}: {e}")
        print("Make sure the Flask server is running")
        return False
    
    # Get current notification stats before creating new test notification
    try:
        before_stats = requests.get(f"{API_BASE}/notifications/stats").json()
        before_count = before_stats["total"]
        print(f"Current notification count: {before_count}")
    except Exception as e:
        print(f"Error getting notification stats: {e}")
        return False
    
    # Get available streams to use a valid stream_id
    try:
        streams = requests.get(f"{API_BASE}/streams").json()["streams"]
        if not streams:
            print("No active streams found. Using 'test-stream' as fallback.")
            stream_id = "test-stream"
        else:
            stream_id = streams[0]["id"]
            print(f"Using stream: {stream_id}")
    except Exception as e:
        print(f"Error getting streams: {e}")
        stream_id = "test-stream"
    
    notifications = []
    # Create multiple test notifications to ensure they're unique
    for i in range(3):
        animal_id = f"test{i+1}"
        notification_type = "owner" if i % 2 == 0 else "pound"
        animal_type = "dog" if i % 2 == 0 else "cat"

        # Create a test notification
        try:
            test_response = requests.get(
                f"{API_BASE}/test-notification?stream_id={stream_id}&animal_type={animal_type}&animal_id={animal_id}&notify_type={notification_type}"
            )
            
            if test_response.status_code == 200:
                print(f"Created test {notification_type} notification for {stream_id}/{animal_type}{animal_id}")
                test_data = test_response.json()
                notification_id = test_data.get('notification', {}).get('id')
                notifications.append({
                    'id': notification_id,
                    'animal_id': animal_id,
                    'animal_type': animal_type,
                    'type': notification_type
                })
                print(f"Test notification ID: {notification_id}")
            else:
                print(f"Test notification endpoint failed with status code {test_response.status_code}")
        except Exception as e:
            print(f"Error with test notification: {e}")
            
        # Add slight delay to ensure timestamps are different
        time.sleep(1)
    
    # Wait a bit for processing
    print("Waiting for stats to update...")
    time.sleep(2)
    
    # Check notification stats again to see if they've updated
    try:
        after_stats = requests.get(f"{API_BASE}/notifications/stats").json()
        after_count = after_stats["total"]
        print(f"Updated notification count: {after_count}")
        print(f"New notifications created: {after_count - before_count}")
        print(f"Stream stats: {json.dumps(after_stats.get('by_stream', {}), indent=2)}")
        print(f"Animal type stats: {json.dumps(after_stats.get('by_animal_type', {}), indent=2)}")
        
        # Check if we have stream_id in any notification
        all_notifications = requests.get(f"{API_BASE}/notifications?limit=10").json()["notifications"]
        if all_notifications:
            print("\nLatest notifications:")
            for i, notification in enumerate(all_notifications[:5]):  # Show first 5
                # Check if stream_id is present directly
                direct_stream = notification.get("stream_id")
                # Also check in animal_info
                info_stream = notification.get("animal_info", {}).get("stream_id")
                stream = direct_stream or info_stream or "unknown"
                animal_info = notification.get("animal_info", {})
                print(f"  {i+1}. ID: {notification.get('id')}")
                print(f"     Type: {notification.get('type')}")
                print(f"     Stream: {stream}")
                print(f"     Animal: {animal_info.get('animal_type')} {animal_info.get('animal_id')}")
                print(f"     Timestamp: {notification.get('timestamp')}")
        else:
            print("No notifications found!")
            
        # Test if we can filter by stream_id
        if stream_id != "test-stream":
            stream_notifications = requests.get(f"{API_BASE}/notifications?stream_id={stream_id}").json()
            print(f"\nFound {stream_notifications.get('count', 0)} notifications for stream {stream_id}")
        
        # Test the new by-animal endpoint
        if notifications:
            test_notification = random.choice(notifications)
            animal_id = test_notification['animal_id']
            animal_type = test_notification['animal_type']
            print(f"\nTesting notifications/by-animal endpoint for {animal_type}{animal_id}")
            try:
                animal_response = requests.get(
                    f"{API_BASE}/notifications/by-animal?stream_id={stream_id}&animal_type={animal_type}&animal_id={animal_id}"
                )
                if animal_response.status_code == 200:
                    animal_data = animal_response.json()
                    print(f"Found {animal_data.get('count', 0)} notifications for {animal_type}{animal_id}")
                    if animal_data.get('count', 0) > 0:
                        print("Verification successful - can retrieve notifications by animal ID")
                else:
                    print(f"by-animal endpoint failed with status code {animal_response.status_code}")
            except Exception as e:
                print(f"Error testing by-animal endpoint: {e}")
        
        # Verify each notification created is unique and has a distinct timestamp
        notification_ids = set()
        notification_timestamps = set()
        for notification in all_notifications:
            notification_ids.add(notification.get('id'))
            notification_timestamps.add(notification.get('timestamp'))
        
        print(f"\nVerification results:")
        print(f"Unique notification IDs: {len(notification_ids)} (Expected: {len(all_notifications)})")
        print(f"Unique timestamps: {len(notification_timestamps)} (Expected: {len(all_notifications)})")
        
        if len(notification_ids) == len(all_notifications) and len(notification_timestamps) == len(all_notifications):
            print("✅ All notifications have unique IDs and timestamps")
        else:
            print("❌ Some notifications have duplicate IDs or timestamps")
        
        return after_count > before_count and len(notification_ids) == len(all_notifications)
    except Exception as e:
        print(f"Error checking notification updates: {e}")
        return False

if __name__ == "__main__":
    print("Notification Test Utility")
    print("========================")
    result = test_notifications()
    print("\nTest result:", "PASSED" if result else "FAILED")
    sys.exit(0 if result else 1) 