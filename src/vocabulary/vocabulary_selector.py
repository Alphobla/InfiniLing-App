#!/usr/bin/env python3
"""
Vocabulary Selector

Handles vocabulary selection using spaced repetition and priority algorithms.
"""

import random
import datetime
from typing import List, Tuple
from .git_database_manager import DatabaseManager


class VocabularySelector:
    """Selects vocabulary words based on spaced repetition and priority."""
    
    def __init__(self, database_manager: DatabaseManager):
        self.database_manager = database_manager
    
    def calculate_word_priority(self, word: str, translation: str) -> int:
        """Calculate priority score for a word (higher = more likely to be selected)."""
        word_key = f"{word}|{translation}"
        
        if word_key not in self.database_manager.word_stats:
            return 100  # New word - high priority
        
        stats = self.database_manager.word_stats[word_key]
        
        # Ensure occurrences exists and is a list
        if 'occurrences' not in stats or not isinstance(stats['occurrences'], list):
            stats['occurrences'] = []
        
        # Calculate days since last use
        if stats['occurrences']:
            try:
                last_used_date = stats['occurrences'][-1]['date']
                days_since_last_use = (datetime.datetime.now() - datetime.datetime.fromisoformat(last_used_date)).days
            except (KeyError, ValueError, TypeError):
                days_since_last_use = 999
        else:
            days_since_last_use = 999
        
        times_used = len(stats['occurrences'])
        times_not_understood = sum(1 for occ in stats['occurrences'] 
                                  if isinstance(occ, dict) and occ.get('repeat', False))
        
        # Priority formula
        base_priority = min(days_since_last_use * 5, 50)  # Max 50 points for age
        misunderstanding_bonus = times_not_understood * 20  # 20 points per misunderstanding
        frequency_penalty = min(times_used * 2, 30)  # Max 30 point penalty
        
        priority = base_priority + misunderstanding_bonus - frequency_penalty
        return max(priority, 1)  # Minimum priority of 1
    
    def select_words_for_session(self, random_sample_size: int, final_selection_size: int) -> List[Tuple[str, str, str]]:
        """Select words for a learning session (wrapper method for compatibility)."""
        vocab_list = self.database_manager.get_vocabulary_list()
        return self.select_words_by_priority(vocab_list, random_sample_size, final_selection_size)
    
    def select_words_by_priority(self, vocab_list: List[Tuple[str, str, str]], 
                                random_sample_size: int = 40, 
                                final_selection_size: int = 20) -> List[Tuple[str, str, str]]:
        """Select words based on priority (spaced repetition with randomness)."""
        
        if not vocab_list:
            print("⚠️ No vocabulary words available for selection")
            return []
        
        # Sample words for priority calculation
        sample_size = min(random_sample_size, len(vocab_list))
        sampled_vocab = random.sample(vocab_list, sample_size)
        
        # Calculate priorities
        word_priorities = []
        for vocab_entry in sampled_vocab:
            word, translation = vocab_entry[0], vocab_entry[1]
            pronunciation = vocab_entry[2] if len(vocab_entry) > 2 else ""
            
            priority = self.calculate_word_priority(word, translation)
            word_priorities.append((word, translation, pronunciation, priority))
            
        # Sort by priority and show urgency bars
        word_priorities.sort(key=lambda x: x[3], reverse=True)
        self._print_urgency_bars(word_priorities, final_selection_size)
        
        # Return selected words
        selected_count = min(final_selection_size, len(word_priorities))
        return [(w, t, pron) for w, t, pron, _ in word_priorities[:selected_count]]
    
    def _print_urgency_bars(self, word_priorities: List[Tuple[str, str, str, int]], count: int):
        """Print urgency visualization bars."""
        if not word_priorities:
            return
            
        max_urgency = max(p for _, _, _, p in word_priorities)
        print(f"\n[ Vocabulary selection: Urgency bars (top {count} marked) ]")
        
        for i, (_, _, _, priority) in enumerate(word_priorities):
            bar_len = int((priority / max_urgency) * 40)
            bar = '█' * bar_len
            mark = '*' if i < count else ' '
            print(f"{bar:<40} {mark}")
    
    def mark_word_used(self, word: str, translation: str):
        """Mark a word as used in current session (not repeated)."""
        self.database_manager.add_occurrence(word, translation, repeat=False)
    
    def mark_word_not_understood(self, word: str, translation: str):
        """Mark a word as not understood (to be repeated)."""
        self.database_manager.add_occurrence(word, translation, repeat=True)
    
    def get_selection_statistics(self, selected_words: List[Tuple[str, str, str]]) -> dict:
        """Get statistics about the selected words."""
        if not selected_words:
            return {}
        
        priorities = []
        new_words = 0
        
        for word, translation, _ in selected_words:
            priority = self.calculate_word_priority(word, translation)
            priorities.append(priority)
            if priority == 100:  # New word
                new_words += 1
        
        return {
            'total_words': len(selected_words),
            'new_words': new_words,
            'experienced_words': len(selected_words) - new_words,
            'avg_priority': sum(priorities) / len(priorities),
            'max_priority': max(priorities),
            'min_priority': min(priorities)
        }
