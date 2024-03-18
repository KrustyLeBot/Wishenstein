import game_pb2_grpc as pb2_grpc
import game_pb2 as pb2
import copy
from player import *


class GameServicer(pb2_grpc.gameServicer):

    def __init__(self, game):
        self.game = game
    
    def SendPosition(self, position, context):
        return position
        uuid = position.uuid
        self.game.distant_players[uuid] = DistantPlayer(self.game, position.uuid, position.pos_x, position.pos_y, position.pos_angle)

        distantPlayer_dict_copy = copy.copy(self.game.distant_players)
        #add local player to dict
        distantPlayer_dict_copy[self.game.player.uuid] = DistantPlayer(self.game, self.game.player.uuid, self.game.player.x, self.game.player.y, self.game.player.angle)
        print
        for key, distantPlayer in distantPlayer_dict_copy.items():
            if key != uuid:
                print('yield')
                result = { 'uuid': key, 'pos_x': distantPlayer.pos_x, 'pos_y': distantPlayer.pos_y, 'pos_angle': distantPlayer.pos_angle }
                yield pb2.PlayerPosition(**result)