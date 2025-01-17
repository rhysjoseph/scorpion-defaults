import os

def ping(host):
  """
  Pings a host and returns True if the host is reachable, False otherwise.
  """
  print(host)
  response = os.system("ping -c 1 " + host)
  print(response)
  if response == 0:
    return True
  else:
    return False

# Get the IP address to ping from the user
ip_address = "10.244.169.64"

# Ping the IP address
if ping(ip_address):
  print(ip_address + " is reachable")
else:
  print(ip_address + " is unreachable")