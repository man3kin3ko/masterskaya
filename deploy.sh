python -m venv venv
source ./venv/bin/activate
python -m pip install -r ./backend/requirements.txt
cd frontend/ && npm install && npm run build
cd .. && ln -s `pwd`/frontend/dist `pwd`/backend/app/ || exit 0
