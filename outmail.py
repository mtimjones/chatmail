# SMTP Helper Class
# M. Tim Jones <mtj@mtjones.com>
#

import os
import smtplib
from email.message import EmailMessage

class OutMail( ):

    def __init__( self ):

        self.username = os.getenv( 'username', None )
        self.password = os.getenv( 'password', None )
        self.smtp_server = os.getenv( 'smtp_server', None )

        if self.username is None or self.password is None or self.smtp_server is None:
            raise "Env Missing"


    def login( self ):

        self.out_mailbox = smtplib.SMTP( self.smtp_server, 587 )
        self.out_mailbox.login( self.username, self.password )


    def send_response( self, sender, subject, body ):

        msg = EmailMessage( )

        msg[ 'From' ] = self.username
        msg[ 'To' ] = sender
        msg[ 'Subject' ] = subject
        msg.set_content( body )

        self.out_mailbox.send_message( msg )

        print("Sent!\n")


    def logout( self ):

        self.out_mailbox.quit( )

