import json
from kivy.network.urlrequest import UrlRequest
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp
from kivy.core.window import Window

from env import URL
from services.connection.main_conn.connection_loop import ConnectionLoop


class ConnectionManager:
    def __init__(self, base_url=URL):
        self.base_url = base_url
        self.server_list = []
        self.selected_server = None

        # Pasamos callback pero se rellenarán luego desde el menú
        self.connectionLoop = ConnectionLoop(
            get_url_callback=self._get_selected_server
        )

    def set_chat_manager(self, chat_manager):
        """Called by EmulatorScreen when initialized."""
        self.connectionLoop.set_chat_manager(chat_manager)

    def _get_selected_server(self):
        return self.selected_server

    def getServerListAndSelect(self, parent_screen):
        # 1. Primero verificamos la versión
        self._check_version(parent_screen)

    def _check_version(self, parent_screen):
        url = f"{self.base_url}/version"
        
        parent_screen.loading = True
        parent_screen.ids.label_servidor.text = "Verificando versión..."
        parent_screen.ids.loading_spinner.anim_delay = 0.05

        def _success(req, result):
            try:
                server_version = result.get("version", "0.0")
                from version import __version__ as client_version
                
                if server_version > client_version:
                     self._show_update_popup(f"Versión del servidor ({server_version}) es mayor a la tuya ({client_version}). Actualiza la app.")
                     parent_screen.loading = False
                     parent_screen.ids.loading_spinner.anim_delay = -1
                     return

                self._fetch_servers(parent_screen)

            except Exception as e:
                parent_screen.ids.label_servidor.text = f"Error version: {e}"
                parent_screen.loading = False
                parent_screen.ids.loading_spinner.anim_delay = -1

        def _error(req, error):
            self._fetch_servers(parent_screen)

        UrlRequest(
            url,
            on_success=_success,
            on_error=_error,
            req_headers={'Accept': 'application/json'},
            decode=True
        )

    def _fetch_servers(self, parent_screen):
        url = f"{self.base_url}/servers"
        parent_screen.ids.label_servidor.text = "Cargando servidores..."

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
            parent_screen.ids.label_servidor.text = "Error cargando servidores"

        UrlRequest(
            url,
            on_success=_success,
            on_error=_error,
            req_headers={'Accept': 'application/json'},
            decode=True
        )

    def _show_update_popup(self, msg):
        content = GridLayout(cols=1, padding=dp(20), spacing=dp(20))
        
        from kivy.uix.label import Label
        label = Label(text=msg, 
                      text_size=(Window.width * 0.7, None),
                      halign='center', 
                      valign='middle',
                      color=(1, 1, 1, 1)) # Explicit white text
        
        content.add_widget(label)
        
        # No dismiss button, forcing update (or restart)
        popup = Popup(title="Actualización Requerida",
                      content=content,
                      size_hint=(0.8, 0.4),
                      auto_dismiss=False)
        popup.open()

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
            btn.bind(on_release=lambda inst, s=servidor:
                     self._select_server(s, parent_screen, popup))
            contenido.add_widget(btn)

        scroll.add_widget(contenido)
        popup.open()

    def _select_server(self, servidor, parent_screen, popup):
        self.selected_server = servidor
        parent_screen.servidor_elegido = True
        parent_screen.ids.label_servidor.text = f"Servidor elegido:\n {servidor}"
        popup.dismiss()

        # Iniciar conexión automática
        self.connectionLoop.start()

