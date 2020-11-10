import requests
import random
from multiprocessing import Pool
import time


user_ids = [1, 2, 3, 4, 5, 6]
app_names = ['product_1', 'product_2', 'product_3']
event_actions = ['page_view', 'button_click', 'scroll', None]
event_categories = ['category_1', 'category_2', 'category_3']
event_values = [37, 8, 5, 12, 54, None]
sleep = [1, 2, 3]


def test(x):
    data = {
        'user_id': user_ids[random.randint(0, len(user_ids)-1)],
        'app_name': app_names[random.randint(0, len(app_names)-1)],
        'event_action': event_actions[random.randint(0, len(event_actions)-1)],
        'event_category': event_categories[random.randint(0, len(event_categories)-1)],
        'event_value': event_values[random.randint(0, len(event_values)-1)]
    }
    requests.post('http://127.0.0.1:8000/track', json=data, headers={"X-Token": "secret_token"})
    # uncomment next string if you want to simulate more real case
    #time.sleep(sleep[random.randint(0, len(sleep)-1)])


if __name__ == '__main__':
    with Pool(10) as p:
        p.map(test, range(10000))
