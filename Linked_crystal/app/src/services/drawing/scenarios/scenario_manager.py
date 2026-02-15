from services.drawing.scenarios.tiles import FULL_SCREEN_CASES, Tiles   

class ScenarioManager:
    def __init__(self, ramData):
        self.ramData = ramData
        self.current_scenario = None
        
        self.scenarios = {
                "overworld": (0, 0, 160, 144),
                "textbox": (0, 0, 160, 96),
                "menu": (0, 0, 80, 104),
                "full_screen_menu": (0, 0, 0, 0)
        }


    def updateScenario(self):
        if self.isFullScreenMenu():
            self.current_scenario = "full_screen_menu"
        elif self.isMenu():
            self.current_scenario = "menu"
        elif self.isTextbox():
            self.current_scenario = "textbox"
        elif self.isOverworld():
            self.current_scenario = "overworld"
    
    def isFullScreenMenu(self):
        if self.ramData.tiles["sup_left"] in FULL_SCREEN_CASES:
            return True
        elif self.ramData.tiles["sup_center"] == Tiles.SAVING_MENU_SUP_CENTER:
            return True
        return False
    
    def isMenu(self):
        if self.ramData.tiles["sup_center"] == Tiles.MENU_SUP_CENTER:
            return True
        return False
    
    def isTextbox(self):
        if self.ramData.tiles["inf_right"] == Tiles.TEXTBOX_INF_RIGHT:
            return True
        return False
    
    def isOverworld(self):
        return True
        
    
