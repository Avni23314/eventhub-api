from django.db import transaction
from rest_framework import serializers

from .models import Event, Reservation


class EventSerializer(serializers.ModelSerializer):
    reservations_count = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id',
            'title',
            'venue',
            'date',
            'total_seats',
            'available_seats',
            'status',
            'created_at',
            'reservations_count',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'reservations_count',
        ]

    def get_reservations_count(self, obj):
        return obj.reservations.filter(status='confirmed').count()

    def validate(self, data):
        total_seats = data.get(
            'total_seats',
            self.instance.total_seats if self.instance else None,
        )
        available_seats = data.get(
            'available_seats',
            self.instance.available_seats if self.instance else None,
        )

        errors = {}

        if total_seats is not None and total_seats < 0:
            errors['total_seats'] = (
                'Total seats cannot be negative.'
            )

        if available_seats is not None and available_seats < 0:
            errors['available_seats'] = (
                'Available seats cannot be negative.'
            )

        if (
            total_seats is not None
            and available_seats is not None
            and available_seats > total_seats
        ):
            errors['available_seats'] = (
                'Available seats cannot exceed total seats.'
            )

        if errors:
            raise serializers.ValidationError(errors)

        return data


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = [
            'id',
            'event',
            'attendee_name',
            'attendee_email',
            'seats_reserved',
            'status',
            'created_at',
        ]
        read_only_fields = ['id', 'status', 'created_at']

    def validate_seats_reserved(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Must reserve at least 1 seat.'
            )
        return value

    def validate(self, data):
        if self.instance is not None:
            raise serializers.ValidationError(
                'Reservations cannot be edited. '
                'Cancel and create a new reservation.'
            )

        event = data.get('event')
        seats = data.get('seats_reserved')

        if event is None:
            raise serializers.ValidationError({
                'event': 'An event is required.'
            })

        if event.status not in ('upcoming', 'ongoing'):
            raise serializers.ValidationError({
                'event': (
                    f'Cannot reserve seats for a {event.status} event.'
                )
            })

        if seats is not None and seats > event.available_seats:
            raise serializers.ValidationError({
                'seats_reserved': (
                    f'Only {event.available_seats} seat(s) available.'
                )
            })

        return data

    @transaction.atomic
    def create(self, validated_data):
        event = Event.objects.select_for_update().get(
            pk=validated_data['event'].pk
        )
        seats = validated_data['seats_reserved']

        if event.status not in ('upcoming', 'ongoing'):
            raise serializers.ValidationError({
                'event': (
                    f'Cannot reserve seats for a {event.status} event.'
                )
            })

        if seats > event.available_seats:
            raise serializers.ValidationError({
                'seats_reserved': (
                    f'Only {event.available_seats} seat(s) available.'
                )
            })

        event.available_seats -= seats
        event.save(update_fields=['available_seats'])

        validated_data['event'] = event
        return Reservation.objects.create(**validated_data)