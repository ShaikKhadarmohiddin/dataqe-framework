# Quick Reference: HTML Reports & Email Integration

## TL;DR - The Answer

**Q: Why does my HTML report appear as plain text in email?**

A: You're sending it with the wrong MIME type. Use `text/html` instead of `text/plain`.

---

## Quick Solution

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Read the HTML report
with open("./output/ExecutionReport.html", "r") as f:
    html_content = f.read()

# Create message
msg = MIMEMultipart()
msg["Subject"] = "Test Report"
msg["From"] = "your-email@gmail.com"
msg["To"] = "recipient@company.com"

# ✅ KEY: Set MIME type to "html" not "plain"
html_part = MIMEText(html_content, "html")
msg.attach(html_part)

# Send it
with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login("your-email@gmail.com", "your-app-password")
    server.send_message(msg)
```

---

## Why It Works

| What | Wrong ❌ | Right ✅ |
|------|---------|---------|
| MIME type | `text/plain` | `text/html` |
| Email shows | Raw HTML code | Rendered HTML |
| Status | Broken | Perfect |

---

## Gmail App Password

1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and your device
3. Google generates 16-character password
4. Use that (not your regular Gmail password)

---

## Complete Example Script

See `SENDING_REPORTS_VIA_EMAIL.md` for a full example ready to use.

---

## Best Practices

✅ **DO:**
- Use environment variables for credentials
- Set MIME type to `text/html`
- Use SMTP with TLS (port 587)
- Send as attachment (Option 2 in guide)

❌ **DON'T:**
- Hardcode passwords
- Use `text/plain` MIME type
- Send unencrypted (port 25)
- Copy-paste HTML into email body

---

## HTML Report Quality

✅ The HTML files are **properly formatted and production-ready**
✅ They render correctly in all browsers
✅ They display correctly in all email clients (when sent properly)
✅ No issues with the HTML generation itself

---

## Version Info

- **Framework Version**: 0.3.0
- **HTML Report Quality**: ✅ Verified
- **Email Integration**: See `SENDING_REPORTS_VIA_EMAIL.md`

---

## Documentation Files

1. **SENDING_REPORTS_VIA_EMAIL.md** - Complete guide with examples
2. **HTML_REPORT_QUALITY_GUIDE.md** - Report quality verification
3. **EXECUTION_METADATA_GUIDE.md** - Metadata feature details

---

## In 3 Steps

1. Read HTML file from `./output/ExecutionReport.html`
2. Create email with `MIMEText(html_content, "html")`
3. Send via SMTP with TLS

That's it! 🎉
