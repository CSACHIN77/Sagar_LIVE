import requests

def get_socket_instance():
    try:
        # Make a GET request to the FastAPI endpoint
        response = requests.get("http://127.0.0.1:9001/get_socket")

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            print("Socket Status:", data)
        else:
            print(f"Failed to get socket. Status code: {response.status_code}, Response: {response.text}")

    except requests.exceptions.RequestException as e:
        print("An error occurred while calling the API:", str(e))

if __name__ == "__main__":
    get_socket_instance()