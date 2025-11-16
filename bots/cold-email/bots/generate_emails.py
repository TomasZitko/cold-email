# bots/generate_emails.py
import os
import pandas as pd
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class EmailGenerator:
    def __init__(self, leads_file='data/qualified-leads.csv', templates_file='data/email-templates.txt', output_file='data/emails-to-send.json'):
        self.leads_file = leads_file
        self.templates_file = templates_file
        self.output_file = output_file
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.templates = self._load_templates()

    def _load_templates(self):
        try:
            with open(self.templates_file, 'r') as f: content = f.read()
            templates = {}
            # Split by a clear delimiter
            for block in content.split('---TEMPLATE---'):
                if 'CATEGORY:' in block:
                    category = block.split('CATEGORY:')[1].split('\n')[0].strip().lower()
                    templates[category] = block
            print(f"✅ Loaded {len(templates)} email templates.")
            return templates
        except FileNotFoundError:
            print(f"❌ Templates file not found at '{self.templates_file}'. Cannot generate emails."); return {}

    def run(self):
        print("\n--- Running Email Generator ---")
        if not self.templates: return
        try:
            df = pd.read_csv(self.leads_file)
        except FileNotFoundError:
            print(f"🤷 Leads file '{self.leads_file}' not found. No leads to process."); return

        # Filter for leads that need an email
        new_leads = df[df['status'] == 'new'].to_dict('records')
        if not new_leads:
            print("🤷 No new leads to generate emails for."); return
        
        print(f"Found {len(new_leads)} new leads to process...")
        generated_emails = []

        for lead in new_leads:
            print(f"📧 Generating email for {lead['website_url']}...")
            
            # Select template, fallback to a 'default' template if specific one isn't found
            category = lead.get('business_category', 'default').lower()
            template = self.templates.get(category, self.templates.get('default'))
            if not template:
                print(f"⚠️ No template for category '{category}' or default. Skipping."); continue

            prompt = f"""
            Based on this template and lead information, generate a compelling, personalized cold email subject and body.
            Be friendly, slightly informal, and professional. Keep it concise.
            
            LEAD INFO:
            - Website: {lead['website_url']}
            - Issues Found: {lead['issues']}
            - Business Category: {lead['business_category']}
            
            TEMPLATE:
            {template}
            
            Generate the Subject and Body. Respond in JSON format like this: {{"subject": "Your Subject", "body": "Your email body..."}}
            """
            
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4-turbo",
                    response_format={"type": "json_object"},
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                email_content = json.loads(response.choices[0].message.content)
                
                generated_emails.append({
                    "to_email": lead['contact_email'],
                    "website_url": lead['website_url'], # For linking back
                    "subject": email_content['subject'],
                    "body": email_content['body']
                })
                # IMPORTANT: Mark this lead as processed in the dataframe
                df.loc[df['website_url'] == lead['website_url'], 'status'] = 'email_generated'
                print(f"   -> Success.")
            except Exception as e:
                print(f"   -> ❌ AI generation failed: {e}")

        if generated_emails:
            with open(self.output_file, 'w') as f:
                json.dump(generated_emails, f, indent=4)
            print(f"\n✅ Saved {len(generated_emails)} new emails to '{self.output_file}'.")
        
        # IMPORTANT: Save the updated dataframe with new statuses
        df.to_csv(self.leads_file, index=False)
        print(f"🔄 Updated statuses in '{self.leads_file}'.")