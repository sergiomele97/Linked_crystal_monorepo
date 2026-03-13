class RamHooks:
    def __init__(self, ramData, pyboy=None, on_save=None):
        self.ramData = ramData
        self.on_save = on_save
        self._prev_bank = 0
        self._prev_save_val = 0
        
        if pyboy:
            pyboy.hook_register(5, 0x4E2D, self._on_rom_save_hook, None)

    def _on_rom_save_hook(self, context):
        """Callback del hook de la ROM cuando se ejecuta la rutina de guardado"""
        if self.on_save:
            self.on_save()
