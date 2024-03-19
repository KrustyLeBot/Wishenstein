import game_pb2_grpc as pb2_grpc
import game_pb2 as pb2
import copy
from player import *


class GameServicer(pb2_grpc.gameServicer):

    def __init__(self, game):
        self.game = game
    
    def SendPosition(self, position, context):
        uuid = position.uuid
        if uuid not in self.game.distant_players:
            self.game.distant_players[uuid] = DistantPlayer(self.game, position.uuid, position.pos_x, position.pos_y, position.pos_angle, position.health)
        else:
            tmp = self.game.distant_players[uuid]
            tmp.x = position.pos_x
            tmp.y = position.pos_y
            tmp.angle = position.pos_angle
            tmp.health = position.health
            tmp.last_update = time.time()
            self.game.distant_players[uuid] = tmp

        distantPlayer_dict_copy = copy.copy(self.game.distant_players)
        #add local player to dict
        distantPlayer_dict_copy[self.game.player.uuid] = DistantPlayer(self.game, self.game.player.uuid, self.game.player.x, self.game.player.y, self.game.player.angle, self.game.player.health)
        for key, distantPlayer in distantPlayer_dict_copy.items():
            if key != uuid:
                result = { 'uuid': key, 'pos_x': distantPlayer.x, 'pos_y': distantPlayer.y, 'pos_angle': distantPlayer.angle, 'health': distantPlayer.health }
                yield pb2.PlayerPosition(**result)

    def GetSprites(self, empty, context):
        for sprite in self.game.object_handler.sprite_list:
            result = {
                'type': sprite.__class__.__name__,
                'uuid': sprite.uuid,
                'pos_x': sprite.x,
                'pos_y': sprite.y,
                'path': sprite.raw_path,
                'scale': sprite.SPRITE_SCALE,
                'shift': sprite.SPRITE_HEIGHT_SHIFT,
                'animation_time': sprite.animation_time
                }
            yield pb2.Sprite(**result)

    def GetNpcs(self, empty, context):
        for key, npc in self.game.object_handler.npc_list.items():
            result = {
                'type': npc.__class__.__name__,
                'uuid': npc.uuid,
                'pos_x': npc.x,
                'pos_y': npc.y,
                'path': npc.raw_path,
                'scale': npc.SPRITE_SCALE,
                'shift': npc.SPRITE_HEIGHT_SHIFT,
                'animation_time': npc.animation_time,
                'ray_cast_uuid': npc.ray_cast_uuid,
                'last_ray_cast_uuid': npc.last_ray_cast_uuid,
                'ray_cast_dist': npc.ray_cast_dist,
                'health': npc.health
                }
            yield pb2.NPC(**result)

    def ShootNpc(self, NpcShot, context):
        if NpcShot.uuid in self.game.object_handler.npc_list:
            npc = self.game.object_handler.npc_list[NpcShot.uuid]
            npc.health -= NpcShot.damage
        return pb2.Empty()
    
    def CheckNewGame(self, empty, context):
        return pb2.NewGame(game_uuid = self.game.game_uuid)