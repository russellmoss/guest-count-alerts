# GitHub Actions Deployment Checklist

## ✅ Ready for Deployment!

Your guest count alert system is ready to deploy to GitHub Actions. Here's what you need to do:

## 1. Create GitHub Repository

```bash
git init
git add .
git commit -m "Initial commit - Guest count alert system"
git remote add origin https://github.com/yourusername/guest-count-alerts.git
git push -u origin main
```

## 2. Configure GitHub Secrets

Go to your repository → Settings → Secrets and variables → Actions, and add these secrets:

### Commerce7 API Credentials
- `C7_APP_ID` = `your_commerce7_app_id`
- `C7_API_KEY` = `your_commerce7_api_key`
- `C7_TENANT_ID` = `your_commerce7_tenant_id`

### Twilio SMS Credentials
- `TWILIO_ACCOUNT_SID` = `your_twilio_account_sid`
- `TWILIO_AUTH_TOKEN` = `your_twilio_auth_token`
- `TWILIO_PHONE_NUMBER` = `your_twilio_phone_number`

### Alert Recipients
- `EMAIL_1` = `your_email@example.com`
- `EMAIL_2` = `manager2@example.com` (optional - add second email recipient)
- `PHONE_1` = `+1234567890`
- `PHONE_2` = `+1234567891` (optional - add second phone recipient)

### SMTP Email Configuration
- `SMTP_EMAIL` = `your_email@example.com`
- `SMTP_PASSWORD` = `your_app_specific_password_here` (Gmail app password)

## 3. Enable GitHub Actions

1. Go to the Actions tab in your repository
2. Enable workflows if prompted
3. The workflow will run automatically every 15 minutes
4. You can also trigger it manually from the Actions tab

## 4. Test the Deployment

1. Go to Actions tab
2. Click "Guest Count Check" workflow
3. Click "Run workflow" to test manually
4. Check the logs to ensure it runs successfully

## 5. Monitor the System

- Check Actions tab for workflow runs
- Look for any failed runs in the logs
- Verify you receive alerts when testing

## Files Included

- ✅ `guest-count-alert-script.py` - Main script
- ✅ `requirements.txt` - Python dependencies
- ✅ `.github/workflows/guest-count-check.yml` - GitHub Actions workflow
- ✅ `env-template.txt` - Environment variables template
- ✅ `setup-instructions.md` - Local setup instructions

## What the System Does

1. **Runs every 15 minutes** via GitHub Actions
2. **Checks Commerce7 orders** from the last 15 minutes
3. **Monitors 3 tasting products**:
   - `3ecdff78-cc2a-495c-a795-ec651e04025e`
   - `8a1a61b5-6840-4540-8849-71db10b01bd7`
   - `ffa635a6-9038-4360-a532-96b539006400`
4. **Sends alerts** for orders with missing guest counts
5. **Converts UTC to EST** for accurate local time display
6. **Supports multiple recipients** - automatically sends to all configured emails and phones

## Multiple Recipients

The system automatically supports multiple recipients:

- **Emails**: `EMAIL_1`, `EMAIL_2`, `EMAIL_3`, etc.
- **Phones**: `PHONE_1`, `PHONE_2`, `PHONE_3`, etc.

Just add the secrets in GitHub and the system will automatically send alerts to all configured recipients. You can add as many as you need by incrementing the numbers.

## Alert Messages

**Email**: "Russell Moss just completed a tasting without a guest count. Order Details: • Order Number: 42632 • Date/Time: September 04, 2025 at 07:27 PM EST • Customer: [name] • Total Amount: $[amount] • Products: Milea Tasting"

**SMS**: "Russell Moss just did a tasting without a guest count. Order #42632 occurred on 09/04 at 07:27PM EST. Please remind them to input guest count data."

## Troubleshooting

- Check GitHub Actions logs for errors
- Verify all secrets are set correctly
- Ensure Gmail app password is valid
- Check Twilio account balance
