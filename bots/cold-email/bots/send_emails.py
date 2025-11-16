# bots/send_emails.py
import os
import json
import smtplib
import time
import pandas as pd
from email.message import EmailMessage
from dotenv import load_dotenv

# Load environment variables from a .env file in the project root
load_dotenv()

class EmailSender:
    """
    Handles sending emails based on a JSON file of generated content,
    updates lead statuses in a CSV, and logs sent emails.
    """
    def __init__(self, emails_file='data/emails-to-send.json', leads_file='data/qualified-leads.csv', log_file='data/sent_log.txt'):
        """
        Initializes the EmailSender with file paths and SMTP credentials from .env.
        """
        self.emails_file = emails_file
        self.leads_file = leads_file
        self.log_file = log_file
        
        # Get credentials from the .env file
        self.EMAIL_SERVER = os.getenv('SMTP_HOST')
        self.EMAIL_PORT = int(os.getenv('SMTP_PORT', 587)) # Default to 587 for TLS
        self.EMAIL_USER = os.getenv('SMTP_USER')
        self.EMAIL_PASS = os.getenv('SMTP_PASSWORD')

    def run(self, delay_seconds=5):
        """
        Main method to execute the email sending workflow.
        """
        print("\n--- 🏃 Running Email Sender ---")
        
        # 1. Validate SMTP Credentials
        if not all([self.EMAIL_SERVER, self.EMAIL_USER, self.EMAIL_PASS]):
            print("❌ Error: Email credentials (SMTP_HOST, SMTP_USER, SMTP_PASSWORD) are not fully set in the .env file.")
            print("Please check your .env file to ensure these variables are correct.")
            return

        # 2. Load Emails to Send
        try:
            with open(self.emails_file, 'r', encoding='utf-8') as f:
                emails_to_send = json.load(f)
            if not emails_to_send:
                print("🤷 No emails to send. The file is empty.")
                return
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"🤷 No emails found in '{self.emails_file}' or the file is invalid.")
            return

        # 3. Load Leads CSV to update statuses
        try:
            df = pd.read_csv(self.leads_file)
        except FileNotFoundError:
            print(f"❌ Error: Leads file '{self.leads_file}' not found. Cannot update statuses.")
            return

        print(f"📬 Found {len(emails_to_send)} email(s) to send...")
        
        # 4. Connect to SMTP Server and Send Emails
        successful_sends = 0
        try:
            # Use a 'with' statement for automatic connection closing
            with smtplib.SMTP(self.EMAIL_SERVER, self.EMAIL_PORT) as server:
                server.set_debuglevel(0) # Set to 1 for verbose connection details
                server.starttls()  # Upgrade connection to secure TLS
                server.login(self.EMAIL_USER, self.EMAIL_PASS)
                print(f"✅ Successfully connected to SMTP server ({self.EMAIL_SERVER}).")

                # Process each email
                for email_data in emails_to_send:
                    # Validate that the email_data dictionary has the required keys
                    required_keys = ['to_email', 'subject', 'body', 'website_url']
                    if not all(key in email_data for key in required_keys):
                        print(f"⚠️  Skipping an invalid email record. Missing keys: {email_data}")
                        continue
                        
                    # Create the email message object
                    msg = EmailMessage()
                    msg['Subject'] = email_data['subject']
                    msg['From'] = self.EMAIL_USER
                    msg['To'] = email_data['to_email']
                    # Set content with UTF-8 encoding for special character support
                    msg.set_content(email_data['body'], charset='utf-8')
                    
                    try:
                        server.send_message(msg)
                        print(f"🚀 Email sent successfully to {email_data['to_email']}")
                        
                        # Update status in the dataframe
                        df.loc[df['website_url'] == email_data['website_url'], 'status'] = 'email_sent'
                        
                        # Log the sent email for tracking
                        with open(self.log_file, 'a', encoding='utf-8') as log:
                            log.write(f"{time.ctime()}: Sent to {email_data['to_email']} for site {email_data['website_url']}\n")
                        
                        successful_sends += 1
                        print(f"    Waiting for {delay_seconds} seconds...")
                        time.sleep(delay_seconds) # Be respectful to the email server

                    except smtplib.SMTPException as e:
                        print(f"❌ Failed to send email to {email_data['to_email']}: {e}")

        except smtplib.SMTPAuthenticationError:
            print("❌ SMTP Authentication Error: Check your EMAIL_USER and EMAIL_PASS in the .env file.")
            return
        except ConnectionRefusedError:
            print(f"❌ Connection Refused: Could not connect to {self.EMAIL_SERVER} on port {self.EMAIL_PORT}. Check server/port and firewall settings.")
            return
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")
            return
        
        # 5. Save changes and clean up
        if successful_sends > 0:
            print(f"💾 Saving updated statuses to '{self.leads_file}'...")
            df.to_csv(self.leads_file, index=False)
            print("✅ Statuses updated.")
            
            # Clear the emails-to-send file as they have been processed
            print(f"🗑️ Clearing '{self.emails_file}'...")
            with open(self.emails_file, 'w') as f:
                f.write('[]') # Write an empty JSON array
            print("✅ File cleared.")
        else:
            print("No emails were sent, skipping file updates.")
            
        print("\n--- ✅ Email Sending Complete ---")

