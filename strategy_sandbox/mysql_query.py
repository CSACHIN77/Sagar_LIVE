import mysql.connector

# Connection details
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="pegasus",
    database="sagar_dataharvesting"
)

try:
    # Creating a cursor object
    cursor = connection.cursor()

    # Writing the query
    query = """
        SELECT count(*) 
        FROM data_harvesting_20241210
        WHERE exchangeInstrumentid = 26000;
    """

    # Executing the query
    cursor.execute(query)

    # Fetching the results
    results = cursor.fetchall()
    print(results)
    # Printing the results
    # for row in results:
    #     print(row)

except mysql.connector.Error as e:
    print(f"Error: {e}")
finally:
    # Closing the connection
    if connection.is_connected():
        cursor.close()
        connection.close()
