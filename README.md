# EventHub API

A RESTful event management API built using Django and Django REST Framework. EventHub lets users browse events, reserve seats, check availability, and cancel reservations.

## Features

- List and retrieve events
- Filter events by status and venue
- Create and view reservations
- Filter reservations by event ID
- Automatically update available seats after reservation creation or cancellation
- Prevent overbooking and invalid seat quantities
- Reject reservations for completed or cancelled events
- Prevent duplicate cancellation
- Enforce database-level constraints for seat counts
- Automated tests for API functionality and validation

## Tech Stack

- Python 3.13
- Django 6.1.2
- Django REST Framework 3.18.3
- SQLite
- Django automated testing framework

## Installation and Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd EVENTHUB
```

Replace `<your-repository-url>` with your GitHub repository URL.

### 2. Create and activate a virtual environment

For Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Apply database migrations

```powershell
python manage.py migrate
```

### 5. Start the development server

```powershell
python manage.py runserver
```

The API base URL is:

`http://127.0.0.1:8000/api/`

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/events/` | List events |
| GET | `/api/events/{id}/` | Retrieve an event |
| GET | `/api/reservations/` | List reservations |
| POST | `/api/reservations/` | Create a reservation |
| GET | `/api/reservations/{id}/` | Retrieve a reservation |
| POST | `/api/reservations/{id}/cancel/` | Cancel a reservation |

Replace `{id}` with the relevant event or reservation ID.

## Filtering

Filter events by status:

`GET /api/events/?status=upcoming`

Filter events by venue:

`GET /api/events/?venue=New%20Delhi`

Filter reservations by event ID:

`GET /api/reservations/?event_id=1`

Use values that match records in your database.

## Creating a Reservation

Send a `POST` request to `/api/reservations/` with a JSON body like this:

```json
{
  "event": 1,
  "attendee_name": "Rahul Sharma",
  "attendee_email": "rahul@example.com",
  "seats_reserved": 2
}
```

The event ID must refer to an existing event. The reservation will be rejected if the seat count is invalid, the requested seats exceed availability, or the event is not accepting reservations.

When the reservation succeeds, the event's available seat count decreases automatically.

## Cancelling a Reservation

Send a `POST` request to `/api/reservations/{id}/cancel/`, replacing `{id}` with the reservation ID.

A successful cancellation marks the reservation as cancelled and restores its reserved seats to the event's available inventory. Attempting to cancel the same reservation again returns an error.

## Running Tests

Run the automated tests with:

```powershell
python manage.py test events
```

The current test suite contains 17 tests covering event and reservation endpoints, filtering, validation, seat availability, cancellation, and database constraints.

## Database Migrations

After changing models, create and apply migrations:

```powershell
python manage.py makemigrations
python manage.py migrate
```

## Project Status

All 17 automated tests currently pass, and Django's system check reports no issues.

## License

No license has been specified yet. Add a license if you intend to distribute this project publicly.