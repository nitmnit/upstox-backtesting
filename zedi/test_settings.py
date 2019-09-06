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
        env_value = os.getenv(env_variable_name)
        settings_value = getattr(settings, django_settings_name, None)
        self.assertIsNotNone(env_value, msg='Environment variable "{}" is not set'.format(env_variable_name))
        self.assertIsNotNone(settings_value, msg='Django settings "{}" is not set'.format(django_settings_name))
        self.assertIn(env_value, dir(AlgorithmRunMode),
                      msg='Invalid value for "{}": {}'.format(env_variable_name, env_value))
        self.assertIn(settings_value, dir(AlgorithmRunMode),
                      msg='Invalid value for "{}": {}'.format(django_settings_name, settings_value))
        self.assertEqual(settings_value, env_value,
                         msg='Settings misconfiguration "{}"!="{}"'.format(env_value, settings_value))


if __name__ == '__main__':
    unittest.main()
