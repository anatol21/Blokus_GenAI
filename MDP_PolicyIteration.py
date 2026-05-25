import os
from typing import Dict, List

# --- STATES: what the opponent just played ---
states: List[str] = [
    "OpponentPlayed_1Block",
    "OpponentPlayed_2Block",
    "OpponentPlayed_3Block",
]

# --- ACTIONS: what YOU can play ---
actions: List[str] = [
    "Place_1BlockPiece",
    "Place_2BlockPiece",
    "Place_3BlockPiece",
]

# --- Transition probabilities ---
transition_prob: Dict[str, Dict[str, float]] = {
    "OpponentPlayed_1Block": {
        "OpponentPlayed_1Block": 0.1,
        "OpponentPlayed_2Block": 0.2,
        "OpponentPlayed_3Block": 0.7,
    },
    "OpponentPlayed_2Block": {
        "OpponentPlayed_1Block": 0.2,
        "OpponentPlayed_2Block": 0.3,
        "OpponentPlayed_3Block": 0.5,
    },
    "OpponentPlayed_3Block": {
        "OpponentPlayed_1Block": 0.2,
        "OpponentPlayed_2Block": 0.3,
        "OpponentPlayed_3Block": 0.5,
    },
}

# --- Rewards ---
reward: Dict[str, Dict[str, float]] = {
    "OpponentPlayed_1Block": {
        "Place_1BlockPiece": 1.0,
        "Place_2BlockPiece": 2.0,
        "Place_3BlockPiece": 3.0,
    },
    "OpponentPlayed_2Block": {
        "Place_1BlockPiece": -1.0,
        "Place_2BlockPiece": 2.0,
        "Place_3BlockPiece": 3.0,
    },
    "OpponentPlayed_3Block": {
        "Place_1BlockPiece": -1.0,
        "Place_2BlockPiece": 2.0,
        "Place_3BlockPiece": 3.0,
    },
}

# --- Initial policy ---
policy: Dict[str, str] = {
    "OpponentPlayed_1Block": "Place_3BlockPiece",
    "OpponentPlayed_2Block": "Place_3BlockPiece",
    "OpponentPlayed_3Block": "Place_3BlockPiece",
}

# --- Value function ---
V: Dict[str, float] = {
    "OpponentPlayed_1Block": 0.0,
    "OpponentPlayed_2Block": 0.0,
    "OpponentPlayed_3Block": 0.0,
}

gamma: float = 0.9  # discount factor


def clear_screen() -> None:
    """Clear the terminal screen in an OS‑portable way."""
    # Optional: you can comment this out if you don't want clearing at all
    os.system("cls" if os.name == "nt" else "clear")


def policy_evaluation(
    states_list: List[str],
    current_policy: Dict[str, str],
    values: Dict[str, float],
    max_iterations: int = 10,
    tolerance: float = 1e-6,
) -> None:
    """Run a few sweeps of policy evaluation to approximate V for the current policy."""
    for _ in range(max_iterations):
        delta = 0.0
        for s in states_list:
            a = current_policy[s]
            old_v = values[s]
            values[s] = reward[s][a] + gamma * sum(
                transition_prob[s][s_next] * values[s_next] for s_next in states_list
            )
            delta = max(delta, abs(old_v - values[s]))
        if delta < tolerance:
            break


def policy_improvement(
    states_list: List[str],
    actions_list: List[str],
    values: Dict[str, float],
) -> Dict[str, str]:
    """Compute a greedy policy given the current value function."""
    new_policy: Dict[str, str] = {}
    for s in states_list:
        best_action: str | None = None
        best_value = float("-inf")

        for a in actions_list:
            value = reward[s][a] + gamma * sum(
                transition_prob[s][s_next] * values[s_next] for s_next in states_list
            )
            if value > best_value:
                best_value = value
                best_action = a

        # best_action will always be set because actions_list is non‑empty
        new_policy[s] = best_action if best_action is not None else actions_list[0]

    return new_policy


def run_interactive() -> None:
    """Interactive loop to visualize policy iteration steps."""
    global policy, V

    while True:
        # --- POLICY EVALUATION ---
        policy_evaluation(states, policy, V)

        clear_screen()
        print("Current Values:")
        print(V)

        # --- POLICY IMPROVEMENT ---
        new_policy = policy_improvement(states, actions, V)

        print("\nNew Policy:")
        print(new_policy)

        policy = new_policy

        entrada = input(
            "\nPress ENTER to iterate again or type 'salir' or 'exit' to quit: "
        )
        if entrada.lower() in ("salir", "exit"):
            break


if __name__ == "__main__":
    run_interactive()
