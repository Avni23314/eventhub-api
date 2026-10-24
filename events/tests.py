from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Event, Reservation
from typing import Any, cast

class EventAPITests(APITestCase):
    def setUp(self):
        self.event = Event.objects.create(
            title="Test Tech Conference",
            venue="New Delhi",
            date=timezone.now() + timedelta(days=30),
            total_seats=30,
            available_seats=30,
            status="upcoming",
        )
        self.events_url = reverse("event-list")

    def test_list_events(self):
        response = self.client.get(self.events_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(cast(Any, response).data), 1)

    def test_filter_events_by_venue(self):
        response = self.client.get(
            self.events_url, {"venue": "Delhi"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(cast(Any, response).data), 1)

    def test_filter_events_by_status(self):
        response = self.client.get(
            self.events_url, {"status": "upcoming"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(cast(Any, response).data), 1)

    def test_reject_available_seats_above_total(self):
        response = self.client.patch(
            reverse("event-detail", args=[self.event.pk]),
            {"available_seats": 31},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_reject_negative_seat_counts(self):
        response = self.client.patch(
            reverse("event-detail", args=[self.event.pk]),
            {"available_seats": -1},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_reject_invalid_seat_count_type(self):
        response = self.client.patch(
            reverse("event-detail", args=[self.event.pk]),
            {"available_seats": "not-a-number"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
    def test_database_rejects_available_seats_above_total(self):
        from django.db import IntegrityError, transaction
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Event.objects.create(
                    title="Invalid Event",
                    venue="Delhi",
                    date=timezone.now().date() + timedelta(days=10),
                    total_seats=10,
                    available_seats=11,
                    status="upcoming",
                )



class ReservationAPITests(APITestCase):
    def setUp(self):
        self.event = Event.objects.create(
            title="Test Workshop",
            venue="Jaipur",
            date=timezone.now() + timedelta(days=15),
            total_seats=30,
            available_seats=30,
            status="upcoming",
        )
        self.reservations_url = reverse("reservation-list")

    def create_reservation(self, seats):
        return self.client.post(
            self.reservations_url,
            {
                "event": self.event.pk,
                "attendee_name": "Rahul Sharma",
                "attendee_email": "rahul@example.com",
                "seats_reserved": seats,
            },
            format="json",
        )

    def test_create_reservation_deducts_seats(self):
        response = self.create_reservation(3)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.event.refresh_from_db()
        self.assertEqual(self.event.available_seats, 27)

    def test_overbooking_is_rejected(self):
        response = self.create_reservation(31)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.event.refresh_from_db()
        self.assertEqual(self.event.available_seats, 30)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_zero_seats_is_rejected(self):
        response = self.create_reservation(0)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_cancel_restores_seats(self):
        reservation_response = self.create_reservation(3)
        self.assertEqual(
            reservation_response.status_code,
            status.HTTP_201_CREATED,
        )

        reservation_id = cast(Any, reservation_response).data["id"]
        cancel_url = reverse(
            "reservation-cancel", args=[reservation_id]
        )

        response = self.client.post(cancel_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            cast(Any, response).data["status"],
            "cancelled",
        )

        self.event.refresh_from_db()
        self.assertEqual(self.event.available_seats, 30)

    def test_cannot_cancel_twice(self):
        reservation_response = self.create_reservation(3)
        reservation_id = cast(Any, reservation_response).data["id"]

        cancel_url = reverse(
            "reservation-cancel", args=[reservation_id]
        )

        first_response = self.client.post(cancel_url)
        second_response = self.client.post(cancel_url)

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.event.refresh_from_db()
        self.assertEqual(self.event.available_seats, 30)

    def test_completed_event_rejects_reservation(self):
        self.event.status = "completed"
        self.event.save(update_fields=["status"])

        response = self.create_reservation(1)

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.event.refresh_from_db()
        self.assertEqual(self.event.available_seats, 30)

    def test_cancelled_event_rejects_reservation(self):
        self.event.status = "cancelled"
        self.event.save(update_fields=["status"])

        response = self.create_reservation(1)

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.event.refresh_from_db()
        self.assertEqual(self.event.available_seats, 30)

    def test_nonexistent_reservation_returns_404(self):
        response = self.client.post(
            reverse("reservation-cancel", args=[99999])
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_reservation_cannot_be_edited(self):
        created = self.create_reservation(3)
        self.assertEqual(
            created.status_code,
            status.HTTP_201_CREATED,
        )

        response = self.client.patch(
            reverse(
                "reservation-detail",
                args=[cast(Any, created).data["id"]],
            ),
            {"seats_reserved": 5},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.event.refresh_from_db()
        self.assertEqual(self.event.available_seats, 27)

    def test_database_rejects_zero_reserved_seats(self):
        from django.db import IntegrityError, transaction
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Reservation.objects.create(
                    event=self.event,
                    attendee_name="Test Attendee",
                    attendee_email="test@example.com",
                    seats_reserved=0,
                )