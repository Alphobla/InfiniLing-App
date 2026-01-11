# Claude Development Notes

## Core Development Principles
After proposing a change in the code, wait. I might ask followup questions. Aim of this project is to create a cool app but also for me to learn core concepts on the way.
### Simplicity First
- **Stick to core functionality** - Start with the minimum viable implementation
- **Keep it simple in the beginning** - Focus on understanding core concepts before adding complexity
- **Avoid premature optimization** - Don't add features that aren't immediately needed

### Database Design Guidelines
- **Normalize only when necessary** - If a relationship is 1:1, consider merging tables
- **Remove unnecessary tables** - Don't create tables for "nice to have" features
- **Focus on spaced repetition core needs**:
  - Individual word tracking (when last seen, success/failure)
  - Per-word timing intervals
  - Session-level analytics are optional/statistics only

### Code Organization
- **Prefer editing existing files** over creating new ones
- **Remove unused code** - Don't keep classes/functions that aren't needed
- **Question every feature** - Ask "Is this needed for core functionality?"

## Project Status

### Database Structure
- **Vocabulary table**: Core word data + example sentences (1:1 relationship)
- **VocabularyOccurrence table**: Track individual reviews (date, repeat flag)
- **No session tracking**: Keep spaced repetition simple, focus on per-word data
