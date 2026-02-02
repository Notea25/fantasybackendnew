from typing import Optional
from app.players.models import Player


# Status priority (lower number = higher priority)
STATUS_PRIORITY = {
    "left_league": 1,
    "red_card": 2,
    "injured": 3,
}


def get_player_status_for_tour(player: Player, tour_number: int) -> Optional[str]:
    """
    Get the active status for a player in a specific tour.
    
    If multiple statuses are active, returns the most critical one based on priority:
    1. left_league (highest priority)
    2. red_card
    3. injured (lowest priority)
    
    Args:
        player: Player model instance (must have statuses relationship loaded)
        tour_number: Tour number to check
    
    Returns:
        Status type string or None if player has no active status
    """
    if not hasattr(player, 'statuses') or not player.statuses:
        return None
    
    # Filter statuses that are active in this tour
    active_statuses = [
        status
        for status in player.statuses
        if status.tour_start <= tour_number and
           (status.tour_end is None or status.tour_end >= tour_number)
    ]
    
    if not active_statuses:
        return None
    
    # Sort by priority (lower number = higher priority)
    active_statuses.sort(
        key=lambda s: STATUS_PRIORITY.get(s.status_type, 99)
    )
    
    return active_statuses[0].status_type