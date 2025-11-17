# bots/generate_emails.py
import os
import pandas as pd
import json
import re
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, List, Optional

load_dotenv()

class EmailGenerator:
    def __init__(self, leads_file='data/qualified-leads.csv', templates_file='data/email-templates.txt', output_file='data/emails-to-send.json'):
        self.leads_file = leads_file
        self.templates_file = templates_file
        self.output_file = output_file
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.templates = self._load_templates()

        # Sales configuration
        self.sender_name = os.getenv("SENDER_NAME", "Váš Web Expert")
        self.sender_company = os.getenv("SENDER_COMPANY", "WebDesign Pro")
        self.portfolio_link = os.getenv("PORTFOLIO_LINK", "https://yourportfolio.com")

    def _load_templates(self):
        """Load email templates with metadata parsing"""
        try:
            with open(self.templates_file, 'r', encoding='utf-8') as f:
                content = f.read()

            templates = []
            for block in content.split('---TEMPLATE---'):
                if 'CATEGORY:' in block:
                    template_data = self._parse_template_block(block)
                    if template_data:
                        templates.append(template_data)

            print(f"✅ Loaded {len(templates)} email templates.")
            return templates
        except FileNotFoundError:
            print(f"❌ Templates file not found at '{self.templates_file}'. Cannot generate emails.")
            return []

    def _parse_template_block(self, block: str) -> Optional[Dict]:
        """Parse a template block to extract metadata and content"""
        try:
            lines = block.strip().split('\n')
            metadata = {}
            content_start = 0

            for i, line in enumerate(lines):
                if ':' in line and not line.startswith('SUBJECT:'):
                    key, value = line.split(':', 1)
                    metadata[key.strip().lower()] = value.strip()
                elif line.startswith('SUBJECT:'):
                    content_start = i
                    break

            content = '\n'.join(lines[content_start:]).strip()

            return {
                'category': metadata.get('category', 'default'),
                'priority': metadata.get('priority', 'medium'),
                'framework': metadata.get('framework', 'generic'),
                'sequence': metadata.get('sequence', '0'),
                'content': content
            }
        except Exception as e:
            print(f"⚠️ Error parsing template block: {e}")
            return None

    def _select_template(self, lead: Dict) -> Optional[Dict]:
        """Select the best template based on lead priority and score"""
        score = lead.get('score', 50)
        priority = lead.get('priority', 'MEDIUM')

        # High priority leads (70+) get custom-demo templates
        if score >= 70 or priority == 'HIGH':
            target_category = 'custom-demo'
        # Medium priority (40-69) get portfolio-showcase
        elif score >= 40:
            target_category = 'portfolio-showcase'
        # Low priority get portfolio-showcase (lighter touch)
        else:
            target_category = 'portfolio-showcase'

        # Filter templates by category
        matching_templates = [t for t in self.templates if t['category'] == target_category and t.get('sequence', '0') == '0']

        if not matching_templates:
            # Fallback to any available template
            matching_templates = [t for t in self.templates if t.get('sequence', '0') == '0']

        # Return a random template from matches (or first if only one)
        import random
        return random.choice(matching_templates) if matching_templates else None

    def _extract_lead_insights(self, lead: Dict) -> Dict:
        """Extract actionable sales insights from lead data"""
        insights = {
            'company_name': lead.get('name', 'Vaše firma'),
            'first_name': lead.get('name', '').split()[0] if lead.get('name') else 'kolego',
            'website_url': lead.get('website_url', ''),
            'industry': lead.get('business_category', 'váš obor'),
            'score': lead.get('score', 50),
            'priority': lead.get('priority', 'MEDIUM'),
        }

        # Parse issues found on website
        issues_raw = lead.get('issues', '')
        if issues_raw and issues_raw != 'None':
            insights['has_issues'] = True
            insights['issues'] = issues_raw
            # Count critical issues
            critical_keywords = ['slow', 'pomalý', 'flash', 'broken', 'mobile', 'ssl', 'https']
            insights['critical_issues'] = sum(1 for kw in critical_keywords if kw.lower() in issues_raw.lower())
        else:
            insights['has_issues'] = False
            insights['issues'] = 'žádné zjevné problémy'
            insights['critical_issues'] = 0

        # Estimate lost revenue based on score and issues
        if insights['critical_issues'] >= 3:
            insights['estimated_lost_revenue'] = '50,000'
        elif insights['critical_issues'] >= 2:
            insights['estimated_lost_revenue'] = '30,000'
        else:
            insights['estimated_lost_revenue'] = '15,000'

        # Determine conversion improvement potential
        if insights['score'] < 40:
            insights['conversion_potential'] = '50-70'
        elif insights['score'] < 60:
            insights['conversion_potential'] = '30-50'
        else:
            insights['conversion_potential'] = '20-30'

        return insights

    def _create_professional_prompt(self, lead: Dict, template: Dict, insights: Dict) -> str:
        """Create a professional sales-oriented AI prompt"""
        framework = template.get('framework', 'generic')

        prompt = f"""You are an EXPERT web design salesperson with a proven track record of closing high-value clients.

Your task: Generate a highly personalized, conversion-focused cold email using the {framework} framework.

=== LEAD INTELLIGENCE ===
Company: {insights['company_name']}
Website: {insights['website_url']}
Industry: {insights['industry']}
Lead Score: {insights['score']}/100 (Priority: {insights['priority']})
Critical Issues Found: {insights['critical_issues']}
Issues Detail: {insights['issues']}
Estimated Monthly Lost Revenue: {insights['estimated_lost_revenue']} Kč
Conversion Improvement Potential: {insights['conversion_potential']}%

=== YOUR OBJECTIVE ===
Write an email that:
1. **Hooks immediately** - Make them curious in the first sentence
2. **Identifies SPECIFIC pain points** - Use the issues found on their website
3. **Quantifies the problem** - Show them what they're losing (money, customers, credibility)
4. **Presents a clear solution** - Position the redesign as the answer
5. **Builds trust with proof** - Include realistic case study metrics
6. **Ends with a soft CTA** - Non-pushy, low-commitment ask

=== PROVEN SALES TECHNIQUES TO USE ===
- **Problem-Agitate-Solution (PAS)**: Identify problem → Make it hurt → Offer solution
- **Specificity Sells**: Use exact numbers, specific examples, concrete details
- **Social Proof**: Reference similar clients (use placeholder like "klient v podobném oboru")
- **Loss Aversion**: Focus on what they're LOSING by not acting
- **Soft CTA**: Ask for 10-15 minute call, not "buy now"

=== TEMPLATE TO ADAPT ===
{template['content']}

=== STYLE GUIDELINES ===
- Language: Czech (professional but friendly)
- Tone: Consultative expert, NOT pushy salesperson
- Length: Subject (5-8 words) + Body (150-200 words max)
- Personalization: Use their company name 2-3 times naturally
- NO generic statements - every sentence should be specific to them
- NO ALL CAPS or excessive punctuation (!!!)
- Use bullet points for clarity when listing issues/benefits

=== OUTPUT FORMAT ===
Respond ONLY with valid JSON:
{{
    "subject": "Your compelling subject line here",
    "body": "Your personalized email body here"
}}

CRITICAL: Make this email feel like it was written specifically for {insights['company_name']} by someone who actually reviewed their website. This is NOT a template - it's a personalized consultation.
"""
        return prompt

    def run(self):
        print("\n=== 🚀 PROFESSIONAL EMAIL GENERATOR ===\n")
        if not self.templates:
            print("❌ No templates loaded. Cannot proceed.")
            return

        try:
            df = pd.read_csv(self.leads_file)
        except FileNotFoundError:
            print(f"❌ Leads file '{self.leads_file}' not found.")
            return

        # Filter for leads that need an email
        new_leads = df[df['status'] == 'new'].to_dict('records')
        if not new_leads:
            print("ℹ️  No new leads to generate emails for.")
            return

        print(f"📊 Found {len(new_leads)} new leads to process\n")
        generated_emails = []
        success_count = 0
        failed_count = 0

        for idx, lead in enumerate(new_leads, 1):
            company_name = lead.get('name', 'Unknown')
            print(f"[{idx}/{len(new_leads)}] 📧 Processing: {company_name}")

            # Select best template for this lead
            template = self._select_template(lead)
            if not template:
                print(f"   ⚠️  No suitable template found. Skipping.")
                failed_count += 1
                continue

            # Extract sales insights
            insights = self._extract_lead_insights(lead)

            # Create professional prompt
            prompt = self._create_professional_prompt(lead, template, insights)

            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4-turbo",
                    response_format={"type": "json_object"},
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional web design sales expert. You write highly personalized cold emails that convert prospects into clients using proven sales frameworks."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.8,  # Slightly higher for creativity
                    max_tokens=1000
                )

                email_content = json.loads(response.choices[0].message.content)

                # Add sender info to email body
                body_with_signature = email_content['body'] + f"\n\n{self.sender_name}\n{self.sender_company}"

                generated_emails.append({
                    "to_email": lead.get('contact_email', ''),
                    "company_name": company_name,
                    "website_url": lead.get('website_url', ''),
                    "priority": insights['priority'],
                    "score": insights['score'],
                    "subject": email_content['subject'],
                    "body": body_with_signature,
                    "template_category": template['category'],
                    "framework": template.get('framework', 'generic')
                })

                # Mark as processed
                df.loc[df['website_url'] == lead['website_url'], 'status'] = 'email_generated'
                success_count += 1
                print(f"   ✅ Email generated ({template['category']} - {template.get('framework', 'generic')})")

            except Exception as e:
                print(f"   ❌ Failed: {e}")
                failed_count += 1

        # Save generated emails
        if generated_emails:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(generated_emails, f, indent=4, ensure_ascii=False)
            print(f"\n✅ SUCCESS: Saved {len(generated_emails)} emails to '{self.output_file}'")

        # Save updated lead statuses
        df.to_csv(self.leads_file, index=False)
        print(f"✅ Updated lead statuses in '{self.leads_file}'")

        # Summary
        print(f"\n=== 📊 GENERATION SUMMARY ===")
        print(f"✅ Successful: {success_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"📈 Success Rate: {(success_count / len(new_leads) * 100):.1f}%")