# Guest Count Alert System

This system monitors Commerce7 orders for missing guest counts and sends email/SMS alerts to managers when orders are placed without guest count information.

## 🚀 Quick Start

### Turning the Script ON/OFF

The script can be easily enabled or disabled using a simple toggle:

#### To TURN OFF the script:
1. Go to your GitHub repository: `russellmoss/guest-count-alerts`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Find the secret named `SCRIPT_ENABLED`
4. Set its value to: `false`
5. The script will stop running on the next scheduled check

#### To TURN ON the script:
1. Go to your GitHub repository: `russellmoss/guest-count-alerts`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Find the secret named `SCRIPT_ENABLED`
4. Set its value to: `true`
5. The script will resume running on the next scheduled check

### Valid Values for SCRIPT_ENABLED:
- **ON**: `true`, `1`, `yes`, `on` (case insensitive)
- **OFF**: `false`, `0`, `no`, `off` (case insensitive)
- **Default**: If not set, the script defaults to **ON**

## 📋 How It Works

- **Schedule**: Runs every 15 minutes via GitHub Actions
- **Monitoring**: Checks Commerce7 orders for missing guest counts
- **Alerts**: Sends email and SMS notifications when issues are found
- **Deduplication**: Prevents duplicate alerts for the same order
- **Persistence**: Remembers previous runs and alerted orders

## 🔧 Configuration

### Required GitHub Secrets:
- `SCRIPT_ENABLED` - Controls if the script runs (true/false)
- `C7_APP_ID` - Commerce7 API App ID
- `C7_API_KEY` - Commerce7 API Key
- `C7_TENANT_ID` - Commerce7 Tenant ID
- `TWILIO_ACCOUNT_SID` - Twilio Account SID
- `TWILIO_AUTH_TOKEN` - Twilio Auth Token
- `TWILIO_PHONE_NUMBER` - Twilio Phone Number
- `EMAIL_1` - Email address to receive alerts
- `PHONE_1` - Phone number to receive SMS alerts
- `SMTP_EMAIL` - SMTP email for sending alerts
- `SMTP_PASSWORD` - SMTP password for sending alerts

## 📊 Monitoring

Check the **Actions** tab in your GitHub repository to see:
- When the script last ran
- Whether it's currently enabled or disabled
- Any errors or issues
- Log output from each run

## 🛠️ Troubleshooting

### Script Not Running?
1. Check if `SCRIPT_ENABLED` is set to `true`
2. Verify all required secrets are configured
3. Check the Actions tab for error messages

### Getting Too Many Alerts?
1. The script has built-in deduplication
2. Check if the same order is being processed multiple times
3. Review the logs in the Actions tab

### Need to Pause for Maintenance?
1. Set `SCRIPT_ENABLED` to `false`
2. The script will stop running but preserve all data
3. Set back to `true` when ready to resume

## 📝 Log Messages

When the script runs, you'll see these key messages:
- `✅ Script is ENABLED - proceeding with checks...` - Script is running normally
- `🚫 Script is DISABLED via SCRIPT_ENABLED environment variable` - Script is turned off
- `No orders found in the time window since last run` - No new orders to check
- `Sending alert for order #XXXXX` - Alert being sent for missing guest count

## 🔄 Manual Testing

You can manually trigger the script by:
1. Going to **Actions** tab in GitHub
2. Clicking on **Guest Count Check** workflow
3. Clicking **Run workflow** button
4. This will run the script immediately regardless of schedule
