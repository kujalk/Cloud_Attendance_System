import boto3
from botocore.exceptions import ClientError

def sendEmail(studentId,firstName,lastName):

    SENDER = "nus.jenkins@gmail.com"
    RECIPIENT_LIST = ["nus.jenkins@gmail.com","grishi2020@gmail.com","zaheernew@gmail.com"]

    SUBJECT = "Student Registered for Cloud Attendance System"

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = ("Hi "+firstName+" "+lastName+"\n\n"
                "You have been registred for attendance system. Please refer more details,\n"+
                "Student ID : "+studentId+"\n"+"Password : Student@123\n\nBest Regards,\nAdminstration"
                )

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses',region_name='ap-southeast-1')

    # Try to send the email.
    try:
        #Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': RECIPIENT_LIST,
            },
            Message={
                'Body': {
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
            
        )

    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])

