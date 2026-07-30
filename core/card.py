import random
from typing import List, Dict, Tuple
from core.utils import カード枚数, 人数別設定

class 山札管理:
    @staticmethod
    def 山札作成() -> List[int]:
        山札 = []
        for 数字, 枚数 in カード枚数.items():
            山札.extend([数字] * 枚数)
        return 山札

    @classmethod
    def ゲームの準備(cls, 参加人数: int) -> Tuple[Dict[int, List[int]], List[int], List[int]]:
        if 参加人数 not in 人数別設定:
            raise ValueError(f"対応人数は2〜5人です。（指定された人数: {参加人数}人）")

        設定 = 人数別設定[参加人数]
        山札 = cls.山札作成()
        random.shuffle(山札)

        全員の手札 = {}
        for プレイヤー in range(参加人数):
            手札 = sorted([山札.pop() for _ in range(設定["手札の枚数"])])
            全員の手札[プレイヤー] = 手札

        伏せカード = [山札.pop() for _ in range(設定["伏せカードの枚数"])]
        公開カード = sorted([山札.pop() for _ in range(設定["公開カードの枚数"])])

        return 全員の手札, 伏せカード, 公開カード