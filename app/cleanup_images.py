import os
import datetime
import logging

# Configure logging
# Note: BasicConfig should ideally be called only once.
# If this script is imported, and the importer also configures logging,
# this might have no effect or conflict. For simplicity in this context,
# we'll leave it. A more robust solution might involve getting a logger instance
# and configuring it if not already configured.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_old_images(image_dir_path: str, days_threshold_value: int):
    """
    Deletes images older than days_threshold_value from the image_dir_path.

    Args:
        image_dir_path (str): The absolute path to the directory containing images.
        days_threshold_value (int): The age in days beyond which files should be deleted.
    
    Returns:
        tuple: (deleted_files_count, error_count)
    """
    logging.info(f"Starting image cleanup in directory: {image_dir_path}")
    logging.info(f"Files older than {days_threshold_value} days will be deleted.")

    if not os.path.isdir(image_dir_path):
        logging.error(f"Target directory {image_dir_path} does not exist or is not a directory.")
        return 0, 0 # Return zero counts if directory is invalid

    deleted_files_count = 0
    error_count = 0
    found_old_files = False # To track if we even encounter any old files

    now = datetime.datetime.now()

    for filename in os.listdir(image_dir_path):
        file_path = os.path.join(image_dir_path, filename)

        if os.path.isfile(file_path):
            try:
                # Get last modification timestamp
                mod_time_timestamp = os.path.getmtime(file_path)
                mod_time_datetime = datetime.datetime.fromtimestamp(mod_time_timestamp)

                # Calculate the age of the file
                file_age = now - mod_time_datetime

                if file_age.days > days_threshold_value:
                    found_old_files = True
                    logging.info(f"Deleting old file: {filename} (age: {file_age.days} days)")
                    os.remove(file_path)
                    deleted_files_count += 1
            except OSError as e:
                logging.error(f"Error deleting file {filename}: {e}")
                error_count += 1
            except Exception as e:
                logging.error(f"An unexpected error occurred with file {filename}: {e}")
                error_count += 1
        else:
            logging.debug(f"Skipping non-file item: {filename}")

    # Log summary
    if not found_old_files and deleted_files_count == 0 and error_count == 0:
        logging.info(f"No files older than {days_threshold_value} days found in {image_dir_path}.")
    
    logging.info(f"Cleanup summary for {image_dir_path}: {deleted_files_count} files deleted, {error_count} errors.")
    return deleted_files_count, error_count


if __name__ == "__main__":
    # Production configuration
    # The script is in app/, images are in static/images/
    # So, we need to go up one level, then into static/images/
    SCRIPT_DIR = os.path.dirname(__file__)
    DEFAULT_TARGET_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'static', 'images'))
    DEFAULT_DAYS_THRESHOLD = 14

    # Ensure the default target directory exists before running
    if not os.path.exists(DEFAULT_TARGET_DIR):
        os.makedirs(DEFAULT_TARGET_DIR)
        logging.info(f"Created directory: {DEFAULT_TARGET_DIR} for application use.")

    clean_old_images(DEFAULT_TARGET_DIR, DEFAULT_DAYS_THRESHOLD)
