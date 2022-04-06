# Python Analisys App

This repo holds the code for the TSB data analysis app.\
This Branch has the updated code.

# Description

Requirements.txt: necessary modules to run the app in Python\
App.py: Main code\
ReadData.py: used by App.py. Reads the data from files\
FakeBoat.py: Test the App's real time functionality. Run FakeBoat.py and then App.py\

Produce executable to the OS you're on. (NOT WORKING WITH PYTHON 3.10. Update to 3.10.1 or downgrade)\
1)Install pyinstaller (pip install pyinstaller) \
2)Do: pyinstaller --onefile --noconsole --icon=app.ico App.py\
Alternatively,\
1)Install cx_freeze\
2)Do python setup.py build\





