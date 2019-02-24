from __future__ import absolute_import, unicode_literals
from celery import shared_task
from freaks.models import QuotesData


@shared_task(bind=True)
def save_quotes(self, data):
    for quote in data:
        if quote.get('timestamp'):
            QuotesData.objects.create(data=quote, timestamp=quote['timestamp'])
