import requests

class ConnectionManager:
    def __init__(self, base_url="https://linkedcrystal.com"):
        self.base_url = base_url
        self.server_list = []

    def getServerList(self):
        try:
            url = f"{self.base_url}/servers"
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            self.server_list = response.json()
            print(self.server_list)
            return self.server_list

        except Exception as e:
            print("Error obteniendo servers:", e)
            return []

    def get_online_data(self):
        pass