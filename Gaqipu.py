import time
import csv
import winsound

from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options

# See helpers.py for functionality
from helpers import give_error, fetch_configs_from_file, fetch_urls_from_file, get_new_driver, clamp
from helpers import AnalysisLog, ProgressWindow, SearchConstants as sc



# Basic set up that is required to run the Gaqipu web scraper
def set_up():
    global DRIVER
    
    print('\n\n' + (30 * '=') + '\n=           GAQIPU           =\n' + (30 * '=') + '\n\n')
    
    time.sleep(0.5)
        
    DRIVER = get_new_driver()
    configs, publishers = fetch_configs_from_file()
    urls = fetch_urls_from_file()
    
    return configs, urls, publishers
    


def run_scraper(configs, urls):
    global DRIVER, PROGRESS, LOG, ITERATION
    
    url_index = 0
    PROGRESS.set_max_value(len(urls))
    slipped_urls = []
    last_journal = None
    journal_configs = []
    
    try:
        
        # If the first iteration, we overwrite the contents of the file, otherwise we append it
        if ITERATION == 0:
            open_style = 'w'
        else:
            open_style = 'a'
            
        output_file = open('output.csv', open_style, newline='', encoding='utf-8')
        writer = csv.writer(output_file)
        
        if open_style == 'w':
            # Write column headers to output.csv file
            writer.writerow(['JOURNAL','ARTICLE','AUTHOR(S)','LINK','DATA AVAILABILITY STATEMENT','NOTES'])
        
        for url in urls:
            
            start_time = time.perf_counter()
            
            # If the journal for this url is the same as the journal of the previous url, then we already have the configurations
            if url.journal != last_journal:
                
                if ITERATION == 0:
                    LOG.start_new_report(url.journal)
                else:
                    LOG.find_report(url.journal)
                
                # We close the current file to commit any changes, then re-open it for each new journal.
                # This helps prevent data loss, as well as stopping the writer from unexpectedly halting the program
                output_file.close()
                output_file = open('output.csv', 'a', newline='', encoding='utf-8')
                writer = csv.writer(output_file)
                    
                print('\n' + (30 * '-') + '\nJOURNAL:', url.journal)
                
                journal_configs = find_configs(url.journal)
                print('>>  found', len(journal_configs), 'configuration(s)\n')
                LOG.add_configs_to_report(len(journal_configs))
                
                last_journal = url.journal
            
            # Search the page for the data availability statement
            data, write_to_file, retry_url = search_page(url, journal_configs)
            
            if write_to_file:
                writer.writerow(data)
            if retry_url:
                slipped_urls.append(url)
                
            execution_time = time.perf_counter() - start_time
            PROGRESS.update_all(execution_time)
            url_index += 1
                
    except TimeoutException as t:
        print(str(t))
        print('A Timeout error occured!')
        return url_index, slipped_urls
                    
    except Exception as e:
        print(str(e))
        print('An unexpected error occured!')
        return -1, slipped_urls
        
    else:
        return url_index, slipped_urls

        
        
        
def find_configs(journal):
    global configs
    global publishers
    journal_configs = []
    
    for c in configs:
        if c.journal == journal:
            # In journals with many links but few data availability statements, the $publisher-standard functionality
            # was implemented. In these cases, the program finds all configurations under the journal's publisher, and
            # searches through all of them. Examples of this can be seen in the config.csv file provided.
            if c.identifier == '$publisher-standard':
                publisher = find_publisher(c.publisher)
                journal_configs.extend(publisher.get_publisher_standard())
            else:
                journal_configs.append(c)
            
    return journal_configs




def find_publisher(publisher):
    global publishers
    
    for p in publishers:
        if p.has_name(publisher):
            return p
        
    return None
        



def search_page(url, configs):
    global DRIVER
    global ITERATION
    
    exception = ' '
    statement = ' '
    
    # Get page's HTML
    DRIVER.get(url.link)
    html = DRIVER.page_source
    soup = BeautifulSoup(html, 'html.parser')
                
    # Search for Data Availability Statement
    das_found = sc.NOT_FOUND
    for c in configs:
        try:
            if c.tag == None:
                header = soup.find_all(string=c.identifier)
            else:
                header = soup.find_all(c.tag, string=c.identifier)
            
            if len(header) == 1:
                das_found = sc.FOUND
                address_parent = header[0].parent
                
                try:
                    # METHOD 1 : Search by sibling
                    statement = address_parent.find_next_sibling(c.search_tag).get_text()
                except:
                    try:
                        # METHOD 2 : Search by tag
                        statement = address_parent.find(c.search_tag).get_text()
                    except:
                        # METHOD 3 : find ultimate parent
                        while address_parent.get_text() == header[0]:
                            address_parent = address_parent.parent
                        statement = address_parent.get_text()
                
            elif len(header) > 1:
                das_found = sc.AMBIGUOUS
                exception += 'Ambiguity with group ' + str(header) + '. '
            
        except Exception as e:
            das_found = sc.ERROR
            print(str(e))
            exception += 'Could not retrieve data availability statement. '
        
        if das_found == True:
            break
              
    # Author Finding
    author_found = sc.NOT_FOUND
    for c in configs:
        try:
            author_set = set()
            author_string = ''
            
            if c.author_secondary_class == None:
                class_ = soup.find_all(class_=c.author_class)
                for author in class_:
                    if c.get_author_by_child:
                        name = author.findChildren('a', recursive=False)[0].get_text()
                    else:
                        name = author.get_text()
                    if name not in author_set:
                        author_set.add(name)
                        author_string += name + ', '
            else:
                first_names = soup.find_all(class_=c.author_class)
                surnames = soup.find_all(class_=c.author_secondary_class)
                for i in range(len(first_names)):
                    name = first_names[i].get_text() + ' ' + surnames[i].get_text()
                    if name not in author_set:
                        author_set.add(name)
                        author_string += name + ', '
                        
            if author_string != '':
                    author_found = sc.FOUND
            
        except Exception as e:
            author_found = sc.ERROR
            exception += 'Could not retrieve author data.'
            
        if author_found == sc.FOUND:
            break
        
    # Output the print code to the console
    print_code = '[' + sc.PRINT_CODES[das_found + 1] + '][' + sc.PRINT_CODES[author_found + 1] + ']'
    extension = ''
    if '?' in print_code:
        extension += '(AMBIGUOUS IDENTIFIER(S) FOUND [SEE OUTPUT FILE])  '
    if '!' in print_code:
        extension += '(ERROR RETRIEVING DATA)'
    print(print_code, url.link, extension)
    
    title = soup.find(class_=c.title_class).get_text()
    
    retry_url = LOG.add_url_to_report(das=clamp(das_found,0,2), author=clamp(author_found,0,1), iteration=ITERATION)
        
    # Returns the data in format [Journal, Title, Author(s), Link, Data Availability Statement, Notes]
    return [
        url.journal,
        title,
        author_string,
        url.link,
        statement,
        exception
    ], clamp(das_found,0,1), retry_url




#####################
### PROGRAM START ###
#####################

winsound.Beep(500, 1000)

DRIVER = None
LOG = AnalysisLog()
ITERATION = 0

PROGRESS = ProgressWindow()
PROGRESS.start()

configs, urls, publishers = set_up()

for ITERATION in range(0, 5):
    
    if len(urls) == 0:
        break
    elif ITERATION > 0:
        border = ('\n\n' + (30 * '=') + '\n\n')
        print('\n\n' + border + 'RETRYING ' + str(len(urls)) + ' FAILED ARTICLES.\nPass ' + str(ITERATION + 1) + ' (max 5)' + border)
        time.sleep(0.5)
        
    url_index = 0
    while url_index < len(urls):
        
        if url_index > 0:
            print('\n\nProcess halted unexpectedly. Rebooting from item ' + str(url_index) + '...\n')
            DRIVER.quit()
            DRIVER = get_new_driver()
            
        temp_index, urls = run_scraper(configs, urls[url_index:])
        
        if temp_index == -1:
            break
        else:
            url_index += temp_index
    
# The driver needs to be closed, otherwise it stays open in the background
DRIVER.quit()

# It generates a log and saves it to the file. Only the total report is printed to the console
with open('log.txt', 'w') as log_file:
    log_file.write(LOG.generate_log())
print(LOG.get_total_report() + 'Full report available in log.txt')

winsound.Beep(500, 1000)

# Closes the ProgressBar window
PROGRESS.quit()