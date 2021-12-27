
MainStat = ['STR','DEX','INT','LUK']


def returnIndex(ele, setToTrack):
    for i in range(0, len(setToTrack)):
        if setToTrack[i].lower() in ele.lower():
            return i
        elif ele.lower() in setToTrack[i].lower():
            return i

def removeN(item, para):
    
    if isinstance(para, str):
        if item.find(para) != -1:
            return item.replace(para, '')
        else:
            return item
    elif isinstance(para, list):
        for i in para:
            if item.find(i) != -1:
                item = item.replace(i, '')
        return item

def assignToDict(tempList):
    
    tempData = {}
    if tempList == None:
        return tempData
    
    for i in tempList:
        if i.find("Attack Speed") != -1:
            tempData["AtkSpd"] = i.split(" ")[-1][1:-1]
        
        elif any(i.find(MS) != -1 for MS in MainStat) == True:
            if i.find(':') != -1:
                tempStr = i.split(" ")[1][1:]
            else:
                tempStr = i.split(" ")[-1][1:]
            
            if "MainStat" in tempData:
                if 'SecStat' in tempData:
                    continue
                tempData["SecStat"] = tempStr
            else:
                tempData["MainStat"] = tempStr
     
        elif i.find("HP") != -1:
            HPstr = i.split(" ")[-1][1:]
            HPstr = removeN(HPstr, ',')
            if HPstr.find("%") != -1:
                tempData['HP'] = HPstr
            else:
                tempData['HP'] = HPstr[1:]
        elif i.find("MP") != -1:
            MPstr = i.split(" ")[-1][1:]
            MPstr = removeN(MPstr, ',')
            if MPstr.find("%") != -1:
                tempData['MP'] = MPstr
            else:
                tempData['MP'] = MPstr[1:]
        elif i.find("Weapon Attack") != -1:
            tempData["ATK"] = i.split(" ")[-1][1:]

        elif i.find("Magic Attack") != -1:
            tempData["MATK"] = i.split(" ")[-1][1:]
        
        elif i.find("All Stats") != -1:
            tempData["AllStat"] = i.split(" ")[-1][1:]

        elif i.find("Boss") != -1:
            tempData["BDMG"] = i.split(" ")[-1][1:-1]

        elif i.find("Ignore") != -1:
            tempData["IED"] = i.split(" ")[-1][1:-1]

        elif i.find("Defense") != -1:
            tempData["DEF"] = i.split(" ")[-1][1:]

        elif i.find("Speed") != -1:
            tempData["SPD"] = i.split(" ")[-1][1:]

        elif i.find("Jump") != -1:
            tempData["JUMP"] = i.split(" ")[-1][1:]
        
        elif i.find("Normal") != -1:
            tempData['NDMG'] = i.split(" ")[-1][1:-1]

        elif i.find("Critical Damage") != -1:
            tempData['CDMG'] = i.split(" ")[-1][1:-1]  

    
    
    return tempData