import random

# NOTE: This file is unimportant in the operation of the Gaqipu scraper itself, and has been
# provided solely to give insight into how the scraper was tested.

# accuracy_checker.py was created to assist in the manual checking of Gaqipu's scraping results.
# After manually checking 15% of articles used in the scrape, we approximated a 97.86%
# success level in Gaqipu's ability to accurately find and return all of the desired data.


def get_percent():
    global yes_counter
    global total_counter
    try:
        return (round(((yes_counter / (total_counter - 1)) * 100) * 100) / 100)
    except:
        return 100.0


f = open('numbers.txt','r')
f_data = f.read()
used = set()
f_numbers = f_data.split(',')
for n in f_numbers:
    try:
        used.add(int(n))
    except:
        pass
f.close()

f2 = open('no_counter.txt', 'r')
no_counter = int(f2.read())

total_counter = len(used)
yes_counter = total_counter - no_counter


random_num = random.randint(2,2184)

while total_counter < 327:
    total_counter += 1
    while random_num in used:
        random_num = random.randint(2, 2184)
    print('#', total_counter, '\t:  ', random_num, '\t\t(', get_percent(),')')
    success = input('(y/n) > ')
    if success == 'y':
        yes_counter += 1
    else:
        no_counter += 1
        with open('no_counter.txt','w') as n:
            n.write(str(no_counter))
    used.add(random_num)
    with open('numbers.txt','a') as f:
        if total_counter > 1:
            f.write(',' + str(random_num))
        else:
            f.write(str(random_num))
    print('\n\n')
        
total_counter += 1
print('TOTAL YES:', yes_counter)
print('TOTAL NO:', no_counter)
print('PERCENTAGE:', get_percent(), '%')
