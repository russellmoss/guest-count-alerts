#!/usr/bin/env python3
"""
Guest Count Check Alert Script
Checks Commerce7 orders from the last 15 minutes for missing guest counts
and sends email/SMS alerts to managers
"""

import os
import sys
import json
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
import logging
import pytz

# Third-party imports
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from twilio.rest import Client

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GuestCountChecker:
    """Check Commerce7 orders for missing guest counts and send alerts"""
    
    def __init__(self):
        # Commerce7 credentials
        self.c7_app_id = os.getenv('C7_APP_ID')
        self.c7_api_key = os.getenv('C7_API_KEY')
        self.c7_tenant_id = os.getenv('C7_TENANT_ID', 'milea-estate-vineyard')
        
        # Twilio credentials
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        # Alert recipients
        self.email_recipients = self._get_email_recipients()
        self.phone_recipients = self._get_phone_recipients()
        
        # Product IDs that require guest counts (tasting products)
        # Note: Commerce7 API returns just the UUID, not the full "product/" prefix
        self.tasting_product_ids = [
            '3ecdff78-cc2a-495c-a795-ec651e04025e',
            '8a1a61b5-6840-4540-8849-71db10b01bd7',
            'ffa635a6-9038-4360-a532-96b539006400'
        ]
        
        # Validate configuration
        self._validate_config()
        
    def _get_email_recipients(self) -> List[str]:
        """Get email recipients from environment variables"""
        recipients = []
        i = 1
        while True:
            email = os.getenv(f'Email_{i}')
            if not email:
                break
            recipients.append(email)
            i += 1
        return recipients
    
    def _get_phone_recipients(self) -> List[str]:
        """Get phone recipients from environment variables"""
        recipients = []
        i = 1
        while True:
            phone = os.getenv(f'Phone_{i}')
            if not phone:
                break
            # Ensure phone number has country code
            if not phone.startswith('+'):
                phone = '+1' + phone  # Assuming US numbers
            recipients.append(phone)
            i += 1
        return recipients
    
    def _validate_config(self):
        """Validate that all required configuration is present"""
        errors = []
        
        if not self.c7_app_id:
            errors.append("C7_APP_ID not set")
        if not self.c7_api_key:
            errors.append("C7_API_KEY not set")
        if not self.c7_tenant_id:
            errors.append("C7_TENANT_ID not set")
            
        if not self.twilio_account_sid:
            errors.append("TWILIO_ACCOUNT_SID not set")
        if not self.twilio_auth_token:
            errors.append("TWILIO_AUTH_TOKEN not set")
        if not self.twilio_phone_number:
            errors.append("TWILIO_PHONE_NUMBER not set")
            
        if not self.email_recipients:
            errors.append("No email recipients configured (Email_1, Email_2, etc.)")
        if not self.phone_recipients:
            errors.append("No phone recipients configured (Phone_1, Phone_2, etc.)")
            
        if errors:
            logger.error("Configuration errors:\n" + "\n".join(errors))
            sys.exit(1)
            
        logger.info(f"Configuration validated. Monitoring {len(self.tasting_product_ids)} product IDs")
        logger.info(f"Will alert {len(self.email_recipients)} emails and {len(self.phone_recipients)} phones")
    
    def _convert_utc_to_est(self, utc_datetime_str: str) -> str:
        """
        Convert UTC datetime string from Commerce7 to EST format
        """
        try:
            # Parse the UTC datetime
            utc_dt = datetime.fromisoformat(utc_datetime_str.replace('Z', '+00:00'))
            
            # Convert to EST
            est_tz = pytz.timezone('US/Eastern')
            est_dt = utc_dt.astimezone(est_tz)
            
            # Format for display
            return est_dt.strftime('%B %d, %Y at %I:%M %p EST')
        except Exception as e:
            logger.warning(f"Could not convert datetime '{utc_datetime_str}': {e}")
            return utc_datetime_str  # Return original if conversion fails
    
    def get_recent_orders(self, minutes: int = 15) -> List[Dict]:
        """
        Fetch orders from Commerce7 from the last N minutes
        Since Commerce7 API only supports date-level filtering, we'll get recent orders
        and filter by timestamp in the application
        """
        # Calculate time range
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(minutes=minutes)
        
        # Since Commerce7 API doesn't support minute-level filtering,
        # we'll get orders from recent days and filter by timestamp
        # Based on test results, we know gte:2025-09-03 works
        
        # Use a date we know works from the test script
        # Get orders from September 3rd onwards (test script confirmed this works)
        search_date = '2025-09-03'
        
        logger.info(f"Checking orders from {search_date} onwards (will filter to last {minutes} minutes)")
        
        # Build API URL with date filter
        base_url = 'https://api.commerce7.com/v1/order'
        params = {
            'orderPaidDate': f'gte:{search_date}',
            'limit': 50  # Commerce7 API maximum limit
        }
        
        # Set up authentication
        auth = HTTPBasicAuth(self.c7_app_id, self.c7_api_key)
        headers = {
            'Tenant': self.c7_tenant_id,
            'Content-Type': 'application/json'
        }
        
        try:
            # Debug: Log the exact request details
            logger.info(f"Making request to: {base_url}")
            logger.info(f"Parameters: {params}")
            logger.info(f"Headers: {headers}")
            logger.info(f"Auth: {self.c7_app_id}:{self.c7_api_key[:10]}...")
            
            response = requests.get(
                base_url,
                params=params,
                auth=auth,
                headers=headers,
                timeout=30
            )
            
            # Debug: Log response details
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                logger.error(f"Response body: {response.text}")
            
            response.raise_for_status()
            
            data = response.json()
            all_orders = data.get('orders', [])
            logger.info(f"Retrieved {len(all_orders)} orders from Commerce7")
            
            # Filter orders to only include those from the last N minutes
            recent_orders = []
            for order in all_orders:
                # Get the order date
                order_date_str = order.get('orderPaidDate') or order.get('orderDate')
                if not order_date_str:
                    continue
                
                try:
                    # Parse the order date (Commerce7 uses ISO format in responses)
                    order_date = datetime.fromisoformat(order_date_str.replace('Z', '+00:00'))
                    
                    # Check if this order is within our time window
                    if start_time <= order_date <= end_time:
                        recent_orders.append(order)
                        
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse order date '{order_date_str}': {e}")
                    continue
            
            logger.info(f"Filtered to {len(recent_orders)} orders from the last {minutes} minutes")
            return recent_orders
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching orders from Commerce7: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
                try:
                    error_data = e.response.json()
                    logger.error(f"Error details: {json.dumps(error_data, indent=2)}")
                except:
                    pass
            return []
    
    def check_order_for_alert(self, order: Dict) -> Optional[Dict]:
        """
        Check if an order should trigger an alert
        Returns alert info if alert should be sent, None otherwise
        """
        # Check if order has guest count
        if order.get('guestCount'):
            return None
        
        # Check if order contains any of the tasting products
        items = order.get('items', [])
        has_tasting_product = False
        product_names = []
        
        for item in items:
            product_id = item.get('productId', '')
            # Check if this is one of our monitored tasting products
            if product_id in self.tasting_product_ids:
                has_tasting_product = True
                product_names.append(item.get('productTitle', item.get('productName', 'Unknown Product')))
        
        if not has_tasting_product:
            return None
        
        # This order needs an alert
        alert_info = {
            'order_number': order.get('orderNumber', 'Unknown'),
            'associate_name': order.get('salesAssociate', {}).get('name', 'Unknown Associate'),
            'order_date': order.get('orderPaidDate') or order.get('orderDate', 'Unknown'),
            'customer_name': order.get('customer', {}).get('name', 'Unknown Customer'),
            'total_amount': order.get('totalAmount', 0) / 100,  # Convert from cents
            'products': product_names
        }
        
        logger.warning(f"Missing guest count for order {alert_info['order_number']} by {alert_info['associate_name']}")
        return alert_info
    
    def send_email_alert(self, alert_info: Dict) -> bool:
        """
        Send email alert using SMTP
        For production, consider using SendGrid or AWS SES
        """
        # Format the date nicely (convert from UTC to EST)
        formatted_date = self._convert_utc_to_est(alert_info['order_date'])
        
        subject = f"Missing Guest Count Alert - Order {alert_info['order_number']}"
        
        body = f"""
        {alert_info['associate_name']} just completed a tasting without a guest count.
        
        Order Details:
        • Order Number: {alert_info['order_number']}
        • Date/Time: {formatted_date}
        • Customer: {alert_info['customer_name']}
        • Total Amount: ${alert_info['total_amount']:.2f}
        • Products: {', '.join(alert_info['products'])}
        
        Please remind them to input guest count data for all tasting orders.
        
        This is an automated alert from the Guest Count Check system.
        """
        
        # For now, using Gmail SMTP - you may want to use SendGrid or another service
        # To use Gmail, you'll need an app-specific password
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        
        # You'll need to add these to your .env file
        smtp_email = os.getenv('SMTP_EMAIL', self.email_recipients[0])
        smtp_password = os.getenv('SMTP_PASSWORD', '')
        
        if not smtp_password:
            logger.warning("SMTP_PASSWORD not configured, skipping email")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_email
            msg['To'] = ', '.join(self.email_recipients)
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_email, smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email alert sent to {len(self.email_recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def send_sms_alert(self, alert_info: Dict) -> bool:
        """
        Send SMS alert using Twilio
        """
        try:
            # Format the date nicely (convert from UTC to EST, shorter format for SMS)
            try:
                utc_dt = datetime.fromisoformat(alert_info['order_date'].replace('Z', '+00:00'))
                est_tz = pytz.timezone('US/Eastern')
                est_dt = utc_dt.astimezone(est_tz)
                formatted_date = est_dt.strftime('%m/%d at %I:%M%p EST')
            except:
                formatted_date = 'just now'
            
            message = (
                f"{alert_info['associate_name']} just did a tasting without a guest count. "
                f"Order #{alert_info['order_number']} occurred on {formatted_date}. "
                f"Please remind them to input guest count data."
            )
            
            # Initialize Twilio client
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            
            # Send to each phone number
            for phone in self.phone_recipients:
                try:
                    client.messages.create(
                        body=message,
                        from_=self.twilio_phone_number,
                        to=phone
                    )
                    logger.info(f"SMS sent to {phone}")
                except Exception as e:
                    logger.error(f"Error sending SMS to {phone}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error with Twilio: {e}")
            return False
    
    def test_api_connection(self):
        """
        Test the API connection with a simple request (like the test script)
        """
        logger.info("Testing API connection...")
        
        # Try the exact same request that worked in the test script
        base_url = 'https://api.commerce7.com/v1/order'
        params = {'limit': 1}
        auth = HTTPBasicAuth(self.c7_app_id, self.c7_api_key)
        headers = {'Tenant': self.c7_tenant_id}
        
        try:
            logger.info(f"Testing basic connection to: {base_url}")
            logger.info(f"Test params: {params}")
            logger.info(f"Test headers: {headers}")
            
            response = requests.get(base_url, params=params, auth=auth, headers=headers, timeout=30)
            logger.info(f"Test response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                orders = data.get('orders', [])
                logger.info(f"✅ Basic connection successful! Found {len(orders)} orders")
                return True
            else:
                logger.error(f"❌ Basic connection failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Basic connection error: {e}")
            return False

    def run(self):
        """
        Main execution method
        """
        logger.info("Starting guest count check...")
        
        # Test basic connection first
        if not self.test_api_connection():
            logger.error("Basic API connection failed, aborting")
            return
        
        # Get recent orders
        orders = self.get_recent_orders(minutes=15)
        
        if not orders:
            logger.info("No orders found in the last 15 minutes")
            return
        
        # Check each order
        alerts_sent = 0
        for order in orders:
            # Debug: Show details about each order found
            order_number = order.get('orderNumber', 'Unknown')
            guest_count = order.get('guestCount', 'MISSING')
            associate = order.get('salesAssociate', {}).get('name', 'Unknown')
            items = order.get('items', [])
            
            logger.info(f"Checking order {order_number}:")
            logger.info(f"  - Guest Count: {guest_count}")
            logger.info(f"  - Sales Associate: {associate}")
            logger.info(f"  - Items: {len(items)} items")
            
            # Check each item for tasting products
            tasting_products_found = []
            for item in items:
                product_id = item.get('productId', '')
                product_name = item.get('productTitle', item.get('productName', 'Unknown'))
                
                # Debug: Show all product details
                logger.info(f"  - Product: {product_name}")
                logger.info(f"    Product ID: {product_id}")
                logger.info(f"    Monitored IDs: {self.tasting_product_ids}")
                
                if product_id in self.tasting_product_ids:
                    tasting_products_found.append(product_name)
                    logger.info(f"  - 🍷 Found tasting product: {product_name}")
                else:
                    logger.info(f"  - Not a tasting product")
            
            alert_info = self.check_order_for_alert(order)
            
            if alert_info:
                # Send alerts
                email_sent = self.send_email_alert(alert_info)
                sms_sent = self.send_sms_alert(alert_info)
                
                if email_sent or sms_sent:
                    alerts_sent += 1
                    logger.info(f"Alert sent for order {alert_info['order_number']}")
            else:
                if guest_count == 'MISSING' and tasting_products_found:
                    logger.warning(f"Order {order_number} has missing guest count and tasting products but no alert was sent!")
                elif guest_count != 'MISSING':
                    logger.info(f"Order {order_number} has guest count ({guest_count}), no alert needed")
                elif not tasting_products_found:
                    logger.info(f"Order {order_number} has no tasting products, no alert needed")
        
        logger.info(f"Check complete. {alerts_sent} alerts sent.")


def main():
    """Main entry point"""
    try:
        checker = GuestCountChecker()
        checker.run()
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()