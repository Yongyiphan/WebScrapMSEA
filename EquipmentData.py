import pandas
import requests
import lxml
import cchardet
import time
from bs4 import BeautifulSoup
from ComFunc import *

### PROGRAM FLOW ####
# MAIN PAGE -> GET EQUIPNAME/LINK 
# TRAVERSE TO EQUIPLINK PAGE -> GET WEAPON SET'S LINK
# TRAVERSE TO WEAPON'LINK -> RECORD INFORMATION
root = 'DefaultData'
defaulturl = "https://maplestory.fandom.com"
weaponUrl = "/wiki/Category:Weapons"
secUrl = "/wiki/Category:Secondary_Weapons"
equipSetUrl = "/wiki/Category:Equipment_Sets"
genesisWeapUrl = "/wiki/Sealed_Genesis_Weapon_Box"
superiorEquipUrl = "/wiki/Category:Superior_Equipment"
androiHeartUrl = "https://maplestory.fandom.com/wiki/Android_Heart"
MainStat = ['STR','DEX','INT','LUK']
EquipSetTrack = [
    'Sengoku', 'Boss Accessory', 'Pitched Boss', 'Seven Days', "Ifia's Treasure",'Mystic','Ardentmill','Blazing Sun'
    ,'8th', 'Root Abyss','AbsoLab', 'Arcane'
    ,'Lionheart', 'Dragon Tail','Falcon Wing','Raven Horn','Shark Tooth'
    ,'Gold Parts','Pure Gold Parts'
    ]
WeapSetTrack = [
    'Utgard', 'Lapis','Lazuli'
    ,'Fafnir','AbsoLab', 'Arcane', 'Genesis'
    ]
ArmorSet = ['Hat','Top','Bottom','Overall','Shoes','Cape','Gloves']
Mclasses = ['Warrior','Knight', 'Bowman', 'Archer', 'Magician','Mage','Thief', 'Pirate']
##NAMING CONVENTION
#NAME, SET, TYPE, CLASSTYPE, SLOT
#LEVEL, MS, SS, AS, HP, MP, DEF, ATK, MATK
SetCol = ['EquipSet','SetEffect','MainStat', 'SecStat','AllStat','HP','MP','DEF','ATK','MATK','NDMG','IED','BDMG','CDMG']
WeapCol = ['WeaponSet','WeaponType','Level','AtkSpd','MainStat','SecStat','HP','DEF','ATK','MATK','SPD','BDMG','IED']
ArmorCol = ['EquipSet','ClassType','EquipSlot','EquipLevel','MainStat','SecStat','AllStat', 'HP','MP','DEF','ATK','MATK','SPD','JUMP','IED']
AccCol = ['EquipName','EquipSet','ClassType','EquipSlot','EquipLevel','MainStat','SecStat','AllStat','HP','MP','DEF','ATK','MATK','SPD','JUMP','IED']
trackMinLevel = 140

def StartScraping():


    ###WEAPON ==> GOTO LINK ==> GOTO HEADER LINK
    ##ITERATE TABLE return DF

    start = time.time()

    WeaponDF = pandas.DataFrame()
    ArmorDF = pandas.DataFrame()
    AccessoriesDF = pandas.DataFrame()
    SetEffectDF = pandas.DataFrame()

    ##PROCESS
    ###EQUIPMENT_SETS ==> GATHER TRACKSET LINKS ###
    ##ITERATE TRACKSET LINKS
    ## CREATE 2 DATAFRAME
    ## 1: EQUIPMENT SET EFFECTS
    ## 2: EQUIPMENT ARMOR/ACCESSORIES
    SetEffectDF, ArmorDF, AccessoriesDF = retrieveEquipmentSet(requests.session())
    
    ##RETRIEVE TYRANT
    tAcc, tArmor = retrieveTyrant(requests.session())


    SetEffectDF = cleanSetEffectDF(SetEffectDF)
    
    WeaponDF = retrieveWeapDF(requests.session())
    WeaponDF = cleanWeapDF(WeaponDF)
        
    ArmorDF = ArmorDF.append(tArmor, ignore_index=True)
    ArmorDF = ArmorDF[ArmorCol]
    ArmorDF = ArmorDF.fillna(0)
    ##MANUALLY ADDING TYRANY



    AccessoriesDF = AccessoriesDF.append(tAcc, ignore_index=True)
    EmblemData = {}
    EmblemData['EquipName'] = "Emblem"
    EmblemData['EquipSet'] = "Emblem"
    EmblemData['ClassType'] = 'Any'
    EmblemData['EquipSlot'] = 'Emblem'
    EmblemData['EquipLevel'] = 100
    EmblemData['AllStat'] = 10
    EmblemData['ATK'] = 2
    EmblemData['MATK'] = 2
    EmblemDF = pandas.DataFrame(EmblemData, index=[0])
    AccessoriesDF = AccessoriesDF.append(EmblemDF, ignore_index=True)
    AccessoriesDF = AccessoriesDF[AccCol]
    AccessoriesDF = AccessoriesDF.fillna(0)
    
    SecWeapDF = retrieveSecWeap(requests.session())
    SecWeapDF = cleanSecWeap(SecWeapDF)
    SecWeapDF = SecWeapDF.fillna(0)
    
    SetEffectDF.to_csv('DefaultData\\EquipmentData\\SetEffectData.csv')
    WeaponDF.to_csv('DefaultData\\EquipmentData\\WeaponData.csv')
    ArmorDF.to_csv('DefaultData\\EquipmentData\\ArmorData.csv')
    AccessoriesDF.to_csv('DefaultData\\EquipmentData\\AccessoriesData.csv')
    SecWeapDF.to_csv('DefaultData\EquipmentData\\\SecondaryWeapData.csv')
    
    end = time.time()

    print(f"Total time taken is {end-start}")
    return

def retrieveEquipmentSet(session):

    equipSetLinkListPage = session.get(defaulturl + equipSetUrl)
    soup = BeautifulSoup(equipSetLinkListPage.content, 'lxml')
    linkLists = soup.find_all('a', class_='category-page__member-link')

    ignoreSetKeyWords = ['Immortal', 'Eternal','Walker','Anniversary']

    ArmorDF = pandas.DataFrame()
    AccessoriesDF = pandas.DataFrame()
    SetEffectDF = pandas.DataFrame()

    for links in linkLists:
        linkText = links.next.lower()
        for li in EquipSetTrack:
            if li.lower() in linkText and any(ig.lower() in linkText for ig in ignoreSetKeyWords) == False:

                Mstart = time.time()
                
                tempCollection = retrieveContents(links['href'], session, li)
                
                SetEffectDF = SetEffectDF.append(tempCollection['SetEffect'], ignore_index=True) 
                ArmorDF = ArmorDF.append(tempCollection['Armor'], ignore_index=True)
                AccessoriesDF = AccessoriesDF.append(tempCollection['Accessories'], ignore_index=True)
                
                Mend = time.time()
                print(f"{li} equips added in {Mend - Mstart }. ")
                break

    return SetEffectDF, ArmorDF, AccessoriesDF

def retrieveContents(subUrl, session, equipSet):

    #SCRAPING EACH PAGE
    subPage = session.get(defaulturl + subUrl)
    if subPage.status_code != 200:
        return
    
    totalPageContent = BeautifulSoup(subPage.content, 'lxml')
    wikitables = totalPageContent.find_all('table', class_="wikitable")


    smallCollection = {}
    smallCollection['SetEffect'] = retrieveSetEffect(wikitables[0], equipSet)
    smallCollection['Armor'], smallCollection['Accessories'] = retrieveEquips(wikitables[1], equipSet)

    
    return smallCollection

def retrieveSetEffect(wikitable, equipSet):

    #SCRAPING EACH TABLE
    start = time.time()
    currentDF = pandas.DataFrame()

    tdContent = wikitable.find_all('td')

    startCounter = len(tdContent) % 2

    for i in range(startCounter, len(tdContent), 2):
        SetData = {}
        SetData['EquipSet'] = equipSet
        SetData['SetEffect'] = tdContent[i].next.next.split(" ")[0]
        statList = tdContent[i].get_text(separator = '\n').split('\n')[1:]
        SetData.update(assignToDict(statList))
    
        currentDF = currentDF.append(SetData, ignore_index=True)
        
    currentDF = currentDF.fillna(0)
    
    return currentDF

def retrieveEquips(wikitable, equipSet):

    ArmorDF = pandas.DataFrame()
    AccDF = pandas.DataFrame()
    tdContent = wikitable.find_all('td')

    for i in range(0, len(tdContent), 4):
        EquipData = {}
        EquipData['EquipSet'] = removeN(equipSet,  ['\n'], '')
        equipName = tdContent[i].get_text()
        equipslot = removeN(tdContent[i+1].get_text(),'\n', '')
        EquipData['EquipSlot'] = equipslot.split(' ')[0] if equipslot.find('Pocket') != -1 else equipslot 
        equipType = 'Armor' if EquipData['EquipSlot'] in ArmorSet else 'Accessories'
        if equipType == 'Accessories':
            TequipName = removeN(equipName, ['\n', ":"], '')
            TequipName = TequipName.split(' ')
            if EquipData['EquipSlot'] in TequipName:
                TequipName.remove(EquipData['EquipSlot'])
            for mc in Mclasses:
                if mc in TequipName:
                    TequipName.remove(mc)
            
            TequipName = ' '.join(TequipName)
            EquipData['EquipName'] = TequipName
            
            
        
        requirements = tdContent[i+2].get_text(separator = '\n').split("\n")
        EquipData['EquipLevel'] = '0' if requirements[0].find('None') != -1 else requirements[0].split(" ")[-1]
        if len(requirements) > 2:
            EquipData['ClassType'] = requirements[1].split(" ")[-1]
        else:
            EquipData['ClassType'] = 'Any'

        
        effects =  tdContent[i+3].get_text(separator = '\n').split('\n')
        EquipData.update(assignToDict(effects))

        if equipType == 'Accessories':
            AccDF = AccDF.append(EquipData, ignore_index=True)
        else:
            ArmorDF = ArmorDF.append(EquipData, ignore_index=True)
        
    ArmorDF = ArmorDF.fillna(0)
    AccDF = AccDF.fillna(0)

    return ArmorDF, AccDF

def retrieveWeapDF(session):

    Page = session.get(defaulturl + weaponUrl)
    ignoreList = ['Secondary','Scepter']
    soup = BeautifulSoup(Page.content, 'lxml')
    weaponLinksList = soup.find_all('a', class_='category-page__member-link')
    WeapDF = pandas.DataFrame()

    for link in weaponLinksList:
        if any(link.next.lower().find(t.lower()) != -1 for t in ignoreList) == True:
            continue
        currentDF = retrieveWeapContent(link['href'], session)
        WeapDF = WeapDF.append(currentDF, ignore_index=True)


    return WeapDF

def retrieveWeapContent(link, session):

    #Navigate to page with weapon in list
    start = time.time()
    weaponListLink = BeautifulSoup(session.get(defaulturl + link).content, 'lxml').find_all('div', class_='mw-parser-output')[0].find_all('a')[0]['href']

    WeaponPage = BeautifulSoup(session.get(defaulturl + weaponListLink).content,'lxml')
    titleContent = WeaponPage.find_all('h1',class_='page-header__title')[0]
    MainContent = WeaponPage.find_all('div', class_='mw-parser-output')[0]

    weaponType = removeN(titleContent.next, ['\n','\t'], '')

    tableC = MainContent.find_all('table',class_='wikitable')[0].find_all('td')
    currentDF = pandas.DataFrame()
    for i in range(0, len(tableC),3):
        ItemData = {}
        if any(ele.lower() in tableC[i].get_text().lower() for ele in WeapSetTrack) == True:
            retrievedSet = tableC[i].get_text()[:-1].replace(weaponType, "")
            if retrievedSet.lower().find("sealed") != -1:
                continue     
            if retrievedSet.lower().find("utgard") != -1:
                ItemData["WeaponSet"] = "Fensalir"
            elif retrievedSet.lower().find("lapis") != -1 or retrievedSet.lower().find("lazuli") != -1:
                ItemData["WeaponSet"] = " ".join(retrievedSet.split(" ")[1:])
                if retrievedSet.lower().find("genesis") != -1:
                    ItemData["WeaponSet"] = 'Genesis'
            else:
                ItemData["WeaponSet"] = WeapSetTrack[returnIndex(retrievedSet, WeapSetTrack)]
                
            ItemData["WeaponType"] = weaponType
            level = tableC[i+1].contents[0].split(" ")[1] 
            ItemData["Level"] = level[:-1] if level.find('\n') != -1 else level
            if int(ItemData['Level']) < trackMinLevel:
                continue
           
            statTable = tableC[i+2].get_text(separator = "\n").split("\n")[:-1]
            ItemData.update(assignToDict(statTable))  
            
            currentDF = currentDF.append(ItemData, ignore_index=True)
    
    end = time.time()

    # print(currentDF)
    print(f'{weaponType} added in {end - start}')


    return currentDF

def retrieveSecWeap(session):
    
    weaponLink = []
    page = session.get(defaulturl + secUrl)
    soup = BeautifulSoup(page.content, 'lxml')

    weapList = soup.find_all('a', class_="category-page__member-link")

    df = pandas.DataFrame()
    for x in weapList:
        weaponLink.append(x['href'])
        
        df = df.append(retreiveSecPage(x['href'], session) , ignore_index=True)

    
    df = df.fillna(0)
    


    return df


def retreiveSecPage(suburl, session):

    
    page = session.get(defaulturl + suburl)
    
    titleContent = BeautifulSoup(page.content, 'lxml').find_all('div', class_= "mw-parser-output")[0].find('a')
    weapListLink = titleContent['href']
    weapType = titleContent.get_text()

    if weapType == "Shield":
        return retrieveShield(weapListLink, session, weapType)

    start = time.time()
    
    weapListPage = session.get(defaulturl + weapListLink)

    PageContent = BeautifulSoup(weapListPage.content, 'lxml').find_all('div', class_= "mw-parser-output")[0]

    wikiTables = PageContent.find_all('table', class_='wikitable')
    headerContent = PageContent.find_all('p')


    for i in headerContent:
        if i.get_text().replace(" ", "").lower().find(weapType.lower()) != -1:
            headerP = i
            break
        if i.get_text().find('exclusive') != -1:
            headerP = i
            break
        continue

    headerPContent = list(headerP.contents)

    Jobs = []
    Cstart = False
    for i in headerPContent:
        if i.get_text().find('exclusive') != -1:
            Cstart = True
            continue
        if i.get_text().find('conjunction') != -1:
            Cstart = False
            break

        if Cstart == True:
            if i.name == 'a':
                JobName = i.next
                Jobs.append(JobName)
 
    currentDF = pandas.DataFrame()

    ignoreList = ["evolving", "frozen"]

    if len(Jobs) == 0:
        return currentDF

    
    counter = min(len(Jobs), len(wikiTables))

    for c in range(0, counter):
        tableContent = wikiTables[c].find_all('td')
        JobType = Jobs[c]
        for i in range(0, len(tableContent), 3):
            ItemData = {}
            if JobType == "Jett":
                continue
            elif JobType == "Dual Blade":
                ItemData["ClassName"] = JobType
                ItemData["WeaponType"] = weapType
                weaponSet = tableContent[i].contents
                for w in weaponSet:
                    if any(ele.lower() in w.get_text().replace(weapType, "").lower() for ele in WeapSetTrack) == True:
                        EquipName = w.get_text()
                        break
                    else:
                        EquipName = ""
                if EquipName == "":
                    continue
                ItemData["EquipName"] = EquipName
                
                EquipLevel = tableContent[i+1].get_text(separator = '\n').split('\n')[0].split(" ")[-1]
                ItemData["EquipLevel"] = EquipLevel

                EquipStat = tableContent[i+2].get_text(separator = "\n").split("\n")[:-1]
                ItemData.update(assignToDict(EquipStat))
            else:
                ItemData["ClassName"] = JobType
                ItemData["WeaponType"] = weapType
                EquipName = tableContent[i].find_all('a')[-1].get_text()
                if EquipName == "":
                    continue
                if any(ele in EquipName.lower() for ele in ignoreList) == True:
                    continue

                ItemData["EquipName"] = EquipName

                EquipLevel = tableContent[i+1].get_text(separator = '\n').split('\n')[0].split(" ")[-1]
                ItemData["EquipLevel"] = EquipLevel

                EquipStat = tableContent[i+2].get_text(separator = "\n").split("\n")[:-1]
                ItemData.update(assignToDict(EquipStat))
            currentDF = currentDF.append(ItemData, ignore_index=True)
        
    end = time.time()

    print(f"{weapType} added in {end -  start}.")
    
    return currentDF

def retrieveShield(weapListLink , session, weapType):

    start = time.time()
    
    currentDF =  pandas.DataFrame()

    for cls in Mclasses:
        newUrl = weapListLink + "/" + cls
        PageContent = session.get(defaulturl + newUrl)
        if PageContent.status_code != 200:
            continue
        currentContent = BeautifulSoup(PageContent.content, 'lxml').find_all('div', class_="wds-tab__content wds-is-current")[0]
        wikitable = currentContent.find_all('td')
        
        for i in range(0, len(wikitable), 3):
            ItemData = {}
            ItemData["ClassName"] = cls
            ItemData["WeaponType"] = weapType
            EquipName = wikitable[i].find_all('a')[-1].get_text()
            if EquipName == "":
                    continue
            ItemData["EquipName"] = EquipName

            EquipLevel = wikitable[i+1].get_text(separator = '\n').split('\n')[0].split(" ")[-1]
            if int(EquipLevel) < 110:
                continue
            ItemData["EquipLevel"] = EquipLevel

            EquipStat = wikitable[i+2].get_text(separator = "\n").split("\n")[:-1]
            ItemData.update(assignToDict(EquipStat))
            currentDF = currentDF.append(ItemData, ignore_index=True)
    end = time.time()
    print(f"Time taken to add Shield is {end - start}")
    return currentDF

def retrieveTyrant(session):
    start = time.time()

    LinksPage = session.get(defaulturl + superiorEquipUrl)

    LinksList = BeautifulSoup(LinksPage.content, 'lxml').find_all('ul', class_='category-page__members-for-char')[2].find_all('a', class_='category-page__member-link')
    tyrantAcc = pandas.DataFrame()
    tyrantArmor =  pandas.DataFrame()
    for link in LinksList:
        
        PageContent = session.get(defaulturl + link['href'])

        soup = BeautifulSoup(PageContent.content,'lxml').find_all('div', class_='mw-parser-output')[0]
        big = soup.find_all('big')[0].get_text().split(' ')
        title = big[:-1] if big[-1] == '' else big 
        equipSet = title[0]
        equipSlot = title[-1]
        if equipSlot.lower().find('boots') != -1:
            equipSlot = 'Shoes'
        elif equipSlot.lower().find('cloak') != -1:
            equipSlot = 'Cape'

        trContent = soup.find_all('tr')[2:]
        EquipData = {}
        EquipData['EquipSet'] = equipSet
        EquipData['EquipSlot'] = equipSlot
        statList = []
        for row in trContent:
            if row.find('th') and row.find('td'):
                th = removeN(row.find('th').next, '\n', '')
                td = removeN(row.find('td').next, '\n', '')
                if th.lower().find('level') != -1:
                    EquipData['EquipLevel'] = td
                    continue
                elif th.lower().find('job') != -1:
                    EquipData['ClassType'] = td
                if th.lower().find('upgrades') != -1:
                    EquipData.update(assignToDict(statList))
                    break
                statList.append(th + ': ' + td)
         
        if EquipData['EquipSlot'] in ArmorSet:
            tyrantArmor = tyrantArmor.append(EquipData, ignore_index=True)
        else:
            EquipData['EquipName'] = equipSet
            tyrantAcc = tyrantAcc.append(EquipData, ignore_index=True)

    end = time.time()
    print(f'Tyrant added in {end - start}')

    return tyrantAcc, tyrantArmor

def tryantPage(link, session):
    PageContent = session.get(defaulturl + link)

    soup = BeautifulSoup(PageContent.content,'lxml').find_all('div', class_='mw-parser-output')[0]
    big = soup.find_all('big')[0].get_text().split(' ')
    title = big[:-1] if big[-1] == '' else big 
    print(type(title))
    equipSet = title[0]
    equipSlot = title[-1]
    
    trContent = soup.find_all('tr')[2:]
    EquipData = {}
    EquipData['EquipSet'] = equipSet
    EquipData['EquipSlot'] = equipSlot
    statList = []
    for row in trContent:
        if row.find('th') and row.find('td'):
            th = removeN(row.find('th').next, '\n', '')
            td = removeN(row.find('td').next, '\n', '')
            if th.lower().find('level') != -1:
                EquipData['EquipLevel'] = td
                continue
            elif th.lower().find('job') != -1:
                EquipData['ClassType'] = td
            if th.lower().find('upgrades') != -1:
                EquipData.update(assignToDict(statList))
                break
            statList.append(th + ': ' + td)

    

    return pandas.DataFrame(EquipData)

def retrieveHeart(session):
    
    EDF = pandas.DataFrame()
    PageContent =  session.get(androiHeartUrl)

    mTable = BeautifulSoup(PageContent.content, 'lxml').find_all('table', class_='wikitable')[0].contents[1]
    tds = mTable.find_all('td')
    
    for r in range(0, len(tds), 3):
        tempDict = {}
        eName = removeN(tds[r].get_text(), '\n', '')
        eLvl = removeN(tds[r + 1].get_text(), '\n', '')
        eStatList = tds[r + 2].get_text(separator = '\n').split('\n');
        if eName == "Black Heart":
            continue
        tempDict[""]

    
    return

def cleanWeapDF(WeapDF):
    
    WeapDF.drop_duplicates(keep='first', inplace=True)
    WeapDF = WeapDF[WeapCol]
    WeapDF = WeapDF.fillna(0)

    WeapDF.loc[(WeapDF.WeaponType == 'Bladecaster'), 'WeaponType'] = 'Tuner'
    WeapDF.loc[(WeapDF.WeaponType == 'Lucent Gauntlet'), 'WeaponType'] = 'Magic Gauntlet'
    WeapDF.loc[(WeapDF.WeaponType == 'Psy-limiter'), 'WeaponType'] = 'Psy Limiter'
    WeapDF.loc[(WeapDF.WeaponType == 'Whispershot'), 'WeaponType'] = 'Breath Shooter'
    WeapDF.loc[(WeapDF.WeaponType == 'Arm Cannon'), 'WeaponType'] = 'Revolver Gauntlet'
    WeapDF.loc[(WeapDF.WeaponType == 'Whip Blade'), 'WeaponType'] = 'Energy Sword'
    WeapDF.loc[(WeapDF.WeaponType == 'Axe'), 'WeaponType'] = 'One-Handed Axe'
    WeapDF.loc[(WeapDF.WeaponType == 'Saber'), 'WeaponType'] = 'One-Handed Sword'
    WeapDF.loc[(WeapDF.WeaponType == 'Hammer'), 'WeaponType'] = 'One-Handed Blunt Weapon'
    WeapDF.loc[(WeapDF.WeaponType == 'One-Handed Mace'), 'WeaponType'] = 'One-Handed Blunt Weapon'
    WeapDF.loc[(WeapDF.WeaponType == 'Two-Handed Mace'), 'WeaponType'] = 'Two-Handed Blunt Weapon'
    WeapDF.loc[(WeapDF.WeaponType == 'Two-Handed Hammer'), 'WeaponType'] = 'Two-Handed Blunt Weapon'

    # WeapDF.drop(WeapDF.loc[int(WeapDF['Level']) < trackMinLevel].index, inplace=True)
    WeapDF.reset_index(drop = True)
    

    return WeapDF

def cleanAccDF(DF):
    
    DF.loc[(DF.EquipSlot == "Android Heart"), "EquipSlot"] = "Heart";
    
    return DF

def cleanSetEffectDF(SEDF):

    SEDF.drop_duplicates(keep='first', inplace=True)
    SEDF = SEDF[SetCol]
    SEDF = SEDF.fillna(0)

    SEDF.reset_index(drop = True)
    
    return SEDF

def cleanSecWeap(SecDF):
    SecDF.drop(SecDF.loc[SecDF['ClassName']=='Beast Tamer'].index, inplace = True)
    
    
    SecDF.loc[(SecDF.ClassName == 'Magician (Fire, Poison)'), 'ClassName'] = 'Fire Poison'
    SecDF.loc[(SecDF.ClassName == 'Magician (Ice, Lightning)'), 'ClassName'] = 'Ice Lightning'

    SecDF.reset_index(drop = True)
    
    return SecDF

if __name__ == "__main__":
    # StartScraping()
    # retrieveSecWeap(requests.session())
    retrieveHeart(requests.session())