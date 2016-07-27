# -*-coding:utf-8 -*-
# 微博详情页
import re, json, logging
from bs4 import BeautifulSoup
from weibo_decorator.decorators import parse_decorator


def get_userid(html):
    pattern = re.compile(r'\$CONFIG\[\'oid\'\]=\'(.*)\';')
    m = pattern.search(html)
    return m.group(1) if m else ''


def get_username(html):
    pattern = re.compile(r'\$CONFIG\[\'onick\'\]=\'(.*)\';')
    m = pattern.search(html)
    return m.group(1) if m else ''


def get_userdomain(html):
    """
    :param html:
    :return:用户类型，并不是用户类的那个domain(历史原因，那个类的属性名我还没改...)
    """
    pattern = re.compile(r'\$CONFIG\[\'domain\'\]=\'(.*)\';')
    m = pattern.search(html)
    return m.group(1) if m else ''


@parse_decorator(1)
def _get_statushtml(html):
    soup = BeautifulSoup(html, "html.parser")
    scripts = soup.find_all('script')
    pattern = re.compile(r'FM.view\((.*)\)')
    cont = ''
    for script in scripts:
        try:
            m = pattern.search(script.string)
            if m and 'pl.content.weiboDetail.index' in script.string:
                all_info = m.group(1)
                cont = json.loads(all_info)['html']
        except TypeError:
            return ''
        except Exception as e:
            print('解析错误')
            logging.info('__get__statushtml()错误,具体错误是'.format(e=e))
            logging.info('网页代码为{page}'.format(page=html))
    return cont


@parse_decorator(1)
def get_mid(html):
    cont = _get_statushtml(html)
    soup = BeautifulSoup(cont, 'html.parser')
    try:
        return soup.find(attrs={'action-type': 'feed_list_item'})['mid']
    except TypeError:
        mid_pattern = r'mid=(\d+)'
        mid_matcher = re.search(mid_pattern, html)
        return mid_matcher.group(1) if mid_matcher else ''
    except Exception as e:
        logging.info('get_mid()发生异常,具体异常为{e}'.format(e=e))


@parse_decorator(1)
def get_orignalmid(html):
    """
    :return: 如果本来就是源微博，则返回微博id,否则返回源微博id
    """
    if is_root(html):
        return get_mid(html)
    else:
        cont = _get_statushtml(html)
        soup = BeautifulSoup(cont, 'html.parser')
        return soup.find(attrs={'action-type': 'feed_list_item'})['omid']


@parse_decorator(1)
def get_statussource(html):
    cont = _get_statushtml(html)
    soup = BeautifulSoup(cont, "html.parser")
    try:
        return soup.find(attrs={'action-type': 'app_source'}).text
    except AttributeError:
        try:
            return soup.find(attrs={'class': 'WB_from S_txt2'}).find_all('a')[1].text
        except Exception:
            return ''


@parse_decorator(1)
def get_statustime(html):
    cont = _get_statushtml(html)
    soup = BeautifulSoup(cont, "html.parser")
    try:
        return soup.find(attrs={'node-type': 'feed_list_item_date'})['title']
    except TypeError:
        return ''


@parse_decorator(0)
def get_repostcounts(html):
    cont = _get_statushtml(html)
    soup = BeautifulSoup(cont, "html.parser")
    try:
        reposts = soup.find(attrs={'node-type': 'forward_btn_text'}).find('span').find('em').find_next_sibling().text
        counts = int(reposts)
        return counts
    except ValueError:
        return 0


@parse_decorator(0)
def get_commentcounts(html):
    cont = _get_statushtml(html)
    soup = BeautifulSoup(cont, "html.parser")
    try:
        comments = soup.find(attrs={'node-type': 'comment_btn_text'}).find('span').find('em').find_next_sibling().text
        counts = int(comments)
        return counts
    except ValueError:
        return 0


@parse_decorator(0)
def get_likecounts(html):
    cont = _get_statushtml(html)
    soup = BeautifulSoup(cont, "html.parser")
    try:
        if is_root(html):
            return int(soup.find(attrs={'node-type': 'like_status'}).text)
        else:
            return int(soup.find_all(attrs={'node-type': 'like_status'})[1].text)
    except ValueError:
        return 0


def is_root(html):
    return False if 'omid=' in html else True


@parse_decorator(1)
def get_rooturl(cururl, html):
    if is_root(html):
        return cururl
    else:
        cont = _get_statushtml(html)
        if cont == '':
            return ''
        soup = BeautifulSoup(cont, 'html.parser')
        try:
            url = soup.find(attrs={'node-type': 'feed_list_forwardContent'}).find(attrs={'class': 'S_txt2'})['href']
            return url
        except TypeError:
            return ''
        except AttributeError:
            print('解析错误')
            return ''


@parse_decorator(2)
def get_reposturls(repostinfo):
    """
    :param repostinfo: 转发信息
    :return: 获取所有转发url
    """
    try:
        repost_urls = []
        prestring = 'http://weibo.com'
        soup = BeautifulSoup(repostinfo, 'html.parser')
        contents = soup.find_all(attrs={'node-type': 'feed_list_item_date'})
        for content in contents:
            repost_urls.append(prestring+content['href'])
        return repost_urls
    except AttributeError:
        return []


def get_upperusername(html, defaultname):
    cont = _get_statushtml(html)
    if 'type=atname' in cont:
        try:
            soup = BeautifulSoup(cont, 'html.parser')
            content = soup.find(attrs={'node-type': 'feed_list_content'}).find(attrs={'render': 'ext', 'extra-data': 'type=atname'}).text
            return content[1:]
        except AttributeError:
            return defaultname
        except Exception as e:
            print(e)
            return defaultname
    else:
        return defaultname


if __name__ == '__main__':
    with open('F:/360data/重要数据/桌面/2.html', 'rb') as f:
        source = f.read().decode('utf-8')
    print(get_repostcounts(source))