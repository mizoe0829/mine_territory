"""
ゲーム設定、カラーパレット、難易度プリセット
"""

# ウィンドウ設定
WINDOW_WIDTH = 1040
WINDOW_HEIGHT = 720
FPS = 60

# 盤面描画エリア
BOARD_SIZE = 640  # 盤面のピクセル幅・高さ
BOARD_X = 30
BOARD_Y = 40

# 難易度プリセット
# cpu_speed: 行動間隔（フレーム数、60FPSで40 = 約0.67秒ごと、25 = 約0.42秒ごと、15 = 約0.25秒ごと）
DIFFICULTY_PRESETS = {
    "easy": {
        "name": "Easy",
        "cols": 15,
        "rows": 15,
        "mine_ratio": 0.10,
        "cpu_speed": 80,
        "desc": "15x15 / 地雷 10% / CPU のんびり"
    },
    "normal": {
        "name": "Normal",
        "cols": 20,
        "rows": 20,
        "mine_ratio": 0.15,
        "cpu_speed": 40,
        "desc": "20x20 / 地雷 15% / CPU 普通"
    },
    "hard": {
        "name": "Hard",
        "cols": 25,
        "rows": 25,
        "mine_ratio": 0.20,
        "cpu_speed": 22,
        "desc": "25x25 / 地雷 20% / CPU 手強い"
    },
}

# スタンペナルティ秒数
STUN_PENALTY_SECONDS = 5.0

# カラーパレット（モダン・サイバー/ダークテーマ）
COLOR_BG = (15, 23, 42)          # #0f172a スレートダーク
COLOR_PANEL_BG = (30, 41, 59)    # #1e293b
COLOR_PANEL_BORDER = (51, 65, 85) # #334155
COLOR_TEXT = (241, 245, 249)     # #f1f5f9
COLOR_TEXT_MUTED = (148, 163, 184)

# プレイヤーカラー定義 (P1=青, CPU1=赤, CPU2=緑, CPU3=黄/オレンジ)
PLAYER_COLORS = {
    1: {
        "name": "Player (You)",
        "main": (14, 165, 233),       # #0ea5e9 シアン
        "bg": (14, 165, 233, 70),     # 薄い塗り
        "bright": (56, 189, 248),
        "dark": (3, 105, 161),
    },
    2: {
        "name": "CPU 1 (NE)",
        "main": (239, 68, 68),        # #ef4444 赤
        "bg": (239, 68, 68, 70),
        "bright": (248, 113, 113),
        "dark": (185, 28, 28),
    },
    3: {
        "name": "CPU 2 (SW)",
        "main": (16, 185, 129),       # #10b981 エメラルド
        "bg": (16, 185, 129, 70),
        "bright": (52, 211, 153),
        "dark": (4, 120, 87),
    },
    4: {
        "name": "CPU 3 (SE)",
        "main": (245, 158, 11),       # #f59e0b アンバー
        "bg": (245, 158, 11, 70),
        "bright": (251, 191, 36),
        "dark": (180, 83, 9),
    },
}

# セル関連カラー
COLOR_CELL_UNREVEALED = (45, 55, 72)        # 未開放マス
COLOR_CELL_BORDER = (30, 41, 59)            # マス枠線
COLOR_CELL_HOVER = (71, 85, 105)            # ホバー中
COLOR_CELL_VALID_TARGET = (56, 189, 248)    # プレイヤーが開けられるマスのハイライト
COLOR_MINE_BG = (127, 29, 29)               # 地雷マス背景
COLOR_MINE_ICON = (254, 202, 202)           # 地雷アイコン色

# 数字のカラー
NUMBER_COLORS = {
    0: (148, 163, 184),
    1: (96, 165, 250),   # 青
    2: (74, 222, 128),   # 緑
    3: (248, 113, 113),  # 赤
    4: (167, 139, 250),  # 紫
    5: (251, 146, 60),   # 橙
    6: (45, 212, 191),   # ターコイズ
    7: (232, 121, 249),  # マゼンタ
    8: (250, 204, 21),   # 黄
}
