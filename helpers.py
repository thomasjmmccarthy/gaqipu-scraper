import subprocess
import sys
import csv
import tkinter as tk
from tkinter import ttk
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from fake_useragent import UserAgent


# helpers.py contains a range of methods and classes that are used by launcher.py and Gaqipu.py
# See Gaqipu.py and launcher.py for their specific uses.
            
            

# Prints the given error in a neat format, and halts execution of the program if requested
def give_error(message, close_program=True):
    print('\n[' + message.upper() + ']')
    if close_program == True:
        sys.exit(0)
        
        

# Creates and returns a new webdriver with a fake user agent.
def get_new_driver():
    # Establish a fake user agent
    # This is required as some websites block standard Selenium Chromedriver access
    ua = UserAgent()
    user_agent = ua.random
    
    # Create options for ChromeDriver
    # Hides Chrome window GUI and applies the fake user agent
    options = Options()
    options.add_argument(f'user-agent={user_agent}')
    options.add_argument('--disable-blink-features=AutomationControlled')    
    options.add_argument('--headless=new')
    options.add_argument('--window-size=1920,1080')
    print('New Webdriver Session:', user_agent, '\n')
    service = Service(executable_path='./chromedriver.exe')
    return webdriver.Chrome(options=options, service=service)
    
    

# Opens and reads both publishers and configurations from config.csv
def fetch_configs_from_file():
    configs = []
    publishers = []
    try:
        with open('config.csv', newline='') as config_file:
            line_reader = csv.reader(config_file, delimiter=',')
            first = True
            for row in line_reader:
                
                if first == False:
                    new_config = Configuration(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
                    configs.append( new_config )
                    
                    found = False
                    for publisher in publishers:
                        found = publisher.try_add_config(new_config)
                        if found:
                            break
                        
                    if found == False:
                        new_publisher = Publisher(row[0])
                        new_publisher.add_config(new_config)
                        publishers.append(new_publisher)
                        
                else:
                    first = False
                    
        print('Found', len(configs), 'configuration(s) in configs.csv')
        print('Found', len(publishers), 'publisher(s) in configs.csv\n')
        return configs, publishers
    except:
        give_error('Could not find config.csv, or failed reading it.')
    
    

# Opens and reads article links from urls.csv
def fetch_urls_from_file():
    urls = []
    try:
        with open('urls.csv', newline='') as config_file:
            journal = ''
            line_reader = csv.reader(config_file, delimiter=',')
            for row in line_reader:
                if len(row) > 1:
                    journal = row[0]
                    new_url = Url(journal, row[1])
                else:
                    new_url = Url(journal, row[0])
                urls.append( new_url )
        print('Found', len(urls), 'URL(s) in urls.csv\n')
        return urls
    except:
        give_error('Could not find url.csv, or failed reading it.')
        
        
        
    
# Clamps a number between two values
def clamp(num, minnum, maxnum):
    return max(min(maxnum, num), minnum)




#########################
##   PROGRESS WINDOW   ##
#########################

# The ProgressWindow class opens a tkinter gui interface that provides information on how close to completion Gaqipu is,
# including a progress bar, article count, as well as an estimated wait time.
# Due to the technicalities of tkinter, ProgressWindow opens on a different thread from the main program, and runs
# alongside/is updated by it.
    
class ProgressWindow(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        
    def run(self):
        self.max_value = 1
        self.value = 0
        self.execution_times = []
        
        self.root = tk.Tk()
        self.root.geometry('300x140')
        self.root.title('Gaqipu Progress Monitor')
        self.root.option_add("*font", "lucida 14 bold")
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)
        
        self.pb = ttk.Progressbar(self.root, orient='horizontal', mode='determinate', length=280)
        self.pb.grid(column=0, row=0, columnspan=2, padx=10, pady=20)
        
        self.percent_label = ttk.Label(self.root, text=self.get_percent())
        self.percent_label.grid(column=0, row=1, columnspan=2)
        
        self.count_label = ttk.Label(self.root, text='getting data...')
        self.count_label.grid(column=0, row=2, columnspan=2)
        self.count_label.config(font=("lucida", 8))
        
        self.time_label = ttk.Label(self.root, text='calculating...')
        self.time_label.grid(column=0, row=3, columnspan=2)
        self.time_label.config(font=("lucida", 8, "italic"))
        
        self.root.mainloop()
        
    def set_max_value(self, max_value):
        self.max_value = max_value
        self.value = 0
        self.update_gui()
        
    def update_gui(self):
        self.pb['value'] = (self.value/self.max_value) * 100
        self.percent_label['text'] = self.get_percent()
        self.count_label['text'] = self.get_count()
        self.time_label['text'] = self.get_time_remaining()
        
    def get_percent(self):
        division = (self.value / self.max_value) * 1000
        division = round(division) / 10
        return str(division) + '%'
    
    def get_count(self):
        return str(self.value) + " of " + str(self.max_value) + " article(s) searched"
    
    def get_time_remaining(self):
        if len(self.execution_times) > 0:
            sample_size = min(30, len(self.execution_times))
            sample = self.execution_times[len(self.execution_times) - sample_size:]
            sample_mean = sum(sample) / sample_size
            time_remaining = round(sample_mean * (self.max_value - self.value))
            hours = int(time_remaining / 3600)
            minutes = int(time_remaining / 60) - (hours * 60)
            return str(hours) + 'h ' + str(minutes) + 'm remaining'
        return 'calculating...'
        
    def update_all(self, execution_time):
        self.value += 1
        self.execution_times.append(execution_time)
        self.update_gui()
        
    def quit(self):
        self.root.destroy()

    
        
        
#########################
##   PUBLISHER CLASS   ##
#########################
        
# The Publisher class stores information for each publisher, as defined in the config file. Each instance stores a list
# of all possible configurations for journals under that publisher, so that they can be requested should a journal rely
# on the $publisher-standard functionality (see Gaqipu.py for more on this).
        
class Publisher:
    
    def __init__(self, name):
        self.name = name.lower()
        self.configs = []
        
    def add_config(self, config):
        self.configs.append(config)
        
    def get_publisher_standard(self):
        return self.configs
    
    def has_name(self, name):
        return self.name == name
    
    def try_add_config(self, config):
        if self.has_name(config.publisher):
            return self.add_config(config)
        return False
    
    def add_config(self, config):
        if config.identifier != '$publisher-standard':
            self.configs.append(config)
        return True
        
    
        
        
#########################
## CONFIGURATION CLASS ##
#########################
    
# A configuration is a representation of how the wanted information may be stored on a web page. Configurations are
# interpreted by Gaqipu during runtime, in order to best find the Data Availability Statement. Journals may have
# multiple configurations.
    
class Configuration:
    
    def __init__(self, publisher, journal, title_class, tag, identifier, search_tag, author_class, author_secondary_class, get_author_by_child):
        self.publisher = publisher.lower()
        self.journal = journal.lower()
        self.title_class = title_class
        if tag == 'n/a':
            self.tag = None
        else:
            self.tag = tag.lower()
        self.identifier = identifier
        self.search_tag = search_tag.lower()
        self.author_class = author_class
        if author_secondary_class == 'n/a':
            self.author_secondary_class = None
        else:
            self.author_secondary_class = author_secondary_class
        if get_author_by_child == 'no':
            self.get_author_by_child = False
        else:
            self.get_author_by_child = True
        
    def __str__(self):
        return 'CONFIG: [ ' + self.journal + ', ' + self.title_class + ', ' + self.tag + ', ' + self.identifier + ', ' + self.search_tag + ', ' + self.author_class + ', ' + self.author_secondary_class + ' ]'
    
    
    

########################
##     URL CLASS      ##
########################
    
# A simple class for storing the journal and link to each article from urls.csv
    
class Url:
    
    def __init__(self, journal, link):
        self.journal = journal.lower()
        self.link = link.lower()
        
    def __str__(self):
        return 'URL: [ ' + self.journal + ', ' + self.link + ' ]'
    
    
    
    

########################
##  SEARCH CONSTANTS  ##
########################
    
# SearchConstants are used in Gaqipu.py to simplify the page searching algorithm.
    
class SearchConstants:
    
    PRINT_CODES = ['!','-','+','?']
    
    FOUND = 1
    AMBIGUOUS = 2
    NOT_FOUND = 0
    ERROR = -1
    
    
    
    
    
########################
##    ANALYSIS LOG    ##
########################
    
# The AnalysisLog stores statistics relating to Gaqipu's scraping as a series of JournalReport instances.
# It can format and return its data on request.
    
class AnalysisLog:
        
    def __init__(self):
        self.journal_reports = []
        self.index = -1
        self.total = JournalReport('Total Data Collected')
        self.total_report_generated = False
        
    def start_new_report(self, name):
        self.journal_reports.append(JournalReport(name))
        self.index += 1
        
    def find_report(self, name):
        for i in range(len(self.journal_reports)):
            if self.journal_reports.name[i] == name:
                self.index = i
                return None
        # If a report by the given name isn't found, start a new report
        self.index = len(self.journal_reports) - 1
        self.start_new_report(name)
        return True
        
    def add_url_to_report(self, das, author, iteration):
        if self.index != -1:
            return self.journal_reports[self.index].add_url(das, author, iteration)
            
    def add_configs_to_report(self, number):
        if self.index != -1:
            self.journal_reports[self.index].add_configs(number)
            
    def generate_log(self):
        log = ''
        
        for report in self.journal_reports:
            
            log += report.generate_report() + '\n\n'
            self.total.configs_found += report.configs_found
            self.total.urls_searched += report.urls_searched
            self.total.urls_found_das += report.urls_found_das
            self.total.urls_found_authors += report.urls_found_authors
            self.total.urls_found_nothing += report.urls_found_nothing
            self.total.ambiguous_urls += report.ambiguous_urls
        
        border = ((30 * '=') + '\n\n\n')
        log = border + str(self.total.generate_report()) + '\n\n\n' + border + log
        self.total_report_generated = True
        return log
    
    def get_total_report(self):
        if self.total_report_generated:
            border = ('\n\n\n' + (30 * '=') + '\n\n\n')
            return border + self.total.generate_report() + border
        else:
            return None
    
    
########################
##   JOURNAL REPORT   ##
########################
        
# Stores statistics for a given journal. Can generate a report for the journal on request.
    
class JournalReport:
    
    def __init__(self, name):
        self.name = name
        self.configs_found = 0
        self.urls_searched = 0
        self.urls_found_das = 0
        self.urls_found_authors = 0
        self.urls_found_nothing = 0
        self.ambiguous_urls = 0
    
    # Returns True if the url is to be retried in the next iteration, False otherwise
    def add_url(self, das, authors, iteration):
        self.urls_searched += 1
        if das == False and authors == False:
            if iteration == 4:
                self.urls_found_nothing += 1
                return False
            else:
                return True
        else:
            if das == 1:
                self.urls_found_das += 1
            elif das == 2:
                self.ambiguous_urls += 1
            if authors:
                self.urls_found_authors += 1
            return False
            
    def add_configs(self, number):
        self.configs_found += number
            
    def generate_report(self):
        report = str(self.name.upper() + ' :\n\n' +
                  '\t' + str(self.urls_searched) + ' articles searched.\n' +
                  '\t' + str(self.urls_found_das) + ' data availability statement(s) found.\n' +
                  '\t' + str(self.urls_found_authors) + ' author(s) found.\n\n' +
                  '\t' + str(self.ambiguous_urls) + ' article(s) contained multiple data availability statements.\n' +
                  '\t' + str(self.urls_found_nothing) + ' article(s) contained no readable data.'
        )
        return report
