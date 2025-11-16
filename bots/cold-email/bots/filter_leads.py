# bots/filter_leads.py
import os
import time
import pandas as pd
import requests
import base64
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class LeadFilterAdvanced:
    def __init__(self, unfiltered_file='data/leads-unfiltered.txt', output_file='data/qualified-leads.csv'):
        self.unfiltered_file = unfiltered_file
        self.output_file = output_file
        self.unqualified_log_file = 'data/analyzed_unqualified.txt'
        self.driver = self._init_selenium()
        
        self.genai_client = None
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            print("⚠️ WARNING: GOOGLE_API_KEY not found in .env. AI analysis will be skipped.")
        else:
            genai.configure(api_key=google_api_key)
            # --- THIS IS THE FIX ---
            # Use the 'latest' tag to ensure you get the right, available model
            self.genai_client = genai.GenerativeModel('gemini-1.5-flash-latest') 
            
        self.CHEAP_ANALYSIS_THRESHOLD = 10 

    def _init_selenium(self):
        print("🚀 Initializing browser for analysis...")
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument("--window-size=1280,1024")
        options.add_argument("--log-level=3")
        try:
            service = Service(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=options)
        except Exception as e:
            print(f"❌ Could not initialize Selenium: {e}"); return None

    def _normalize_url(self, url):
        clean_url = url.strip().lower()
        if not re.match(r'^(?:f|ht)tps?://', clean_url):
            return f'https://{clean_url}'
        return clean_url

    def take_screenshot_in_memory(self, url):
        if not self.driver: 
            return None, None
        try:
            self.driver.get(url)
            time.sleep(3)
            png_bytes = self.driver.get_screenshot_as_png() 
            encoded_string = base64.b64encode(png_bytes).decode('utf-8')
            print(f"📸 Screenshot captured for {url}")
            return encoded_string, png_bytes
        except Exception as e:
            print(f"⚠️ Failed to take screenshot for {url}: {e}")
            return None, None

    # --- REPLACED: This now uses Google Gemini ---
    def get_combined_ai_analysis(self, image_bytes):
        """
        Uses Google Gemini (Flash model) to analyze the screenshot.
        This is reliable, fast, and very cheap.
        """
        if not self.genai_client or not image_bytes:
            return {"summary": "AI analysis skipped.", "penalty": 0, "category": "Unknown"}
            
        print("🤖 Submitting to Google Gemini (Flash) for critique...")
        try:
            image_part = {"mime_type": "image/png", "data": image_bytes}
            
            # --- MORE ROBUST PROMPT ---
            prompt = "Analyze the website screenshot. Is the design 'Modern' or 'Outdated'? Respond with *only* the single word 'Modern' or 'Outdated'."
            
            response = self.genai_client.generate_content([prompt, image_part])
            
            # --- MORE ROBUST PARSING ---
            raw_answer = response.text.strip().lower()
            answer = "unknown" # Default
            if "outdated" in raw_answer:
                answer = "outdated"
            elif "modern" in raw_answer:
                answer = "modern"
            
            print(f"🧠 Gemini AI Analysis: Raw='{raw_answer}', Parsed='{answer}'")

            penalty = 0
            summary = f"AI classified as '{answer}'."
            
            if answer == "outdated":
                penalty = 8 
            elif answer != "modern": # If it's ambiguous or 'unknown'
                penalty = 4
            
            return {"summary": summary, "penalty": penalty, "category": "Unknown"}

        except Exception as e:
            print(f"❌ Error during Google Gemini analysis. Type: {type(e).__name__}, Error: {e}")
            return {"summary": "AI failed.", "penalty": 5, "category": "Error"}

    def scrape_contact_info(self, soup, base_url):
        # ... (function is unchanged)
        text = soup.get_text()
        emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text))
        email = next(iter(emails), f"info@{urlparse(base_url).netloc}")
        phone = next(iter(set(re.findall(r'\(?\+?\d{1,3}\)?\s?\d{3}[\s.-]?\d{3}[\s.-]?\d{3}', text))), "N/A")
        return email, phone

    def analyze_website(self, url):
        # ... (function is unchanged)
        print("-" * 40 + f"\n🕵️ Analyzing {url}")
        report = {'url': url, 'rating': 0, 'issues': []}
        try:
            response = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            raw_text = response.text 
            soup = BeautifulSoup(raw_text, 'html.parser')
            report['email'], report['phone'] = self.scrape_contact_info(soup, url)
        except requests.RequestException:
            report.update({'rating': 20, 'issues': ["Site Unreachable"], 'category': 'N/A'})
            return report

        if urlparse(url).scheme == 'http': 
            report['rating'] += 10; report['issues'].append("No SSL")
        if soup.find('frameset'):
            report['rating'] += 10; report['issues'].append("Uses Deprecated Frameset")
        if not soup.find('meta', attrs={'name': 'viewport'}): 
            report['rating'] += 5; report['issues'].append("No Mobile Viewport")
        if not soup.find('h1'): 
            report['rating'] += 2; report['issues'].append("Missing H1 Tag")
        if '.swf' in raw_text or 'application/x-shockwave-flash' in raw_text:
            report['rating'] += 10; report['issues'].append("Contains Flash Content")

        try:
            footer_text = (soup.find('footer') or soup.find(id='footer') or soup.find(class_='footer')).get_text()
            if footer_text:
                years = re.findall(r'\b(19\d{2}|20\d{2})\b', footer_text)
                if years:
                    latest_year = max(int(y) for y in years)
                    if latest_year < 2020: 
                        report['rating'] += 4; report['issues'].append(f"Old Copyright ({latest_year})")
        except Exception:
            pass 

        if report['rating'] >= self.CHEAP_ANALYSIS_THRESHOLD:
            print(f"⏩ High score ({report['rating']}) on basic checks. Skipping AI.")
            report['category'] = 'Unknown (AI Skipped)'
            return report
            
        print(f"✅ Passed local checks. Taking screenshot...")
        base64_screenshot, png_bytes = self.take_screenshot_in_memory(url) 
        
        if not png_bytes:
            report['rating'] += 5; report['issues'].append("Screenshot Failed")
            return report

        ai_results = self.get_combined_ai_analysis(png_bytes)
        
        report['category'] = ai_results['category']
        if ai_results['penalty'] > 0:
            report['rating'] += ai_results['penalty']
            report['issues'].append(f"AI Critique: '{ai_results['summary']}'")
            
        return report

    def run(self):
        # ... (function is unchanged)
        print("\n--- Running Lead Filter ---")
        
        processed_urls = set()
        try:
            df_qualified = pd.read_csv(self.output_file)
            processed_urls.update(df_qualified['website_url'].tolist())
        except FileNotFoundError:
            pass 
        try:
            with open(self.unqualified_log_file, 'r') as f:
                processed_urls.update([line.strip() for line in f])
        except FileNotFoundError:
            pass 
        
        if processed_urls:
            print(f"🧠 Loaded {len(processed_urls)} previously analyzed URLs to prevent re-analysis.")

        if not os.path.exists(self.unfiltered_file):
            print(f"❌ Unfiltered leads file not found at '{self.unfiltered_file}'. Please create it."); return
        with open(self.unfiltered_file, 'r') as f: leads_to_process = [line.strip() for line in f if line.strip()]
        if not leads_to_process: print("🤷 Unfiltered leads file is empty. Nothing to do."); return
        
        new_qualified_leads = []
        new_unqualified_leads = []

        for url in leads_to_process:
            url = self._normalize_url(url)
            
            if url in processed_urls:
                print(f"⏩ Skipping {url}, it has been analyzed before."); continue
            
            report = self.analyze_website(url)
            
            if report['rating'] >= 5: 
                priority = "High" if report['rating'] >= 10 else "Medium"
                new_qualified_leads.append({
                    'website_url': url,
                    'contact_email': report.get('email'),
                    'phone_number': report.get('phone'),
                    'business_category': report.get('category'),
                    'priority': priority,
                    'rating_score': report['rating'],
                    'issues': ', '.join(report['issues']),
                    'status': 'new'
                })
            else:
                print(f"👍 Website {url} is good. Marking as unqualified.")
                new_unqualified_leads.append(url)

        if self.driver: self.driver.quit()

        if new_qualified_leads:
            try:
                existing_df = pd.read_csv(self.output_file)
            except FileNotFoundError:
                existing_df = pd.DataFrame()
            new_df = pd.DataFrame(new_qualified_leads)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df.to_csv(self.output_file, index=False)
            print(f"\n✅ Added {len(new_qualified_leads)} new qualified leads.")
        else:
            print("\n🤷 No new qualified leads found this run.")

        if new_unqualified_leads:
            with open(self.unqualified_log_file, 'a') as f:
                for url in new_unqualified_leads:
                    f.write(f"{url}\n")
            print(f"✅ Logged {len(new_unqualified_leads)} new unqualified websites to prevent future analysis.")

        open(self.unfiltered_file, 'w').close()
        print(f"🗑️ Cleared '{self.unfiltered_file}'.")