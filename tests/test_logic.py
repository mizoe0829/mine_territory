import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pygame
pygame.init()

from board import Board
from player import HumanPlayer, CPUPlayer

# 1. ボード初期化テスト
b = Board(cols=15, rows=15, mine_ratio=0.15, only_adjacent_rule=True)
p1 = HumanPlayer(1)
cpus = {pid: CPUPlayer(pid, "normal", 25) for pid in (2, 3, 4)}

print(f"Board created: {b.cols}x{b.rows}, cell_size={b.cell_size}")
p1_openable = b.get_openable_cells(1)
print(f"P1 initially openable cells: {p1_openable}")
assert len(p1_openable) > 0, "P1 should have adjacent unrevealed cells"

# 2. 開放アクション & フラグテスト
tx, ty = p1_openable[0]
flag_ok = b.toggle_flag(tx, ty)
assert flag_ok, "Toggle flag should succeed"
assert b.get_cell(tx, ty).is_flagged, "Cell should be flagged"
# フラグマスは通常開けない
res_blocked = b.reveal_cell(1, tx, ty)
assert res_blocked["status"] == "invalid", "Flagged cell should not be revealable"
# フラグ解除
b.toggle_flag(tx, ty)
assert not b.get_cell(tx, ty).is_flagged, "Flag should be toggled off"

res = b.reveal_cell(1, tx, ty)
print(f"P1 opened ({tx}, {ty}) -> Result: {res['status']}")

# 2.5 コード開放テスト
# 開放済み数字マスに対してコード開放メソッドが呼べるかテスト
chord_res = b.chord_reveal(1, tx, ty)
print(f"Chord reveal test result: {chord_res}")

# 3. CPUの思考テスト (各難易度)
for diff in ("easy", "normal", "hard"):
    cpu = CPUPlayer(2, difficulty=diff, speed_frames=15)
    action = cpu.choose_action(b)
    print(f"CPU ({diff}) chosen action: {action}")
    assert action is not None

# 4. 全員で高速シミュレーション（100ターン回してみる）
step = 0
mines_hit = 0
while not b.is_game_finished() and step < 200:
    step += 1
    # P1
    p1_moves = b.get_openable_cells(1)
    if p1_moves and not p1.is_stunned:
        m = p1_moves[0]
        r = b.reveal_cell(1, m[0], m[1])
        if r["status"] == "mine":
            p1.trigger_stun()
            mines_hit += 1

    # CPUs
    for pid in (2, 3, 4):
        c = cpus[pid]
        act = c.choose_action(b)
        if act and not c.is_stunned:
            r = b.reveal_cell(pid, act[0], act[1])
            if r["status"] == "mine":
                c.trigger_stun()
                mines_hit += 1

    # Update stun
    p1.update(0.1)
    for c in cpus.values():
        c.update(0.1)

scores = b.get_scores()
print(f"Simulation ended after {step} steps. Total mines hit: {mines_hit}")
print(f"Final Scores: {scores}")
print("ALL LOGIC CHECKS PASSED!")
