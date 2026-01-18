class RamHooks:
    def __init__(self, ramData, on_save=None):
        self.ramData = ramData
        self.on_save = on_save
        self._is_saving_frames = 0
        self._prev_is_saving = 0

    def handle_hooks(self):
        """
        Monitoriza la RAM en cada tick para disparar efectos secundarios automáticos.
        """
        # Auto-save detection robusto
        current_save_val = self.ramData.is_saving
        
        if current_save_val > 0:
            self._is_saving_frames += 1
        else:
            # Si volvemos a 0 tras haber detectado un "guardado largo" (> 60 ticks / 1 seg)
            if self._is_saving_frames > 60:
                print(f"[DEBUG] Guardado detectado ({self._is_saving_frames} frames). Lanzando backup...")
                if self.on_save:
                    self.on_save()
            self._is_saving_frames = 0
        
        self._prev_is_saving = current_save_val
