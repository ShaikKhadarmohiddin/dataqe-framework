# Sending HTML Reports via Email

## Overview

DataQE Framework generates properly formatted HTML reports that display beautifully in web browsers. If you want to send these reports via email, this guide shows you how to do it correctly so the HTML displays properly instead of appearing as plain text.

## The Problem

When you copy-paste HTML content into an email body as plain text:

```python
# ❌ WRONG - Email will show raw HTML text
email_body = """
<html>
<head>...</head>
<body>...</body>
</html>
"""
```

Most email clients treat this as **plain text** and display the raw HTML code instead of rendering it.

## The Solution

When sending HTML via email, you need to set the proper MIME type (`text/html`) so the email client knows to render the HTML.

### Using Python's built-in `smtplib`

**Option 1: Send HTML as proper MIME type (Recommended)**

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Read the HTML report
with open("./output/ExecutionReport.html", "r") as f:
    html_content = f.read()

# Create message
msg = MIMEMultipart("alternative")
msg["Subject"] = "Test Execution Report"
msg["From"] = "your-email@gmail.com"
msg["To"] = "recipient@company.com"

# Attach HTML content with proper MIME type
html_part = MIMEText(html_content, "html")
msg.attach(html_part)

# Send via SMTP
with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login("your-email@gmail.com", "your-app-password")
    server.send_message(msg)

print("✅ HTML report sent successfully!")
```

**Option 2: Send HTML file as attachment (Best practice)**

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Create message
msg = MIMEMultipart()
msg["Subject"] = "Test Execution Report"
msg["From"] = "your-email@gmail.com"
msg["To"] = "recipient@company.com"

# Add text body
body = MIMEText("Please find attached the Test Execution Report.")
msg.attach(body)

# Attach HTML file
with open("./output/ExecutionReport.html", "rb") as attachment:
    part = MIMEBase("application", "octet-stream")
    part.set_payload(attachment.read())

encoders.encode_base64(part)
part.add_header(
    "Content-Disposition",
    "attachment; filename= ExecutionReport.html",
)
msg.attach(part)

# Send via SMTP
with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login("your-email@gmail.com", "your-app-password")
    server.send_message(msg)

print("✅ HTML report sent as attachment!")
```

## Key Points

### ✅ DO THIS

1. **Set MIME type to `text/html`**
   ```python
   html_part = MIMEText(html_content, "html")  # ✅ Correct
   ```

2. **Use proper email headers**
   ```python
   msg["Subject"] = "Your Subject"
   msg["From"] = "sender@company.com"
   msg["To"] = "recipient@company.com"
   ```

3. **Use SMTP with TLS encryption**
   ```python
   with smtplib.SMTP("smtp.gmail.com", 587) as server:
       server.starttls()  # Encrypt connection
   ```

4. **Use app-specific passwords (Gmail)**
   - Go to https://myaccount.google.com/apppasswords
   - Generate a 16-character password
   - Use this in your code (not your regular password)

### ❌ DON'T DO THIS

1. **Don't send as plain text**
   ```python
   text_part = MIMEText(html_content, "plain")  # ❌ Wrong
   ```

2. **Don't hardcode passwords**
   ```python
   password = "myPassword123"  # ❌ Never do this!
   ```

3. **Don't copy-paste HTML into email body**
   ```python
   email_body = "<html>...</html>"  # ❌ Won't render as HTML
   ```

## Common SMTP Servers

### Gmail / Google Workspace

```python
smtp_server = "smtp.gmail.com"
smtp_port = 587
use_tls = True
sender_email = "your-email@gmail.com"
sender_password = "your-app-specific-password"  # 16-character password
```

### Office 365 / Outlook

```python
smtp_server = "smtp.office365.com"
smtp_port = 587
use_tls = True
sender_email = "your-email@company.com"
sender_password = "your-office365-password"
```

### Custom Corporate Mail Server

```python
smtp_server = "mail.company.com"
smtp_port = 587  # or 25 or 465 depending on server
use_tls = True
sender_email = "your-email@company.com"
sender_password = "your-password"
```

## Complete Example Script

Create a file `send_report.py`:

```python
#!/usr/bin/env python
"""Send DataQE Framework HTML report via email."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

def send_html_report(
    html_file_path,
    recipient_email,
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    sender_email=None,
    sender_password=None,
    sender_name="DataQE Framework",
    subject=None,
    custom_body=None,
    also_include_csv=None
):
    """
    Send HTML report via email with proper formatting.

    Args:
        html_file_path: Path to ExecutionReport.html
        recipient_email: Email to send to
        smtp_server: SMTP server (default: Gmail)
        smtp_port: SMTP port (default: 587)
        sender_email: Sender email address
        sender_password: Sender password or app-specific password
        sender_name: Display name (default: DataQE Framework)
        subject: Email subject (default: auto-generated)
        custom_body: Custom email body text
        also_include_csv: Optional path to CSV report
    """
    if not sender_email or not sender_password:
        raise ValueError("sender_email and sender_password are required")

    # Create message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject or f"Test Execution Report - {datetime.now().strftime('%Y-%m-%d')}"
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = recipient_email

    # Add text body
    body = custom_body or "Please find attached the Test Execution Report."
    text_part = MIMEText(body, "plain")
    msg.attach(text_part)

    # Attach HTML report
    with open(html_file_path, "rb") as attachment:
        html_part = MIMEBase("application", "octet-stream")
        html_part.set_payload(attachment.read())

    encoders.encode_base64(html_part)
    html_part.add_header(
        "Content-Disposition",
        "attachment; filename= ExecutionReport.html",
    )
    msg.attach(html_part)

    # Optionally attach CSV
    if also_include_csv:
        with open(also_include_csv, "rb") as attachment:
            csv_part = MIMEBase("application", "octet-stream")
            csv_part.set_payload(attachment.read())

        encoders.encode_base64(csv_part)
        csv_part.add_header(
            "Content-Disposition",
            "attachment; filename= ExecutionReport.csv",
        )
        msg.attach(csv_part)

    # Send email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        print(f"✅ Report sent successfully to {recipient_email}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed. Check your email and password.")
        return False

    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {e}")
        return False

    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False


if __name__ == "__main__":
    import os

    # Get credentials from environment variables
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    recipient = os.getenv("RECIPIENT_EMAIL", "recipient@company.com")

    if not sender_email or not sender_password:
        print("Error: Set SENDER_EMAIL and SENDER_PASSWORD environment variables")
        exit(1)

    # Send the report
    success = send_html_report(
        html_file_path="./output/ExecutionReport.html",
        recipient_email=recipient,
        sender_email=sender_email,
        sender_password=sender_password,
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        also_include_csv="./output/ExecutionReport.csv"
    )

    exit(0 if success else 1)
```

### Usage

```bash
# Set environment variables (don't hardcode them!)
export SENDER_EMAIL="your-email@gmail.com"
export SENDER_PASSWORD="your-app-specific-password"
export RECIPIENT_EMAIL="team@company.com"

# Run tests
dataqe-run --config config.yml --all-blocks

# Send report
python send_report.py
```

## Troubleshooting

### Problem: "Login unsuccessful"
**Cause**: Using regular Gmail password instead of app password
**Solution**: Get app password from https://myaccount.google.com/apppasswords

### Problem: "Connection timeout"
**Cause**: Firewall blocking SMTP port
**Solution**: Contact IT, or try port 465 with SSL instead of 587 with TLS

### Problem: "SMTP error: (535, b'5.7.8 Username and password not accepted')"
**Cause**: Incorrect credentials
**Solution**: Verify sender_email and sender_password are correct

### Problem: Email received but looks like attachment
**Cause**: Email client doesn't support HTML
**Solution**: The recipient's email client doesn't support HTML emails. Use text alternative.

## Security Best Practices

✅ **DO**
- Store credentials in environment variables
- Use app-specific passwords (Gmail)
- Use TLS encryption (port 587)
- Read credentials from `.env` file in production

✅ **DON'T**
- Hardcode passwords in source code
- Commit credentials to version control
- Send password in plain text
- Use simple passwords

## Integration with DataQE CLI

You can create a wrapper script that runs tests and sends reports:

```bash
#!/bin/bash

# Run DataQE tests
echo "Running tests..."
dataqe-run --config config.yml --all-blocks

# Check if tests completed successfully
if [ $? -eq 0 ]; then
    echo "Tests completed. Sending report..."
    python send_report.py
else
    echo "Tests failed. Skipping email."
    exit 1
fi
```

## HTML Report Quality

DataQE Framework generates reports with:

✅ **Proper HTML5 structure**
- Valid DOCTYPE declaration
- Complete head and body sections
- Semantic HTML elements

✅ **Professional styling**
- Color-coded test results
- Responsive layout
- Summary cards with metrics
- Execution metadata section
- Easy-to-read tables

✅ **Email-compatible CSS**
- Inline styles supported by email clients
- No external stylesheets
- Compatible with Outlook, Gmail, Apple Mail, etc.

The HTML files are production-ready and display beautifully in any email client when sent with the proper MIME type.

## Summary

To send DataQE Framework HTML reports via email:

1. ✅ Read the HTML file from `./output/ExecutionReport.html`
2. ✅ Create an email message with MIME type `text/html`
3. ✅ Set SMTP credentials (use environment variables)
4. ✅ Send via SMTP with TLS encryption
5. ✅ Verify recipient can open the email

The reports are already properly formatted - just send them with the correct email configuration!
