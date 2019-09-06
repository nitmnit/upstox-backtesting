import os
import unittest
from django.conf import settings

from zedi.constants import AlgorithmRunMode


class ZediSettingsTestCase(unittest.TestCase):
    def test_settings_configuration(self):
        """
        Validate zedi settings are configured properly
        :return:
        """
        env_variable_name = 'ZZ_ALGORITHM_RUN_MODE'
        django_settings_name = 'ALGORITHM_RUN_MODE'
        self.assertIsNotNone(os.getenv(env_variable_name),
                             msg='Environment variable "{}" is not set'.format(env_variable_name))
        self.assertIsNotNone(getattr(settings, django_settings_name, None),
                             msg='Django settings "{}" is not set'.format(django_settings_name))
        self.assertIn(os.getenv(env_variable_name), dir(AlgorithmRunMode),
                      msg='Invalid value for "{}": {}'.format(env_variable_name, os.getenv(env_variable_name)))
        self.assertIn(getattr(settings, django_settings_name, None), dir(AlgorithmRunMode),
                      msg='Invalid value for "{}": {}'.format(django_settings_name,
                                                              getattr(settings, django_settings_name, None)))
        self.assertEqual(getattr(settings, django_settings_name, None), os.getenv(env_variable_name),
                         msg='Settings misconfiguration "{}"!="{}"'.format(os.getenv(env_variable_name),
                                                                           getattr(settings, django_settings_name,
                                                                                   None)))


if __name__ == '__main__':
    unittest.main()
