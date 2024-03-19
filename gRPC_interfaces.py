import grpc
import game_pb2_grpc as pb2_grpc
from concurrent import futures
from gRPC_game_servicer import *

# todo implem a text box to connect to server
HOST = 'localhost'
PORT = 4002

class gRPC_Client_Interface():
    def __init__(self, game):
        self.game = game
        self.channel = grpc.insecure_channel('{}:{}'.format(HOST, PORT), options=[(b'grpc.enable_http_proxy', 0)])
        try:
            grpc.channel_ready_future(self.channel).result(timeout=5)
            self.stub = pb2_grpc.gameStub(self.channel)
        except grpc.FutureTimeoutError:
            self.game.exit()
    
    def SendPosition(self, uuid, pos_x, pos_y, pos_angle, health):
        playerPosition = pb2.PlayerPosition(uuid = uuid, pos_x = pos_x, pos_y = pos_y, pos_angle = pos_angle, health = health)
        return self.stub.SendPosition(playerPosition)
    
    def GetSprites(self):
        empty = pb2.Empty()
        return self.stub.GetSprites(empty)
    
    def GetNpcs(self):
        empty = pb2.Empty()
        return self.stub.GetNpcs(empty)
    
    def ShootNpc(self, uuid, damage):
        npcShot = pb2.NpcShot(uuid = uuid, damage = damage)
        self.stub.ShootNpc(npcShot)

    def CheckNewGame(self):
        empty = pb2.Empty()
        return self.stub.CheckNewGame(empty)
    

class gRPC_Server_Interface():
    def __init__(self, game):
        self.game = game
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=64))
        pb2_grpc.add_gameServicer_to_server(GameServicer(game), self.server)
        self.server.add_insecure_port('{}:{}'.format(HOST, PORT))
        self.server.start()

    def update(self):
        # remove distant players not updated since 1 sec
        now = time.time()
        distantPlayer_dict_copy = copy.copy(self.game.distant_players)
        key_to_delete = []
        for key, distantPlayer in distantPlayer_dict_copy.items():
            if (now - distantPlayer.last_update) > 1:
                key_to_delete.append(key)

        for key in key_to_delete:
            self.game.distant_players.pop(key)