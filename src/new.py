import requests
link = input("username: ")
payload = {"accept": "application/json"}
result = requests.get(
    "https://api.lamadava.com/v1/user/stories/by/username?username={}&access_key=alUN2F6VcVKLm3NV6eCUUzYAsBne6AOs".format(link))
result = result.json()
print(result)
for key, value in result.items()[0]:
    print(key, value)

