import json
from kivy.network.urlrequest import UrlRequest
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

class ConnectionManager:
    def __init__(self, base_url="https://linkedcrystal.com"):
        self.base_url = base_url
        self.server_list = []
        self.selected_server = None

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
            parent_screen.ids.label_servidor.text = f"Error al cargar: {error}"
            parent_screen.ids.loading_spinner.anim_delay = -1

        UrlRequest(
            url,
            on_success=_success,
            on_error=_error,
            req_headers={'Accept': 'application/json'},
            decode=True  # importante para que result no sea bytes
        )

    def _show_server_modal(self, parent_screen):
        contenido = BoxLayout(orientation='vertical', spacing=10, padding=10)
        popup = Popup(title="Selecciona un servidor",
                      content=contenido,
                      size_hint=(0.8, 0.6))

        for servidor in self.server_list:
            btn = Button(text=str(servidor), size_hint_y=None, height=40)
            btn.bind(on_release=lambda inst, s=servidor: self._select_server(s, parent_screen, popup))
            contenido.add_widget(btn)

        popup.open()
        self._popup = popup

    def _select_server(self, servidor, parent_screen, popup):
        self.selected_server = servidor
        parent_screen.servidor_elegido = True
        parent_screen.ids.label_servidor.text = f"Servidor elegido:\n {servidor}"
        parent_screen.connectionManager.selected_server = servidor
        popup.dismiss()

    def get_online_data(self):
        pass
