"""Spaced Repetition System (SRS) service using SM-2 algorithm."""

from datetime import datetime, timedelta
from typing import Optional, Tuple


class SRSService:
    """
    SM-2 spaced repetition algorithm implementation.

    The algorithm adjusts review intervals based on performance scores (0-5):
    - 0-2: Failure, reset repetitions
    - 3-5: Success, increase interval
    """

    # SM-2 Algorithm parameters
    INITIAL_INTERVAL = 1       # First review after 1 day
    SECOND_INTERVAL = 6        # Second review after 6 days
    MIN_EASINESS = 1.3         # Minimum easiness factor
    INITIAL_EASINESS = 2.5     # Starting easiness factor

    @staticmethod
    def calculate_easiness_factor(current_ef: float, score: int) -> float:
        """
        Calculate new easiness factor based on performance (SM-2 formula).

        Args:
            current_ef: Current easiness factor
            score: Performance score 0-5

        Returns:
            New easiness factor (minimum 1.3)
        """
        # SM-2 formula: EF' = EF + (0.1 - (5-q)*(0.08+(5-q)*0.02))
        new_ef = current_ef + (0.1 - (5 - score) * (0.08 + (5 - score) * 0.02))
        return max(new_ef, SRSService.MIN_EASINESS)

    @staticmethod
    def calculate_next_interval(repetitions: int, easiness_factor: float, current_interval: int) -> int:
        """
        Calculate next review interval in days.

        Args:
            repetitions: Number of successful repetitions
            easiness_factor: Current easiness factor
            current_interval: Current interval in days

        Returns:
            Next review interval in days
        """
        if repetitions == 0:
            return SRSService.INITIAL_INTERVAL
        elif repetitions == 1:
            return SRSService.SECOND_INTERVAL
        else:
            return int(current_interval * easiness_factor)

    @staticmethod
    def process_review(
        score: int,
        current_ef: Optional[float] = None,
        current_repetitions: Optional[int] = None,
        current_interval: Optional[int] = None
    ) -> Tuple[float, int, int, datetime]:
        """
        Process a review and calculate new SRS parameters.

        Args:
            score: Performance score 0-5
            current_ef: Current easiness factor (defaults to 2.5)
            current_repetitions: Current repetition count (defaults to 0)
            current_interval: Current interval in days (defaults to 1)

        Returns:
            Tuple of (new_ef, new_repetitions, new_interval, next_review_date)
        """
        # Use defaults for new words
        ef = current_ef if current_ef is not None else SRSService.INITIAL_EASINESS
        reps = current_repetitions if current_repetitions is not None else 0
        interval = current_interval if current_interval is not None else 1

        # Calculate new easiness factor
        new_ef = SRSService.calculate_easiness_factor(ef, score)

        # Determine success/failure
        success = score >= 3
        if success:
            new_reps = reps + 1
        else:
            new_reps = 0  # Reset on failure

        # Calculate new interval
        new_interval = SRSService.calculate_next_interval(new_reps, new_ef, interval)

        # Calculate next review date
        next_review = datetime.utcnow() + timedelta(days=new_interval)

        return new_ef, new_reps, new_interval, next_review
