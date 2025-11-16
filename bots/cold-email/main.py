import sys
import time
from bots.filter_leads import LeadFilterAdvanced
from bots.filter_leads_v2 import LeadFilterAdvancedV2
from bots.generate_emails import EmailGenerator
from bots.send_emails import EmailSender
from bots.analyze_responses import ResponseAnalyzer

def main():
    print("🤖 Welcome to the Lead Outreach Bot 🤖")
    print("="*40)
    print("This bot uses a status system in 'qualified-leads.csv' to track progress.")
    print("1. Filter Leads V1 (URL-based, finds new leads, marks them as 'new')")
    print("2. Filter Leads V2 (CSV-based, advanced 0-100 scoring)")
    print("3. Generate Emails (Processes 'new' leads, marks them as 'email_generated')")
    print("4. Send Emails (Processes 'email_generated' leads, marks them as 'email_sent')")
    print("5. Analyze Responses (Checks inbox for replies)")
    print("6. Run Full Workflow (All steps in sequence)")
    print("="*40)

    choice = input("Enter your choice (1-6): ")

    if choice == '1':
        bot = LeadFilterAdvanced()
        bot.run()

    elif choice == '2':
        print("\n🚀 Lead Filter V2 - Advanced Scoring System")
        print("="*40)
        input_file = input("Enter path to CSV/Excel file (or press Enter for sample_input.csv): ").strip()
        if not input_file:
            input_file = 'data/sample_input.csv'

        try:
            bot = LeadFilterAdvancedV2(config_path='config.yaml')
            bot.run(input_file)
        except Exception as e:
            print(f"❌ Error running V2 filter: {e}")

    elif choice == '3':
        bot = EmailGenerator()
        bot.run()

    elif choice == '4':
        print("🚨 You are about to send emails in PRODUCTION mode.")
        confirm = input("Are you sure you want to proceed? (yes/no): ")
        if confirm.lower() == 'yes':
            bot = EmailSender()
            bot.run(delay_seconds=10) # Set a delay between emails
        else:
            print("Email sending cancelled.")

    elif choice == '5':
        bot = ResponseAnalyzer()
        bot.check_inbox()

    elif choice == '6':
        print("\n--- Running Full Workflow ---")
        # Step 1: Find new leads
        print("\n[STEP 1/4] Filtering for new leads...")
        LeadFilterAdvanced().run()
        time.sleep(2)

        # Step 2: Generate emails for them
        print("\n[STEP 2/4] Generating personalized emails...")
        EmailGenerator().run()
        time.sleep(2)

        # Step 3: Send the generated emails
        print("\n[STEP 3/4] Sending generated emails...")
        confirm = input(f"Are you sure you want to proceed with sending emails? (yes/no): ")
        if confirm.lower() == 'yes':
            EmailSender().run(delay_seconds=30)
        else:
            print("Workflow stopped before sending emails.")
            sys.exit(0)

        # Step 4: Analyze responses after a delay
        print("\n[STEP 4/4] Waiting 1 hour before checking for responses...")
        # time.sleep(3600) # Uncomment to wait for an hour
        ResponseAnalyzer().check_inbox()

        print("\n🎉 Full workflow complete! 🎉")

    else:
        print("Invalid choice. Please run the script again.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nAn unexpected error occurred in the main workflow: {e}")