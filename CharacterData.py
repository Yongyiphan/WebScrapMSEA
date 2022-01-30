import pandas
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as BS
import time
import requests
from webdriver_manager.chrome import ChromeDriverManager
from ComFunc import *
mainUrl = 'https://grandislibrary.com'
classesUrl = 'https://grandislibrary.com/classes'




def StartScraping():
    start = time.time()
    CharacterDF, UnionDF, MWeaponDF, SWeaponDF = navigateClasses()
    
    CharacterDF = cleanCharDF(CharacterDF)
    
    UnionDF = cleanUDF(UnionDF)

    CharacterDF.to_csv('DefaultData\\CharacterData\\CharacterData.csv')
    UnionDF.to_csv('DefaultData\\CharacterData\\UnionData.csv')
    MWeaponDF.to_csv('DefaultData\\CharacterData\\ClassMainWeapon.csv')
    SWeaponDF.to_csv('DefaultData\\CharacterData\\ClassSecWeapon.csv')

    
    end = time.time()
    print(f'Total time taken: {end-start}')
    return

def navigateClasses():

    browser = webdriver.Chrome(ChromeDriverManager().install())

    browser.get(classesUrl)

    browser = scrollDown(browser, 10)
    
    lazyLoadDiv = browser.find_elements(By.CLASS_NAME, 'lazyload-wrapper')
    
    ClassesLinks = []
    for a in lazyLoadDiv:
        classChunkList = a.find_elements_by_tag_name('a')
        for link in classChunkList:
            ClassesLinks.append(link.get_attribute('href'))
            

    browser.close()
    
    
    request_session = requests.session()
    CharacterDF = pandas.DataFrame()
    UnionDF = pandas.DataFrame()
    ClassMWeaponDF = pandas.DataFrame()
    ClassSWeaponDF = pandas.DataFrame()
    
    ignoreClasses = ['Beast-Tamer', 'Jett']
    for link in ClassesLinks:
        if any(c.lower() in link.lower() for c in ignoreClasses) == True:
            continue
        
        charCollection = retrieveClassPage(link, request_session)
        CharacterDF = CharacterDF.append(charCollection[0], ignore_index=True)
        UnionDF = UnionDF.append(charCollection[1],ignore_index=True)
        ClassMWeaponDF = ClassMWeaponDF.append(charCollection[2], ignore_index=True)
        ClassSWeaponDF = ClassSWeaponDF.append(charCollection[3], ignore_index=True)

    
    return CharacterDF, UnionDF, ClassMWeaponDF, ClassSWeaponDF

def scrollDown(browser, noOfScrollDown):
    
    body = browser.find_element_by_tag_name("body")
    
    while noOfScrollDown >=0:
        body.send_keys(Keys.PAGE_DOWN)
        noOfScrollDown -=1
        
        
    
    return browser
    
def retrieveClassPage(subUrl, session):
    start = time.time()
    PageContent = session.get(subUrl)
    
    MainContent = BS(PageContent.content, 'lxml')
    ClassName = MainContent.find('h1').next

    ClassDetailsTable = MainContent.find_all('tbody')[0].find_all('tr')
    
    if ClassName.find("Fire") != -1 and ClassName.find('Poison') != -1:
        ClassName = 'Fire Poision'
    elif ClassName.find("Ice") != -1 and ClassName.find('Lightning') != -1:
        ClassName = 'Ice Lightning'
    
    ResistanceGrp = ['Demon', 'Xenon']
    specialMod = [',', '+']
    CS = {}
    CS['ClassName'] = ClassName
    for tr in ClassDetailsTable:
        th = tr.find('th')
        td = tr.find('td')
        if th.get_text().find('Class Group') != -1:
            
            faction = removeN(td.next, '\n', '')
            if any(c.lower() in faction.lower() for c in ResistanceGrp) == True:
                faction = 'Resistance'
            elif ClassName == 'Zero':
                faction = 'Transcendant'
            elif ClassName == 'Kinesis':
                faction = 'FriendStory'
            CS['Faction'] = faction
            
        elif th.get_text().find('Job Group') != -1:
            CT = td.next
            if any(m in td.get_text() for m in specialMod) == True:
                CT = 'SPECIAL'
            CS['ClassType'] = CT
        elif th.get_text().find('Primary Stat') != -1:
            stat = td.next
            if any(m in td.get_text() for m in specialMod) == True:
                stat = 'SPECIAL'
            CS['MainStat'] = stat
        elif th.get_text().find('Secondary Stat') != -1:
            stat = td.next
            if any(m in td.get_text() for m in specialMod) == True:
                stat = 'SPECIAL'
            
            CS['SecStat'] = stat
            
        elif th.get_text().find('Legion') != -1:
            UET = 'FLAT'
            UE = removeN(td.contents[0].get_text(), [',', 'and'], '')
            UES = td.contents[1].get_text()
            UES = removeN(UES, ["+","(", ")"], '')
            UES = UES.split('/')
            
            if UES[-1].find('%') != -1:
                UET = 'PERC'
                UES[-1] =UES[-1].split('%')[0]

            if UE.find('%') != -1:
                UE = UE.split('%')[1]
                if UE.find('(') != -1:
                    UE = UE.split('(')[0] 

            CS['UnionEffect'] = UE
            CS['UnionEffectStat'] = UES
            CS['UnionEffectType'] = UET
        elif th.get_text().find('Weapon') != -1:
            WeaponList = []
            
            if "PWeap" in CS:
                for weap in td:
                    t = removeN(weap.get_text(), '\n', '')
                    if ClassName == 'Zero':
                        t = 'Heavy Sword'
                    WeaponList.append(removeFLSpace(t))
                CS['SWeap'] = WeaponList
            else:
                for weap in td:
                    t = removeN(weap.get_text(), '\n', '')
                    t = t[1:] if t[0] == ' ' else t
                    if ClassName == 'Zero':
                        t = 'Long Sword'
                    WeaponList.append(t)
                CS['PWeap'] = WeaponList          

    UnionD = {
            'Effect' : CS['UnionEffect'],
            'Rank B' : CS['UnionEffectStat'][0],
            'Rank A' : CS['UnionEffectStat'][1],
            'Rank S' : CS['UnionEffectStat'][2],
            'Rank SS' : CS['UnionEffectStat'][3],
            'Rank SSS' : CS['UnionEffectStat'][4],
            'EffectType' : CS['UnionEffectType']
        }
    UnionDF = pandas.DataFrame(
        UnionD, index = [0]
    )
    CS.pop('UnionEffectStat')
    
    tempJ = []
    tempW = []
    for w  in CS['PWeap']:
        tempJ.append(CS['ClassName'])
        tempW.append(w)
    MWeapon = {
            'ClassName' : tempJ ,
            'WeaponType' : tempW
        }
    ClassMWeaponDF = pandas.DataFrame(
        MWeapon   
    )
    CS.pop('PWeap')
    tempJ = []
    tempW = []
    for w  in CS['SWeap']:
        tempJ.append(CS['ClassName'])
        tempW.append(w)
    SWeapon = {
            'ClassName' : tempJ ,
            'WeaponType' : tempW
        }
    ClassSWeaponDF = pandas.DataFrame(
        SWeapon
    )
    
    CS.pop('SWeap')
    
    CharacterDF = pandas.DataFrame(CS, index=[0])

    smallCollection = [CharacterDF, UnionDF, ClassMWeaponDF, ClassSWeaponDF]
    
    end = time.time()
    print(f' {ClassName} added in {end-start}')    
    
    return smallCollection


def cleanUDF(DF):
    
    DF.drop_duplicates(keep='first', inplace=True)
    DF = DF.reset_index(drop = True)
    
    return DF

def cleanCharDF(DF):
    
    tempCT = pandas.Series(DF['ClassType']).str.replace("Archer", "Bowman")
    DF['ClassType'] = tempCT
    
    return DF

if __name__ == '__main__':
    StartScraping()

