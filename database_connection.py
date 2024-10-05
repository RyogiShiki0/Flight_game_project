import mysql.connector

connection = mysql.connector.connect(
         host='127.0.0.1',
         port='3306',
         database='flight_game',
         user='root',
         password='114514',
         autocommit=True
         )
