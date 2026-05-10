import os

bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"
workers = 1
worker_class = "gthread"
threads = 2
timeout = 300
keepalive = 75
# Restart the worker after this many requests to prevent memory leak accumulation
max_requests = 200
max_requests_jitter = 50
accesslog = "-"
errorlog = "-"
loglevel = "info"
