import pandas
import requests
import time
from bs4 import BeautifulSoup as bsoup
from ComFunc import *


defaultUrl = 'https://strategywiki.org'
STSFurl = '/wiki/MapleStory/Spell_Trace_and_Star_Force#Star_Force_Enhancement'
formulaUrl ='/MapleStory/Formulas'
def StartScraping():

    start = time.time()

    StarforceDF, AddDF = retrieveStarforce()

    StarforceDF = StarforceDF.fillna(0)
    AddDF = AddDF.fillna(0)
    
    StarforceDF = StarforceDF.astype(int)
    AddDF = AddDF.astype(int)
    StarforceDF.to_csv('DefaultData\\CalculationsData\\StarforceGains.csv')
    AddDF.to_csv('DefaultData\\CalculationsData\\AddStarforceGains.csv')
    
    end = time.time()
    print(f'Total time taken is {end-start}')

    return

def retrieveStarforce():
    start = time.time()
    request_session = requests.session()
    Page = request_session.get(defaultUrl + STSFurl)
    MainContent =  bsoup(Page.content, 'lxml')    
    
    startR = MainContent.select('#Stats_Boost')[0].parent
    SFCompiledTable = startR.find_next_sibling('table')

    tableR = SFCompiledTable.contents[1].contents
    tableR = [value for value in tableR if value != '\n'][1:]
    
    currentDF = pandas.DataFrame()
    AddDF =  pandas.DataFrame()
    
    for row in tableR:
        
        r = [td for td in row.contents if td != '\n']
        currentRow = r[0]
        SFStats = r[1]
        temp = removeN(currentRow.next, ['★','→']).split(',')
        addSF = {}
        for sfid in temp:
            sfid = [int(value) for value in sfid.split(' ') if value != '']
            
            SFD = {}
            CSF = max(sfid)
            


            SFD['SFID'] = CSF
            if not isinstance(SFStats, list):
                if CSF > 15:
                    SFStats = [value for value in SFStats if value not in ['', '\n']]
                    varTable = SFStats[0].find_all('tr')[1:]
                    SFStats = SFStats[1].get_text().split('\n')
                    for mR in varTable:
                        addSF['SFID'] = CSF

                        Levelr = [value for value in mR.contents if value != '\n'][0].get_text().split('~')[0]
                        addSF['LevelRank'] = returnLevelRank(int(Levelr))
                        statsL = mR.find_all('ul')[0].get_text().split('\n')
                        addSF.update(ATDSF(statsL))
                        AddDF = AddDF.append(addSF, ignore_index=True)

                    
                else:
                    SFStats = SFStats.find_all('ul')[0].get_text().split('\n')

                
            SFStats = [value for value in SFStats if value != '']
            SFD.update(ATDSF(SFStats))
            currentDF = currentDF.append(SFD, ignore_index=True)
            

        
            end = time.time()
            print(f'Starforce at {CSF} added in {end-start}')

    return currentDF, AddDF

def retrieveWeapMod():
    start = time.time()
    request_session = requests.session()
    Page = request_session.get(defaultUrl + formulaUrl)
    MainContent =  bsoup(Page.content, 'lxml')    
    
    startR = MainContent.select('#Weapon_Multiplier')[0].parent
    WeapModTable = startR.find_next_sibling('table')
    WeapModTable = [value for value in WeapModTable if value != '\n']

    ContentTable = WeapModTable[0]

    WeaponList = []
    WeaponMod = []
    for row in ContentTable.find_all('tr'):
        weaponL = row.find('th').next.split(',')
        td = row.find('td').next.split(' ')[0]

        for weap in weaponL:
            if weap.find('/') != -1:
                weap = weap.split('/')[0]
            elif weap.find('(') != -1:
                weap =  weap.split('(')[0]

            

            WeaponList.append(removeFLSpace(removeN(weap, '\n')))
            WeaponMod.append(removeN(td, '\n'))
    
    tempD = {'WeaponType':WeaponList, 'Multiplier':WeaponMod}
    WeapMDF = pandas.DataFrame(tempD) 


    return WeapMDF

def ATDSF(statList):
    delimiter = ['+', '%', "'s", "s'"]
    tempD = {}

    for stat in statList:
        stat =  removeN(stat, delimiter)
        if findString(stat, '-'):
            stat = stat.replace('-', ' ')
        
        t =  stat.split(' ')
        value = t[-1]
        name = " ".join(t[:-1])
        tempD[name] = value


    return tempD

def findString(s, toFind):

    if s.find(toFind) != -1:
        return True
    else:
        return False

def returnLevelRank(level):

    level = int(level)

    if level >= 128 and level <= 137:
        return 5
    elif level >= 138 and level <= 149:
        return 4
    elif level >= 150 and level <= 159:
        return 3
    elif level >= 160 and level <= 199:
        return 2
    elif level >= 200:
        return 1

if __name__ == "__main__":
    StartScraping()

