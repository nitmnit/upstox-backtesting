from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options


class SeleniumConnector(object):
    def __init__(self, logger, is_headless=True):
        self.logger = logger
        self.logger.info('Selenium Connect Started')
        chrome_options = Options()
        if is_headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument('window-size=1920,1080')
        # chrome_options.add_argument("download.default_directory=C:/Users/Administrator/PycharmProjects/Stock/downloads")
        # prefs = {'download.default_directory': 'C:/Users/Administrator/PycharmProjects/Stock/downloads'}
        # chrome_options.add_experimental_option('prefs', prefs)
        desired_capabilities = DesiredCapabilities.CHROME
        desired_capabilities['loggingPrefs'] = {"browser": "SEVERE"}
        self.driver = webdriver.Chrome(executable_path='/usr/bin/chromedriver',
                                       desired_capabilities=DesiredCapabilities.CHROME, chrome_options=chrome_options)
        self.wait_time = 3
        self.logger.info('Selenium Connect Ended')
