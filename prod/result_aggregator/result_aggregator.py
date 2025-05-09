import time
import logging
import signal
import threading
import json
import os
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from prod.config import (
    REDIS_HOST,
    REDIS_PORT, 
    REDIS_DB,
    REDIS_PASSWORD,
    RECOGNITION_QUEUE,
    RESULTS_STORE,
    DATABASE_URL
)
from prod.utils import (
    get_redis_connection,
    decode_recognition_result
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('result_aggregator')

class ResultAggregator:
    """Aggregates face recognition results and stores them."""
    
    def __init__(self, workers: int = 1, result_ttl: int = 3600):
        """
        Initialize the result aggregator.
        
        Args:
            workers: Number of worker threads to process results
            result_ttl: Time-to-live for results in seconds
        """
        self.workers = workers
        self.result_ttl = result_ttl
        self.redis_client = get_redis_connection()
        self.stop_event = threading.Event()
        self.worker_threads = []
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"Result aggregator initialized with workers: {workers}, result TTL: {result_ttl}s")
    
    def _signal_handler(self, sig, frame):
        """Handle termination signals gracefully."""
        logger.info(f"Received signal {sig}, shutting down...")
        self.stop_event.set()
    
    def start(self):
        """Start the result aggregator workers."""
        # Start worker threads
        for i in range(self.workers):
            thread = threading.Thread(
                target=self._process_results,
                args=(i,),
                daemon=True
            )
            self.worker_threads.append(thread)
            thread.start()
            logger.info(f"Started worker thread {i}")
        
        # Start periodic cleanup thread
        cleanup_thread = threading.Thread(
            target=self._periodic_cleanup,
            daemon=True
        )
        self.worker_threads.append(cleanup_thread)
        cleanup_thread.start()
        logger.info("Started cleanup thread")
        
        # Keep the main thread alive
        try:
            while not self.stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down...")
        finally:
            self._cleanup()
    
    def _process_results(self, worker_id: int):
        """
        Process recognition results from the queue.
        
        Args:
            worker_id: Identifier for this worker thread
        """
        logger.info(f"Worker {worker_id} starting to process results")
        
        while not self.stop_event.is_set():
            try:
                # BLPOP waits for items in the queue with a timeout
                queue_item = self.redis_client.blpop(RECOGNITION_QUEUE, timeout=1)
                
                if not queue_item:
                    continue
                
                # Extract the result data (queue name and data)
                _, result_data = queue_item
                
                # Decode the result data
                result = json.loads(result_data.decode('utf-8'))
                
                # Store result in Redis
                self._store_result(result)
                
                # Store result in database
                self._store_in_database(result)
                
                logger.debug(f"Worker {worker_id} processed result for {result.get('stream_id')}")
                
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {str(e)}")
                time.sleep(1)
        
        logger.info(f"Worker {worker_id} stopping")
    
    def _store_result(self, result: Dict[str, Any]):
        """
        Store result in Redis.
        
        Args:
            result: Recognition result data
        """
        try:
            # Generate a unique key for this detection
            stream_id = result.get('stream_id')
            timestamp = result.get('timestamp')
            bbox = result.get('bbox')
            
            # Create a key in format stream_id:timestamp:bbox
            bbox_str = '_'.join(map(str, bbox))
            result_key = f"{stream_id}:{timestamp}:{bbox_str}"
            
            # Store as hash with TTL
            self.redis_client.hset(RESULTS_STORE, result_key, json.dumps(result))
            self.redis_client.expire(RESULTS_STORE, self.result_ttl)
            
        except Exception as e:
            logger.error(f"Error storing result: {str(e)}")
    
    def _store_in_database(self, result: Dict[str, Any]):
        """
        Store result in database for persistent storage.
        
        Args:
            result: Recognition result data
        """
        # This would use Prisma to store in PostgreSQL - for now, just log
        try:
            # In a real implementation, this would connect to PostgreSQL and insert the data
            # For the purposes of this demo, we just log the data
            logger.debug(f"Would store in database: {result}")
            
            # TODO: Add actual database storage logic with Prisma
            # from prisma import Prisma
            # db = Prisma()
            # await db.connect()
            # await db.detection.create(...)
            
        except Exception as e:
            logger.error(f"Error storing in database: {str(e)}")
    
    def _periodic_cleanup(self):
        """Periodically clean up old results."""
        while not self.stop_event.is_set():
            try:
                # Sleep for a while
                time.sleep(self.result_ttl / 2)
                
                # Remove old keys
                # This is handled by Redis TTL, but we could implement additional cleanup here
                logger.debug("Performing periodic cleanup")
                
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {str(e)}")
    
    def _cleanup(self):
        """Clean up resources before shutdown."""
        logger.info("Cleaning up resources...")
        self.stop_event.set()
        
        # Wait for all threads to finish
        for i, thread in enumerate(self.worker_threads):
            thread.join(timeout=2)
            logger.info(f"Thread {i} joined")
        
        logger.info("Result aggregator shutdown complete")


def main():
    """Main entry point for the result aggregator service."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Result Aggregator Service')
    parser.add_argument('--workers', type=int, default=1, help='Number of worker threads')
    parser.add_argument('--ttl', type=int, default=3600, help='Time-to-live for results in seconds')
    
    args = parser.parse_args()
    
    aggregator = ResultAggregator(workers=args.workers, result_ttl=args.ttl)
    aggregator.start()


if __name__ == "__main__":
    main() 