import json
from kivy.network.urlrequest import UrlRequest
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp
from kivy.core.window import Window

from env import URL
from services.connection.connection_loop import ConnectionLoop


class ConnectionManager:
    def __init__(self, base_url=URL):
        self.base_url = base_url
        self.server_list = []
        self.selected_server = None

        self.connectionLoop = ConnectionLoop(
            get_url_callback=self._get_selected_server
        )

    def _get_selected_server(self):
        """
        Required by ConnectionLoop para obtener la URL elegida.
        """
        return self.selected_server

    def getServerListAndSelect(self, parent_screen):
        url = f"{self.base_url}/servers"

        # Mostrar spinner
        parent_screen.loading = True
        parent_screen.ids.label_servidor.text = "Cargando servidores..."
        parent_screen.ids.loading_spinner.anim_delay = 0.05

        def _success(req, result):
            try:
                if isinstance(result, str):
                    result = json.loads(result)
                self.server_list = result
            except Exception as e:
                parent_screen.ids.label_servidor.text = f"Error parseando JSON: {e}"
                parent_screen.loading = False
                parent_screen.ids.loading_spinner.anim_delay = -1
                return

            parent_screen.loading = False
            parent_screen.ids.loading_spinner.anim_delay = -1
            self._show_server_modal(parent_screen)

        def _error(req, error):
            parent_screen.loading = False
            parent_screen.ids.loading_spinner.anim_delay = -1

        UrlRequest(
            url,
            on_success=_success,
            on_error=_error,
            req_headers={'Accept': 'application/json'},
            decode=True 
        )

    def _show_server_modal(self, parent_screen):
        scroll = ScrollView(size_hint=(1, 1))
        contenido = GridLayout(cols=1, spacing=dp(10), padding=dp(10), size_hint_y=None)
        contenido.bind(minimum_height=contenido.setter('height'))

        popup = Popup(title="Selecciona un servidor",
                    content=scroll,
                    size_hint=(0.8, 0.6))

        window_height = Window.height
        button_height = max(dp(50), window_height * 0.08) 

        for servidor in self.server_list:
            btn = Button(
                text=str(servidor),
                size_hint_y=None,
                height=button_height
            )
            btn.bind(on_release=lambda inst, s=servidor: self._select_server(s, parent_screen, popup))
            contenido.add_widget(btn)

        scroll.add_widget(contenido)
        popup.open()
        self._popup = popup

    def _select_server(self, servidor, parent_screen, popup):
        self.selected_server = servidor
        parent_screen.servidor_elegido = True
        parent_screen.ids.label_servidor.text = f"Servidor elegido:\n {servidor}"
        parent_screen.connectionManager.selected_server = servidor
        popup.dismiss()

        # Iniciar conexión WebSocket
        self.connectionLoop.start()

    def get_online_data(self):
        pass
