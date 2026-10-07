from client.network import NetworkClient


client = NetworkClient()

result = client.send_request("LIST_EVENTS")

print(result)