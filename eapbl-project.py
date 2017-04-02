import mechanize
from bs4 import BeautifulSoup
import os
import csv
import zipfile
import shutil

'''
Program to download images from the endangered archives collection from http://eap.bl.uk/database/collections.a4d
'''

# list of project urls to downloads
urls = [#'http://eap.bl.uk/database/results.a4d?projID=EAP183',
        # 'http://eap.bl.uk/database/results.a4d?projID=EAP314',
        # 'http://eap.bl.uk/database/results.a4d?projID=EAP458',
        ]

# create a directory to work in and cd into it
try:
    os.mkdir(os.path.join(os.getcwd(), 'eapbl-project'))
except OSError:
    print "Directory 'eapbl-project' already exists! Not creating it again!"

os.chdir('eapbl-project')

br = mechanize.Browser()
abspath = os.path.abspath('.')

for url in urls:

    # TODO: don't download page if already exists
    print "Downloading page: " + url
    html_page = br.open(url).read()

    soup = BeautifulSoup(html_page, 'html.parser')
    results = soup.select('#results')
    heading = results[0].find('th').h3.text     # heading is the name of the project
    heading = heading.replace(':', '-')

    try:
        os.mkdir(os.path.join(abspath, heading))
    except OSError:
        print "Directory " + heading + " already exists! Not creating it again!"

    # don't write page if already exists
    if not os.path.exists(os.path.join(abspath+'/'+heading, 'page.html')):
        with open(os.path.join(abspath+'/'+heading, 'page.html'), 'w') as f:
            f.write(html_page)
    else:
        print "Not writing 'page.html' - already exists"

# list all the directories
dirs = [d for d in os.listdir('.') if os.path.isdir(d) and not d.startswith('.')]

for directory in dirs:
    print "Switching to directory: " + directory
    os.chdir(directory)

    # check if pubs.csv file exists - and write accordingly
    if not os.path.exists('pubs.csv'):
        soup = BeautifulSoup(open('page.html', 'r'), 'html.parser')
        results = soup.select("#results")

        base_url = 'http://eap.bl.uk/database/'

        with open('pubs.csv', 'wb') as f:
            writer = csv.writer(f, delimiter='@', quoting=csv.QUOTE_MINIMAL)
            for tr in results[0].find_all('tr'):
                for x in range(1, len(tr.find_all('td')), 2):
                    title = tr.find_all('td')[x].a.text.encode('utf-8').strip()                 # encode to utf-8
                    link = base_url + tr.find_all('td')[x].a['href'].encode('utf-8').strip()    # encode to utf-8

                    writer.writerow([title, link])
    else:
        print "Not writing 'pubs.csv' already exists"

    # read the pubs.csv, create a folder for every publication
    with open('pubs.csv', 'r') as f:
        abspath = os.path.abspath('.')
        br = mechanize.Browser()
        reader = csv.reader(f, delimiter='@')
        for row in reader:
            title = row[0].replace('/', '-').replace(':', '-')
            link = row[1]

            # skip 1 iteration if zip file of title name exists
            if os.path.exists(title + '.zip'):
                print "Already downloaded and zipped " + title
                continue

            # don't load link and write if thumbs.html already exists
            if not os.path.exists(os.path.join(title, 'thumbs.html')):
                print "Loading publication link: " + link
                page = br.open(link).read()

                try:
                    os.mkdir(os.path.join(abspath, title))
                except OSError:
                    print "Directory: " + title + " already exists! Not creating it again. Not downloading again."

                with open(os.path.join(abspath + '/' + title, 'thumbs.html'), 'w') as f:
                    f.write(page)
            else:
                print "Already exists! folder: " + title + " and thumbs.html"

    # get a list of folder names, cd into it, parse the thumbs.html file and store the urls of the image in a file
    folders = [d for d in os.listdir('.') if os.path.isdir(d) and not d.startswith('.')]
    base_image_url = 'http://eap.bl.uk/'
    for f in folders:
        os.chdir(f)
        print "Switched to folder: " + f + ". Downloading images."
        image_soup = BeautifulSoup(open('thumbs.html', 'r'), 'html.parser')
        ul = image_soup.find('ul', class_='ad-thumb-list')

        try:
            for li in ul.find_all('li'):
                image_link = li.a['href']
                full_image_link = base_image_url + li.a['href']
                image_file_name = image_link.replace('/', '_')
                image_path = os.path.join(os.path.abspath('.'), image_file_name)

                # don't download image if already exists
                if not os.path.exists(image_file_name):
                    # download and write the image
                    print "Retrieving image: " + full_image_link
                    br.retrieve(full_image_link, image_path)
                else:
                    print "Already exists! image: " + image_file_name

        except AttributeError:
            print "AttributeError - There may be no images available yet."
            pass

        os.chdir('..')

    # zip up all folders
    for pub_folder in os.listdir('.'):
        if os.path.isdir(pub_folder):
            shutil._make_zipfile(pub_folder, pub_folder)    # create a zip archive of the folder
            shutil.rmtree(pub_folder)                       # delete the folder & contents

    # return to previous directory
    os.chdir('..')

print "DONE!"
