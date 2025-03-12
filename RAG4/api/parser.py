from bs4 import BeautifulSoup
import requests

url =   'https://stackoverflow.com/questions'
st_useragent = "Mozilla/5.0"
st_accept = "text/html"

headers = {
   "Accept": st_accept,
   "User-Agent": st_useragent
}
def getInfo():
    quotes = []
    recquest = requests.get(url, headers= headers)
    src = recquest.text
    soup = BeautifulSoup(src, 'lxml')
    quote_elements = soup.find_all('h3', class_="s-post-summary--content-title")
    #print(quote_elements)
    for quote_element in quote_elements:
        textWithLink = quote_element.find('a', class_='s-link')
        if textWithLink:
            text = textWithLink.get_text()
            print(text)
    '''
    # the URL of the home page of the target website

    # retrieve the page and initializing soup...

    # get the "Next →" HTML element
    next_li_element = soup.find('li', class_='next')

    # if there is a next page to scrape
    while next_li_element is not None:
        next_page_relative_url = next_li_element.find('a', href=True)['href']

        # get the new page
        page = requests.get(url + next_page_relative_url, headers=headers)

        # parse the new page
        soup = BeautifulSoup(page.text, 'html.parser')

        # scraping logic...

        # look for the "Next →" HTML element in the new page
        next_li_element = soup.find('li', class_='next')
'''

if __name__ == "__main__":
    getInfo()