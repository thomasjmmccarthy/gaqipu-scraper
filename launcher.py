import subprocess


# launcher.py installs the packages and libraries required to run the Gaqipu web scraper.
# It also initialises a new virtual environment for the scraper to run in.
# Once all requirements have been checked, Gaqipu is launched automatically.



# Calls a list of python-related cmd commands using the subprocess library
def call_python_subprocesses(include_m, commands):
    prefix = 'python '
    if include_m == True:
        prefix += '-m '
    for c in commands:
        subprocess.run(prefix + c)
        


#####################
### PROGRAM START ###
#####################
        
print('Checking Pre-Requisits for Gaqipu Scraper...\n\n\n')
    
call_python_subprocesses(True, [
    'pip install --upgrade pip',
    'pip install selenium',
    'pip install virtualenv',
    'pip install fake_useragent',
    'pip install tk',
    'virtualenv venv'
])

exec(open('venv/Scripts/activate_this.py').read(), {'__file__': 'venv/Scripts/activate_this.py'})

call_python_subprocesses(True, ['pip install chromedriver-autoinstaller',
                'pip install requests',
                'pip install beautifulsoup4'])

print('\n\nPre-requisites met. Launching Gaqipu scraper...\n\n')

call_python_subprocesses(False, ['Gaqipu.py'])
