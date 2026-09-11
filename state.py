import os
from dotenv import load_dotenv

load_dotenv()


print(f"Host IP: {os.environ.get('HOST_IP')}")
network_state = f"{os.environ.get('HOST_IP')}"

