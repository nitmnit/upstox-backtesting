from django.db import models

from django_extensions.db.models import TimeStampedModel

NAME_LENGTH = 60


class Credential(TimeStampedModel):
    name = models.CharField(max_length=NAME_LENGTH)
    description = models.CharField(max_length=NAME_LENGTH)
    client_id = models.CharField(max_length=NAME_LENGTH)
    password = models.CharField(max_length=NAME_LENGTH)
    api_secret = models.CharField(max_length=NAME_LENGTH)
    api_key = models.CharField(max_length=NAME_LENGTH)
    access_token = models.CharField(max_length=NAME_LENGTH, null=True, blank=True)

    def __str__(self):
        return self.name

    def set_access_token(self):
        con = SeleniumConnector(logger=self.logger)
        con.driver.get(self.con.login_url())
        time.sleep(3)
        username_input = con.driver.find_element_by_css_selector('input[type="text"]')
        password_input = con.driver.find_element_by_css_selector('input[type="password"]')
        submit_button = con.driver.find_element_by_css_selector('button[type="submit"]')
        username_input.send_keys(settings.KITE['USERNAME'])
        password_input.send_keys(settings.KITE['PASSWORD'])
        submit_button.click()
        time.sleep(5)
        sq1_el = con.driver.find_element_by_css_selector('.twofa-form > div:nth-child(2) input')
        sq2_el = con.driver.find_element_by_css_selector('.twofa-form > div:nth-child(3) input')
        question1 = sq1_el.get_attribute('label')
        question2 = sq2_el.get_attribute('label')
        answer1 = self.get_answer(question1)
        answer2 = self.get_answer(question2)
        sq1_el.send_keys(answer1)
        sq2_el.send_keys(answer2)
        answer_submit_button = con.driver.find_element_by_css_selector('button[type="submit"]')
        answer_submit_button.click()
        time.sleep(3)
        parsed = urlparse.urlparse(con.driver.current_url)
        request_token = urlparse.parse_qs(parsed.query)['request_token'][0]
        con.driver.close()
        self.log('Got request token. {}'.format(request_token))



class SecurityQuestion(TimeStampedModel):
    question = models.CharField(max_length=NAME_LENGTH * 10)
    answer = models.CharField(max_length=NAME_LENGTH)
    credentials = models.ForeignKey(Credential, on_delete=models.CASCADE)

    def __str__(self):
        return self.question
