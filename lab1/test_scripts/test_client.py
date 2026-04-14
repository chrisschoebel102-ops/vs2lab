import clientserver

client = clientserver.Client()

client.get("herbert")
client.get("jurgen")

client.getall()

client.close()