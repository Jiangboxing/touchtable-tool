# DEMKit

## REQUIREMENTS

The following software is required / tested:
* Python >= 3.4 (3.4.1 and 3.6.5 work)
* InfluxDB >= 0.9
* Grafana >= 3.0

The following python modules are required and can be installed using pip (or possibly pip3 for python 3), please refer to a python pip guide for your system)
* requests
* numpy
* pytz
* astral

For networking, you will also need:
* zmq
* eve

For the smartHouse, you will also need:
* pyserial (NOTE: serial is WRONG)
* and the networking requirements


## SETUP
For the first run, some software needs to be set up and installed. I cannot maintain this documentation for all platforms, so please get yourself familiar with the tools by reading guides, following tutorials and google around.

### GIT
Obviously, you will need Git to grab the last version of DEMKit using git clone(and later on, to update, git pull). If you are not familiar with git, please read some tutorials to get yourself familiar with git clone, pull, commit and push commands. 

The clone url is ssh://vcs@vcs.utwente.nl/source/DEMKit.git . Depending on the research goals, it may be wise to checkout the "develop".

Furthermore, it is recommended to create a separate "workspace"-directory. Here you can checkout the example model:
ssh://vcs@vcs.utwente.nl/source/DEMkit_example.git

You may need to provide an SSH key to the Phabricator website. Please google how this is done for your platform (or check below if using Windows).

All code is hosted within the version control system of the University of Twente: https://vcs.utwente.nl
More specifically, these pages are of interest
- Project: https://vcs.utwente.nl/project/view/87/
- DEMKit: https://vcs.utwente.nl/source/DEMKit/
- Example Model: https://vcs.utwente.nl/source/DEMkit_example/



### InfluxDB
Go to https://www.influxdata.com/downloads/ and download the zip file or package for the OS you are running. However, your package manager may also have the package available.

Databases can be changed using the influx CLI (read the InfluxDB documentation). Within models, you can call the clearDatabase() function of the host within the model. This will also create the database when it does not exist yet. See the example model.

### Grafana
Grafana is used to display the data from the InfluxDB. The default start date of simulations is January 1 2016. Executables/packages exist for all major platforms (Windows, Mac OS X, Linux). The tool is quite powerful in managing data and you can create custom dashboards to display the (current) relevant data. Note that it is best to set the interval lenght for a graph in Grafana to the same value as used in the simulation. Otherwise, data may not be as expected, or even nothing appears.

Grafana can be accessed using a web browser at http://localhost:3000

For the first time you will need to add a connection to the Database. You should connect using the InfluxDB >= 0.9 API. Usernames and passwords can be omitted, but make sure that you connect to the database defined in the model, which by default is "dem". 

## Running
Before you can run simulations, you will need to set up your environment by adding your own models folder inin the 'conf' folder. Please open the example and set it up according to your system. Then save it as 'usrconf.py'. Furthermore, under Linux/MacOS it is wise to make the demkit.py file executable (i.e. 'chmod +x demkit.py').

A model is run by executing demkit.py with 2 arguments:
demkit.py -f <model folder> -m <model name>

Run the program without arguments to see the help file. More options exists, such as passing an number to the model or selecting a different database.

There are a couple of examples that you can use to test the setup and also serve as a living example that can be used as a template to setup your own models. You can find these in the models/example folder. Assuming that the configuration has example as model folder:
- One house with all equipment and different types of controllers. Run this model using python3 demkit.py -m demohouse
- Multiple (configurable) houses in a street, based on the previous model. Run using python3 demkit.py -m demostreet
- The same as above, but now with a physical network model from Lochem. Run using python3 demkit.py -m modelloadflow

Be sure to check the other folders as well. The smarthouse folder contains the config for the demonstration house, which also includes interfacing with OpenHAB and the custom hardware. The config folder of gerwin contains more sophisticated models with different three-phase control settings, but also distributed control across multiple nodes.

## Making your own model
Please add a folder with your own name and put your models in there. You can copy the contents from example to make life easier.

## Windows pointers
Some things I (Gijs) ran into while installing the software under Windows:
- If Windows complains that it doesn't know a certain command like python or git in the command line you need to add it to your path variable. To do this go to Start Menu, right click Computer, select Properties, select Advanced system settings, select Environment Variables, under System variables find path and add the location of the 'missing' program to the list (delimited by ;).
- To add packages to python you can use pip (comes preinstalled with Python), just run: python -m pip install -U pip, after that you can install packages using: pip install <package name>. 
- To get an SSH key see: http://guides.beanstalkapp.com/version-control/git-on-windows.html#installing-ssh-keys after generating the key add it to your profile on the GitLab website.
Installing most of the software is very straightforward, however if you get stuck come to me and I will try and help.

## Installation on Ubuntu 16.04
Installation under Ubuntu 16.04 is straightforward (for questions about the instructions below, ask Marco).
- Install InfluxDB and Grafana using the package manager (packages: influxdb, influxdb-client, grafana)
- Follow the general instructions above.  When something does not work or is unclear, follow the instructions below.
- Grafana requires a username/password for login.  Use: admin/admin
- Add a new data source.  Use the following settings:
  Default: check; URL: http://localhost:8083; Access: proxy; Database: dem; User: admin; Password: admin
  Note that the user and password are just there to annoy you.  Saving is not possible without entering them.  They are ignored by Grafana.

## Installation on macOS 10.13
Installation under macOS has its quirks, the following steps may help:
- Install the Command Line Tools for Xcode (required for python) by typing 'xcode-select --install' in a Terminal window. 
- Install Homebrew from https://brew.sh. Homebrew is a package manager for Mac OS X, just as you might have for a Linux system.
- Install python3 using Homebrew, type 'brew install python3' in a Terminal window.
- Install InfluxDB and Grafana with 'brew install influxdb' and 'brew install grafana'
- Install the required python modules (see Requirements) using pip, for example 'pip3 install numpy' to install numpy. Pip is a package manager for python modules, automatically installed if you install python with Homebrew.

Make sure InfluxDB and Grafana are running by searching for 'grafana-server' and 'influxdb' in Activity Monitor. If not, follow the steps below:
- Make sure Homebrew services is running by typing 'brew tap homebrew/services' in a Terminal window.
- Type 'brew services start grafana' and 'brew services start influxdb' in a Terminal window to start Grafana and InfluxDB.

## Remarks
Feel free to add tips/tricks to this documentation!


