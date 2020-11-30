import re


def generate_pages_list(total_pages, range, init_page_id):
    page_list = list()
    k = init_page_id

    while k + range - 1 <= total_pages:
        page_list.append((k, k + range -1))
        k += range

    if k + range - 1 < total_pages:
        page_list.append((k, total_pages))

    return page_list


def count_chn(string):
    '''Count Chinese numbers and calculate the frequency of Chinese occurrence.

    # Arguments:
        string: Each part of crawled website analyzed by BeautifulSoup.
    '''
    pattern = re.compile(u'[\u1100-\uFFFDh]+?')
    result = pattern.findall(string)
    chn_num = len(result)
    possible = chn_num / len(str(string))
    return chn_num, possible