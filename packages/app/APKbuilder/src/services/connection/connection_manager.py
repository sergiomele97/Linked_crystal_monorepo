from kivy.network.urlrequest import UrlRequest

class ConnectionManager:
    def __init__(self, base_url="https://linkedcrystal.com"):
        self.base_url = base_url
        self.server_list = []

    def getServerList(self, on_success=None, on_error=None):
        """
        Obtiene la lista de servidores de forma asíncrona usando UrlRequest.
        on_success y on_error son callbacks opcionales que recibe la pantalla.
        """
        url = f"{self.base_url}/servers"

        def _success(req, result):
            self.server_list = result
            if on_success:
                on_success(result)

        def _error(req, error):
            if on_error:
                on_error(error)

        UrlRequest(url, on_success=_success, on_error=_error)
        return self.server_list

    def get_online_data(self):
        pass
