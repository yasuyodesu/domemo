# server/main.py
import os
import sys
from urllib.parse import unquote

# プロジェクトルートのパスを通す
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from server.room_manager import 部屋管理者

app = FastAPI()

# 403回避のためのCORS設定を追加
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

マネージャー = 部屋管理者()

@app.get("/", response_class=HTMLResponse)
def ホーム画面(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

# パスパラメータを英字(room_code)にしてルーティングエラーを回避
@app.websocket("/ws/{room_code}")
async def websocket_endpoint(websocket: WebSocket, room_code: str):
    # ★重要: 処理の最優先でハンドシェイクを承認して403拒否を防ぐ
    await websocket.accept()

    # クエリパラメーターの取得とデコード
    query_params = websocket.query_params
    raw_name = query_params.get("名前", "名無し")
    名前 = unquote(raw_name)
    
    try:
        募集人数 = int(query_params.get("募集人数", 2))
    except (ValueError, TypeError):
        募集人数 = 2

    # 「NEW」の場合は新規に部屋を作成
    if room_code.upper() == "NEW":
        部屋 = マネージャー.部屋作成(募集人数)
    else:
        部屋 = マネージャー.部屋取得(room_code)

    if 部屋 is None:
        await websocket.send_json({"イベント": "エラー", "メッセージ": "指定された部屋が見つかりません。"})
        await websocket.close()
        return

    プレイヤー = 部屋.プレイヤー追加(名前, websocket)
    if プレイヤー is None:
        await websocket.send_json({"イベント": "エラー", "メッセージ": "部屋が満員か、既にゲームが始まっています。"})
        await websocket.close()
        return

    # 自分の情報（IDや部屋コード）を通知
    await websocket.send_json({
        "イベント": "参加完了",
        "プレイヤーID": プレイヤー.プレイヤーID,
        "部屋コード": 部屋.部屋コード,
        "目標人数": 部屋.目標人数,
        "現在の参加人数": len(部屋.参加プレイヤー)
    })

    # 部屋の全員に状態を配信する共通関数
    async def 全員に画面更新を通知():
        for p in 部屋.参加プレイヤー:
            try:
                if 部屋.ゲーム開始フラグ and 部屋.ゲーム:
                    表示データ = 部屋.ゲーム.プレイヤー用の表示データを取得(閲覧者のプレイヤーID=p.プレイヤーID)
                    データ = {
                        "イベント": "画面更新",
                        "ゲームデータ": 表示データ,
                        "プレイヤー名一覧": [x.名前 for x in 部屋.参加プレイヤー]
                    }
                else:
                    データ = {
                        "イベント": "待機中",
                        "現在の参加人数": len(部屋.参加プレイヤー),
                        "目標人数": 部屋.目標人数,
                        "プレイヤー名一覧": [x.名前 for x in 部屋.参加プレイヤー]
                    }
                await p.socket.send_json(データ)
            except Exception:
                pass

    await 全員に画面更新を通知()

    try:
        while True:
            受信データ = await websocket.receive_json()
            コマンド = 受信データ.get("コマンド")

            if コマンド == "数字宣言" and 部屋.ゲーム:
                宣言 = 受信データ.get("数字")
                try:
                    部屋.ゲーム.数字を宣言する(プレイヤー.プレイヤーID, 宣言)
                    await 全員に画面更新を通知()
                except ValueError as e:
                    await websocket.send_json({"イベント": "エラー", "メッセージ": str(e)})

    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    import uvicorn
    # Renderが指定するポート番号を取得（ローカルなら8000）
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server.main:app", host="0.0.0.0", port=port)