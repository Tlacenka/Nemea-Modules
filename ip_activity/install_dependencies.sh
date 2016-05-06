if [ -f /etc/debian_version ]; then
   echo "Installing dependencies for debian based system"

   echo "Installing yaml_cpp"
   sudo apt-get install libyaml-cpp-dev

   echo "Installing Python packages"
   sudo apt-get install python-dev
   sudo apt-get install python-pip 
   sudo pip install beautifulsoup4
   sudo pip install bitarray
   sudo pip install ipaddress
   sudo pip install pyyaml
   sudo pip install Pillow

   echo "Installing Python 3 packages"
   sudo apt-get install python3-pip
   sudo pip3 install beautifulsoup4
   sudo pip3 install bitarray
   sudo pip3 install ipaddress
   sudo pip3 install pyyaml
   sudo pip3 install Pillow


elif [ -f /etc/redhat-release ]; then
    echo "Installing dependencies for RPM based system"

    echo "Installing yaml_cpp"
    sudo yum install libyaml-cpp-devel

    echo "Installing Python packages"
    sudo yum install python-setuptools
    sudo easy_install pip
    sudo pip install beautifulsoup4
    sudo pip install bitarray
    sudo pip install ipaddress
    sudo pip install pyyaml
   sudo pip install Pillow

    echo "Installing Python 3 packages"
    sudo yum install python34-setuptools
    sudo easy_install pip
    sudo pip3 install beautifulsoup4
    sudo pip3 install bitarray
    sudo pip3 install ipaddress
    sudo pip3 install pyyaml
    sudo pip3 install Pillow
    
    

else
    echo "This is something else than debian or RedHat"
fi
