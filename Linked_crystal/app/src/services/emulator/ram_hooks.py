class RamHooks:
    def __init__(self, ramData, on_save=None):
        self.ramData = ramData
        self.on_save = on_save
        self._prev_bank = 0
        self._prev_save_val = 0

    def handle_hooks(self):
        """
        Monitoriza la RAM en cada tick para disparar efectos secundarios automáticos.
        """
        curr_bank = self.ramData.wram_bank
        curr_val = self.ramData.is_saving
        
        # TRANSICIÓN PROPUESTA: Banco 1 (255) -> Banco 6 (0)
        if (self._prev_bank == 1 and self._prev_save_val == 255) and \
           (curr_bank == 6 and curr_val == 0):
            
            # print(f"[DEBUG] ¡Transición de Guardado Detectada! (Bank 1:255 -> Bank 6:0). Lanzando backup...")
            if self.on_save:
                self.on_save()
        
        self._prev_bank = curr_bank
        self._prev_save_val = curr_val
