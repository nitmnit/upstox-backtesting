import string, logging, logging.handlers
import settings

MAILHOST = settings.EMAIL_SETTINGS['HOST']
FROM = settings.EMAIL_SETTINGS['USER'][1]
TO = settings.MANAGERS
MAIL_PORT = settings.EMAIL_SETTINGS['PORT']
if settings.DEBUG:
    SUBJECT = 'Freaky Bananas Testing'
else:
    SUBJECT = 'Freaky Bananas'


class TlsSMTPHandler(logging.handlers.SMTPHandler):
    def emit(self, record):
        """
        Emit a record.

        Format the record and send it to the specified addressees.
        """
        try:
            import smtplib
            import string  # for tls add this line
            try:
                from email.utils import formatdate
            except ImportError:
                formatdate = self.date_time
            port = self.mailport
            if not port:
                port = smtplib.SMTP_PORT
            smtp = smtplib.SMTP(self.mailhost, port)
            msg = self.format(record)
            msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\nDate: %s\r\n\r\n%s" % (
                self.fromaddr,
                string.join(self.toaddrs, ","),
                self.getSubject(record),
                formatdate(), msg)
            if self.username:
                smtp.ehlo()  # for tls add this line
                smtp.starttls()  # for tls add this line
                smtp.ehlo()  # for tls add this line
                smtp.login(self.username, self.password)
            smtp.sendmail(self.fromaddr, self.toaddrs, msg)
            smtp.quit()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


logger = logging.getLogger()

gm = TlsSMTPHandler((settings.EMAIL_SETTINGS['HOST'], settings.EMAIL_SETTINGS['PORT']),
                    settings.EMAIL_SETTINGS['USER'][1], settings.MANAGERS, SUBJECT,
                    (settings.EMAIL_SETTINGS['USER'][1], settings.EMAIL_SETTINGS['PASSWORD']))

gm.setLevel(logging.ERROR)

logger.addHandler(gm)
