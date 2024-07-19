# POP3 Helper Class
# M. Tim Jones <mtj@mtjones.com>
#

import os
import poplib
from email import parser
from email.message import EmailMessage

class InMail( ):

    def __init__( self ):

        self.username = os.getenv( 'username', None )
        self.password = os.getenv( 'password', None )
        self.pop3_server = os.getenv( 'pop3_server', None )

        if self.username is None or self.password is None or self.pop3_server is None:
            raise "Env Missing"


    def login( self ):

        self.in_mailbox = poplib.POP3( self.pop3_server, 110 )
        self.in_mailbox.user( self.username )
        self.in_mailbox.pass_( self.password )


    def get_payload( self, msg ):

        body = ''
        filename = ''

        print('a')
        if msg.is_multipart( ):
            print('b')
            for part in msg.walk( ):
                print('c')
                content_type = part.get_content_type( )
                print('d ' + content_type )
                content_disposition = part.get_content_disposition( )
                print('e')

                if content_type == "text/plain":
                    print('z')
                    if content_disposition is not None:
                        print("x")
                        if 'attachment' in content_disposition:
                            print("y")
                            print('attachment')
                            # Parse and save the attachment.
                            filename = part.get_filename( )
                            data = part.get_payload( decode = True )
                            f = open( filename, 'wb' )
                            f.write( data )
                            f.close( )
                            print("w")
                    else:
                        print('f')
                        body = part.get_payload( decode=True ).decode( )
                        print('g')
                        print( body )
                #elif content_type == "text/html":
                #    print('h')
                #    body = part.get_payload( decode=True ).decode( )
                #    print('i')
                #    print( body )

        else:
            body = msg.get_payload( decode=True ).decode( )

        return body, filename


    def get_email( self ):

        message_list = len( self.in_mailbox.list( )[ 1 ] )

        if message_list == 0:

            return None, None, None, None

        # For now, just process one message.
        for i in range( message_list ):

            ( _response, lines, _octets ) = self.in_mailbox.retr( i+1 )

            message_bytes = b'\n'.join( lines )

            # print( message_bytes.decode('utf-8') )

            message = parser.Parser().parsestr( message_bytes.decode( 'utf-8' ) )

            print( message )

            subject = message[ 'subject' ]
            sender  = message[ 'from' ]

            try:
                body, filename = self.get_payload( message )
            except Exception as e:
                print( "Failed get_payload" )
                print( e )
                sender = None
                subject = None
                body = None
                filename = None

            self.in_mailbox.dele( i+1 )

            print( sender )
            print( body )

            return sender, subject, body, filename

    def logout( self ):

        self.in_mailbox.quit( )

