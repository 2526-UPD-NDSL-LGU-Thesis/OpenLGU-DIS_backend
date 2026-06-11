# Installing Prerequisites
Make sure you have python installed in your system. Use a stable version of python with wheels, such as Python 3.12. (Use the appropriate keyword for python installed in your system, such as `python` or `python3`).
```bash
python --version
```
Make sure you have pip installed.
```bash
pip --version
```
Get the latest version of the project.
```bash
gh repo clone 2526-UPD-NDSL-LGU-Thesis/customizeable-lgu-id
git pull
```
Go to the project root and download the prerequisites in your virtual environment.
```bash
cd customizeable-lgu-id
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
Install these system libraries:
```bash
sudo apt update
sudo apt install zlib1g-dev libzbar0 libgl1 libgles2-mesa-dev
```
Initialize the django project.
```bash
python manage.py makemigrations
python manage.py migrate
```
Create a Django superuser. This will open the interactive terminal for user creation.
```bash
python manage.py createsuperuser
```
After creating the superuser, run the Django server.
```bash
python manage.py runserver <PORT>
```