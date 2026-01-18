from datetime import datetime, timedelta

def calculate_next_review(current_level: int, is_correct: bool):
    """
    Calculates the next review interval based on a simplified spaced repetition algorithm.
    
    Levels correspond roughly to:
    0: New
    1: 1 day
    2: 3 days
    3: 7 days
    4: 14 days
    5: 30 days
    ...
    """
    if not is_correct:
        # If incorrect, reset progress or stay at 0
        new_level = 0
        interval_days = 0 # Review immediately/soon means we treat it as "new" technically, 
                          # but effectively for the user flow we might want it back in the queue soon.
                          # For simplicity here: 0 days (due now)
    else:
        new_level = current_level + 1
        if new_level == 1:
            interval_days = 1
        elif new_level == 2:
            interval_days = 3
        elif new_level == 3:
            interval_days = 7
        elif new_level == 4:
            interval_days = 14
        else:
            # Simple exponential growth for higher levels
            interval_days = 30 * (2 ** (new_level - 5))
            
    next_review_date = datetime.now() + timedelta(days=interval_days)
    return new_level, next_review_date
