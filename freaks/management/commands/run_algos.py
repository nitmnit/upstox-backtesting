import os
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand

import exceptions
from zedi import constants


class Command(BaseCommand):
    help = 'Start the algorithm'

    def add_arguments(self, parser):
        parser.add_argument(
            '--algorithm',
            help='Choose the algorithm to run',
        )
        parser.add_argument(
            '--run-mode',
            help='Mode to run algorithm in',
        )
        parser.add_argument(
            '--start',
            help='Start Date time',
        )
        parser.add_argument(
            '--end',
            help='End Date time',
        )

    def handle(self, *args, **options):
        self.run_validations(options)

    def run_validations(self, options):
        if 'algorithm' not in options or not options['algorithm']:
            raise exceptions.MissingOptionsException(message='algorithm option not passed', errors=None)
        if 'run_mode' not in options or not options['run_mode']:
            raise exceptions.MissingOptionsException(message='run-mode option not passed', errors=None)
        if options['run_mode'] not in dir(constants.AlgorithmRunMode):
            raise exceptions.MissingOptionsException(message='Invalid run mode passed', errors=None)
        if not options['run_mode'] == settings.ALGORITHM_RUN_MODE == os.getenv('ZZ_ALGORITHM_RUN_MODE'):
            raise exceptions.ConflictingEnvironmentsException(
                message='Invalid environment, run-mode:'
                        ' {}, settings: {}, env: {}'.format(options['run_mode'], settings.ALGORITHM_RUN_MODE,
                                                            os.getenv('ZZ_ALGORITHM_RUN_MODE')), errors=None)
        if options['run_mode'] in [constants.AlgorithmRunMode.HISTORICAL,
                                   constants.AlgorithmRunMode.SIMULATED_SEMI_LIVE]:
            if 'start' not in options or not options['start']:
                raise exceptions.MissingOptionsException(message='start option not passed', errors=None)
            if 'end' not in options or not options['end']:
                raise exceptions.MissingOptionsException(message='end option not passed', errors=None)
            try:
                start_date_time = datetime.strptime(options['start'], '%d-%m-%y%H:%M:%S')
            except ValueError as e:
                exceptions.InvalidOptionException(message='Invalid start value passed')
            try:
                end_date_time = datetime.strptime(options['end'], '%d-%m-%y%H:%M:%S')
            except ValueError as e:
                exceptions.InvalidOptionException(message='Invalid end value passed')
