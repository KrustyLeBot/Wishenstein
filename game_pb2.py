# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: game.proto
# Protobuf Python Version: 4.25.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\ngame.proto\x12\x04game\"\x07\n\x05\x45mpty\"_\n\x0ePlayerPosition\x12\x0c\n\x04uuid\x18\x01 \x01(\t\x12\r\n\x05pos_x\x18\x02 \x01(\x02\x12\r\n\x05pos_y\x18\x03 \x01(\x02\x12\x11\n\tpos_angle\x18\x04 \x01(\x02\x12\x0e\n\x06health\x18\x05 \x01(\x05\"\x86\x01\n\x06Sprite\x12\x0c\n\x04type\x18\x01 \x01(\t\x12\x0c\n\x04uuid\x18\x02 \x01(\t\x12\r\n\x05pos_x\x18\x03 \x01(\x02\x12\r\n\x05pos_y\x18\x04 \x01(\x02\x12\x0c\n\x04path\x18\x05 \x01(\t\x12\r\n\x05scale\x18\x06 \x01(\x02\x12\r\n\x05shift\x18\x07 \x01(\x02\x12\x16\n\x0e\x61nimation_time\x18\x08 \x01(\x02\"\x83\x01\n\x03NPC\x12\x0c\n\x04type\x18\x01 \x01(\t\x12\x0c\n\x04uuid\x18\x02 \x01(\t\x12\r\n\x05pos_x\x18\x03 \x01(\x02\x12\r\n\x05pos_y\x18\x04 \x01(\x02\x12\x0c\n\x04path\x18\x05 \x01(\t\x12\r\n\x05scale\x18\x06 \x01(\x02\x12\r\n\x05shift\x18\x07 \x01(\x02\x12\x16\n\x0e\x61nimation_time\x18\x08 \x01(\x02\x32\x9a\x01\n\x04game\x12>\n\x0cSendPosition\x12\x14.game.PlayerPosition\x1a\x14.game.PlayerPosition\"\x00\x30\x01\x12+\n\nGetSprites\x12\x0b.game.Empty\x1a\x0c.game.Sprite\"\x00\x30\x01\x12%\n\x07GetNpcs\x12\x0b.game.Empty\x1a\t.game.NPC\"\x00\x30\x01\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'game_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_EMPTY']._serialized_start=20
  _globals['_EMPTY']._serialized_end=27
  _globals['_PLAYERPOSITION']._serialized_start=29
  _globals['_PLAYERPOSITION']._serialized_end=124
  _globals['_SPRITE']._serialized_start=127
  _globals['_SPRITE']._serialized_end=261
  _globals['_NPC']._serialized_start=264
  _globals['_NPC']._serialized_end=395
  _globals['_GAME']._serialized_start=398
  _globals['_GAME']._serialized_end=552
# @@protoc_insertion_point(module_scope)
