import argparse
from tqdm import trange
import requests
import os
import csv
import pandas as pd
from time import sleep
from datetime import datetime
from operator import itemgetter
import operator
import json
import sys
#import asyncio
#import aiohttp


# URLs to make api calls - significa as chamadas de API, é aqui que o usuário irá sempre verificar o link do API e comparar com o original
BASE_URL = "https://metamon-api.radiocaca.com/usm-api" # API ORIGINAL
TOKEN_URL = f"{BASE_URL}/login" # link do token buscando o API ORIGINAL
LIST_MONSTER_URL = f"{BASE_URL}/getWalletPropertyBySymbol" # faz referência ao API ORIGINAL
CHANGE_FIGHTER_URL = f"{BASE_URL}/isFightMonster" # faz referência ao API ORIGINAL
START_FIGHT_URL = f"{BASE_URL}/startBattle" # faz referência ao API ORIGINAL
LIST_BATTLER_URL = f"{BASE_URL}/getBattelObjects" # faz referência ao API ORIGINAL
WALLET_PROPERTY_LIST = f"{BASE_URL}/getWalletPropertyList" # faz referência ao API ORIGINAL
LVL_UP_URL = f"{BASE_URL}/updateMonster" # faz referência ao API ORIGINAL
MINT_EGG_URL = f"{BASE_URL}/composeMonsterEgg" # faz referência ao API ORIGINAL
CHECK_BAG_URL = f"{BASE_URL}/checkBag" # faz referência ao API ORIGINAL
EXP_UP_URL = f"{BASE_URL}/expUpMonster" # faz referência ao API ORIGINAL
POWER_UP_URL = f"{BASE_URL}/addAttr" # faz referência ao API ORIGINAL
CHECK_POWER_UP_URL = f"{BASE_URL}/addAttrNeedAsset" # faz referência ao API ORIGINAL
DEFAULT_METAMON_BATTLE = '{"code":"SUCCESS","data":{"objects":[{"con":95,"crg":48,"id":"791430","inte":95,"inteMax":200,"inv":48,"luk":19,"lukMax":50, "level":"40","race":"demon","rarity":"N","sca":305,"tokenId":"405133"}]}}'
# código para manipulação do jogo, nada malicioso.
SQUAD_LIST_URL = f"{BASE_URL}/kingdom/teamList" # faz referência ao API ORIGINAL
JOIN_TEAM_URL = f"{BASE_URL}/kingdom/teamJoin" # faz referência ao API ORIGINAL
BUY_VALHALLA_URL = f"{BASE_URL}/official-sale/buy" # faz referência ao API ORIGINAL
ADD_HEALTHY = f"https://metamon-api.radiocaca.com/usm-api/addHealthy?address=" # faz referência ao API ORIGINAL
RESET_EXP = f"{BASE_URL}/resetMonster" # faz referência ao API ORIGINAL
MONSTER_LVL_60 = f"{BASE_URL}/kingdom/monsterList" # faz referência ao API ORIGINAL

def datetime_now():
    return datetime.now().strftime("%m/%d/%Y %H:%M:%S") # informações de data


def post_formdata(payload, url="", headers=None, params=None, is_sleep=True): #método para se comunicar com o jogo, tudo OK! <<<INÌCIO>>>
    """Method to send request to game"""
    files = []
    if headers is None:
        headers = {}
    if params is None:
        params = {}
    for _ in range(5):
        try:
            # Add delay to avoid error from too many requests per second

            if is_sleep:
                sleep(1)
            response = requests.request("POST",
                                        url,
                                        headers=headers,
                                        data=payload,
                                        params=params,
                                        files=files)
            return response.json()
        except:
            continue
    return {}
    #<<FIM DA PARTE>> OK!
def auto_buy_request(url, address, headers, session, requestsNumber): # comunicação com o jogo, se refere ao playload, endereço, orderID e componentes power score. Nada malicioso.
    """Method to send request to game"""
    tasks = []   
    requestsNumber = requestsNumber + 50
    payload = {'address': address, 'orderId': "111"}
    for i in range(0,requestsNumber):
        tasks.append(asyncio.create_task(session.post(url, data =payload, headers=headers, ssl=False)))

    return tasks

def get_battler_score(monster):
    """ Get opponent's power score"""
    return monster["sca"]
# <fim da parte. Analisado.>

def picker_battler(monsters_list, other_fighting_mode): #Se refere ao Picking opponent no jogo, rarity, Battle, etc. Nada malicioso.
    """ Picking opponent """
    battlers = list(filter(lambda m: m["rarity"] == "N", monsters_list))

    if len(battlers) == 0:
        battlers = list(filter(lambda m: m["rarity"] == "R", monsters_list))

    battler = battlers[0]
    score_min = get_battler_score(battler)
   
    for i in range(1, len(battlers)):
        score = get_battler_score(battlers[i])
        if score < score_min:
            battler = battlers[i]
            score_min = score
    if other_fighting_mode[0] == True:
        battlers_sorted = sorted(battlers, key=itemgetter('sca','luk', 'crg', 'inv', 'con', 'inte'))
        battler = battlers[0]
        
    target_monster_id = battler.get("id")
    target_luk = battler.get("luk")
    target_size = battler.get("con")
    target_inte = battler.get("inte")
    target_courage = battler.get("crg")
    target_inv = battler.get("inv")
    target_level = battler.get("level")
    target_power = battler.get("sca")
    target_race = battler.get("race")
    print(f"Battle Monsters - ID: {target_monster_id}, Race:{target_race}, Score: {target_power}, Luk: {target_luk}, Wisdom: {target_inte}, Size: {target_size}, Courage: {target_courage}, Stealth: {target_inv}")
    return battler


def pick_battle_level(level=1):
    # pick highest league for given level - se refere ao level no jogo. Nada malicioso.
    if 21 <= level <= 40:
        return 2
    if 41 <= level <= 60:
        return 3
    return 1
# <fim da parte>

class MetamonPlayer: #inclui as informações no jogo para permitir as alterações. 
    
    def __init__(self,
                 address,
                 sign,
                 msg="LogIn",
                 name = "",
                 auto_lvl_up=False,
                 other_fighting_mode = False,
                 lowest_score = False,
                 auto_exp_up = False,
                 auto_power_up = False,
                 battle_record = False,
                 output_stats=False,
                 average_sca_default = 335,
                 average_sca = 0,
                 find_squad_only = False,
                 add_healthy = False,
                 is_use_green_potion_only = False):
        self.no_enough_money = False
        self.output_stats = output_stats
        self.total_bp_num = 0
        self.total_success = 0
        self.total_fail = 0
        self.total_powup_success = 0
        self.total_powup_fail = 0
        self.mtm_stats_df = []
        self.token = None
        self.address = address
        self.sign = sign
        self.msg = msg
        self.name = name
        self.auto_lvl_up = auto_lvl_up,
        self.other_fighting_mode = other_fighting_mode,
        self.lowest_score = lowest_score
        self.auto_exp_up = auto_exp_up,
        self.auto_power_up = auto_power_up,
        self.battle_record = battle_record,
        self.rate = 0,
        self.log_file = open("battle_record.log","w")
        self.average_sca_default = average_sca_default,
        self.find_squad_only = find_squad_only
        self.add_healthy = add_healthy
        self.is_use_green_potion_only = is_use_green_potion_only
    def init_token(self):
        """Obtain token for game session to perform battles and other actions""" #comentário do próprio desenvolvedor explicando o uso.
        payload = {"address": self.address, "sign": self.sign, "msg": self.msg, "network": "1", "clientType": "MetaMask"} #busca informação do token
        response = post_formdata(payload, TOKEN_URL)
        if response.get("code") != "SUCCESS": #caso retorne o token, informe o sucesso.
            sys.stderr.write("Login failed, token is not initialized. Terminating\n") #caso o token não seja informado, retorna o erro.
            sys.exit(-1)
        self.token = response.get("data").get("accessToken") #envia a informação para o código abaixo
        #a parte do código acima somente obtém o token MetaMask para realizar as operações no jogo, como podemos ver a seguir:
    def get_token_ids(self):
        self.init_token()
        print("Metamons token id are exporting ...")
        mtms = self.get_wallet_properties()
        mtm_stats = []
        for mtm in mtms:
            token_id = mtm.get("tokenId")
            print(f"Export Metamon Token Id {token_id}") #exporta id Metamon Token, operação do Jogo. OK!
            level = mtm.get("level")
            print (token_id)
            mtm_stats.append({
                "TokenId": token_id
            })
            mtm_stats_df = pd.DataFrame(mtm_stats)
            self.mtm_stats_df.append(mtm_stats_df)
        mtm_stats_df.to_csv("Metamon Token Id", sep="\t", index=False)
        
    def reset_exp(self, mtmId):
        """Obtain list of opponents""" 
        try:
            payload = {
                "address": self.address,
                "nftId": mtmId,
            }
            headers = {
                "accessToken": self.token,
            }
            response = post_formdata(payload, RESET_EXP, headers)
            print(response)
            return response
        except Exception as e:
            print(f"Reset monster failed {e}") # se refere aos oponentes no jogo. OK!
        return None
       
    def buy_item(self):
        print("Starting buy purple potion...") # Operações do jogo. OK!
        if self.token == None:
            self.init_token()
        headers = {
           "accessToken": self.token,
        }
        payload = {'address': self.address, 'orderId': "111"}
        item_buy_count = self.metamon_unlock(-1)
        print(f"Purple potion available to buy: {item_buy_count}")
        for i in range(0, item_buy_count):
            response = post_formdata(payload, BUY_VALHALLA_URL, headers, is_sleep=False)
            time = datetime_now()
            print(f"Buy purple potion {time} {response}")
            
    def add_metamon_healthy(self, nftId):
        if self.token is None:
            self.init_token()
        headers = {
           "accessToken": self.token,
        }
        payload = {'nftId': nftId}
        response = post_formdata(payload, f"{ADD_HEALTHY}{self.address}", headers, is_sleep=False)
        print(response)
        
    def get_kingdom_monsters(self):
        """ Get List of squad ing metamon kingdom""" #Se refere a operações do Jogo. OK!
        payload = {'address': self.address, 'orderType': 2, 'position': 2}
        headers = {
            "accesstoken": self.token,
        }
        response = post_formdata(payload, MONSTER_LVL_60, headers, False)
        monsters = []
        code = response.get("code")

        if code == "SUCCESS":
            monsters = response.get("data", [])
        return monsters
        
    def get_squads(self):
        """ Get List of squad ing metamon kingdom""" #Se refere a operações do Jogo. OK!
        payload = {'address': self.address, 'teamId': -1, 'pageSize': 9999}
        headers = {
            "accesstoken": self.token,
        }
        response = post_formdata(payload, SQUAD_LIST_URL, headers, False)
        squads = []
        code = response.get("code")#Se refere a operações do Jogo. OK!
        if code == "SUCCESS":
            squads = response.get("data", {}).get("list", [])
        return squads 
        
    def metamon_unlock(self, bpType):
        """ Get List of squad ing metamon kingdom"""
        payload = {"address": self.address}
        headers = {
            "accesstoken": self.token,#Se refere a operações do Jogo. OK!
        }
        response = post_formdata(payload, CHECK_BAG_URL, headers)
        mtm = response.get("data", {}).get("item", [])
        result = 0
        mtm_60_island = 0
        for metamon in mtm:
            mtm_type = metamon.get("bpType")
            mtm_num = metamon.get("bpNum")
            
            if mtm_type == bpType:
                result = int(mtm_num)
                break
        if bpType == -1:
            wallet_monsters = self.get_wallet_properties()
            available_monsters = [
                #monster for monster in wallet_monsters if monster.get("tear") > 0 and monster.get("exp") < 600 and monster.get("level") < 60
                monster for monster in wallet_monsters if monster.get("level") >= 60
            ]
            result = len(available_monsters) + result
        return result
        
    def join_squad(self, name, teamId):
        """Join squad"""
        payload = {'address': self.address, 'teamId': teamId}
        headers = {
            "accesstoken": self.token,
        }
        response = post_formdata(payload, JOIN_TEAM_URL, headers)
        code = response.get("code")
        mtm_num = 0
        if code == "SUCCESS":
            mtm_num = response.get("data", {}).get("monsterNum", 0)
            
        print(f"{mtm_num} metamon warriors have joined to {name} kingdom for {''.join(self.name)}")   #Se refere a operações do Jogo. OK!
        return mtm_num
        
    def start_find_squads(self):
        is_finding = self.find_squads()
        while(is_finding):
            is_finding = self.find_squads()
            
    def find_squads(self):
        """ Find best squad to join"""#Se refere a operações do Jogo. OK!
        if self.token == None:
            self.init_token()
        mtm_unlock = self.metamon_unlock(-2)

        if mtm_unlock == 0 and self.find_squad_only == False:
            print(f"Not found metamon on metamon kingdom for {''.join(self.name)} wallet")#Se refere a operações do Jogo. OK!
            return False
        squads = self.get_squads()
        if not squads:
            print("Not found squads to join. Continue finding...")
            return True
        else:
            average_sca_default = self.average_sca_default[0]
            best_squads = []
            for sq in squads:
                totalSca = 0
                
                if sq.get("totalSca") is not None:
                    totalSca = int(sq.get("totalSca"))
                name = sq.get("name")
                monsterNum = int(sq.get("monsterNum"))
                monsterNumMax = int(sq.get("monsterNumMax"))
                teamId = sq.get("id")
                average_sca = 0
                if monsterNum > 0:
                    average_sca = totalSca / monsterNum
                if mtm_unlock >= monsterNumMax and monsterNum == 0:
                    """Join squad"""
                    self.join_squad(name, teamId)
                    return True
                else:
                    if average_sca >= average_sca_default:
                        best_squads.append(sq)
            if not best_squads:
                print(f"Not found any squad with average score {average_sca_default} in metamon kingdom. Continue finding...")#Se refere a operações do Jogo. OK!
                return True
            else:
                best_squads = sorted(best_squads, key=lambda x: (int(operator.itemgetter("totalSca")(x)), int(operator.itemgetter("monsterNumRarity")(x))), reverse=True)
                for bs in best_squads:
                    monsterNumMax = bs.get("monsterNumMax")
                    monsterNum = bs.get("monsterNum")
                    totalSca = 0
                    if bs.get("totalSca") is not None:
                        totalSca = int(bs.get("totalSca"))
                    squad_slot = monsterNumMax - monsterNum
                    squad_num_condition = squad_slot - mtm_unlock
                    name = bs.get("name")
                    teamId = bs.get("id")
                    averageSca = 0
                    if monsterNum > 0:
                        averageSca = str(round(totalSca / monsterNum, 2))
                    if self.find_squad_only == True:
                        print(f"Found kingdom {teamId} {name} with average power {averageSca} have {monsterNum} metamon warriors. Continue finding...")  #Se refere a operações do Jogo. OK!
                        return True                          
                    else:
                        if squad_num_condition <= 100:
                            """Join squad"""
                            self.join_squad(name, teamId)
                            return False
                        else:
                           print(f"Found kingdom {teamId} {name} with average power {averageSca} have {monsterNum} metamon warriors. Continue finding...")#Se refere a operações do Jogo. OK!
                           return True
        return False

    def change_fighter(self, monster_id):
        """Switch to next metamon if you have few"""#Se refere a operações do Jogo. OK!
        payload = {
            "metamonId": monster_id,
            "address": self.address,
        }
        post_formdata(payload, CHANGE_FIGHTER_URL)

    def list_battlers(self, monster_id, front=1):
        """Obtain list of opponents"""
        if self.lowest_score == True:
            response = json.loads(DEFAULT_METAMON_BATTLE)
            return response.get("data", {}).get("objects")#Se refere a operações do Jogo. OK!
        else:
            payload = {
            "address": self.address,
            "metamonId": monster_id,
            "front": front,
            }
            headers = {
            "accessToken": self.token,
            }
            response = post_formdata(payload, LIST_BATTLER_URL, headers)

            return response.get("data", {}).get("objects")#Se refere a operações do Jogo. OK!
        
        
    def exp_up(self, monster_id):
        """Up exp for metamon"""
        payload = {
            "address": self.address,
            "nftId": monster_id
        }
        headers = {
            "accessToken": self.token,
        }
        response = post_formdata(payload, EXP_UP_URL, headers)
        return response
        
    def power_up(self, monster_id, attr_type = 1):
        """Up exp for metamon"""#Se refere a operações do Jogo. OK!
        payload = {
            "attrType": attr_type,
            "nftId": monster_id
        }
        params = {'address': self.address}
        headers = {
            "accessToken": self.token,#Se refere a operações do Jogo. OK!
        }
        response = post_formdata(payload, POWER_UP_URL, headers, params)
        return response  

    def check_power_up(self, monster_id, attr_type = 1):
        """Up exp for metamon"""
        payload = {
            "attrType": attr_type,
            "nftId": monster_id#Se refere a operações do Jogo. OK!
        }
        params = {'address': self.address}
        headers = {
            "accessToken": self.token,
        }
        response = post_formdata(payload, CHECK_POWER_UP_URL, headers, params)
        return response          
        
    def auto_up_exp(self):
        """Automatically up exp for metamon"""#Se refere a operações do Jogo. OK!
        self.init_token()
        wallet_monsters = self.get_wallet_properties()
        for monster in wallet_monsters:
            my_monster_token_id = monster.get("tokenId")
            my_monster_id = monster.get("id")
            exp_up_response = self.exp_up(my_monster_id) 
            while (exp_up_response.get("code") == "SUCCESS"):
                data = exp_up_response.get("data")
                print(f"+{data} EXP FOR METAMON {my_monster_token_id}")
                exp_up_response = self.exp_up(my_monster_id)
        print("Automatically exp up finish")#Se refere a operações do Jogo. OK!
            
    def auto_up_power(self):
        """Automatically up power for metamon"""
        #TODO
        self.init_token()
        wallet_monsters = self.get_wallet_properties()
        available_monsters = []
        available_monsters = [
            monster for monster in wallet_monsters if monster.get("allowUpper") == True#Se refere a operações do Jogo. OK!
        ]
        kingdom_monsters = [
            monster for monster in self.get_kingdom_monsters() if monster.get("allowUpper") == True
        ]
        
        monsters_power_up = available_monsters + kingdom_monsters
        print(f"Available Metamon to up power: {len(monsters_power_up)}")
        monsters_power_up = sorted(monsters_power_up, key=lambda x: int(operator.itemgetter("sca")(x)), reverse=True)
        for monster in monsters_power_up:
            my_monster_token_id = monster.get("tokenId")
            my_monster_id = monster.get("id")
            my_luk = monster.get("luk")
            my_size = monster.get("con")
            my_inte = monster.get("inte")
            my_courage = monster.get("crg")
            my_inv = monster.get("inv")
            my_power = monster.get("sca")
            attr_up_type = 5
            attr_up_name = "Stealth"
            if my_luk < 50:
               attr_up_type = 1 
            elif my_courage < my_inv and my_courage < 100:
                attr_up_type = 2
                attr_up_name = "Courage"#Se refere a operações do Jogo. OK!
            elif my_inv < my_courage and my_inv < 100:
                attr_up_type = 5
                attr_up_name = "Stealth"
            elif my_inte < my_size and my_inte < 200:#Se refere a operações do Jogo. OK!
                attr_up_type = 3
                attr_up_name = "Wisdom"#Se refere a operações do Jogo. OK!
                attr_up_type = 4
                attr_up_name = "Size"
            if self.is_use_green_potion_only == True and my_power >= 380:#Se refere a operações do Jogo. OK!
                continue
            self.my_power_up(my_monster_id, my_monster_token_id, attr_up_type, attr_up_name, my_power)    
            if self.is_use_green_potion_only == True:
                continue
            for i in range(0, 5):
               self.my_power_up(my_monster_id, my_monster_token_id, attr_up_type, attr_up_name, my_power)
                    
    def my_power_up(self,my_monster_id, my_monster_token_id, attr_up_type, attr_up_name, my_power):
        
        if self.is_use_green_potion_only == True:
            check_power_up_response = self.check_power_up(my_monster_id, attr_up_type)#Se refere a operações do Jogo. OK!
            if check_power_up_response.get("code") != "SUCCESS":
                print(f"Metamon {my_monster_token_id} already powerup. Please try again tommorow !")
                return
        power_up_response = self.power_up(my_monster_id, attr_up_type)#Se refere a operações do Jogo. OK!
        print(f"gaga {power_up_response}")
        if power_up_response.get("code") == "SUCCESS":
            data = power_up_response.get("data")
            if data.get("upperNum") == 0:
                print(f"\nUp {attr_up_name} for metamon {my_monster_token_id} failed")#Se refere a operações do Jogo. OK!
            else:
                attr_num = data.get("attrNum")
                upper_num = data.get("upperNum")
                upper_attr_num = data.get("upperAttrNum")
                sca = data.get("sca")#Se refere a operações do Jogo. OK!
                upper_sca = data.get("upperSca")
                print(f"{attr_up_name} of metamon {my_monster_token_id} +{upper_num}: {attr_num} -> {upper_attr_num}")
                print(f"Score of metamon {my_monster_token_id}: {sca} -> {upper_sca}")#Se refere a operações do Jogo. OK!
        elif power_up_response.get("code") == "INSUFFICIENT_PROP_ERROR":#Se refere a operações do Jogo. OK!
            self.is_use_green_potion_only = True
            print(f"You don't have enough purple potion to power up for Metamon {my_monster_token_id}")
        elif power_up_response.get("code") == "ATTR_UPPER_PURPLE_EXIST_ERROR":#Se refere a operações do Jogo. OK!
            print(f"Metamon {my_monster_token_id} has power up, try tomorrow")
        else:
            print(f"Power up unsuccesful")#Se refere a operações do Jogo. OK!
    def display_battle(self,
                       challenge_record,
                       challenge_monster,
                       my_monster_id,
                       my_monster_token_id,
                       my_monster_luk,
                       my_monster_size,
                       my_monster_inv,
                       my_monster_crg,
                       my_monster_inte,
                       old_stdout,
                       maximum_length,
                       game_count):
        count = 0
        opponent_crit_count = 0;
        str_start = "*"#Se refere a operações do Jogo. OK!
        str_start_game =  f"START GAME {game_count}"
        for i in range(maximum_length - len(str_start_game) - 3):#Se refere a operações do Jogo. OK!
            str_start = str_start + " "
            count_temp = maximum_length/2 - len(str_start_game)
            if count_temp == i:#Se refere a operações do Jogo. OK!
                str_start = str_start + str_start_game
        str_start = str_start + " *"#Se refere a operações do Jogo. OK!
        print(f"{str_start}")    
        
        for record in challenge_record:

            count += 1
            target_monster_size = challenge_monster.get("con")
            target_monster_inte = challenge_monster.get("inte")
            target_monster_crg = challenge_monster.get("crg")
            target_monster_inv = challenge_monster.get("inv")#Se refere a operações do Jogo. OK!
            
            monsteraId = record.get("monsteraId")
            attackType = record.get("attackType")
            defenceType = record.get("defenceType")
            monsteraLife = record.get("monsteraLife")
            finalDame = record.get("monsterbLifelost")#Se refere a operações do Jogo. OK!
            #monsterBLife = record.get("monsterbLife")
            attackTypeStr = ""
            defenceTypeStr = ""
            
            if attackType == 0:
               attackTypeStr = "Wisdom"#Se refere a operações do Jogo. OK!
            else:
               attackTypeStr = "Size"
            if defenceTypeStr == 0:
               defenceTypeStr = "Courage"#Se refere a operações do Jogo. OK!
            else:
               defenceTypeStr = "Stealth"     
               
            attribute_random_info = f"* Turn {count}: Attack {attackTypeStr}, Defence {defenceTypeStr}"#Se refere a operações do Jogo. OK!

            for i in range(maximum_length - len(attribute_random_info) - 2):
                attribute_random_info = attribute_random_info + " "
            attribute_random_info = attribute_random_info + " *"#Se refere a operações do Jogo. OK!
            print(f"{attribute_random_info}")               

            if monsteraId == my_monster_id:
                str_metamon_info = f"* My Metamon Fighting: Health {monsteraLife}, Final Dame = {finalDame}"#Se refere a operações do Jogo. OK!
                for i in range(maximum_length - len(str_metamon_info) - 2):
                    str_metamon_info = str_metamon_info + " "
                str_metamon_info_print = str_metamon_info + " *"
                print(f"{str_metamon_info_print}")
                if attackType == 0 and defenceType == 0:
                    if finalDame == (my_monster_inte - target_monster_crg*2) or finalDame == (my_monster_inte*2 - target_monster_crg*2):
                        opponent_crit_count += 1
                elif attackType == 0 and defenceType == 1:
                    if finalDame == (my_monster_inte - target_monster_inv*2) or finalDame == (my_monster_inte*2 - target_monster_inv*2):
                        opponent_crit_count += 1                
                elif attackType == 1 and defenceType == 0:
                    if finalDame == (my_monster_size - target_monster_crg*2) or finalDame == (my_monster_size*2 - target_monster_crg*2):
                        opponent_crit_count += 1                  
                elif attackType == 1 and defenceType == 1:
                    if finalDame == (my_monster_size - target_monster_inv*2) or finalDame == (my_monster_size*2 - target_monster_inv*2):
                        opponent_crit_count += 1                   
            else:#Se refere a operações do Jogo. OK!
                str_target_info = f"* Opponent's Metamon Fighting: Health {monsteraLife}, Final Dame = {finalDame}"
                for i in range(maximum_length - len(str_target_info) - 2):
                    str_target_info = str_target_info + " "
                str_target_info = str_target_info + " *"               
                print(f"{str_target_info}")
                if attackType == 0 and defenceType == 0:
                    if finalDame == (target_monster_inte*2 - my_monster_crg) or finalDame == (target_monster_inte*2 - my_monster_crg*2):
                        opponent_crit_count += 1
                elif attackType == 0 and defenceType == 1:
                    if finalDame == (target_monster_inte*2 - my_monster_inv) or finalDame == (target_monster_inte*2 - my_monster_inv*2):
                        opponent_crit_count += 1                
                elif attackType == 1 and defenceType == 0:
                    if finalDame == (target_monster_size*2 - my_monster_crg) or finalDame == (target_monster_size*2 - my_monster_crg*2):
                        opponent_crit_count += 1                  
                elif attackType == 1 and defenceType == 1:
                    if finalDame == (target_monster_size*2 - my_monster_inv) or finalDame == (target_monster_size*2 - my_monster_inv*2):
                        opponent_crit_count += 1
        str_target_crit_count = f"* Opponent's crit: {opponent_crit_count} times in battle"#Se refere a operações do Jogo. OK!
        for i in range(maximum_length - len(str_target_crit_count) - 2):
           str_target_crit_count = str_target_crit_count + " "
        str_target_crit_count = str_target_crit_count + " *"               
        print(f"{str_target_crit_count}") 
        str_end = "*"
        str_end_game = f"END GAME {game_count}"
        for i in range(maximum_length - len(str_end_game) - 3):
            str_end = str_end + " "
            count_temp = maximum_length/2 - len(str_end_game)
            if count_temp == i:
                str_end = str_end + str_end_game
        str_end = str_end + " *"
        print(f"{str_end}\n") 
        return opponent_crit_count
             
    def start_fight(self,
                    my_monster,
                    target_monster_id,
                    target_monster_race,
                    target_monster_size,
                    target_monster_luk,
                    target_monster_inv,
                    target_monster_crg,
                    target_monster_inte,
                    target_monster_sca,
                    loop_count=1):
        """ Main method to initiate battles (as many as monster has energy for)"""#Se refere a operações do Jogo. OK!
        success = 0
        fail = 0
        total_bp_fragment_num = 0
        mtm_stats = []
        my_monster_id = my_monster.get("id")
        my_monster_token_id = my_monster.get("tokenId")
        my_luk = my_monster.get("luk")
        my_size = my_monster.get("con")
        my_inte = my_monster.get("inte")
        my_courage = my_monster.get("crg")
        my_inv = my_monster.get("inv")
        my_level = my_monster.get("level")
        my_exp = my_monster.get("exp")
        my_power = my_monster.get("sca")
        my_race = my_monster.get("race")
        my_allow_upper = my_monster.get("allowUpper")
        my_allow_reset = my_monster.get("allowReset")
        my_healthy = my_monster.get("healthy")
        battle_level = pick_battle_level(my_level)
        tbar = trange(loop_count)
        if my_healthy <= 90:
            self.add_metamon_healthy(my_monster_id)
        if  self.auto_exp_up[0] == True:    
            exp_up_response = self.exp_up(my_monster_id)
            while (exp_up_response.get("code") == "SUCCESS"):#Se refere a operações do Jogo. OK!
                data = exp_up_response.get("data")
                print(f"\nEXP UP FOR METAMON {my_monster_token_id} SUCCESS : +{data}")
                exp_up_response = self.exp_up(my_monster_id)#Se refere a operações do Jogo. OK!
            if self.auto_lvl_up[0]:
                # Try to lvl up
                headers = {
                    "accessToken": self.token,
                }
                res = post_formdata({"nftId": my_monster_id, "address": self.address},
                                    LVL_UP_URL,
                                    headers)
                code = res.get("code")
                if code == "SUCCESS":
                    tbar.set_description("LVL UP successful! Continue fighting...")#Se refere a operações do Jogo. OK!
                    my_level += 1
                    # Update league level if new level is 21 or 41
                    battle_level = pick_battle_level(my_level)
        if self.auto_power_up[0] == True and my_allow_upper == True:
            attr_up_type = 1
            attr_up_name = "Luck"#Se refere a operações do Jogo. OK!
            if my_courage < 50:
                attr_up_type = 2#Se refere a operações do Jogo. OK!
                attr_up_name = "Courage"#Se refere a operações do Jogo. OK!
            elif my_inte < 101:
                attr_up_type = 3
                attr_up_name = "Wisdom"#Se refere a operações do Jogo. OK!
            elif my_size < 101:
                attr_up_type = 4
                attr_up_name = "Size"#Se refere a operações do Jogo. OK!
            elif my_inv < 50:
                attr_up_type = 5
                attr_up_name = "Stealth"#Se refere a operações do Jogo. OK!
            power_up_response = self.power_up(my_monster_id, attr_up_type)
            if power_up_response.get("code") == "SUCCESS":#Se refere a operações do Jogo. OK!
                data = power_up_response.get("data")
                if data.get("upperNum") == 0:
                    self.total_powup_fail += 1
                    print(f"\nUp {attr_up_name} for metamon {my_monster_token_id} failed")
                else:
                    attr_num = data.get("attrNum")
                    upper_num = data.get("upperNum")
                    upper_attr_num = data.get("upperAttrNum")
                    sca = data.get("sca")
                    upper_sca = data.get("upperSca")
                    self.total_powup_success += 1
                    print(f"\n{attr_up_name} of metamon {my_monster_token_id} +{upper_num}: {attr_num} -> {upper_attr_num}")
                    print(f"Score of metamon {my_monster_token_id}: {sca} -> {upper_sca}")
            else:
                print(f"\nUp {attr_up_name} for metamon {my_monster_token_id} unsuccesful")

        tbar.set_description("Fighting...")

        if self.battle_record[0] == True:
            old_stdout = sys.stdout
            sys.stdout = self.log_file
            str_end = ""
            maximum_length = 98
            my_metamon_print = f"* My Metamon: ID {my_monster_token_id}, Luk {my_luk}, Wisdom {my_inte}, Size {my_size}, Courage {my_courage}, Stealth {my_inv} "
            target_metamon_print = f"* Target Metamon: ID {target_monster_id}, Luk {target_monster_luk}, Wisdom {target_monster_inte}, Size {target_monster_size}, Courage {target_monster_crg}, Stealth {target_monster_inv} "
            for i in range(maximum_length):
                str_end = str_end + "*"
            print(f"{str_end}")

            if maximum_length - len(my_metamon_print) > 0:
                for i in range(maximum_length - len(my_metamon_print) - 1):
                    my_metamon_print = my_metamon_print + " "
                my_metamon_print = my_metamon_print + "*"
            print(f"{my_metamon_print}")
            
            if maximum_length - len(target_metamon_print) > 0:
                for i in range(maximum_length - len(target_metamon_print) - 1):
                    target_metamon_print = target_metamon_print + " "
                target_metamon_print = target_metamon_print + "*"
            print(f"{target_metamon_print}")            
        game_count = 0
        opp_crit_count = 0
        for _ in tbar:
            if (my_level == 59 and my_exp >= 600) or (my_level == 60 and my_exp >= 395 and my_allow_reset == False):
                break
            if my_level >= 60 and my_exp >= 395:
                resetResponse = self.reset_exp(my_monster_id)
                if resetResponse == None or resetResponse.get("code") != "SUCCESS":
                    break
                else:
                    print("Reset EXP Success!")
                    my_exp = 0
                    
            payload = {
                "monsterA": my_monster_id,
                "monsterB": target_monster_id,
                "address": self.address,
                "battleLevel": battle_level,
            }
            headers = {
                "accessToken": self.token,
            }
            response = post_formdata(payload, START_FIGHT_URL, headers)

            code = response.get("code")
            if code == "BATTLE_NOPAY":
                self.no_enough_money = True
                break
            if code != "SUCCESS":
                print("Battle Failed")
                break
                
            data = response.get("data", {})
            challenge_monster = data.get("challengedMonster")
            challenge_record = data.get("challengeRecords")
            fight_result = data.get("challengeResult", False)
            bp_fragment_num = data.get("bpFragmentNum", 10)
            
            target_monster_id = challenge_monster.get("id")
            target_monster_luk = challenge_monster.get("luk")
            target_monster_size = challenge_monster.get("con")
            target_monster_inte = challenge_monster.get("inte")
            target_monster_crg = challenge_monster.get("crg")
            target_monster_inv = challenge_monster.get("inv")
            target_monster_sca = challenge_monster.get("sca")
            target_monster_race = challenge_monster.get("race")
            opp_crit_count = 0
            game_count +=1
            if self.battle_record[0] == True:
                opp_crit_count = self.display_battle(challenge_record,challenge_monster, my_monster_id, my_monster_token_id, my_luk, my_size, my_inv, my_courage, my_inte, old_stdout, maximum_length, game_count)
                
            if self.auto_lvl_up[0] and my_level < 59:
                # Try to lvl up
                res = post_formdata({"nftId": my_monster_id, "address": self.address},
                                    LVL_UP_URL,
                                    headers)
                code = res.get("code")
                if code == "SUCCESS":#Se refere a operações do Jogo. OK!
                    tbar.set_description("LVL UP successful! Continue fighting...")#Se refere a operações do Jogo. OK!
                    my_level += 1
                    # Update league level if new level is 21 or 41
                    battle_level = pick_battle_level(my_level)

            self.total_bp_num += bp_fragment_num
            total_bp_fragment_num += bp_fragment_num
            if fight_result:
                my_exp = int(my_exp)+5
                success += 1
                self.total_success += 1
            else:
                my_exp = int(my_exp)+3
                fail += 1
                self.total_fail += 1
        if self.battle_record[0] == True:
            str_end = ""
            for i in range(maximum_length):
                str_end = str_end + "*"
            print(f"{str_end}") 
            sys.stdout = old_stdout
        mtm_stats.append({
            "TokenId": my_monster_token_id,
            "Race": my_race,
            "Power": my_power,
            "Level": my_level,
            "Size": my_size,
            "Wisdom": my_inte,
            "Courage": my_courage,
            "Luck": my_luk,
            "Stealth": my_inv,
            "Opp TokenId": target_monster_id,
            "Opp Race": target_monster_race,
            "Opp Luk": target_monster_luk,
            "Opp Courage": target_monster_crg,
            "Opp Wisdom": target_monster_inte,
            "Opp Size": target_monster_size,
            "Opp Stealth": target_monster_inv,
            "Opp Power": target_monster_sca,
            "Opp Crit Times": opp_crit_count,
            "Total battles": loop_count,
            "Victories": success,
            "Defeats": fail,
            "Total egg shards": total_bp_fragment_num,
            "Timestamp": datetime_now(),
        })
        mtm_stats_print = []
        mtm_stats_print.append({
            "MonId": my_monster_token_id,
            "Race": my_race,
            "Power": my_power,
            "Level": my_level,
            "Healthy": my_healthy,
            "Total battles": loop_count,
            "Victories": success,
            "Defeats": fail,
            "Total egg shards": total_bp_fragment_num,
            "Timestamp": datetime_now(),
        })
        mtm_stats_df = pd.DataFrame(mtm_stats)
        print(f"{mtm_stats_print}")
        self.mtm_stats_df.append(mtm_stats_df)

    def get_wallet_properties(self):
        """ Obtain list of metamons on the wallet"""#Se refere a operações do Jogo. OK!

        payload = {"address": self.address}
        headers = {
            "accesstoken": self.token,
        }
        response = post_formdata(payload, WALLET_PROPERTY_LIST, headers)
        mtms = response.get("data", {}).get("metamonList", [])#Se refere a operações do Jogo. OK!
        return mtms

    def list_monsters(self):
        """ Obtain list of metamons on the wallet (deprecated)"""#Se refere a operações do Jogo. OK!
        payload = {"address": self.address, "page": 1, "pageSize": 150, "payType": -6}
        headers = {"accessToken": self.token}#Se refere a operações do Jogo. OK!
        response = post_formdata(payload, LIST_MONSTER_URL, headers)
        monsters = response.get("data", {}).get("data", {})
        return monsters

    def battle(self, w_name=None):
        """ Main method to run all battles for the day"""#Se refere a operações do Jogo. OK!
        if w_name is None:
            w_name = self.address

        summary_file_name = f"{w_name}_summary.tsv"
        mtm_stats_file_name = f"{w_name}_stats.tsv"
        self.init_token()
        
        monsters = self.list_monsters()
        wallet_monsters = self.get_wallet_properties()

        available_monsters = [
            #monster for monster in wallet_monsters if monster.get("tear") > 0 and monster.get("exp") < 600 and monster.get("level") < 60
            monster for monster in wallet_monsters if monster.get("tear") > 0
        ]
        stats_l = []
        print(f"Available Monsters : {len(available_monsters)}")#Se refere a operações do Jogo. OK!
       
        for monster in available_monsters:
            monster_id = monster.get("id")
            tear = monster.get("tear")
            level = monster.get("level")#Se refere a operações do Jogo. OK!
            exp = monster.get("exp")
            allow_reset = monster.get("allowReset")
  
            if (level == 59 and exp >= 600) or (level >= 60 and  allow_reset == False):
                print(f"Monster {monster_id} cannot fight due to "
                      f"max lvl and/or exp overflow. Skipping...")  
                continue
            if level >= 60 and exp >= 395:
                resetResponse = self.reset_exp(monster_id)
                if resetResponse == None or resetResponse.get("code") != "SUCCESS":
                    continue
                else:
                    print("Reset EXP Success!")#Se refere a operações do Jogo. OK!
                    monster["exp"] = 0
            battlers = self.list_battlers(monster_id)
            ofm = self.other_fighting_mode
            battler = picker_battler(battlers, ofm)
            target_monster_id = battler.get("id")
            target_monster_race = battler.get("race")
            target_monster_size = battler.get("con")
            target_monster_luk = battler.get("luk")
            target_monster_inv = battler.get("inv")
            target_monster_crg = battler.get("crg")#Se refere a operações do Jogo. OK!
            target_monster_inte = battler.get("inte")
            target_monster_sca = battler.get("sca")
            
            self.change_fighter(monster_id)

            self.start_fight(monster,
                             target_monster_id,
                             target_monster_race,
                             target_monster_size,
                             target_monster_luk,
                             target_monster_inv,
                             target_monster_crg,
                             target_monster_inte,
                             target_monster_sca,
                             loop_count=tear)
            if self.no_enough_money:
                print("Not enough u-RACA")
                break
        total_count = self.total_success + self.total_fail
        success_percent = .0
        if total_count > 0:
            success_percent = (self.total_success / total_count) * 100

        success_powup_percent = .0
        total_powup_count = self.total_powup_success + self.total_powup_fail
        if total_powup_count > 0:
            success_powup_percent = (self.total_powup_success / total_powup_count) * 100        
        if total_count <= 0:
            print("No battles to record")
            return

        stats_l.append({
            "Victories": self.total_success,
            "Defeats": self.total_fail,
            "Win Rate": f"{success_percent:.2f}%",#Se refere a operações do Jogo. OK!
            "Total Egg Shards": self.total_bp_num,
            "Powerup Success Rate": f"{success_powup_percent: .2f}%",
            "Datetime": datetime_now()
        })

        stats_df = pd.DataFrame(stats_l)
        print(stats_df)
        if os.path.exists(summary_file_name) and self.output_stats:
            back_fn = f"{summary_file_name}.bak"
            os.rename(summary_file_name, back_fn)
            tmp_df = pd.read_csv(back_fn, sep="\t", dtype="str")#Se refere a operações do Jogo. OK!
            stats_upd_df = pd.concat([stats_df, tmp_df])
            stats_df = stats_upd_df
            os.remove(back_fn)

        if self.output_stats:
            stats_df.to_csv(summary_file_name, index=False, sep="\t")

        mtm_stats_df = pd.concat(self.mtm_stats_df)
        if os.path.exists(mtm_stats_file_name) and self.output_stats:
            back_fn = f"{mtm_stats_file_name}.bak"
            os.rename(mtm_stats_file_name, back_fn)
            tmp_df = pd.read_csv(back_fn, sep="\t", dtype="str") #Se refere a operações do Jogo. OK!
            upd_df = pd.concat([mtm_stats_df, tmp_df])
            mtm_stats_df = upd_df
            os.remove(back_fn)
        if self.output_stats:
            mtm_stats_df.to_csv(mtm_stats_file_name, sep="\t", index=False)
        self.log_file.close()

    def mint_eggs(self):
        self.init_token()

        headers = {
            "accessToken": self.token,
        }#Se refere a operações do Jogo. OK!
        payload = {"address": self.address}

        # Check current egg fragments
        check_bag_res = post_formdata(payload, CHECK_BAG_URL, headers)
        items = check_bag_res.get("data", {}).get("item")#Se refere a operações do Jogo. OK!
        total_egg_fragments = 0
        if (items is None):
            print("GET ASSETS IN PACKAGE FAIL")
        else:
            for item in items:
                if item.get("bpType") == 1:
                    total_egg_fragments = item.get("bpNum")
                    break

            total_egg = int(int(total_egg_fragments) / 1000)

            if total_egg < 1:
                print("You don't have enough egg fragments to mint") #Se refere a operações do Jogo. OK!
                return

            # Mint egg
            res = post_formdata(payload, MINT_EGG_URL, headers)
            code = res.get("code")
            if code != "SUCCESS":
                print("Mint eggs failed!")#Se refere a operações do Jogo. OK!
                return

            print(f"Minted Eggs Total: {total_egg}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--input-tsv", help="Path to tsv file with wallets' "
                                                  "access records (name, address, sign, login message) "
                                                  "name is used for filename with table of results. "
                                                  "Results for each wallet are saved in separate files",
                        default="wallets.tsv", type=str)
    parser.add_argument("-nl", "--no-lvlup", help="Disable automatic lvl up "
                                                  "(if not enough potions/diamonds it will be disabled anyway) "
                                                  "by default lvl up will be attempted after each battle",
                        action="store_true", default=False)
    parser.add_argument("-nb", "--skip-battles", help="No battles, use when need to only mint eggs from shards",
                        action="store_true", default=False)
    parser.add_argument("-e", "--mint-eggs", help="Automatically mint eggs after all battles done for a day",
                        action="store_true", default=False)
    parser.add_argument("-s", "--save-results", help="To enable saving results on disk use this option. "
                                                     "Two files <name>_summary.tsv and <name>_stats.tsv will "
                                                     "be saved in current dir.",
                        action="store_true", default=False)
                        
    parser.add_argument("-ofm", "--other-fighting-mode", help="To select metamon have lowest Wisdom, Size, Luck, Courage, Stealth to play for more win",
                        action="store_true", default=False)
    parser.add_argument("-ls", "--lowest-score", help="To select metamon have lowest score by hardcode metamon id",
                        action="store_true", default=False)                      
    parser.add_argument("-expup", "--auto-exp-up", help="Automatically up exp for metamon before battle",
                        action="store_true", default=False)
    parser.add_argument("-powerup", "--auto-power-up", help="Automatically up power for metamon before battle",
                        action="store_true", default=False)
    parser.add_argument("-uppo", "--use-green-potion-only", help="Automatically up power for metamon before battle without using purple potion",
                        action="store_true", default=False)
    parser.add_argument("-br","--battle-record", help="Watching record of each battle, Creating log after finish",
                        action="store_true", default=False)
                        
    parser.add_argument("-as","--average-sca", help="Find Squad with average score inputing to join", default=335, type=int) 
  
    parser.add_argument("-fso","--find-squad-only", help="Find squad with average score from 335 when dont have any metamon level 60",
                        action="store_true", default=False)

    parser.add_argument("-kdm","--kingdom-mode", help="Run functions on Metamon Kingdom",
                        action="store_true", default=False) 
                        
    parser.add_argument("-ti","--token-id", help="Get TokenId of metamon in bags",
                        action="store_true", default=False)

    parser.add_argument("-buy","--buy-purple-potion", help="Buy purple potion equal with number of metamon in metamon kingdom", action="store_true", default=False)                         
    
    parser.add_argument("-ah","--add-healthy", help="Automatically adding healthy for metamon have healthy below 90", action="store_true", default=False)                             
    
    args = parser.parse_args()

    if not os.path.exists(args.input_tsv):
        print(f"Input file {args.input_tsv} does not exist")#Se refere a operações do Jogo. OK!
        sys.exit(-1)

    # determine delimiter char from given input file
    with open(args.input_tsv) as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.readline(), "\t ;,")
        delim = dialect.delimiter#Se refere a operações do Jogo. OK!

    wallets = pd.read_csv(args.input_tsv, sep=delim)

    auto_lvlup = not args.no_lvlup
    auto_powerup = args.auto_power_up
    auto_expup = args.auto_exp_up
    other_fmode = args.other_fighting_mode
    lscore = args.lowest_score
    average_sca = args.average_sca
    is_kingdom_mode = args.kingdom_mode
    fso = args.find_squad_only#Se refere a operações do Jogo. OK!
    ti = args.token_id
    buy_purple_potion = args.buy_purple_potion
    add_healthy = args.add_healthy
    use_green_potion_only = args.use_green_potion_only
    for i, r in wallets.iterrows():
        name = ""
        if hasattr(r,"walletname"):
            name = r.walletname
        mtm = MetamonPlayer(address=r.address,
                            sign=r.sign,
                            msg=r.msg,
                            name = name,
                            auto_lvl_up=auto_lvlup,
                            other_fighting_mode =other_fmode,
                            lowest_score = lscore,
                            auto_exp_up = auto_expup,
                            auto_power_up = auto_powerup,
                            battle_record = args.battle_record,
                            output_stats=args.save_results,
                            average_sca_default = average_sca,
                            find_squad_only = fso,
                            add_healthy = add_healthy,
                            is_use_green_potion_only = use_green_potion_only)                 
        if is_kingdom_mode or fso:
            mtm.start_find_squads()
        elif ti:
            mtm.get_token_ids()
        elif buy_purple_potion:
            mtm.buy_item()
        else:
            if not args.skip_battles:
                mtm.battle(w_name=name)
            else:
                if args.auto_exp_up:
                    mtm.auto_up_exp()
                if args.auto_power_up:
                    mtm.auto_up_power()
            if args.mint_eggs:
                mtm.mint_eggs()
           
