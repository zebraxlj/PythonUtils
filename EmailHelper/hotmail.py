import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# 发件人和收件人信息
sender_email = 'lx223809@hotmail.com'
receiver_email = 'lx223809@sina.com'
password = 'Eason_1874'

# 创建 MIMEMultipart 对象
message = MIMEMultipart()
message['From'] = sender_email
message['To'] = receiver_email
message['Subject'] = 'Test Email from Outlook SMTP'

# 邮件正文内容
body = 'This is a test email sent from Python using Outlook SMTP server.'
message.attach(MIMEText(body, 'plain'))

# 连接到 SMTP 服务器并发送邮件
try:
    # 使用 TLS
    server = smtplib.SMTP('smtp-mail.outlook.com', 587)
    print('here:', server.ehlo())
    server.starttls()
    # 登录到 SMTP 服务器
    server.login(sender_email, password)
    # 发送邮件
    server.sendmail(sender_email, receiver_email, message.as_string())
    print('Email sent successfully!')
except Exception as e:
    print(f'Failed to send email. Error: {e}')
finally:
    # 关闭服务器连接
    server.quit()
