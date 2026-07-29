# API guide

All protected routes require `Authorization: Bearer <JWT>`.

| Method | Route | Purpose |
|---|---|---|
| POST | `/api/v1/auth/signup` | Create account |
| POST | `/api/v1/auth/login` | Obtain JWT |
| GET | `/api/v1/profile` | Learner profile |
| POST | `/api/v1/assessment` | Store adaptive assessment |
| GET | `/api/v1/lessons/daily` | Personalized plan |
| POST | `/api/v1/grammar/correct` | Explained correction |
| POST | `/api/v1/writing/coach` | Writing coaching |
| POST | `/api/v1/conversation` | Mentor response |
| GET | `/api/v1/dashboard` | Scores and trends |
| GET | `/api/v1/recommendations` | Next learning action |
