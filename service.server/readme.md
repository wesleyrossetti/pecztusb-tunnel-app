pip install -r requirements.txt
pyinstaller --noconsole --name server --hidden-import "waitress" server.py