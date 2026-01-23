import pickle
import os
from collections import deque

class EmailEnqueue:
    def __init__(self):
        self.queue_file = os.environ.get('EMAIL_QUEUE_PATH', 'email_queue.pkl')
        self.load_queue()
    
    def load_queue(self):
        if os.path.exists(self.queue_file):
            try:
                with open(self.queue_file, 'rb') as f:
                    EmailEnqueue._queue = pickle.load(f)
            except Exception as e:
                print(f"Failed to load queue: {e}")
                EmailEnqueue._queue = deque()
        else:
            EmailEnqueue._queue = deque()
            print(f"Queue file not found, starting empty: {self.queue_file}")
    
    def save_queue(self):
        try:
            with open(self.queue_file, 'wb') as f:
                pickle.dump(EmailEnqueue._queue, f)
        except Exception as e:
            print(f"Failed to save queue: {e}")
    
    def email_enqueue(self, email, password):  # NOW TAKES PASSWORD TOO!
        """Add email + password tuple to queue"""
        EmailEnqueue._queue.append((email, password))  # Store as tuple
        print(f"Added to queue: {EmailEnqueue._queue}")
        self.save_queue()
        
        # if EmailEnqueue._queue:
        #     peek_email, peek_password = EmailEnqueue._queue[0]
    
    def email_dequeue(self):
        """Remove and return front email + password"""
        if EmailEnqueue._queue:
            email_password = EmailEnqueue._queue.popleft()
            self.save_queue()
            return email_password  # Returns (email, password) tuple
        print("Queue is empty")
        return None
    
    def get_queue_size(self):
        size = len(EmailEnqueue._queue)
        print(f"Queue size: {size}")
        return size
