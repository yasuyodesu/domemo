# server/room_manager.py
import uuid
from typing import Dict, List, Optional
from fastapi import WebSocket
from core.game_state import ドメモ進行管理

class プレイヤー情報:
    def __init__(self, プレイヤーID: int, 名前: str, socket: WebSocket):
        self.プレイヤーID = プレイヤーID
        self.名前 = 名前
        self.socket = socket

class 部屋:
    def __init__(self, 部屋コード: str, 目標人数: int):
        self.部屋コード = 部屋コード
        self.目標人数 = 目標人数
        self.参加プレイヤー: List[プレイヤー情報] = []
        self.ゲーム: Optional[ドメモ進行管理] = None
        self.ゲーム開始フラグ: bool = False

    def プレイヤー追加(self, 名前: str, socket: WebSocket) -> Optional[プレイヤー情報]:
        if len(self.参加プレイヤー) >= self.目標人数 or self.ゲーム開始フラグ:
            return None
        
        プレイヤーID = len(self.参加プレイヤー)
        新プレイヤー = プレイヤー情報(プレイヤーID, 名前, socket)
        self.参加プレイヤー.append(新プレイヤー)

        # 全員揃ったらゲーム開始
        if len(self.参加プレイヤー) == self.目標人数:
            self.ゲーム開始フラグ = True
            self.ゲーム = ドメモ進行管理(参加人数=self.目標人数)

        return 新プレイヤー

class 部屋管理者:
    def __init__(self):
        self.全部屋: Dict[str, 部屋] = {}

    def 部屋作成(self, 人数: int) -> 部屋:
        # 4桁のランダムな部屋コード（例: A1B2）
        部屋コード = "".join([random.randrange(10) for i in range(4)])
        新部屋 = 部屋(部屋コード, 人数)
        self.全部屋[部屋コード] = 新部屋
        return 新部屋

    def 部屋取得(self, 部屋コード: str) -> Optional[部屋]:
        return self.全部屋.get(部屋コード.upper())