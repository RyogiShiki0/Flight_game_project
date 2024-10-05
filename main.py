from geopy import location,distance
import random

from sqlalchemy import values

from database_connection import connection

def welcome():
    print("Welcome to Flight Game!")
    play_choice=input("[1]Create a new game\n[2]Continue last game\n")
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

    name = input("Please enter your game ID:")
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
    start_country = select_country()
    start_airport = select_airport(start_country)
    money = 600
    fuel = 10
    create_new_player(name, money, fuel)
    start_game(money,fuel,start_airport,name)

def start_game(money,fuel,location,name):
    choice = input('\n[1]Start transport mission\n[2]Upgrading aircraft\n[3]Save game\n[4]Check your status\nChoose Things to Do:')
    if (choice == '1'):
        money,total_value = purchase_goods(money,location,name)
        print('The purchase of goods has been completed!')
        start_flight(money, fuel, location, name)

    elif(choice == '2'):
        money = purchase_upgrade(money,name)
    start_game(money, fuel, location, name)

def start_flight(money,fuel,location,name):
    print('Please select your flight destination.')
    num = random.randint(1,6)
    if(num == 1 or num == 6):
        bonus = 10
    else: bonus = num
    print(f'Rolled the dice, the number is {num}, you got {bonus} fuel points.')
    fuel += bonus
    dest_country = select_country()
    dest_airport = select_airport(dest_country)
    airport_distance = distance_calculator(location, dest_airport)
    fuel_reduction = 1 - (check_fuel_reduction(name) / 100)
    airport_distance = airport_distance * fuel_reduction
    need_fuel_point = int(airport_distance/100)
    if (need_fuel_point == 0):
        need_fuel_point = 1



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
                print(f"Purchase Success! You have {money} money left\n")
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
                print(f'Purchase Success!')
    return (money,total_value)


play_choice = welcome()

if play_choice == "1":
    new_game()
    dest_country = select_country()
    dest_airport = select_airport(dest_country)
    airport_distance = distance_calculator(start_airport, dest_airport)
    print(airport_distance)

