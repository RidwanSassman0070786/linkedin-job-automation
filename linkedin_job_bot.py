#!/usr/bin/env python3
"""
LinkedIn Job Automation Bot
Automatically searches and applies for remote global jobs on LinkedIn
Targeting: Solution Architect, AI Architect, Cloud Architect positions
"""

import os
import time
import json
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('linkedin_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LinkedInJobBot:
    def __init__(self):
        self.email = os.getenv('LINKEDIN_EMAIL')
        self.password = os.getenv('LINKEDIN_PASSWORD')
        self.driver = None
        self.applied_jobs = self.load_applied_jobs()
        
    def load_applied_jobs(self):
        """Load previously applied job IDs from file"""
        try:
            with open('applied_jobs.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def save_applied_jobs(self):
        """Save applied job IDs to file"""
        with open('applied_jobs.json', 'w') as f:
            json.dump(self.applied_jobs, f, indent=2)
    
    def setup_driver(self):
        """Initialize Chrome WebDriver with headless options"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        logger.info("WebDriver initialized successfully")
    
    def login(self):
        """Login to LinkedIn"""
        try:
            logger.info("Navigating to LinkedIn login page...")
            self.driver.get('https://www.linkedin.com/login')
            
            # Wait for and fill email
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'username'))
            )
            email_field.send_keys(self.email)
            
            # Fill password
            password_field = self.driver.find_element(By.ID, 'password')
            password_field.send_keys(self.password)
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            login_button.click()
            
            time.sleep(5)  # Wait for login to complete
            logger.info("Successfully logged in to LinkedIn")
            return True
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False
    
    def search_jobs(self, keywords, location='Worldwide', remote=True):
        """Search for jobs with specified criteria"""
        try:
            # Build search URL
            base_url = 'https://www.linkedin.com/jobs/search/'
            params = {
                'keywords': keywords,
                'location': location,
                'f_WT': '2' if remote else '',  # Remote filter
                'sortBy': 'R'  # Sort by most recent
            }
            
            search_url = base_url + '?' + '&'.join([f"{k}={v}" for k, v in params.items() if v])
            logger.info(f"Searching jobs: {search_url}")
            
            self.driver.get(search_url)
            time.sleep(3)
            
            return True
            
        except Exception as e:
            logger.error(f"Job search failed: {str(e)}")
            return False
    
    def get_job_listings(self):
        """Extract job listings from search results"""
        try:
            # Wait for job cards to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.job-card-container'))
            )
            
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, '.job-card-container')
            logger.info(f"Found {len(job_cards)} job listings")
            
            jobs = []
            for card in job_cards[:20]:  # Limit to first 20 jobs
                try:
                    job_id = card.get_attribute('data-job-id')
                    if job_id and job_id not in self.applied_jobs:
                        job_title = card.find_element(By.CSS_SELECTOR, '.job-card-list__title').text
                        company = card.find_element(By.CSS_SELECTOR, '.job-card-container__company-name').text
                        jobs.append({
                            'id': job_id,
                            'title': job_title,
                            'company': company
                        })
                except Exception as e:
                    logger.warning(f"Error extracting job info: {str(e)}")
                    continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"Failed to get job listings: {str(e)}")
            return []
    
    def apply_to_job(self, job):
        """Apply to a specific job (Easy Apply only)"""
        try:
            job_url = f"https://www.linkedin.com/jobs/view/{job['id']}/"
            self.driver.get(job_url)
            time.sleep(2)
            
            # Look for Easy Apply button
            try:
                easy_apply_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.jobs-apply-button'))
                )
                
                if 'Easy Apply' in easy_apply_button.text:
                    easy_apply_button.click()
                    time.sleep(2)
                    
                    # Handle application modal
                    # Note: This is simplified - actual implementation needs to handle
                    # multi-step forms, file uploads, and custom questions
                    self._complete_application()
                    
                    self.applied_jobs.append(job['id'])
                    self.save_applied_jobs()
                    
                    logger.info(f"✓ Applied to: {job['title']} at {job['company']}")
                    return True
                else:
                    logger.info(f"⊘ Not Easy Apply: {job['title']} at {job['company']}")
                    return False
                    
            except TimeoutException:
                logger.info(f"⊘ No Easy Apply button found: {job['title']}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to apply to job: {str(e)}")
            return False
    
    def _complete_application(self):
        """Complete the Easy Apply application form"""
        try:
            # This is a simplified version - actual implementation needs to:
            # 1. Handle multi-step forms
            # 2. Upload resume/cover letter
            # 3. Answer custom questions
            # 4. Review and submit
            
            max_attempts = 10
            for _ in range(max_attempts):
                try:
                    # Look for Next or Review button
                    next_button = self.driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Continue to next step"]')
                    next_button.click()
                    time.sleep(1)
                except NoSuchElementException:
                    break
            
            # Submit application
            submit_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Submit application"]'))
            )
            submit_button.click()
            time.sleep(2)
            
        except Exception as e:
            logger.warning(f"Application completion encountered issues: {str(e)}")
    
    def run(self):
        """Main execution method"""
        try:
            logger.info("="*60)
            logger.info(f"LinkedIn Job Bot Started - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("="*60)
            
            # Setup and login
            self.setup_driver()
            if not self.login():
                logger.error("Failed to login. Exiting.")
                return
            
            # Define job search queries
            job_searches = [
                'Solution Architect',
                'AI Architect',
                'Cloud Architect',
                'Solution Architect AI',
                'Machine Learning Architect'
            ]
            
            total_applied = 0
            
            for search_term in job_searches:
                logger.info(f"\nSearching for: {search_term}")
                
                if not self.search_jobs(search_term, location='Worldwide', remote=True):
                    continue
                
                jobs = self.get_job_listings()
                logger.info(f"Found {len(jobs)} new jobs to apply to")
                
                for job in jobs:
                    if self.apply_to_job(job):
                        total_applied += 1
                        time.sleep(3)  # Rate limiting
                
                time.sleep(5)  # Pause between searches
            
            logger.info("="*60)
            logger.info(f"Job application session completed")
            logger.info(f"Total applications submitted: {total_applied}")
            logger.info(f"Total jobs applied to date: {len(self.applied_jobs)}")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"Bot execution failed: {str(e)}")
        
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver closed")

if __name__ == '__main__':
    bot = LinkedInJobBot()
    bot.run()
