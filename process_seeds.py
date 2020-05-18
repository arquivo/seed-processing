import requests
from urllib.parse import urlparse
import re
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import click
import time
import os
import multiprocessing
import glob
from timeout import timeout
import fasttext
import argparse

##Setup information

#Load the model to detect the language fo a text
model = fasttext.load_model('lid.176.bin')

#User Agent od the requests
headers = {
    'User-Agent': 'arquivo-web-crawler (compatible; heritrix)'
}

##Next we present the regexes that were found. 
##These have been put on lists so that in a next version it will be easier afterwards to receive these regexes from an external source (exp: google sheet)

##First the regex for the original URL
URLs = ["(.*)hi5.com(.*)", "(.*)groups.yahoo.com(.*)", "(.*)groups.msn.com(.*)", "(.*)communities.msn(.*)"]
combined_urls = "(" + ")|(".join(URLs) + ")"

##Second the regex for the redirect URL 
URLs_redirect = ["(.*)blogin(.*)blogspotURL(.*)", "(.*)sites.comunidades.net(.*)", "(.*)www.hugedomains.com(.*)", "(.*)404.html(.*)"]
# = [http://100vergonhas.blogspot.com/, http://aasantaisabel.no.comunidades.net, http://22blog.com]
combined_redirect_urls = "(" + ")|(".join(URLs_redirect) + ")"

##Third the regex for the redirect URL selenium 
URLs_redirect_selenium = ["(.*)internetswatch.com/?subid=zzt(.*)", "(.*)quatrefeuillepolonaise.xyz(.*)", "(.*)www.hugedomains.com(.*)"]
# = [http://area-de-projecto.blogspot.com]
combined_redirect_urls_selenium = "(" + ")|(".join(URLs_redirect_selenium) + ")"

##Fourth the regex for the body text of each page
text_from_body = ["(.*)domain(.*)sale(.*)", "(.*)web hosting(.*)", "(.*)comprar(.*)domínio(.*)", "(.*)buy(.*)domain(.*)", "(.*)sedo domain parking(.*)",
                    "(.*)internal server error(.*)", "(.*)an error occurred(.*)", "(.*)page cannot be displayed(.*)", 
                    "(.*)site(.*)disabled(.*)", "(.*)is no longer available(.*)", "(.*)the authors have deleted this site(.*)", 
                    "(.*)this site is marked private by its owner(.*)", "(.*)site(.*)not available(.*)", "(.*)page(.*)not found(.*)", 
                    "(.*)website indisponível(.*)", "(.*)a página que procura já não existe(.*)", "(.*)you don't have permission to access this resource.(.*)", 
                    "(.*)pagina de malware(.*)", "(.*)website indisponível(.*)"]
# = [http://www.onegocio.com/, http://caritas.org.cv, http://amanteprofissional.com/blog/, http://www.work.shapept.com, http://www.whitestaff.com, http://www.wokinghamremembers.com, http://www.work-telephone-manners.com/, http://www.yournetindex.com, http://twshg.homestead.com/, https://sergiomago.wordpress.com/, https://sergiomago.wordpress.com/, https://moveispeixotogondomar.wordpress.com/, http://victorneves.arquitectura.g2gm.com/, http://gmtel.com/novo/?option=com_content&task=view&id=24&Itemid=134, http://www.inoxnet.com, http://www.lojasonline.net/sn/directorio/ver_site.cfm?id=19016,  http://www.worknshop.com]
combined_text_from_body = "(" + ")|(".join(text_from_body) + ")"

##Fifth the regex for the body text specifically for blogspot
text_from_blogspot = ["não existem mensagens", "(.*)blog(.*)não existe(.*)", "(.*)blog(.*)does not exist(.*)", "(.*)blog(.*)foi removido(.*)", "(.*)nenhuma postagem(.*)", "(.*)não existem mensagens(.*)"]
# = [http://castingportugal.blogspot.com, http://zhongyaoxue.blogspot.com/, http://greenoport.blogspot.com/, http://aartedafuda.blogspot.com, http://castingportugal.blogspot.com]
combined_text_from_blogspot = "(" + ")|(".join(text_from_blogspot) + ")"

#Parameters
parser = argparse.ArgumentParser(description='Process seeds')
parser.add_argument('-f','--file', help='Localization of the file', default= "./seeds.txt")
parser.add_argument('-l','--lines', help='Number of lines in each temporary file', type=int, default= 1000)
args = vars(parser.parse_args())

##The next two functions can be used if you need to put a timeout. Sometimes the timeout of the get functions does not work properly.
"""
@timeout(10)
def get_redirect_url(url):
    status = "400"
    response = requests.get(url, headers=headers)
    redirect_url = response.url
    status = str(response.status_code)
    return status, redirect_url

@timeout(25)
def driver_get_redirect_url(url):
    driver.get(url)
    time.sleep(20)
    redirect_url = driver.current_url
    return redirect_url
"""


def getlanguage(text):
    """
    Given a text the function detect the language of each line and than return the language with more occurrences.
    """
    list_sentece = text.rstrip().split("\n")
    predict = model.predict(list_sentece)
    dict_predict = {}
    for elem in predict[0]:
        predict_aux = elem[0].replace('__label__','')
        if predict_aux not in dict_predict:
            dict_predict[predict_aux] = 1
        else:
            dict_predict[predict_aux] += 1
    final_predict = max(dict_predict, key=dict_predict.get)
    return final_predict


def process_file(file_name):

    #First setp is initialize the selenium firefox.
    binary = r'/usr/bin/firefox'
    options = Options()
    options.set_headless(headless=True)
    options.binary = binary
    cap = DesiredCapabilities().FIREFOX
    cap["marionette"] = True #optional
    profile = webdriver.FirefoxProfile()
    profile.set_preference("general.useragent.override", "arquivo-web-crawler (compatible; heritrix)")
    driver = webdriver.Firefox(profile, firefox_options=options, capabilities=cap, executable_path="/data/FORA/geckodriver")
    driver.set_page_load_timeout(25) 

    with open(file_name) as file, open(file_name + "_good", 'w') as file_good, open(file_name + "_lixo", 'w') as file_lixo:
        lines = file.readlines()
        with click.progressbar(length=len(lines), show_pos=True) as progress_bar:
            for line in lines:
                progress_bar.update(1)
                url = line.rstrip()
                ##First check if the url match with url consider "trash"
                if re.match(combined_urls, url):
                    file_lixo.write(line)
                else:
                    try:
                        ##Second check the status code of a given url
                        response = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
                        status = str(response.status_code)
                        if status.startswith("2") or status.startswith("3"):
                            ##Third check if the redirect_url match with redirect_url consider "trash"
                            redirect_url = response.url
                            if re.match(combined_redirect_urls, redirect_url):
                                file_lixo.write(line)
                            else:
                                ##Fourth check if the redirect_url given by selenium match with redirect_url consider "trash"
                                ##This step is used due to the fact that there are extreme cases of redirects. Mainly because of this site: http://casteleiro-sabugal.new.fr
                                driver.get(url)
                                time.sleep(20)
                                redirect_url_selenium = driver.current_url
                                if re.match(combined_redirect_urls_selenium, redirect_url_selenium):
                                    file_lixo.write(line)
                                ##http://casteleiro-sabugal.new.fr
                                elif url + "/listing" in redirect_url_selenium:
                                    file_lixo.write(line)
                                else:
                                    ##Fifth check if the body of the text present in the url match specific strings
                                    el = driver.find_element_by_tag_name('body')
                                    parsed_uri = urlparse(url)
                                    result = '{uri.netloc}'.format(uri=parsed_uri)
                                    if el.text == '':
                                        file_lixo.write(line)
                                    elif re.match(combined_text_from_body, el.text.lower().replace('\n', ' ')):
                                        file_lixo.write(line)
                                    elif result + "is for sale" in el.text.lower(): ##http://www.unitel.net/
                                        file_lixo.write(line)
                                    elif el.text.startswith("Index of /"): ##http://cam.cv
                                        file_lixo.write(line)
                                    elif "create an account in 30 seconds, and you may continue with the registration of" in el.text.lower() and ".ws" in url: ##http://www.workingonline.ws
                                        file_lixo.write(line)
                                    elif re.match(combined_text_from_blogspot, el.text.lower().replace('\n', ' ')) and "blogspot" in url:
                                        file_lixo.write(line)
                                    else:
                                        ##Last check if the language of the text
                                        lang = getlanguage(el.text)
                                        if lang == "zh" or lang == "ja" or lang == "ko" or lang == "id":
                                            file_lixo.write(line)
                                        else:
                                            #Next Feature. It is could be a cool feature see if the redirect url change, but does not work very well
                                            file_good.write(line)
                        else:
                            file_lixo.write(line)
                    except:
                        #Problems with some URLs which can affect the ".get()". Exp: http://www.wolfd.com, http://www.wolfcare.com/
                        file_lixo.write(line)
    driver.quit()


def script():

    ##Process seed.txt

    #Get the parameters
    file_to_process = args['file']
    lines = args['lines']

    #Sort and get unique urls
    uniq_file = file_to_process.replace(".txt", "_uniq.txt")
    if not os.path.exists(uniq_file):
        os.system("sort " + file_to_process +" | uniq -u > " + uniq_file)

    #Split the file into multifiles to do multiprocessing
    os.system("split --lines=" + str(lines) + " --numeric-suffixes --suffix-length=2 " + uniq_file + " t_tmp")    

    #Process each file in paralel
    p = multiprocessing.Pool()
    for f in glob.glob("t_tmp*"):
        p.apply_async(process_file, [f]) 

    p.close()
    p.join()
    
    #Concatenate all the files and eliminate the tmp files
    os.system("cat ./*_lixo > seeds_lixo.txt")
    os.system("cat ./*_good > seeds_good.txt")
    os.system("rm -rf t_tmp*")


if __name__ == '__main__':
    script()