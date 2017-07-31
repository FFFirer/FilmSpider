# -*- coding:utf-8 -*-

import re
import urllib
import urllib.request
import time
import random
import mysql.connector
import json

url_root = 'http://www.xl720.com/'
HEADERs = {
    'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'
}
conn = mysql.connector.connect(user='root', password='123456', database='film')
insertSQL = 'insert into filmdetail (postId, name, direct, screenWriter, mainPerformer, style, officalWebsite, location, language, publishTime, timeLength, otherName, IMDblink) values ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'

#cate为json,其他为txt
logCateFileName = "logCate"
logWaitFileName = "logWait"
logDoneFileName = "logDone"
logUrlFileName = "log"
logNextUrlFileName = "logNextUrl"
logPageFileName = "logPage"
logErrorFileName = "logError"

#定义一个电影类
class film(object):


    def __init__(self, postid, name, direct, screenwriter, mainperformer, style, officalwebsite, location, lang, pubtime,
     timelen, othername, IMDblink):
        self.name = name
        self.postid = postid
        self.direct = direct
        self.screenwriter = screenwriter
        self.mainperformer = mainperformer
        self.style = style
        self.officalwebsite = officalwebsite  
        self.location = location
        self.lang = lang
        self.pubtime = pubtime
        self.timelen = timelen
        self.othername = othername
        self.IMDblink = IMDblink


#获取链接所指页面内容
def getPageContent(url,headers):
    addlog(logUrlFileName,url)
    # print("url 已写入log")
    max_try = 10
    req = urllib.request.Request(url=url, headers=headers) 
    for i in range(max_try):
        try:
            html = urllib.request.urlopen(req,timeout=10).read().decode('utf-8')
            break
        except urllib.request.URLError as e:
            if(i < max_try):
                max_try -= 1
                print("Timed out! Try Again: "+str(i))
                continue
            else:
                addlog(logErrorFileName,url+": "+str(e))
    
    return html

#判断是否存在
def isExist(postid):
    querySQL = 'select * from filmdetail where postId=%s'
    cursor = conn.cursor()
    cursor.execute(querySQL, [postid])
    res = cursor.fetchall()
    cursor.close()
    if(len(res) == 0):
        return True
    else:
        return False

#从首页获取分类列表
def getCateList(htmlContent):
    href_dict = {}
    href_wait = []
    pattern_ul = r'<ul id="nav" class="sf-menu">(.*?)</ul>'
    match_ul = re.findall(pattern_ul, htmlContent, re.S | re.M)
    #找出列表中的所有链接
    if (len(match_ul) > 0):
        pattern_href = r'<a href="(http://www.xl720.com/category/.*?)">(.*?)</a>'
        match_hrefs = re.findall(pattern_href, match_ul[0], re.S | re.M)
        for i in range(len(match_hrefs)):
            href_dict[str(match_hrefs[i][0])] = match_hrefs[i][1]
            href_wait.append(match_hrefs[i][0])
    else:
        print('Null')

    return href_dict, href_wait

#分类列表下获取下一个链接的地址
def getNextUrl(html):
    print("获取下一页地址")
    pattern_next = r'<a class="nextpostslink" rel="next" href="(.*?)">»</a>'  #获取下跳链接的正则表达式
    match_next = re.findall(pattern_next, html, re.S | re.M)
    if (len(match_next) > 0):
        return match_next[0]
    else:
        return 'null'

#获取匹配列表第一项
def getMatchesFirst(matchlist):
    if(len(matchlist) > 0):
        return matchlist[0]
    else:
        return "null"

#去掉字符串中的a标签
def removeLinkText(texts):
    pattern_af = r'<a href=.*? target="_blank" rel="bookmark">'
    pattern_ab = r'</a>'

    match_ab = re.sub(pattern_ab, "", texts)
    match_af = re.sub(pattern_af, "", match_ab)

    return match_af

#获取详情页面中的各种信息
def getFilmDetail(pagecontent):

    pattern_postId = r'<div id="post-(.*?)" class="entry lazyload"><h1 class="postli-1">'
    pattern_info = r'<div id="info">.*?</div>'
    pattern_name = r'<h1 class="postli-1">(.*?)</h1>'
    pattern_direct = r'<div id="info">导演: <a href.*?>(.*?)</a><br />'
    pattern_screenwriter = r'<br /> 编剧: <a href=.*?>(.*?)</a><br />'
    pattern_mainperformer = r'<br /> 主演: (.*?)<br />'
    pattern_style = r'<br /> 类型: (.*?)<br />'
    pattern_officalwebsite = r'<br /> 官方网站: (.*?)<br />'
    pattern_location = r'<br /> 制片国家/地区: (.*?)<br />'
    pattern_language = r'<br /> 语言: (.*?)<br />'
    pattern_publishtime = r'<br /> 上映日期: (.*?)<br />'
    pattern_timelen = r'<br /> 片长: (.*?)<br />'
    pattern_othername = r'<br /> 又名: (.*?)<br />'
    pattern_IMDblink = r'<br /> IMDb链接: (.*?)</div>'

    contents = []
    #print("开始匹配")
    #获取简介信息
    match_postId = re.findall(pattern_postId, pagecontent, re.S|re.M)
    PostId = getMatchesFirst(match_postId)
    contents.append(PostId)

    match_info = re.findall(pattern_info, pagecontent, re.S | re.M)
    Info = getMatchesFirst(match_info)

    match_name = re.findall(pattern_name, pagecontent, re.S | re.M)
    Name = getMatchesFirst(match_name)
    contents.append(Name)

    if (Info != "null"):
        match_direct = re.findall(pattern_direct, Info, re.S | re.M)
        Direct = getMatchesFirst(match_direct)
        Direct = removeLinkText(Direct)
        contents.append(Direct)

        match_screenwriter = re.findall(pattern_screenwriter, Info, re.S | re.M)
        ScreenWriter = getMatchesFirst(match_screenwriter)
        ScreenWriter = removeLinkText(ScreenWriter)
        contents.append(ScreenWriter)

        match_mainperformer = re.findall(pattern_mainperformer, Info, re.S | re.M)
        MainPerformer = getMatchesFirst(match_mainperformer)
        MainPerformer = removeLinkText(MainPerformer)
        contents.append(MainPerformer)

        match_style = re.findall(pattern_style, Info, re.S | re.M)
        Style = getMatchesFirst(match_style)
        Style = removeLinkText(Style)
        contents.append(Style)

        match_officalwebsite = re.findall(pattern_officalwebsite, Info, re.S | re.M)
        OfficalWebsite = getMatchesFirst(match_officalwebsite)
        OfficalWebsite = removeLinkText(OfficalWebsite)
        contents.append(OfficalWebsite)

        match_location = re.findall(pattern_location, Info, re.S | re.M)
        Location = getMatchesFirst(match_location)
        Location = removeLinkText(Location)
        contents.append(Location)

        match_language = re.findall(pattern_language, Info, re.S | re.M)
        Language = getMatchesFirst(match_language)
        Language = removeLinkText(Language)
        contents.append(Language)

        match_publishtime = re.findall(pattern_publishtime, Info, re.S | re.M)
        PublishTime = getMatchesFirst(match_publishtime)
        PublishTime = removeLinkText(PublishTime)
        contents.append(PublishTime)

        match_timelen = re.findall(pattern_timelen, Info, re.S | re.M)
        TimeLen = getMatchesFirst(match_timelen)
        TimeLen = removeLinkText(TimeLen)
        contents.append(TimeLen)

        match_othername = re.findall(pattern_othername, Info, re.S | re.M)
        OtherName = getMatchesFirst(match_othername)
        OtherName = removeLinkText(OtherName)
        contents.append(OtherName)

        match_IMDblink = re.findall(pattern_IMDblink, Info, re.S | re.M)
        IMDbLink = getMatchesFirst(match_IMDblink)
        contents.append(IMDbLink)

        #thisFilm = film(PostId, Name, Direct, ScreenWriter, MainPerformer, Style, OfficalWebsite, Location, Language,
        #PublishTime, TimeLen, OtherName, IMDbLink)
        # print("获取成功")
        return contents
    else:
        return [PostId, Name, "null", "null", "null", "null", "null", "null", "null", "null", "null", "null", "null"]

#获取一个页面中所有电影列表的链接，返回一个链接列表
def getPerpageFilmlist(html, cate):
    print("获取电影列表: "+cate)
    #<h3 class="entry-title  postli-1"><a href="(.*?)" title=".*?" rel="bookmark" target="_blank">。*？</a></h3>
    pattern_filmlink = r'<h3 class="entry-title  postli-1"><a href="(.*?)" title=".*?" rel="bookmark" target="_blank">.*?</a></h3>'
    match_film = re.findall(pattern_filmlink, html, re.S|re.M)
    print("获取完毕")
    #print(match_film)
    return match_film

#保存电影
def SaveFilm(detail,url):
    cursor = conn.cursor()
    # cursor.execute(insertSQL, detail)
    # conn.commit()
    # cursor.close()
    try:
        cursor.execute(insertSQL, detail)
        conn.commit()
        cursor.close()
    except mysql.connector.Error as e:
        print("Mysql errpr: " + str(e) + "\n" + url)
        addlog(logErrorFileName,url+": "+str(e))

#获取所有电影并写入数据库
def getAllFilms(url, cate):

    pattern_page = r'/page/([0-9]+?)$'
    match_page = re.findall(pattern_page, url, re.S|re.M)
    pageCount = getMatchesFirst(match_page)

    html = getPageContent(url, HEADERs)
    print("======Downloaded======")
    filmUrls = getPerpageFilmlist(html, cate)
    nextUrl = getNextUrl(html)
    writelog(logPageFileName, url)
    writelog(logNextUrlFileName, nextUrl)
    print("开始对该页面进行搜索 页数："+pageCount)
    for everUrl in filmUrls:
        filmDetailPage = getPageContent(everUrl,HEADERs)
        filmDetail = getFilmDetail(filmDetailPage)
        '''
        print(filmDetail.postid)
        print(filmDetail.name)
        print(filmDetail.direct)
        print(filmDetail.screenwriter)
        print(filmDetail.mainperformer)
        print(filmDetail.style)
        print(filmDetail.officalwebsite)
        print(filmDetail.location)
        print(filmDetail.lang)
        print(filmDetail.pubtime)
        print(filmDetail.timelen)
        print(filmDetail.othername)
        print(filmDetail.IMDblink)'''
        if(isExist(filmDetail[0])):
            SaveFilm(filmDetail, everUrl)
            print("success: "+filmDetail[1])
            # for i in filmDetail:
            #     print(i)

        else:
            print("已存在: "+filmDetail[1])
            continue
        
    if(nextUrl != 'null'):
        # print(nextUrl)
        getAllFilms(nextUrl, cate)
    else:
        writelog(logPageFileName, "")
        print("no next url!")
# def writelog(filename,url):
#     with open(filename,'w') as f:
#         f.write(url)

def getcate(url):
    pattern_cate = r'category/(.*?)/page'
    match_cate = re.findall(pattern_cate, url, re.S|re.M)
    cate = getMatchesFirst(match_cate)
    return cate

#将url写入log
def writelog(filename,content):
    with open(filename+'.txt','w') as f:
        f.write(content)

def addlog(filename,content):
    try:
        with open(filename+'.txt','a') as f:
            f.write(content+"\n")
    except:
        print("未找到文件")
        writelog(filename,content)
        print("创建成功，写入")

    
#将字典写入json
def writedict2json(filename,content):
    jscontent = json.dumps(content)
    with open(filename+'.json', 'w') as f:
        f.write(jscontent)
#将列表写入txt
def writelist2txt(filename,content):
    with open(filename+'.txt', 'w') as f:
        for item in content:
            f.write(str(item))
            f.write('\n')
#读取log
def readlist(filename):
    log = []
    with open(filename+'.txt','r') as f:
        c = f.read()
        log = c.splitlines()
        return log
def readjson(filename):
    with open(filename+'.json','r') as f:
        # return json.loads(f.read())
        try:
            return json.loads(f.read())
        except:
            return json.loads("{}")


def readUrl(filename):
    with open(filename+'.txt','r') as f:
        return f.read()
#主程序
def main():
    print('初始化log...')
    writelog(logUrlFileName,str(time.localtime(time.time()))+'\n')
    catelog = readjson(logCateFileName)
    waitlog = readlist(logWaitFileName)
    donelog = readlist(logDoneFileName)
    pagelog = readUrl(logPageFileName)
    pageCate = getcate(pagelog)
    pageCateLink = "http://www.xl720.com/category/"+pageCate
    hrefs_waiting = []
    hrefs_done = []
    
    print("检查日志")
    if(catelog == {}):
        print("无日志，重新开始")
        index = getPageContent(url_root, HEADERs)
        cates = getCateList(index)
        hrefs_dict = cates[0]
        hrefs_waiting = cates[1]
        writedict2json(logCateFileName,hrefs_dict)
        writelist2txt(logWaitFileName,hrefs_waiting)
        writelist2txt(logDoneFileName,hrefs_done)
    else:
        print('有日志，加载日志')
        hrefs_dict = catelog
        hrefs_waiting = waitlog
        hrefs_done = donelog
         
    # print(hrefs_waiting)
    # print(hrefs_dict)
    # print(hrefs_done)

    if(pagelog != "null" and pageCateLink in hrefs_waiting):
        print("有pagelog记录，继续爬")
        cateCurrent = hrefs_dict[pageCateLink]
        print(cateCurrent)
        getAllFilms(pagelog, cateCurrent)
        hrefs_waiting.remove(pageCateLink)
        hrefs_done.append(pageCateLink)
    else:
        print("没有log")
        pass
    
    print("重头开始爬")
    for url_cate in hrefs_waiting:
        cateCurrent = hrefs_dict[url_cate]
        print('开始搜索：'+cateCurrent)
        getAllFilms(url_cate, cateCurrent)
        
        #修改log
        hrefs_waiting.remove(url_cate)
        hrefs_done.append(url_cate)
        writelist2txt(logWaitFileName,hrefs_waiting)
        writelist2txt(logDoneFileName,hrefs_done)
        if(len(hrefs_waiting) == 0):
            print("Game Over")
            break
    print('bye bye')
if __name__ == '__main__':
    main()
