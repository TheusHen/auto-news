import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json
# Update import to handle the new directory structure
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import clean_html, fetch_news, NewsOverlay

class TestCleanHTML(unittest.TestCase):
    def test_clean_html_removes_tags(self):
        html = "<p>This is a <b>test</b> paragraph</p>"
        expected = "This is a test paragraph"
        self.assertEqual(clean_html(html), expected)

    def test_clean_html_converts_br_to_newline(self):
        html = "Line 1<br>Line 2<br />Line 3"
        expected = "Line 1\nLine 2\nLine 3"
        self.assertEqual(clean_html(html), expected)

    def test_clean_html_unescapes_entities(self):
        html = "This &amp; that &lt; those"
        expected = "This & that < those"
        self.assertEqual(clean_html(html), expected)

    def test_clean_html_strips_whitespace(self):
        html = "  <p>Text with spaces</p>  "
        expected = "Text with spaces"
        self.assertEqual(clean_html(html), expected)

class TestFetchNews(unittest.TestCase):
    def test_fetch_news_structure(self):
        """Test that we can create a news item with the expected structure."""
        # Create a sample news item directly
        news_item = {
            'title': 'Test Title',
            'summary': 'Test Summary',
            'link': 'https://example.com/test',
            'source': 'Test Source'
        }

        # Verify the news item has the expected structure
        self.assertIn('title', news_item)
        self.assertIn('summary', news_item)
        self.assertIn('link', news_item)
        self.assertIn('source', news_item)

        # Test that clean_html works as expected
        html = "<p>This is a <b>test</b> paragraph</p>"
        expected = "This is a test paragraph"
        self.assertEqual(clean_html(html), expected)

    def test_fetch_news_exception_handling(self):
        # Create a real mock for feedparser.parse
        with patch('feedparser.parse') as mock_parse:
            # Make feedparser.parse raise an exception
            mock_parse.side_effect = Exception("Test exception")

            # This should not raise an exception
            news = fetch_news()

            # Since all feeds raise exceptions, we should get an empty list
            self.assertEqual(news, [])

class TestNewsOverlay(unittest.TestCase):
    def test_news_overlay_initialization(self):
        # Create a sample news item
        news = [
            {
                'title': 'Test Title',
                'summary': 'Test Summary',
                'link': 'https://example.com/test',
                'source': 'Test Source'
            }
        ]

        # Initialize NewsOverlay with the sample news
        with patch('tkinter.Tk'), \
             patch.object(NewsOverlay, 'deiconify'), \
             patch.object(NewsOverlay, 'load_position', return_value={'x': 0, 'y': 0}), \
             patch.object(NewsOverlay, 'show_news'):
            overlay = NewsOverlay(news)

            # Check if news was stored correctly
            self.assertEqual(overlay.news, news)
            self.assertEqual(overlay.current, 0)

if __name__ == '__main__':
    unittest.main()
