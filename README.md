# cg-add-global-prefix
This script updates CloudGenix Enteprise Global Prefixes based on an input CSVFile
```
usage: cg-add-global-prefix.py [-h] [--token "MYTOKEN"]
                               [--authtokenfile "MYTOKENFILE.TXT"] --csvfile
                               csvfile
```
CloudGenix script
---------------------------------------
```
optional arguments:
  -h, --help            show this help message and exit
  --token "MYTOKEN", -t "MYTOKEN"
                        specify an authtoken to use for CloudGenix
                        authentication
  --authtokenfile "MYTOKENFILE.TXT", -f "MYTOKENFILE.TXT"
                        a file containing the authtoken
  --csvfile csvfile, -c csvfile
                        the CSV Filename to read that contains IP Subnets to
                        add as Global Prefixes
```
# Notes:
```
The push from this script is an atomic push which replaces all previous entries. 
Take care that the new update does not remove existing entries which are 
critical for the operation of the SDWAN solution.

RFC1918 Validation - Because of the nature of the push, this script will 
validate that the CSV file includes the 3 standard RFC1918 addesses. If it does
not, it will confirm and ask before pushing.
```
