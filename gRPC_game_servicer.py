import game_pb2_grpc as pb2_grpc
import game_pb2 as pb2
import copy
import json
import win_precise_time as wpt
from player import *


class GameServicer(pb2_grpc.gameServicer):
    def __init__(self, game):
        self.game = game
    
    def SendPosition(self, position, context):
        uuid = position.uuid

        if uuid not in self.game.distant_players:
            self.game.distant_players[uuid] = DistantPlayer(self.game, position.uuid, position.pos_x, position.pos_y, position.pos_angle, position.health, position.last_move)
        else:
            tmp = self.game.distant_players[uuid]
            tmp.x = position.pos_x
            tmp.y = position.pos_y
            tmp.angle = position.pos_angle
            
            # if player was revived, keep server health and reset revive flag
            if position.health < 1 and tmp.revived == True:
                pass
            else:
                tmp.health = position.health
                tmp.revived = False

            tmp.last_update = wpt.time()
            tmp.last_move = position.last_move
            self.game.distant_players[uuid] = tmp

        distantPlayer_dict_copy = copy.copy(self.game.distant_players)
        #add local player to dict
        distantPlayer_dict_copy[self.game.player.uuid] = DistantPlayer(self.game, self.game.player.uuid, self.game.player.x, self.game.player.y, self.game.player.angle, self.game.player.health, self.game.player.last_move)
        for key, distantPlayer in distantPlayer_dict_copy.items():
            if key != uuid or distantPlayer.revived:
                result = { 'uuid': key, 'pos_x': distantPlayer.x, 'pos_y': distantPlayer.y, 'pos_angle': distantPlayer.angle, 'health': distantPlayer.health, 'last_move': distantPlayer.last_move }
                yield pb2.PlayerPosition(**result)

    def GetSprites(self, empty, context):
        for key, sprite in self.game.object_handler.sprite_list.items():
            result = {
                'type': sprite.__class__.__name__,
                'uuid': sprite.uuid,
                'pos_x': sprite.x,
                'pos_y': sprite.y,
                'path': sprite.raw_path,
                'scale': sprite.SPRITE_SCALE,
                'shift': sprite.SPRITE_HEIGHT_SHIFT,
                'animation_time': sprite.animation_time,
                'state': sprite.state if sprite.__class__.__name__ == StateSprite.__name__ else 0,
                'hold': sprite.hold if sprite.__class__.__name__ == StateSprite.__name__ else False,
                'last_press_uuid': sprite.last_press_uuid if sprite.__class__.__name__ == StateSprite.__name__ else ''
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
    
    def ToggleSprite(self, toggled, context):
        if toggled.uuid in self.game.object_handler.sprite_list:
            sprite = self.game.object_handler.sprite_list[toggled.uuid]

            if toggled.presser_uuid != '':
                if toggled.state == sprite.on_state:
                    sprite.press(appy_state = True, presser_uuid = toggled.presser_uuid)
                else:
                    sprite.release(appy_state = True, presser_uuid = toggled.presser_uuid)
            else:
                sprite.toggle(toggled.state, appy_state = True)
        return pb2.Empty()
    
    def GetMap(self, empty, context):
        return pb2.Map(map = json.dumps(self.game.map.mini_map))
    
    def Revive(self, revive, context):
        if revive.uuid in self.game.distant_players:
            self.game.distant_players[revive.uuid].revive()
        elif revive.uuid == self.game.player.uuid:
            self.game.player.revive()
        return pb2.Empty()