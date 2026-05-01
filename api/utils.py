import logging
import time
from pathlib import Path
from datetime import datetime, timedelta
import threading

# Configure logging — stdout only so logs appear in Render's log viewer
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


class JobCleanupService:
    """Service to cleanup old jobs and files"""

    def __init__(self, upload_folder, output_folder, retention_hours=24):
        self.upload_folder = Path(upload_folder)
        self.output_folder = Path(output_folder)
        self.retention_hours = retention_hours
        self.running = False
        self.thread = None

    def start(self):
        """Start the cleanup service"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.thread.start()
        logger.info("Cleanup service started")

    def stop(self):
        """Stop the cleanup service"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Cleanup service stopped")

    def _cleanup_loop(self):
        """Main cleanup loop"""
        while self.running:
            try:
                self.cleanup_old_files()
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

            # Run every hour
            time.sleep(3600)

    def cleanup_old_files(self):
        """Remove files older than retention period"""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        removed_count = 0

        # Cleanup upload folder
        for file_path in self.upload_folder.glob("*"):
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_time:
                    try:
                        file_path.unlink()
                        removed_count += 1
                        logger.info(f"Removed old upload file: {file_path.name}")
                    except Exception as e:
                        logger.error(f"Failed to remove {file_path}: {e}")

        # Cleanup output folder
        for file_path in self.output_folder.glob("*"):
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_time:
                    try:
                        file_path.unlink()
                        removed_count += 1
                        logger.info(f"Removed old output file: {file_path.name}")
                    except Exception as e:
                        logger.error(f"Failed to remove {file_path}: {e}")

        if removed_count > 0:
            logger.info(f"Cleanup completed: removed {removed_count} files")
