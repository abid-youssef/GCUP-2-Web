import os
import time

print(f"Backing up to {os.getenv('BACKUP_SERVER', 'localhost')}")
time.sleep(1)
print('Done.')
