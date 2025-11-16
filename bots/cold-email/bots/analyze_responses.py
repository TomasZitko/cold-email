import os
import imaplib
import email
import pandas as pd
from dotenv import load_dotenv
from notion_client import Client

class ResponseAnalyzer:
    def __init__(self, qualified_leads_file='data/qualified-leads.csv'):
        load_dotenv()
        self.leads_df = pd.read_csv(qualified_leads_file)
        self.notion = None
        if os.getenv('NOTION_API_KEY') and os.getenv('NOTION_DATABASE_ID'):
            self.notion = Client(auth=os.getenv('NOTION_API_KEY'))
            self.database_id = os.getenv('NOTION_DATABASE_ID')
        
        self.imap_config = {
            'host': os.getenv('IMAP_HOST'),
            'user': os.getenv('IMAP_USER'),
            'password': os.getenv('IMAP_PASSWORD')
        }
        if not all(self.imap_config.values()):
            raise ValueError("IMAP configuration is missing in .env file.")

    def check_inbox(self):
        print("\n--- Checking for Email Responses ---")
        positive_keywords = ['mám zájem', 'pošlete mi to', 'zní to dobře', 'kdy máte čas', 'call', 'meeting']
        
        try:
            mail = imaplib.IMAP4_SSL(self.imap_config['host'])
            mail.login(self.imap_config['user'], self.imap_config['password'])
            mail.select('inbox')
            
            # Search for unseen emails
            status, messages = mail.search(None, 'UNSEEN')
            if status != 'OK':
                print("No new messages found.")
                return

            for num in messages[0].split():
                status, data = mail.fetch(num, '(RFC822)')
                if status != 'OK':
                    continue
                
                msg = email.message_from_bytes(data[0][1])
                from_address = email.utils.parseaddr(msg['From'])[1]
                
                # Check if the sender is in our qualified leads
                if from_address in self.leads_df['contact_email'].values:
                    subject = msg['subject']
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == 'text/plain':
                                body = part.get_payload(decode=True).decode()
                                break
                    else:
                        body = msg.get_payload(decode=True).decode()

                    # Simple keyword check for positive response
                    if any(keyword in body.lower() or keyword in subject.lower() for keyword in positive_keywords):
                        print(f"✅ Positive response from {from_address}!")
                        lead_info = self.leads_df[self.leads_df['contact_email'] == from_address].iloc[0]
                        self.add_to_notion(lead_info)
            
            mail.logout()
        except Exception as e:
            print(f"❌ Error checking inbox: {e}")

    def add_to_notion(self, lead_info):
        if not self.notion:
            print("Notion integration not configured. Skipping.")
            return
        
        print(f"📝 Adding {lead_info['business_name']} to Notion...")
        try:
            self.notion.pages.create(
                parent={"database_id": self.database_id},
                properties={
                    "Name": {"title": [{"text": {"content": lead_info['business_name']}}]},
                    "Website": {"url": lead_info['website_url']},
                    "Email": {"email": lead_info['contact_email']},
                    "Status": {"select": {"name": "Positive Reply"}},
                    "Issues": {"rich_text": [{"text": {"content": lead_info['all_issues']}}]}
                }
            )
            print("✅ Successfully added to Notion.")
        except Exception as e:
            print(f"❌ Error adding to Notion: {e}")