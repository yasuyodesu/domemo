let socket = null;
let myPlayerId = null;

function joinGame() {
    const name = document.getElementById("player-name").value || "名無し";
    let roomCode = document.getElementById("room-code-input").value.trim();
    const playerCount = document.getElementById("player-count").value;

    if (!roomCode) {
        roomCode = "NEW"; // 空欄なら新規作成
    }

    const wsProtocol = location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${wsProtocol}//${location.host}/ws/${roomCode}?名前=${encodeURIComponent(name)}&募集人数=${playerCount}`;

    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        console.log("WebSocket接続完了");
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log("受信データ:", data);

        if (data.イベント === "参加完了") {
            myPlayerId = data.プレイヤーID;
            document.getElementById("my-player-id").innerText = myPlayerId;
            document.getElementById("my-player-name").innerText = name;
            document.getElementById("display-room-code").innerText = data.部屋コード;

            document.getElementById("lobby-screen").classList.add("hidden");
            document.getElementById("waiting-screen").classList.remove("hidden");
        } else if (data.イベント === "待機中") {
            document.getElementById("current-members").innerText = data.現在の参加人数;
            document.getElementById("target-members").innerText = data.目標人数;
            const memberList = document.getElementById("member-list");
            memberList.innerHTML = data.プレイヤー名一覧.map(n => `<li>${n}</li>`).join("");
        } else if (data.イベント === "画面更新") {
            document.getElementById("waiting-screen").classList.add("hidden");
            document.getElementById("game-screen").classList.remove("hidden");
            updateGameScreen(data);
        } else if (data.イベント === "エラー") {
            alert(data.メッセージ);
        }
    };

    socket.onclose = () => {
        console.log("接続が切断されました");
    };
}

function updateGameScreen(data) {
    const game = data.ゲームデータ;
    const names = data.プレイヤー名一覧;

    // 手番表示
    const isMyTurn = game.現在のプレイヤーID === myPlayerId;
    const turnText = isMyTurn ? "★ あなたの手番です！ ★" : `プレイヤー ${game.現在のプレイヤーID} (${names[game.現在のプレイヤーID]}) の手番`;
    document.getElementById("turn-indicator").innerText = turnText;

    // ボタンの有効/無効
    const actionArea = document.getElementById("action-area");
    if (isMyTurn && !game.ゲーム終了) {
        actionArea.classList.remove("hidden");
    } else {
        actionArea.classList.add("hidden");
    }

    // 場札・捨て札
    document.getElementById("open-cards").innerHTML = game.公開カード.map(c => `<span class="tile-badge">${c}</span>`).join("") || "なし";
    document.getElementById("discarded-cards").innerHTML = game.場の捨て札.map(c => `<span class="tile-badge">${c}</span>`).join("") || "なし";

    // 手札状況
    const handsContainer = document.getElementById("hands-container");
    handsContainer.innerHTML = "";

    for (let id in game.全員の手札) {
        const pId = parseInt(id);
        const hand = game.全員の手札[pId];
        const isCurrent = pId === game.現在のプレイヤーID;
        const isMe = pId === myPlayerId;

        const handHtml = hand.map(c => {
            const isSecret = c === "?";
            return `<span class="tile-badge ${isSecret ? 'secret' : ''}">${c}</span>`;
        }).join("");

        const box = document.createElement("div");
        box.className = `player-hand-box ${isCurrent ? 'active-turn' : ''}`;
        box.innerHTML = `
            <strong>プレイヤー ${pId} (${names[pId]})${isMe ? ' [あなた]' : ''}</strong>
            <div>${handHtml}</div>
        `;
        handsContainer.appendChild(box);
    }

    // 勝利判定
    if (game.ゲーム終了) {
        alert(`🎉 プレイヤー ${game.勝者ID} (${names[game.勝者ID]}) の勝利です！`);
    }
}

function declareNumber(num) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            コマンド: "数字宣言",
            数字: num
        }));
    }
}