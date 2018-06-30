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


# gm = TlsSMTPHandler((settings.EMAIL_SETTINGS['HOST'], settings.EMAIL_SETTINGS['PORT']),
#                     settings.EMAIL_SETTINGS['USER'][1], settings.MANAGERS, SUBJECT,
#                     (settings.EMAIL_SETTINGS['USER'][1], settings.EMAIL_SETTINGS['PASSWORD']))
#
# gm.setLevel(logging.ERROR)
#
# logger.addHandler(gm)


log_format = '[%(asctime)s] %(levelname)s in %(module)s [%(pathname)s:%(lineno)d] - %(message)s'


# def get_logger():
#     logging.basicConfig(level=logging.DEBUG, format=log_format)
#     formatter = logging.Formatter(log_format, '%m-%d %H:%M:%S')
#     handler = logging.RotatingFileHandler('freaky_bananas.log', maxBytes=10000000, backupCount=10)
#     handler.setLevel(logging.DEBUG)
#     handler.setFormatter(formatter)
#     logger = logging.getLogger('freakybananas')
#     logger.addHandler(handler)
#     return logger
