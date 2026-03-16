# Felhoalapu_HF1

Django photo album implementation with:

- In-memory data store (no persistent database)
- No authentication
- Photo upload and delete
- Photo listing with sorting by name or upload date
- Clickable list entries with image preview

## TODO

- [x] Auth (registration, login, logout)
- [x] Restrict upload/delete to authenticated users only
- [x] Deploy on BME OpenShift (OKD)
- [x] Persistent database (PostgreSQL instead of in-memory storage)
- [x] Separate app and database layers for scalable deployment
- [x] Configure automatic GitHub-triggered build/deploy pipeline
- [x] Add tests for required upload/delete/list/sort/auth flows
- [x] Nicer UI


