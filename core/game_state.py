# core/game_state.py
from typing import List, Dict, Optional, Any
from core.card import 山札管理

class ドメモ進行管理:
    """ドメモのゲーム進行・手番・当たり判定を管理するクラス"""

    def __init__(self, 参加人数: int, 連続手番を許可: bool = True):
        """
        Args:
            参加人数: 2〜5人
            連続手番を許可: 正解した時に連続で手番を行えるか（デフォルト: True）
        """
        self.参加人数 = 参加人数
        self.連続手番を許可 = 連続手番を許可
        
        # 山札管理を使って初期配布
        self.全員の手札, self.伏せカード, self.公開カード = 山札管理.ゲームの準備(参加人数)
        
        # 正解して場に出されたカード（オープンされた捨て札）
        self.場の捨て札: List[int] = []
        
        self.現在のプレイヤーID: int = 0
        self.ゲーム終了フラグ: bool = False
        self.勝者ID: Optional[int] = None
        self.宣言履歴: List[Dict[str, Any]] = []

    def 数字を宣言する(self, プレイヤーID: int, 宣言した数字: int) -> Dict[str, Any]:
        """
        手番のプレイヤーが「◯番！」と数字を宣言したときの処理
        """
        if self.ゲーム終了フラグ:
            raise ValueError("ゲームは既に終了しています。")
        if プレイヤーID != self.現在のプレイヤーID:
            raise ValueError(f"プレイヤー {プレイヤーID} の手番ではありません。")
        if not (1 <= 宣言した数字 <= 7):
            raise ValueError("宣言できる数字は 1 から 7 までです。")

        自分の手札 = self.全員の手札[プレイヤーID]
        当たりフラグ = 宣言した数字 in 自分の手札

        結果データ = {
            "プレイヤーID": プレイヤーID,
            "宣言した数字": 宣言した数字,
            "当たり": 当たりフラグ,
            "ゲーム終了": False,
            "勝者": None
        }

        if 当たりフラグ:
            # 当たった場合：自分の手札から1枚取り除き、捨て札へ移動
            自分の手札.remove(宣言した数字)
            self.場の捨て札.append(宣言した数字)
            self.場の捨て札.sort()

            # 勝利判定（手札がなくなったら上がり）
            if len(自分の手札) == 0:
                self.ゲーム終了フラグ = True
                self.勝者ID = プレイヤーID
                結果データ["ゲーム終了"] = True
                結果データ["勝者"] = プレイヤーID
            elif not self.連続手番を許可:
                # 連続手番ルールオフの場合は次のプレイヤーへ
                self._次の手番へ()
        else:
            # ハズレの場合：必ず次のプレイヤーへ
            self._次の手番へ()

        self.宣言履歴.append(結果データ)
        return 結果データ

    def _次の手番へ(self):
        """手番を次のプレイヤーに進める"""
        self.現在のプレイヤーID = (self.現在のプレイヤーID + 1) % self.参加人数

    def プレイヤー用の表示データを取得(self, 閲覧者のプレイヤーID: int) -> Dict[str, Any]:
        """
        特定プレイヤーの画面用データを生成。
        自分の手札のみ '?' に隠し、他人の手札や場札は見せる。
        """
        表示用の全員の手札 = {}
        for プレイヤーID, 手札 in self.全員の手札.items():
            if プレイヤーID == 閲覧者のプレイヤーID:
                # 自分の手札は枚数分だけ '?' で隠す
                表示用の全員の手札[プレイヤーID] = ["?"] * len(手札)
            else:
                # 相手の手札はそのまま見せる
                表示用の全員の手札[プレイヤーID] = 手札.copy()

        return {
            "参加人数": self.参加人数,
            "現在のプレイヤーID": self.現在のプレイヤーID,
            "全員の手札": 表示用の全員の手札,
            "公開カード": self.公開カード.copy(),
            "場の捨て札": self.場の捨て札.copy(),
            "ゲーム終了": self.ゲーム終了フラグ,
            "勝者ID": self.勝者ID,
            "直近の履歴": self.宣言履歴[-5:]
        }