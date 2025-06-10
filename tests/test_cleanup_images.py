import unittest
import os
import tempfile
import time
import shutil # For robust directory removal if tempfile has issues
from unittest.mock import patch, MagicMock

# Adjust the Python path to include the 'app' directory
# This allows us to import 'cleanup_images' from the 'app' directory
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.cleanup_images import clean_old_images, logging as cleanup_logging # Import the logger from the script

class TestCleanupImages(unittest.TestCase):

    def setUp(self):
        """
        Set up a temporary directory structure for testing.
        This will be like:
        /tmp/random_dir/
            static/
                images/
                    old_file.png
                    new_file.jpg
                    old_text_file.txt
        """
        self.base_temp_dir = tempfile.TemporaryDirectory()
        # Mimic the structure the script expects relative to a base path
        self.test_static_dir = os.path.join(self.base_temp_dir.name, 'static')
        self.test_image_dir = os.path.join(self.test_static_dir, 'images')
        os.makedirs(self.test_image_dir, exist_ok=True)

        self.days_threshold = 14

        # File paths
        self.old_file_path = os.path.join(self.test_image_dir, "old_image.png")
        self.new_file_path = os.path.join(self.test_image_dir, "new_image.jpg")
        self.old_text_file_path = os.path.join(self.test_image_dir, "old_text_file.txt") # Non-image file

        # Create an old file (older than threshold)
        with open(self.old_file_path, "w") as f:
            f.write("This is an old image.")
        old_file_mtime = time.time() - ( (self.days_threshold + 1) * 24 * 60 * 60) # 15 days ago
        os.utime(self.old_file_path, (old_file_mtime, old_file_mtime))

        # Create a new file (newer than threshold)
        with open(self.new_file_path, "w") as f:
            f.write("This is a new image.")
        new_file_mtime = time.time() - (1 * 24 * 60 * 60) # 1 day ago
        os.utime(self.new_file_path, (new_file_mtime, new_file_mtime))
        
        # Create an old non-image file
        with open(self.old_text_file_path, "w") as f:
            f.write("This is an old text file.")
        old_text_mtime = time.time() - ( (self.days_threshold + 2) * 24 * 60 * 60) # 16 days ago
        os.utime(self.old_text_file_path, (old_text_mtime, old_text_mtime))


    def tearDown(self):
        """
        Clean up the temporary directory.
        """
        self.base_temp_dir.cleanup()

    def test_delete_old_files(self):
        """Test that files older than the threshold are deleted."""
        # Initial check
        self.assertTrue(os.path.exists(self.old_file_path))
        self.assertTrue(os.path.exists(self.old_text_file_path))

        clean_old_images(self.test_image_dir, self.days_threshold)

        self.assertFalse(os.path.exists(self.old_file_path), "Old image file should be deleted.")
        self.assertFalse(os.path.exists(self.old_text_file_path), "Old text file should be deleted.")

    def test_keep_new_files(self):
        """Test that files newer than the threshold are NOT deleted."""
        self.assertTrue(os.path.exists(self.new_file_path))
        clean_old_images(self.test_image_dir, self.days_threshold)
        self.assertTrue(os.path.exists(self.new_file_path), "New image file should not be deleted.")

    def test_empty_directory(self):
        """Test the script with an empty directory."""
        # Create a new empty directory for this test
        with tempfile.TemporaryDirectory() as empty_base_dir:
            empty_image_dir = os.path.join(empty_base_dir, 'static', 'images')
            os.makedirs(empty_image_dir, exist_ok=True)
            
            deleted_count, error_count = clean_old_images(empty_image_dir, self.days_threshold)
            self.assertEqual(deleted_count, 0, "No files should be deleted from an empty directory.")
            self.assertEqual(error_count, 0, "No errors should occur in an empty directory.")
            self.assertEqual(len(os.listdir(empty_image_dir)), 0, "Directory should remain empty.")

    def test_non_existent_directory(self):
        """Test the script with a non-existent directory."""
        non_existent_dir = os.path.join(self.base_temp_dir.name, "non_existent_static", "images")
        # Ensure it doesn't exist
        if os.path.exists(non_existent_dir):
            shutil.rmtree(non_existent_dir)
            
        deleted_count, error_count = clean_old_images(non_existent_dir, self.days_threshold)
        self.assertEqual(deleted_count, 0)
        self.assertEqual(error_count, 0) # The function itself logs an error but returns 0,0

    @patch.object(cleanup_logging, 'info') # Patching the logger object used in cleanup_images.py
    @patch.object(cleanup_logging, 'error')
    def test_logging_messages(self, mock_log_error: MagicMock, mock_log_info: MagicMock):
        """Test that appropriate messages are logged."""
        # Test deletion logging
        clean_old_images(self.test_image_dir, self.days_threshold)
        
        # Check if specific log messages were called
        # Example: Check if deletion message for old_file_path was logged
        # The exact filename might be tricky due to path joining, so check for parts
        # This is a bit fragile if log messages change format significantly.
        
        # Check that "Deleting old file" was called for the two old files
        delete_log_calls = [call for call in mock_log_info.call_args_list if "Deleting old file" in call[0][0]]
        self.assertEqual(len(delete_log_calls), 2, "Should log deletion for two old files.")

        # Check for the summary log
        summary_log_calls = [call for call in mock_log_info.call_args_list if "Cleanup summary" in call[0][0]]
        self.assertTrue(any("2 files deleted" in call[0][0] for call in summary_log_calls), "Summary log should reflect 2 deleted files.")

        # Test logging for an empty directory
        mock_log_info.reset_mock() # Reset mock for the next call
        with tempfile.TemporaryDirectory() as empty_base_dir:
            empty_image_dir = os.path.join(empty_base_dir, 'static', 'images')
            os.makedirs(empty_image_dir, exist_ok=True)
            clean_old_images(empty_image_dir, self.days_threshold)
            
            no_old_files_log_calls = [call for call in mock_log_info.call_args_list if "No files older than" in call[0][0]]
            self.assertTrue(len(no_old_files_log_calls) >= 1, "Should log 'No files older than' for empty directory.")

        # Test logging for non-existent directory
        mock_log_error.reset_mock()
        non_existent_dir = os.path.join(self.base_temp_dir.name, "non_existent_for_log_test")
        clean_old_images(non_existent_dir, self.days_threshold)
        
        error_log_calls = [call for call in mock_log_error.call_args_list if "Target directory" in call[0][0] and "does not exist" in call[0][0]]
        self.assertTrue(len(error_log_calls) >= 1, "Should log error for non-existent directory.")


if __name__ == '__main__':
    unittest.main()
