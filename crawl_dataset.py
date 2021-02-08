import requests
from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.parse import quote_plus
import re


### Pagination 순회하며 이름 얻기
### ==================================================================

# 해당 content가 포켓몬의 이름을 담고 있는지 확인. '포켓몬이름 (포켓몬)' 양식을 따라야 함
def is_name(content):
    return content.split(' ')[-1] == '(포켓몬)'

# URL에 사용 가능하도록 이름 형식을 처리하고, 이름값과 함께 반환
def process_name(name_string):
    names = name_string.split(' ')
    return ('_'.join(names), names[0])

# 한 페이지 내에서 URL에 맞게 변형된 포켓몬 이름 가져오기
def get_names(soup):
    title = soup.select('#mw-content-text > div.category-page__members > ul > li > a')
    names = [process_name(t.text) for t in title if is_name(t.text)]
    # print(names)
    return names

# 포켓몬 위키에 등록된 모든 포켓몬들의 이름과 url 가져오기
def get_all_names(first_page_html):
    all_info = []
    soup = BeautifulSoup(first_page_html.text, 'html.parser')
    while True:
        # print(get_names(soup))
        all_info.extend(get_names(soup))
        next_page_elem = soup.select_one("#mw-content-text > div.category-page__pagination > a.category-page__pagination-next.wds-button.wds-is-secondary")
        if not next_page_elem:
            break
        next_page_url = next_page_elem['href']
        next_response = requests.get(next_page_url)
        soup = BeautifulSoup(next_response.text, 'html.parser')
    return all_info



### 모든 포켓몬들의 공식 일러스트 가져오기
### ==================================================================

# 포켓몬의 url에서 이미지를 다운로드 받는다
def download_image(pokemon_url, pokemon_name):
    response = requests.get(pokemon_url)
    if response.status_code != 200:
        print(f"Failed to get image of {pokemon_name}")
        return
    soup = BeautifulSoup(response.text, 'html.parser')
    image_src= soup.select_one('#pokemon > div:nth-child(1) > div > div.image.rounded > a > img')
    if not image_src:
        image_src = soup.select_one('#mw-content-text > div > div.infobox-pokemon.rounded > div.image.rounded > a > img')
    image_src = image_src["data-src"]
    high_resol_source = ''.join(re.split('/scale-to-width-down/[0-9]*', image_src))
    
    with urlopen(high_resol_source) as f:
        with open('./Pokemons/' + pokemon_name + '.png', 'wb') as h:
            img = f.read()
            h.write(img)

    print(f"Image of {pokemon_name} has been downloaded to pokedex.")



if __name__ == '__main__':
    BASE_URL = 'https://pokemon.fandom.com/ko/wiki/'
    NAMES_URL = 'https://pokemon.fandom.com/ko/wiki/분류:포켓몬_(생물)' # url/모래두지_(포켓몬) 이런 식으로 생김
    
    html_response = requests.get(NAMES_URL)
    # HTTP request error 발생 시
    if html_response.status_code != 200:
        print(f"Request to get pokemon names got error: {html_response.status_code}")
    
    # 모든 포켓몬들의 이름을 얻는다
    all_names = get_all_names(html_response)
    print(f"Total {len(all_names)} pokemons are registered in this pokedex")

    # 모든 포켓몬의 데이터를 다운로드 받는다
    for name_url, name in all_names:
        download_image(BASE_URL + name_url, name)
