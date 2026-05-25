import os

# --- STATES: what the opponent just played ---
states = ["OpponentPlayed_1Block", "OpponentPlayed_2Block", "OpponentPlayed_3Block"]

# --- ACTIONS: what YOU can play ---
actions = ["Place_1BlockPiece", "Place_2BlockPiece", "Place_3BlockPiece"]

# --- Transition probabilities ---
# After you play, the opponent randomly chooses next piece size
transition_prob = {
    "OpponentPlayed_1Block": {
        "OpponentPlayed_1Block": 0.1,
        "OpponentPlayed_2Block": 0.2,
        "OpponentPlayed_3Block": 0.7
    },
    "OpponentPlayed_2Block": {
        "OpponentPlayed_1Block": 0.2,
        "OpponentPlayed_2Block": 0.3,
        "OpponentPlayed_3Block": 0.5
    },
    "OpponentPlayed_3Block": {
        "OpponentPlayed_1Block": 0.2,
        "OpponentPlayed_2Block": 0.3,
        "OpponentPlayed_3Block": 0.5
    }
}

# --- Rewards ---
# Simple rule:
# - Same size: +2
# - Larger piece: +3
# - Smaller piece: -1

def calculate_reward(state, action):
    opponent_piece_size = int(state.split("_")[1][0])  # Extract size from state
    your_piece_size = int(action.split("_")[1][0])  # Extract size from action

    if your_piece_size == opponent_piece_size:
        return 2
    elif your_piece_size > opponent_piece_size:
        return 3
    else:
        return -1
    
reward = {
    "OpponentPlayed_1Block": {
        "Place_1BlockPiece": (calculate_reward),
        "Place_2BlockPiece": (calculate_reward),
        "Place_3BlockPiece": (calculate_reward) 
    },
    "OpponentPlayed_2Block": {
        "Place_1BlockPiece": (calculate_reward),
        "Place_2BlockPiece": (calculate_reward),
        "Place_3BlockPiece": (calculate_reward)
    },
    "OpponentPlayed_3Block": {
        "Place_1BlockPiece": (calculate_reward),
        "Place_2BlockPiece": (calculate_reward),
        "Place_3BlockPiece": (calculate_reward)
    }
}

# --- Initial policy ---
policy = {
    "OpponentPlayed_1Block": "Place_3BlockPiece",
    "OpponentPlayed_2Block": "Place_3BlockPiece",
    "OpponentPlayed_3Block": "Place_3BlockPiece"
}

# --- Value function ---
V = {
    "OpponentPlayed_1Block": 0.0,
    "OpponentPlayed_2Block": 0.0,
    "OpponentPlayed_3Block": 0.0
}

gamma = 0.9  # discount factor

while True:

    # --- POLICY EVALUATION ---
    for s in states:
        a = policy[s]
        V[s] = reward[s][a] + gamma * sum(
            transition_prob[s][s_next] * V[s_next]
            for s_next in states
        )

    os.system('cls' if os.name == 'nt' else 'clear')
    print("Current Values:")
    print(V)

    # --- POLICY IMPROVEMENT ---
    new_policy = {}

    for s in states:
        best_action = None
        best_value = float("-inf")

        for a in actions:
            value = reward[s][a] + gamma * sum(
                transition_prob[s][s_next] * V[s_next]
                for s_next in states
            )

            if value > best_value:
                best_value = value
                best_action = a

        new_policy[s] = best_action

    print("\nNew Policy:")
    print(new_policy)

    policy = new_policy

    entrada = input("\nPress ENTER to iterate again or type 'salir' to exit: ")
    if entrada.lower() == "salir":
        break
