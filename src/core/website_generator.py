"""
Dynamic Website Generator
=========================
Generates personalized demo websites for leads WITHOUT creating thousands of files.

Approach:
- Single index.html with JavaScript
- Lead data in JSON file
- URL parameters: demo.thomas.cz?lead=abc123
- Client-side personalization

This avoids:
- GitHub repo bloat
- Deployment issues
- Cleanup complexity
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from jinja2 import Template

from src.utils.logger import SystemLogger
from src.utils.helpers import FileHelper, IDGenerator
from src.utils.validators import Validators


class WebsiteGenerator:
    """
    Generate personalized demo websites dynamically.
    """

    def __init__(self, config: Dict):
        """Initialize website generator."""
        self.config = config
        self.logger = SystemLogger.get_logger(__name__, config.get('logging'))

        self.templates = {}
        self._load_templates()

        self.logger.info("Website Generator initialized")

    def _load_templates(self):
        """Load HTML templates for each niche."""
        templates_path = Path(self.config.get('website_generation', {})
                              .get('templates', {})
                              .get('base_path', 'src/templates/'))

        if not templates_path.exists():
            self.logger.warning(f"Templates path not found: {templates_path}")
            return

        # Load each template
        for template_file in templates_path.glob('*.html'):
            niche_name = template_file.stem
            with open(template_file, 'r', encoding='utf-8') as f:
                self.templates[niche_name] = f.read()
                self.logger.info(f"Loaded template: {niche_name}")

    def generate_demo_data(self, leads: List[Dict], output_file: str) -> bool:
        """
        Generate JSON data file for all leads.

        Args:
            leads: List of lead dictionaries
            output_file: Path to output JSON file

        Returns:
            True if successful
        """
        self.logger.info(f"Generating demo data for {len(leads)} leads...")

        # Prepare lead data
        demo_data = {}

        for lead in leads:
            lead_id = lead.get('lead_id')
            if not lead_id:
                lead_id = IDGenerator.generate_lead_id(
                    lead.get('email', ''),
                    lead.get('company_name', '')
                )

            # Extract personalization data (handle pandas NaN)
            import math
            demo_data[lead_id] = {
                'company_name': str(lead.get('company_name', 'Your Business')) if lead.get('company_name') and not (isinstance(lead.get('company_name'), float) and math.isnan(lead.get('company_name'))) else 'Your Business',
                'niche': str(lead.get('niche', 'default')),
                'industry': str(lead.get('industry', 'business')) if lead.get('industry') and not (isinstance(lead.get('industry'), float) and math.isnan(lead.get('industry'))) else 'business',
                'location': self._extract_location(str(lead.get('address', '')) if lead.get('address') else ''),
                'phone': str(lead.get('phone', '')) if lead.get('phone') and not (isinstance(lead.get('phone'), float) and math.isnan(lead.get('phone'))) else '',
                'email': str(lead.get('email', '')) if lead.get('email') and not (isinstance(lead.get('email'), float) and math.isnan(lead.get('email'))) else '',
                'website': str(lead.get('website', '')) if lead.get('website') and not (isinstance(lead.get('website'), float) and math.isnan(lead.get('website'))) else '',
                'tier': str(lead.get('tier', 'tier3')),
                'score': int(lead.get('score', 0)),
                'generated_at': self._get_timestamp()
            }

        # Save to JSON
        try:
            FileHelper.save_json(output_file, demo_data)
            self.logger.info(f"Saved demo data to {output_file}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save demo data: {e}")
            return False

    def generate_index_html(self, output_file: str) -> bool:
        """
        Generate the main index.html file that dynamically renders demos.

        This is the SINGLE file that handles all leads.
        """
        html_content = '''<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow">
    <title>Webová Prezentace - Demo</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary-color: #2563eb;
            --secondary-color: #1e40af;
            --text-color: #1f2937;
            --bg-color: #f9fafb;
            --card-bg: #ffffff;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        /* Loading State */
        .loading {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            flex-direction: column;
        }

        .spinner {
            border: 4px solid rgba(0, 0, 0, 0.1);
            border-left-color: var(--primary-color);
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Hero Section */
        .hero {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 80px 20px;
            text-align: center;
            border-radius: 20px;
            margin-bottom: 40px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }

        .hero h1 {
            font-size: 3em;
            margin-bottom: 20px;
            font-weight: 800;
        }

        .hero p {
            font-size: 1.3em;
            opacity: 0.95;
            max-width: 600px;
            margin: 0 auto 30px;
        }

        .cta-button {
            display: inline-block;
            background: white;
            color: var(--primary-color);
            padding: 15px 40px;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 600;
            font-size: 1.1em;
            transition: transform 0.3s, box-shadow 0.3s;
        }

        .cta-button:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
        }

        /* Features Section */
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-bottom: 60px;
        }

        .feature-card {
            background: var(--card-bg);
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
            transition: transform 0.3s, box-shadow 0.3s;
        }

        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
        }

        .feature-icon {
            font-size: 3em;
            margin-bottom: 20px;
        }

        .feature-card h3 {
            font-size: 1.5em;
            margin-bottom: 15px;
            color: var(--primary-color);
        }

        .feature-card p {
            color: #6b7280;
            line-height: 1.8;
        }

        /* About Section */
        .about {
            background: var(--card-bg);
            padding: 60px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
            margin-bottom: 40px;
        }

        .about h2 {
            font-size: 2.5em;
            margin-bottom: 30px;
            color: var(--primary-color);
        }

        .about p {
            font-size: 1.1em;
            color: #4b5563;
            margin-bottom: 20px;
            line-height: 1.8;
        }

        /* Contact Section */
        .contact {
            background: linear-gradient(135deg, #f3f4f6, #e5e7eb);
            padding: 60px;
            border-radius: 15px;
            text-align: center;
        }

        .contact h2 {
            font-size: 2.5em;
            margin-bottom: 30px;
            color: var(--text-color);
        }

        .contact-info {
            display: flex;
            justify-content: center;
            gap: 40px;
            flex-wrap: wrap;
            margin-top: 30px;
        }

        .contact-item {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 1.1em;
        }

        .contact-item a {
            color: var(--primary-color);
            text-decoration: none;
            font-weight: 600;
        }

        .contact-item a:hover {
            text-decoration: underline;
        }

        /* Footer */
        footer {
            text-align: center;
            padding: 40px 20px;
            color: #9ca3af;
            font-size: 0.9em;
        }

        /* Error State */
        .error {
            text-align: center;
            padding: 100px 20px;
        }

        .error h2 {
            color: #ef4444;
            font-size: 2em;
            margin-bottom: 20px;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .hero h1 {
                font-size: 2em;
            }

            .hero p {
                font-size: 1.1em;
            }

            .features {
                grid-template-columns: 1fr;
            }

            .about, .contact {
                padding: 40px 20px;
            }
        }

        /* Niche-specific color schemes */
        .niche-restaurant { --primary-color: #dc2626; --secondary-color: #991b1b; }
        .niche-hotel { --primary-color: #7c3aed; --secondary-color: #5b21b6; }
        .niche-cafe { --primary-color: #ca8a04; --secondary-color: #854d0e; }
        .niche-salon { --primary-color: #ec4899; --secondary-color: #be185d; }
        .niche-fitness { --primary-color: #059669; --secondary-color: #047857; }
        .niche-retail { --primary-color: #2563eb; --secondary-color: #1e40af; }
    </style>
</head>
<body>
    <!-- Loading State -->
    <div id="loading" class="loading">
        <div class="spinner"></div>
        <p style="margin-top: 20px; color: #6b7280;">Načítám demo...</p>
    </div>

    <!-- Main Content (hidden initially) -->
    <div id="content" style="display: none;">
        <div class="container">
            <!-- Hero Section -->
            <section class="hero">
                <h1 id="company-name">Vaše Firma</h1>
                <p id="company-tagline">Moderní webové řešení pro váš byznys</p>
                <a href="#contact" class="cta-button">Kontaktujte nás</a>
            </section>

            <!-- Features -->
            <section class="features">
                <div class="feature-card">
                    <div class="feature-icon">🚀</div>
                    <h3>Moderní Design</h3>
                    <p>Profesionální vzhled, který zaujme vaše zákazníky na první pohled.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📱</div>
                    <h3>Mobilní Optimalizace</h3>
                    <p>Perfektní zobrazení na všech zařízeních - telefon, tablet, počítač.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">⚡</div>
                    <h3>Rychlé Načítání</h3>
                    <p>Optimalizovaný kód zajistí bleskurychlé načítání stránek.</p>
                </div>
            </section>

            <!-- About -->
            <section class="about">
                <h2>O Nás</h2>
                <p id="about-text">
                    Jsme <span id="company-name-about">vaše firma</span>,
                    <span id="company-location">působící v České republice</span>.
                    Naše služby jsou navrženy tak, aby splnily všechny vaše potřeby.
                </p>
                <p>
                    S naší pomocí můžete rozšířit svou působnost online a oslovit nové zákazníky.
                    Moderní webová prezentace je dnes nutností pro každý byznys.
                </p>
            </section>

            <!-- Contact -->
            <section id="contact" class="contact">
                <h2>Kontakt</h2>
                <p>Máte zájem o naše služby? Neváhejte nás kontaktovat!</p>
                <div class="contact-info">
                    <div class="contact-item" id="phone-section" style="display: none;">
                        📞 <a href="#" id="phone-link"></a>
                    </div>
                    <div class="contact-item" id="email-section" style="display: none;">
                        ✉️ <a href="#" id="email-link"></a>
                    </div>
                </div>
            </section>

            <!-- Footer -->
            <footer>
                <p>© 2024 <span id="company-name-footer">Vaše Firma</span>. Všechna práva vyhrazena.</p>
                <p style="margin-top: 10px; font-size: 0.8em;">
                    Toto je demo webová stránka vytvořená společností
                    <a href="https://tomaszitko.cz" style="color: #2563eb;">Tomáš Žitko</a>
                </p>
            </footer>
        </div>
    </div>

    <!-- Error State -->
    <div id="error" style="display: none;">
        <div class="error">
            <h2>Demo nenalezeno</h2>
            <p>Omlouváme se, požadované demo nebylo nalezeno nebo již vypršelo.</p>
        </div>
    </div>

    <script>
        // Get lead ID from URL
        const urlParams = new URLSearchParams(window.location.search);
        const leadId = urlParams.get('lead');

        // Load demo data
        async function loadDemo() {
            if (!leadId) {
                showError();
                return;
            }

            try {
                // Fetch demo data
                const response = await fetch('demos.json');
                const data = await response.json();

                if (!data[leadId]) {
                    showError();
                    return;
                }

                const lead = data[leadId];
                personalizeDemo(lead);
                showContent();

                // Track view (optional analytics)
                trackView(leadId);
            } catch (error) {
                console.error('Error loading demo:', error);
                showError();
            }
        }

        function personalizeDemo(lead) {
            // Apply niche-specific styling
            if (lead.niche) {
                document.body.classList.add(`niche-${lead.niche}`);
            }

            // Company name
            const companyName = lead.company_name || 'Vaše Firma';
            document.getElementById('company-name').textContent = companyName;
            document.getElementById('company-name-about').textContent = companyName;
            document.getElementById('company-name-footer').textContent = companyName;

            // Tagline based on industry
            const taglines = {
                'restaurant': 'Skvělé jídlo, skvělý zážitek',
                'hotel': 'Váš dokonalý pobyt začíná zde',
                'cafe': 'Kde se potkává kvalita a pohoda',
                'salon': 'Krása a péče na profesionální úrovni',
                'fitness': 'Vaše cesta k lepší kondici',
                'retail': 'Kvalitní produkty pro vaše potřeby',
                'default': 'Profesionální služby pro váš byznys'
            };
            const tagline = taglines[lead.niche] || taglines['default'];
            document.getElementById('company-tagline').textContent = tagline;

            // Location
            if (lead.location) {
                document.getElementById('company-location').textContent =
                    `působící v oblasti ${lead.location}`;
            }

            // Contact info
            if (lead.phone) {
                document.getElementById('phone-section').style.display = 'flex';
                document.getElementById('phone-link').textContent = lead.phone;
                document.getElementById('phone-link').href = `tel:${lead.phone.replace(/\s/g, '')}`;
            }

            if (lead.email) {
                document.getElementById('email-section').style.display = 'flex';
                document.getElementById('email-link').textContent = lead.email;
                document.getElementById('email-link').href = `mailto:${lead.email}`;
            }
        }

        function showContent() {
            document.getElementById('loading').style.display = 'none';
            document.getElementById('content').style.display = 'block';
        }

        function showError() {
            document.getElementById('loading').style.display = 'none';
            document.getElementById('error').style.display = 'block';
        }

        function trackView(leadId) {
            // Optional: Send analytics to your server
            // fetch(`/api/track?lead=${leadId}&event=view`);
            console.log(`Demo viewed: ${leadId}`);
        }

        // Load demo on page load
        loadDemo();
    </script>
</body>
</html>'''

        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)

            self.logger.info(f"Generated index.html at {output_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to generate index.html: {e}")
            return False

    def _extract_location(self, address: str) -> str:
        """Extract city/location from address."""
        if not address:
            return "České republice"

        # Try to extract city name (simplified)
        # Format: "Street 123, 110 00 Prague"
        parts = address.split(',')
        if len(parts) >= 2:
            location = parts[-1].strip()
            # Remove postal code
            location = ' '.join([part for part in location.split() if not part[0].isdigit()])
            return location.strip() if location else "České republice"

        return "České republice"

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

    def generate_all(self, leads: List[Dict], output_dir: str) -> Dict[str, str]:
        """
        Generate all demo files.

        Args:
            leads: List of lead dictionaries
            output_dir: Directory to save files

        Returns:
            Dict with paths to generated files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = {}

        # Generate demos.json
        demos_file = output_path / 'demos.json'
        if self.generate_demo_data(leads, str(demos_file)):
            results['demos_json'] = str(demos_file)

        # Generate index.html
        index_file = output_path / 'index.html'
        if self.generate_index_html(str(index_file)):
            results['index_html'] = str(index_file)

        self.logger.info(f"Generated {len(results)} demo files in {output_dir}")

        return results
