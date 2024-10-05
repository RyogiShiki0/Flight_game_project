from geopy import location,distance
import random

from sqlalchemy import values

from database_connection import connection

def welcome():
    print(" _   _               _ _        _____ _ _       _     _   \n| \ | | ___  _ __ __| (_) ___  |  ___| (_) __ _| |__ | |_ \n|  \| |/ _ \| '__/ _` | |/ __| | |_  | | |/ _` | '_ \| __|\n| |\  | (_) | | | (_| | | (__  |  _| | | | (_| | | | | |_ \n|_|_\_|\___/|_|  \__,_|_|\___| |_|   |_|_|\__, |_| |_|\__|\n/ ___|(_)_ __ ___  _   _| | __ _| |_ ___  |___/           \n\___ \| | '_ ` _ \| | | | |/ _` | __/ _ \| '__|           \n ___) | | | | | | | |_| | | (_| | || (_) | |              \n|____/|_|_| |_| |_|\__,_|_|\__,_|\__\___/|_|              ")
    print("Welcome to Nordic Flight Simulator!")
    play_choice=input("[1]Create a new game\n[2]Continue last game\nPlease input the number to select: ")
    return play_choice

def select_country():
    sql = f"select name from country where name in {'norway','finland','sweden','denmark'}"
    cursor = connection.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    for i in result:
        print(i[0])
    country = input("Please select a country:")
    return(country)

def select_airport(country):
    sql = f"select name from airport where iso_country = (select iso_country from country where name = '{country}' and type in ('large_airport','medium_airport'))"
    cursor = connection.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    num=1
    for i in result:
        print(f'[{num}]: {i[0]}')
        num+=1
    airport = int(input("Please select a airport:"))
    airport = result[airport-1][0]
    return(airport)

def create_name():

    name = input("Please input the name you want to appear in the game:")
    repeat = check_name_repeat(name)
    while (repeat != 0):
        name = input("This username has been taken. Please try again.:")
        repeat = check_name_repeat(name)
    return name


def check_name_repeat(name):
    sql = f"select player_name from player"
    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql)
    result = cursor.fetchall()
    repeat = 0
    for i in result:
        if name in i.values():
            repeat = 1
    return(repeat)

def create_new_player(name,money,fuel):
    sql = f"INSERT INTO player (player_name, money, fuel_points) VALUES ('{name}',{money},{fuel})"
    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql)

def distance_calculator(departure,arrival):
    departure = get_location_by_name(departure)
    arrival = get_location_by_name(arrival)
    airport_distance = int(distance.distance(departure,arrival).km)
    return airport_distance

def get_location_by_name(name):
  sql= f"SELECT latitude_deg,longitude_deg FROM airport where name = '{name}'"
  cursor = connection.cursor(dictionary=True)
  cursor.execute(sql)
  result = cursor.fetchone()
  latitude = result['latitude_deg']
  longitude = result['longitude_deg']
  airport = (latitude, longitude)
  return airport

def new_game():
    name = create_name()
    print(f'Hi {name}, now you will choose your initial starting point.')
    start_country = select_country()
    start_airport = select_airport(start_country)
    money = 600
    fuel = 0
    create_new_player(name, money, fuel)
    print('Great! Now you are here. You can choose the thing you want to do by input the number.')
    start_game(money,fuel,start_airport,name)

def load_save(name):
    sql = f"SELECT * FROM player where player_name = '{name}'"
    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql)
    result = cursor.fetchone()
    if result is None:
        print('Unable to find your save')
        start_program()
    else:
        print('successfully find your save!')
        print(result)
        money = result['money']
        fuel = result['fuel_points']
        location = result['location']
        start_game(money, fuel, location, name)





def start_game(money,fuel,location,name):
    choice = input('\n[1]Start transport mission\n[2]Upgrading aircraft\n[3]Save game\n[4]Check your status\nChoose Things to Do:')
    if (choice == '1'):
        money,total_value = purchase_goods(money,location,name)
        print('The purchase of goods has been completed!')
        start_flight(money, fuel, location, name, total_value)

    elif(choice == '2'):
        money = purchase_upgrade(money,name)

    elif (choice == '3'):
        save_game(money, fuel, location, name)

    elif (choice == '4'):
        print(f'name:{name}; money:{money}; fuel:{fuel}; current location:{location}')

    start_game(money, fuel, location, name)

def save_game(money, fuel, location, name):
    sql = f"update player set money = {money}, fuel_points = {fuel}, location = '{location}' where player_name = '{name}'"
    cursor = connection.cursor()
    cursor.execute(sql)
    print('\nGame has been saved!')


def start_flight(money,fuel,location,name,total_value):
    num = random.randint(1,6)
    if(num == 1 or num == 6):
        bonus = 10
    else: bonus = num
    print(f'\nRolled the dice, the number is {num}, you got {bonus} fuel points.')
    print('\nPlease select your flight destination.')
    fuel += bonus
    enough_fuel = False
    while(enough_fuel != True):
        dest_country = select_country()
        dest_airport = select_airport(dest_country)
        airport_distance = distance_calculator(location, dest_airport)
        fuel_reduction = 1 - (check_fuel_reduction(name) / 100)
        need_fuel_point = airport_distance * fuel_reduction
        need_fuel_point = int(need_fuel_point/100)
        if (need_fuel_point == 0):
            need_fuel_point = 1
        if(fuel < need_fuel_point):
            print('\nYou do not have enough fuel points!\n')
        else:
            enough_fuel = True
    total_value = total_value * (1 + airport_distance/1000)
    print(f'\nYou successfully reached your destination and earned {total_value}\n')
    money += total_value
    fuel -= need_fuel_point
    location = dest_airport
    start_game(money, fuel, location, name)


def check_fuel_reduction(name):
    sql = f"SELECT sum(fuel_reduction_percentage) FROM upgrade where upgrade_id in (select upgrade_id from player_upgrade where player_ID = '{get_player_ID(name)}')"
    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql)
    result = cursor.fetchone()
    num = result['sum(fuel_reduction_percentage)']
    if(num is None):
        num = 0
    return float(num)

def check_capacity_increase(name):
    sql = f"SELECT sum(capacity_increase_percentage) FROM upgrade where upgrade_id in (select upgrade_id from player_upgrade where player_ID = '{get_player_ID(name)}')"
    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql)
    result = cursor.fetchone()
    num = result['sum(capacity_increase_percentage)']
    if (num is None):
        num = 0
    return float(num)

def get_player_ID(name):
    sql = f"select player_id from player where player_name = '{name}'"
    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql)
    result = cursor.fetchone()
    return result['player_id']

def purchase_upgrade(money,name):
    choice = 0
    while (choice != 'q'):
        sql = f"select * from upgrade where upgrade_ID not in (select upgrade_ID from player_upgrade where player_ID = (select player_ID from player where player_name = '{name}'))"
        cursor = connection.cursor(dictionary=True)
        cursor.execute(sql)
        result = cursor.fetchall()
        num = 1
        for i in result:
            if i['type'] == '1':
                print(f'[{num}] capacity increase:{i['capacity_increase_percentage']}; cost: {i["cost"]}')
            elif i['type'] == '2':
                print(f'[{num}] {i["fuel_reduction_percentage"]} percent reduction in fuel; cost: {i["cost"]}')
            num += 1
        choice = input('Please select the items to upgrade. Enter q to end.')
        if (choice != 'q'):
            choice = int(choice)
            if(result[choice-1]['cost']>money):
                print('\nYou do not have enough money!\n')
            else:
                money = money - result[choice-1]['cost']
                print(f"\nPurchase Success! You have {money} money left\n")
                sql = f"INSERT INTO player_upgrade (player_id, upgrade_id) VALUES ('{get_player_ID(name)}','{result[choice-1]['upgrade_ID']}')"
                cursor = connection.cursor()
                cursor.execute(sql)

    return money



def purchase_goods(money,location,name):
    sql = f"select * from goods where goods_id in (select goods_id from goods_in_country where iso_country = (SELECT iso_country FROM airport where name = '{location}'))"
    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql)
    result = cursor.fetchall()
    num=1
    capacity = 100 + check_capacity_increase(name)
    for i in result:
        print(f'[{num}] {i['goods_name']} weight:{i["goods_weight"]} value:{i["goods_value"]}\n')
        num+=1
    choice =0
    total_value = 0
    while (choice != 'q'):
        print(f'You have {money} money and and {capacity} storage spaces left.')
        choice = input('Please select the items to purchase. Enter q to end.')
        if(choice != 'q'):
            choice = int(choice)
            amount = int(input('Please enter the amount of goods:'))
            value = result[choice-1]['goods_value']
            weight = result[choice-1]['goods_weight']
            if(amount*value > money):
                print('Your money is not enough buying these!')
            elif(amount*weight > capacity):
                print('You don’t have enough storage space!')
            else:
                total_value = amount*value + total_value
                money = money- amount*value
                capacity = capacity-weight*amount
                print(f'\nPurchase Success!\n')
    return (money,total_value)

def start_program():
    play_choice = welcome()
    if play_choice == "1":
        new_game()
    elif play_choice == '2':
        name = input('Please enter your name: ')
        load_save(name)

start_program()