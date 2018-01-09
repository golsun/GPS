# GPS

Global Pathway Selection (GPS) is an algorithm that effectively generates reduced (skeletal) chemistry mechanisms, ​which speeds up your simulations. You can also use it as a systematic analytics tool to extract insights from complex reacting system.

To improve the accuracy of reduced mechanisms, GPS considers all-generation relation between species, and minimizes the risk of broken pathway or dead-end issue. 

This algorithm is developed by Prof. Wenting Sun's group at Georgia Tech (http://sun.gatech.edu/)

## How to use

To run GPS, one needs to store the following python packages
* networkx
* PyQt4 
* cantera

then GPS can be started by typing the following commands in terminal

cd [the path of GPS folder]
python GPS.py

for more detailed tutorial, please see [Tutorial_v1.0.0.pdf]

## How to cite
* X. Gao, S. Yang, W. Sun, A global pathway selection algorithm for the reduction of detailed chemical kinetic mechanisms, Combustion and Flame, 167 (2016) 238–247

## Related publication
* X. Gao, W. Sun, Using Global Pathway Selection Method to Understand Chemical Kinetics, 55th AIAA Aerospace Sciences Meeting, (2017) AIAA 2017-0836.
* X. Gao, W. Sun, Global Pathway Analysis of the Autoignition and Extinction of Aromatic/Alkane mixture,  53rd AIAA/SAE/ASEE Joint Propulsion Conference, Atlanta, Georgia, 2017.
* S. Yang, X. Gao, W. Sun, Global Pathway Analysis of the Extinction and Re-ignition of a Turbulent Non-Premixed Flame,  53rd AIAA/SAE/ASEE Joint Propulsion Conference, Atlanta, Georgia, 2017.