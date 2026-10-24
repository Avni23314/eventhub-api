from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from typing import cast
from rest_framework.request import Request
from .models import Event, Reservation
from .serializers import EventSerializer, ReservationSerializer


class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer

    def get_queryset(self):
        queryset = Event.objects.all()
        request=cast(Request,self.request)
        status_param = request.query_params.get('status')
        venue_param = request.query_params.get('venue')

        if status_param:
            queryset = queryset.filter(status=status_param)

        if venue_param:
            queryset = queryset.filter(venue__icontains=venue_param)

        return queryset


class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer

    def get_queryset(self):
        queryset = Reservation.objects.select_related('event')

        request = cast(Request, self.request)
        event_id = request.query_params.get('event_id')

        if event_id:
            queryset = queryset.filter(event_id=event_id)

        return queryset

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        with transaction.atomic():
            reservation = get_object_or_404(
                Reservation.objects.select_for_update(),
                pk=pk,
            )

            event = Event.objects.select_for_update().get(
                pk=reservation.event.pk
            )

            if reservation.status == 'cancelled':
                return Response(
                    {'error': 'Already cancelled.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            event.available_seats += reservation.seats_reserved
            event.save(update_fields=['available_seats'])

            reservation.status = 'cancelled'
            reservation.save(update_fields=['status'])

        return Response(self.get_serializer(reservation).data)