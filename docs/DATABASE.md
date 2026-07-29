# Database schema

| Table | Responsibility |
|---|---|
| `users` | Identity, role, industry, password hash |
| `learner_profiles` | Current competency scores, strengths, weaknesses, preferences |
| `assessments` | Immutable assessment attempts and generated results |
| `memories` | Long-term learning signals, categorized and ranked by importance |
| `learning_sessions` | Daily lesson content and completion events |
| `corrections` | Grammar and writing coaching history |
| `vocabulary` | Per-user words, mastery score, next spaced-repetition review |

All learner-owned records have a `user_id` foreign key. Add row-level tenant controls and audit metadata when introducing enterprise organizations.
