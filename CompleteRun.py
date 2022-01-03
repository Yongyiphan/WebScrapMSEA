import CharacterData
import EquipmentData
import CalculationData
import time


def main():
    start =  time.time()
    CharacterData.StartScraping()
    EquipmentData.StartScraping()
    CalculationData.StartScraping()
    
    end = time.time()
    print(f'Total time taken is {end-start}')
    
    
    return



if __name__ == '__main__':
    main()
    

