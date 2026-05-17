import json
import os
import copy
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[0]
OUT_DIR = REPO_ROOT / "import_json_tests_duo"
OUT_DIR.mkdir(exist_ok=True)

with open(REPO_ROOT / "fixtures" / "states" / "duo_initial_state.json", "r") as f:
    base_state = json.load(f)

# 1. 01_piece_in_rack_and_board.json
# piece 'I1' on board but also in rack.
c1 = copy.deepcopy(base_state)
# Put 'I1' for blue on board
c1["board"][4] = c1["board"][4][:4] + "B" + c1["board"][4][5:]
c1["history"].append({
    "player": "blue", "piece": "I1", "x": 4, "y": 4, "rotation": 0, "flipped": False
})
c1["current_player"] = "red"
# 'I1' is still in remaining_pieces for blue
with open(OUT_DIR / "01_piece_in_rack_and_board.json", "w") as f:
    json.dump(c1, f, indent=2)

# 2. 02_invalid_remaining_squares_sum.json
# Remove a piece but don't add to board.
c2 = copy.deepcopy(base_state)
c2["remaining_pieces"]["blue"].remove("F5")
with open(OUT_DIR / "02_invalid_remaining_squares_sum.json", "w") as f:
    json.dump(c2, f, indent=2)

# 3. 03_illegal_piece_placement.json
c3 = copy.deepcopy(base_state)
c3["remaining_pieces"]["blue"].remove("I2")
# Place I2 at 4,4
c3["board"][4] = c3["board"][4][:4] + "BB" + c3["board"][4][6:]
c3["history"].append({
    "player": "blue", "piece": "I2", "x": 4, "y": 4, "rotation": 1, "flipped": False
})
# Now place another blue piece sharing an edge, say I1 at 3,4
c3["remaining_pieces"]["blue"].remove("I1")
c3["board"][3] = c3["board"][3][:4] + "B" + c3["board"][3][5:]
c3["history"].append({
    "player": "blue", "piece": "I1", "x": 4, "y": 3, "rotation": 0, "flipped": False
})
with open(OUT_DIR / "03_illegal_piece_placement.json", "w") as f:
    json.dump(c3, f, indent=2)

# 4. 04_wrong_current_player.json
c4 = copy.deepcopy(base_state)
c4["remaining_pieces"]["blue"].remove("I1")
c4["board"][4] = c4["board"][4][:4] + "B" + c4["board"][4][5:]
c4["history"].append({
    "player": "blue", "piece": "I1", "x": 4, "y": 4, "rotation": 0, "flipped": False
})
# Forgot to advance current player
c4["current_player"] = "blue"
with open(OUT_DIR / "04_wrong_current_player.json", "w") as f:
    json.dump(c4, f, indent=2)

# 5. 05_incorrect_player_scores.json (Mapped to finished flag mismatch since scores are dynamic)
c5 = copy.deepcopy(base_state)
c5["finished"] = True # Will cause Finished flag mismatch
with open(OUT_DIR / "05_incorrect_player_scores.json", "w") as f:
    json.dump(c5, f, indent=2)

# 6. 06_misconfigured_board.json
c6 = copy.deepcopy(base_state)
c6["board"] = c6["board"][:-1] # 13 rows instead of 14
with open(OUT_DIR / "06_misconfigured_board.json", "w") as f:
    json.dump(c6, f, indent=2)

# 7. 07_wrong_starting_corners.json
c7 = copy.deepcopy(base_state)
c7["remaining_pieces"]["blue"].remove("I1")
c7["board"][0] = "B" + c7["board"][0][1:] # Placed at 0,0 instead of 4,4
c7["history"].append({
    "player": "blue", "piece": "I1", "x": 0, "y": 0, "rotation": 0, "flipped": False
})
c7["current_player"] = "red"
with open(OUT_DIR / "07_wrong_starting_corners.json", "w") as f:
    json.dump(c7, f, indent=2)

# 8. 08_invalid_history_moves.json
c8 = copy.deepcopy(base_state)
c8["history"].append({
    "player": "blue", "piece": "I1", "x": -1, "y": -1, "rotation": 0, "flipped": False
})
with open(OUT_DIR / "08_invalid_history_moves.json", "w") as f:
    json.dump(c8, f, indent=2)

print("Generated 8 edge cases.")
