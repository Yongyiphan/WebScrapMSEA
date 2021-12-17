from bs4.element import PageElement
from numpy import true_divide
import pandas
import requests
import lxml
import cchardet
import time
from bs4 import BeautifulSoup

### PROGRAM FLOW ####
# MAIN PAGE -> GET EQUIPNAME/LINK 
# TRAVERSE TO EQUIPLINK PAGE -> GET WEAPON SET'S LINK
# TRAVERSE TO WEAPON'LINK -> RECORD INFORMATION
weaponLink = []
weaponNameList = []
defaulturl = "https://maplestory.fandom.com"
weaponUrl = "/wiki/Category:Weapons"
setToTrack = ['Genesis', 'Arcane', 'Utgard','Absolab', 'Fafnir', 'Lapis','Lazuli']
Mclasses = ['Warrior', 'Bowman', 'Magician','Mage','Thief', 'Pirate']
trackMinLevel = 140

def main():
    
    start = time.time()
    
    weapDF = retrieveMainWeap()
    weapDF.loc[(weapDF.WeaponType == 'Bladecaster'), 'WeaponType'] = 'Tuner'
    weapDF.loc[(weapDF.WeaponType == 'LucentGauntlet'), 'WeaponType'] = 'MagicGauntlet'
    weapDF.loc[(weapDF.WeaponType == 'Psy-limiter'), 'WeaponType'] = 'PsyLimiter'
    weapDF.loc[(weapDF.WeaponType == 'Whispershot'), 'WeaponType'] = 'BreathShooter'


    weapDF.to_csv("WeaponData.csv", encoding='utf-8')

    end = time.time()

    print(f"Time take: {end - start}")
    return

def retrieveMainWeap():

    request_session = requests.sessions.session()
    
    page = request_session.get(defaulturl + weaponUrl)

    soup  = BeautifulSoup(page.content, "lxml")
    weaponList = list(soup.find_all('a', class_='category-page__member-link'))
    
    

    df = pandas.DataFrame()
    for x in weaponList:
        if(x['href'].find("Secondary_Weapons") != -1):
            continue
        weaponLink.append(x['href'])
        df = df.append(retreiveConsolidatedPage(x['href'], request_session, setToTrack), ignore_index=True)
    
    # print(retreiveConsolidatedPage(weaponLink[33], request_session, setToTrack))
    # print(df)
    df = df.fillna(0)
    print(df)
    return df


def retreiveConsolidatedPage(suburl, session, trackSet):

    start = time.time()
    page = session.get(defaulturl + suburl)
    
    PageContent = BeautifulSoup(page.content, 'lxml').find_all('div', class_= "mw-parser-output")
    weapListURL = PageContent[0].find_all('a')[0]['href']
    weapType = PageContent[0].find_all('a')[0].get_text()
    weapListPage = session.get(defaulturl + weapListURL)
    soup = BeautifulSoup(weapListPage.content, "lxml")
    tableC =  soup.find_all('table', class_="wikitable")[0].find_all('td')   

    headerP = soup.find_all('div', class_="mw-parser-output")[0].find_all('p')[0]
    headerLinks = headerP.find_all('a')
    
    JobType = ""
    headerPcontent = list(headerP.contents)
    
    if headerP.get_text().lower().find("exclusive") != -1:
        for i in range(0, len(headerPcontent)):
            if  headerPcontent[i].get_text().find('exclusive') != -1:
                JobType = headerPcontent[i+1].contents[0].replace(" ", "") if headerPcontent[i+1].contents[0].find(" ") != -1 else headerPcontent[i+1].contents[0]
    elif headerP.get_text().lower().find("conjunction") != -1:
        JobType = headerLinks[0].get_text()
    elif headerP.get_text().lower().find("bow") != -1:
        JobType = "Bowman"
    elif headerP.get_text().lower().find("dagger") != -1:
        JobType = "Thief"
    elif headerP.get_text().lower().find("knuckles") != -1:
        JobType = "Pirate"
    elif headerP.get_text().lower().find("claw") != -1:
        JobType = "Thief"
    else:
        for ele in Mclasses:
            if headerP.get_text().lower().find(ele.lower()) != -1:
                JobType = ele
                
    currentDF = pandas.DataFrame()
    
    for i in range(0, len(tableC),3):
        ItemData = {}
        ItemData["ClassType"] = JobType
        if any(ele.lower() in tableC[i].get_text().lower() for ele in setToTrack) == True:
            retrievedSet = tableC[i].get_text()[:-1].replace(weapType, "")
            if retrievedSet.lower().find("sealed") != -1:
                continue     
            if retrievedSet.lower().find("utgard") != -1:
                ItemData["WeaponSet"] = "Fensalir"
            elif retrievedSet.lower().find("lapis") != -1 or retrievedSet.lower().find("lazuli") != -1:
                ItemData["WeaponSet"] = "".join(retrievedSet.split(" ")[1:])
            else:
                ItemData["WeaponSet"] = setToTrack[returnIndex(retrievedSet)]
            ItemData["WeaponType"] = weapType.replace(" ","") if weapType.find(" ") else weapType
            level = tableC[i+1].contents[0].split(" ")[1] 
            ItemData["Level"] = level[:-1] if level.find('\n') != -1 else level
            if (int(ItemData["Level"]) < trackMinLevel) and ItemData["ClassType"].lower() != "zero":
                continue
            statTable = tableC[i+2].get_text(separator = "\n").split("\n")[:-1]
            ItemData.update(assignToDict(statTable))  
            if not currentDF.empty:
                if  ItemData["ClassType"] in currentDF.values and ItemData["WeaponSet"] in currentDF.values:
                    continue
                else:
                    currentDF = currentDF.append(ItemData, ignore_index=True)
            else:              
                currentDF = currentDF.append(ItemData, ignore_index=True)
    
    end = time.time()
    print(f"Time taken for {weapType} to be added is  {end - start}")
      
    return currentDF
    
    # return

def returnIndex(ele):
    for i in range(0, len(setToTrack)):
        if setToTrack[i].lower() in ele.lower():
            return i
        elif ele.lower() in setToTrack[i].lower():
            return i


def assignToDict(tempList):
    
    tempData = {}
    
    for i in tempList:
        if i.find("Attack Speed") != -1:
            tempData["AtkSpd"] = i.split(" ")[-1][1:-1]
            continue
        elif i.find("STR") != -1:
            if "MainStat" in tempData:
                tempData["SecStat"] = i.split(" ")[1][1:]
            else:
                tempData["MainStat"] = i.split(" ")[1][1:]
            continue
        elif i.find("DEX") != -1:
            if "MainStat" in tempData:
                tempData["SecStat"] = i.split(" ")[1][1:]
            else:
                tempData["MainStat"] = i.split(" ")[1][1:]
            continue       
        elif i.find("INT") != -1:
            if "MainStat" in tempData:
                tempData["SecStat"] = i.split(" ")[1][1:]
            else:
                tempData["MainStat"] = i.split(" ")[1][1:]
            continue
        elif i == "LUK":
            if "MainStat" in tempData:
                tempData["SecStat"] = i.split(" ")[1][1:]
            else:
                tempData["MainStat"] = i.split(" ")[1][1:]
            continue
        elif i.find("HP") != -1:
            tempData["HP"] = i.split(" ")[-1][1:].replace(",", "")
            continue
        elif i.find("Weapon Attack") != -1:
            tempData["Atk"] = i.split(" ")[-1][1:]
            continue
        elif i.find("Magic Attack") != -1:
            tempData["MAtk"] = i.split(" ")[-1][1:]
            continue
        elif i.find("Boss") != -1:
            tempData["BossDMG"] = i.split(" ")[-1][1:-1]
            continue
        elif i.find("Ignore") != -1:
            tempData["IED"] = i.split(" ")[-1][1:-1]
            continue
        elif i.find("Speed") != -1:
            tempData["SPD"] = i.split(" ")[-1][1:]
            continue
        
        
    
    
    return tempData


main()


# def retrieveSubPageDetails(suburl, session):
#     pageurl = defaulturl + suburl
#     page = session.get(pageurl);
#     soup = BeautifulSoup(page.content, "lxml")
    
#     linkTrack = []

#     df = pandas.DataFrame(columns=[])
    
#     for a in soup.find_all('a', class_='category-page__member-link'):
#         for i in a.get_text().split(" "):
#             if i.lower() in setToTrack:
#                 linkTrack.append(a['href'])
#                 dataDict = {}
#                 dataDict["WeaponType"] = suburl.split("/")[2].split(":")[1]
#                 dataDict["WeaponSet"] = a['href'].split("/")[2].split("_")[0]
#                 dataDict.update(retrieveItemStat(a['href'], session))
                
#                 df = df.append(dataDict, ignore_index=True)
    
    
#     return df
    
# def retrieveItemStat(url, session):
#     tempTitle = []
#     tempValue = []
    
#     page = session.get(defaulturl + url);
#     soup = BeautifulSoup(page.content, "lxml")
#     tableC = soup.find_all('tbody')[0]
#     th = tableC.find_all('th')
#     td = tableC.find_all('td')
    
    
#     for i in range(0, len(td), 2):
#         tempValue.append(td[i].get_text()[:-1])

#     for i in th:
#         tempTitle.append(i.get_text()[:-1])
    
#     tempValue = tempValue[1:]
#     tempData = {}
    
    
#     for i in range(0, len(tempTitle)):
#         if tempTitle[i] == "REQ Level":
#             tempData["Level"] = tempValue[i]
#             continue
#         elif tempTitle[i] == "REQ Job":
#             tempData["ClassType"] = tempValue[i]
#             continue
#         elif tempTitle[i] == "Attack Speed":
#             tempData["AtkSpd"] = tempValue[i].split(" ")[1][1:-1]
#             continue
#         elif tempTitle[i] == "STR":
#             if "MainStat" in tempData:
#                 tempData["SecStat"] = tempValue[i][1:]
#             else:
#                 tempData["MainStat"] = tempValue[i][1:]
#             continue
#         elif tempTitle[i] == "DEX":
#             if "MainStat" in tempData:
#                 tempData["SecStat"] = tempValue[i][1:]
#             else:
#                 tempData["MainStat"] = tempValue[i][1:]
#             continue        
#         elif tempTitle[i] == "INT":
#             if "MainStat" in tempData:
#                 tempData["SecStat"] = tempValue[i][1:]
#             else:
#                 tempData["MainStat"] = tempValue[i][1:]
#             continue
#         elif tempTitle[i] == "LUK":
#             if "MainStat" in tempData:
#                 tempData["SecStat"] = tempValue[i][1:]
#             else:
#                 tempData["MainStat"] = tempValue[i][1:]
#             continue
#         elif tempTitle[i] == "Weapon Attack":
#             tempData["Atk"] = tempValue[i][1:]
#             continue
#         elif tempTitle[i] == "Magic Attack":
#             tempData["MAtk"] = tempValue[i][1:]
#             continue
#         elif tempTitle[i].find("Knockback") != -1:
#             tempData["Knockback"] = tempValue[i][:-1]
#             continue
#         elif tempTitle[i].find("Boss") != -1:
#             tempData["BossDMG"] = tempValue[i][1:-1]
#             continue
#         elif tempTitle[i].find("Ignore") != -1:
#             tempData["IED"] = tempValue[i][1:-1]
#             continue
#         elif tempTitle[i].find("Movement") != -1:
#             tempData["SPD"] = tempValue[i][1:]
#             continue
#     return tempData
