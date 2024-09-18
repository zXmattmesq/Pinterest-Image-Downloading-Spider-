import requests

def load_user_agents(filepath):
    with open(filepath, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def save_valid_user_agents(filepath, valid_user_agents):
    with open(filepath, 'w') as file:
        for user_agent in valid_user_agents:
            file.write(user_agent + "\n")

def validate_user_agent(user_agent):
    test_url = "http://www.example.com"
    headers = {"User-Agent": user_agent}
    try:
        response = requests.get(test_url, headers=headers, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def main():
    user_agents = load_user_agents('users.txt')
    valid_user_agents = []

    for user_agent in user_agents:
        if validate_user_agent(user_agent):
            valid_user_agents.append(user_agent)

    save_valid_user_agents('valid_user_agents.txt', valid_user_agents)
    print(f"Validation complete. {len(valid_user_agents)} valid user agents saved to valid_user_agents.txt.")

if __name__ == "__main__":
    main()
