from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Save quotes data into database'

    def handle(self, *args, **kwargs):
        # Create a ws connection with Zerodha
        # Start receiving quotes for selected 5 stocks
        # Save them in the database

        # TODO Create a model to save quotes
        # TODO Create a class to receive to websockets
        # TODO As soon as you receive the data, save that in database
        # TODO Create a background celery task to save data in database
        pass
