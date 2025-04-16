import unittest
from unittest.mock import patch
import time
from Segment import *

class TestClearQBeyondXSeconds(unittest.TestCase):
    def setUp(self):
        self.seg = lambda d: Segment(duration=d)

    @patch('time.time', return_value=210)
    def test_clear_beyond_enough(self, mock_time):
        tracker = SegmentsTracker([
            self.seg(10), self.seg(5), self.seg(3), self.seg(4), self.seg(5)
        ])
        current_playback = {"segment": tracker.segments[0], "start_time": 200}
        tracker.clearQBeyondXSeconds(10, current_playback)
        self.assertEqual(len(tracker.segments), 4)  # 10s passed - only 1s left from seg0

    @patch('time.time', return_value=205)
    def test_clear_nothing_needed(self, mock_time):
        tracker = SegmentsTracker([
            self.seg(10), self.seg(5), self.seg(3)
        ])
        current_playback = {"segment": tracker.segments[0], "start_time": 200}
        tracker.clearQBeyondXSeconds(4, current_playback)
        self.assertEqual(len(tracker.segments), 1)  # 5s played, 5s left

    @patch('time.time', return_value=215)
    def test_clear_all_but_one(self, mock_time):
        tracker = SegmentsTracker([
            self.seg(10), self.seg(5), self.seg(3)
        ])
        current_playback = {"segment": tracker.segments[0], "start_time": 200}
        tracker.clearQBeyondXSeconds(0, current_playback)
        self.assertEqual(len(tracker.segments), 1)  # Only current seg kept

    @patch('time.time', return_value=200)
    def test_clear_none_all_needed(self, mock_time):
        tracker = SegmentsTracker([
            self.seg(4), self.seg(3), self.seg(3)
        ])
        current_playback = {"segment": tracker.segments[0], "start_time": 200}
        tracker.clearQBeyondXSeconds(10, current_playback)
        self.assertEqual(len(tracker.segments), 3)  # All needed to reach 10s

    @patch('time.time', return_value=202)
    def test_segment_time_left_is_zero(self, mock_time):
        tracker = SegmentsTracker([
            self.seg(2), self.seg(5), self.seg(5)
        ])
        current_playback = {"segment": tracker.segments[0], "start_time": 200}
        tracker.clearQBeyondXSeconds(5, current_playback)
        self.assertEqual(len(tracker.segments), 2)  # s0 expired, need s1 only to hit 5s
    
    @patch('time.time', return_value=202)
    def test_blank_segments_to_clear(self, mock_time):
        tracker = SegmentsTracker([])
        current_playback = {"segment": None, "start_time": 200}
        tracker.clearQBeyondXSeconds(5, current_playback)
        self.assertEqual(len(tracker.segments), 0) 
    
    @patch('time.time', return_value=202)
    def test_current_playback_is_none(self, mock_time):
        tracker = SegmentsTracker([self.seg(4), self.seg(3)])
        current_playback = None
        tracker.clearQBeyondXSeconds(5, current_playback)
        self.assertEqual(len(tracker.segments), 2) 

if __name__ == '__main__':
    unittest.main()
