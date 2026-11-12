import threading
import time
from server import app
from crawler import start_crawling
from db_setup import initialize_database

def start_flask_server():
  print('Serverul Flask pornește pe http://localhost:5000')
  app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)


def start_crawler_thread():
  start_crawling()


if __name__ == '__main__':
  print('==============================================')
  print('SE PORNESTE NEBUNIA')
  print('==============================================')


  flask_thread = threading.Thread(target=start_flask_server, daemon=True)


  crawler_thread = threading.Thread(target=start_crawler_thread, daemon=True)

  try:
    initialize_database()
    flask_thread.start()
    crawler_thread.start()


    while True:
      time.sleep(1)

  except KeyboardInterrupt:
    print('\n\n SE OPRESTE TOT!')