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

   echo "Installing Python 3 packages"
   sudo apt-get install python3-pip
   sudo pip3 install beautifulsoup4
   sudo pip3 install bitarray
   sudo pip3 install ipaddress
   sudo pip3 install pyyaml


elif [ -f /etc/redhat-release ]; then
    echo "Installing dependencies for RPM based system"

    echo "Installing yaml_cpp"
    sudo yum install libyaml.x86_64

    echo "Installing Python packages"
    sudo yum -y install python-devel
    sudo pip install beautifulsoup4
    sudo pip install bitarray
    sudo pip install ipaddress
    sudo pip install pyyaml

    echo "Installing Python 3 packages"
    sudo apt-get install python3-pip
    sudo pip3 install beautifulsoup4
    sudo pip3 install bitarray
    sudo pip3 install ipaddress
    sudo pip3 install pyyaml
    
    

else
    echo "This is something else than debian or RedHat"
fi
