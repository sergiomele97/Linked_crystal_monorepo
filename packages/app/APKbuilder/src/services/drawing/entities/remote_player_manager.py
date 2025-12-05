from services.drawing.entities.remote_player_entity import RemotePlayerEntity


class RemotePlayerManager:

    MISSING_TICKS_LIMIT = 100 

    def __init__(self, ramData, serverPackets, onScreenPlayers):
        self.ram = ramData
        self.serverPackets = serverPackets
        self.onScreenPlayers = onScreenPlayers

        self.players_missing_ticks = {}  # player_id → int

    def updateOnScreenPlayersFromNetwork(self):
        for pid in self.onScreenPlayers:
            self.players_missing_ticks[pid] = self.players_missing_ticks.get(pid, 0) + 1

        for packet in self.serverPackets:
            pid = packet.player_id
            
            self.players_missing_ticks[pid] = 0

            if (
                not packet.IsOverworld or
                packet.map_bank != self.ram.map_bank or
                packet.map_number != self.ram.map_number
            ):
                if pid in self.onScreenPlayers:
                    del self.onScreenPlayers[pid]
                    del self.players_missing_ticks[pid]
                continue

            # Agregar nuevos jugadores
            if pid not in self.onScreenPlayers:
                self.onScreenPlayers[pid] = RemotePlayerEntity(
                    player_id=pid,
                    initial_x=packet.player_x_coord,
                    initial_y=packet.player_y_coord
                )
            
            self.onScreenPlayers[pid].update_from_network(packet)

        # Eliminar jugadores que llevan demasiado tiempo sin paquete
        to_delete = [
            pid for pid, ticks in self.players_missing_ticks.items()
            if ticks > self.MISSING_TICKS_LIMIT
        ]
        for pid in to_delete:
            del self.onScreenPlayers[pid]
            del self.players_missing_ticks[pid]
