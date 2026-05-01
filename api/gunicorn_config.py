import os

bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"
workers = 1
worker_class = "gthread"
threads = 4
timeout = 300
keepalive = 75
accesslog = "-"
errorlog = "-"
loglevel = "info"
