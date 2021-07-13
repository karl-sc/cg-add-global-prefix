#!/usr/bin/env python
PROGRAM_NAME = "cg-add-global-prefix.py"
PROGRAM_DESCRIPTION = """
CloudGenix script description
---------------------------------------
This script updates CloudGenix Enteprise Global Prefixes based on an input CSVFile
usage: cg-add-global-prefix.py [-h] [--token "MYTOKEN"]
                               [--authtokenfile "MYTOKENFILE.TXT"] --csvfile
                               csvfile

CloudGenix script
---------------------------------------

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

Notes:

The push from this script is an atomic push which replaces all previous entries. 
Take care that the new update does not remove existing entries which are 
critical for the operation of the SDWAN solution.

RFC1918 Validation - Because of the nature of the push, this script will 
validate that the CSV file includes the 3 standard RFC1918 addesses. If it does
not, it will confirm and ask before pushing.

"""

####Library Imports
from cloudgenix import API, jd
import os
import sys
import argparse
import ipaddress
from csv import reader

def parse_arguments():
    CLIARGS = {}
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=PROGRAM_DESCRIPTION
            )
    parser.add_argument('--token', '-t', metavar='"MYTOKEN"', type=str, 
                    help='specify an authtoken to use for CloudGenix authentication')
    parser.add_argument('--authtokenfile', '-f', metavar='"MYTOKENFILE.TXT"', type=str, 
                    help='a file containing the authtoken')
    parser.add_argument('--csvfile', '-c', metavar='csvfile', type=str, 
                    help='the CSV Filename to read that contains IP Subnets to add as Global Prefixes', required=True)
    args = parser.parse_args()
    CLIARGS.update(vars(args))
    return CLIARGS

def validate_ip_subnet(subnet_str):
    try:
        ip_prefix = ipaddress.ip_network(subnet_str,strict=False)
        if str(ip_prefix) != str(subnet_str):
            print("Warning, input subnet",subnet_str,"does not match network address",ip_prefix)
        return ip_prefix
    except:
        return False

def authenticate(CLIARGS):
    print("AUTHENTICATING...")
    user_email = None
    user_password = None
    
    sdk = API()    
    ##First attempt to use an AuthTOKEN if defined
    if CLIARGS['token']:                    #Check if AuthToken is in the CLI ARG
        CLOUDGENIX_AUTH_TOKEN = CLIARGS['token']
        print("    ","Authenticating using Auth-Token in from CLI ARGS")
    elif CLIARGS['authtokenfile']:          #Next: Check if an AuthToken file is used
        tokenfile = open(CLIARGS['authtokenfile'])
        CLOUDGENIX_AUTH_TOKEN = tokenfile.read().strip()
        print("    ","Authenticating using Auth-token from file",CLIARGS['authtokenfile'])
    elif "X_AUTH_TOKEN" in os.environ:              #Next: Check if an AuthToken is defined in the OS as X_AUTH_TOKEN
        CLOUDGENIX_AUTH_TOKEN = os.environ.get('X_AUTH_TOKEN')
        print("    ","Authenticating using environment variable X_AUTH_TOKEN")
    elif "AUTH_TOKEN" in os.environ:                #Next: Check if an AuthToken is defined in the OS as AUTH_TOKEN
        CLOUDGENIX_AUTH_TOKEN = os.environ.get('AUTH_TOKEN')
        print("    ","Authenticating using environment variable AUTH_TOKEN")
    else:                                           #Next: If we are not using an AUTH TOKEN, set it to NULL        
        CLOUDGENIX_AUTH_TOKEN = None
        print("    ","Authenticating using interactive login")
    ##ATTEMPT AUTHENTICATION
    if CLOUDGENIX_AUTH_TOKEN:
        sdk.interactive.use_token(CLOUDGENIX_AUTH_TOKEN)
        if sdk.tenant_id is None:
            print("    ","ERROR: AUTH_TOKEN login failure, please check token.")
            sys.exit()
    else:
        while sdk.tenant_id is None:
            sdk.interactive.login(user_email, user_password)
            # clear after one failed login, force relogin.
            if not sdk.tenant_id:
                user_email = None
                user_password = None            
    print("    ","SUCCESS: Authentication Complete")
    return sdk

def logout(sdk):
    print("Logging out")
    sdk.get.logout()


##########MAIN FUNCTION#############
def go(sdk, CLIARGS):
    ####CODE GOES BELOW HERE#########
    resp = sdk.get.tenants()
    if resp.cgx_status:
        tenant_name = resp.cgx_content.get("name", None)
        print("======== TENANT NAME",tenant_name,"========")
    else:
        logout()
        print("ERROR: API Call failure when enumerating TENANT Name! Exiting!")
        print(resp.cgx_status)
        sys.exit((vars(resp)))
    
    csvfilename = CLIARGS['csvfile']
    
# open file in read mode
    
    with open(csvfilename, 'r') as read_obj:
        csv_reader = reader(read_obj)
        print("Opened File",csvfilename,"successfully")
        prefix_list = []
        counter = 0
        for row in csv_reader:
            counter += 1 
            input_prefix = str(row).strip().replace(",","").replace(" ","").replace("[","").replace("]","").replace("'","").replace("\"","")
            prefix = validate_ip_subnet(input_prefix)
            if prefix:
                print("ROW",counter,":",str(row),"Added SUCCESSFULLY")
                prefix_list.append(str(prefix))
            else:
                print("ROW",counter,":",str(row),"FAILURE TO ADD")
                print("Error parsing prefix '" + str(input_prefix) + "'", "Ignoring...")
                print("")
    if "10.0.0.0/8" not in prefix_list:
        user_input = ""
        input_options = ['a', 'i', 'q', 'abort', 'ignore', 'quit']
        while str(user_input).lower() not in input_options:
            user_input = str(input("Warning, 10.0.0.0/8 is missing from Global Prefixes. This may break RFC1918 traffic. Would you like to ADD this to the prefix list, IGNORE, or QUIT (A/I/Q)? ")).lower()
        if user_input[0] == 'q':
            print("Quitting program...")
            logout(sdk)
            sys.exit()
        if user_input[0] == 'a':
            print("Adding Prefix 10.0.0.0/8")
            prefix_list.append("10.0.0.0/8")

    if "172.16.0.0/12" not in prefix_list:
        user_input = ""
        input_options = ['a', 'i', 'q', 'abort', 'ignore', 'quit']
        while str(user_input).lower() not in input_options:
            user_input = str(input("Warning, 172.16.0.0/12 is missing from Global Prefixes. This may break RFC1918 traffic. Would you like to ADD this to the prefix list, IGNORE, or QUIT (A/I/Q)? ")).lower()
        if user_input[0] == 'q':
            print("Quitting program...")
            logout(sdk)
            sys.exit()
        if user_input[0] == 'a':
            print("Adding Prefix 172.16.0.0/12")
            prefix_list.append("172.16.0.0/12")

    if "192.168.0.0/16" not in prefix_list:
        user_input = ""
        input_options = ['a', 'i', 'q', 'abort', 'ignore', 'quit']
        while str(user_input).lower() not in input_options:
            user_input = str(input("Warning, 192.168.0.0/16 is missing from Global Prefixes. This may break RFC1918 traffic. Would you like to ADD this to the prefix list, IGNORE, or QUIT (A/I/Q)? ")).lower()
        if user_input[0] == 'q':
            print("Quitting program...")
            logout(sdk)
            sys.exit()
        if user_input[0] == 'a':
            print("Adding Prefix 192.168.0.0/16")
            prefix_list.append("192.168.0.0/16")
            
    put_data = {"ipv4_enterprise_prefixes": prefix_list}
    
    print("The Following Prefixes will be addded:")
    jd(put_data)
    
    user_input = ""  
    input_options = ['y', 'n', "yes", "no"]
    while str(user_input).lower() not in input_options:
        user_input = str(input("Proceed (Y/N)? ")).lower()
    if user_input[0] == "y":
        result = sdk.put.enterpriseprefixset(put_data)
        if result.cgx_status:
            print("")
            print("Enterprise Prefixes Added Successfully")
        else:
            print("ERROR adding prefixes")
    else:
        print("Aborting")
        return False

if __name__ == "__main__":
    ###Get the CLI Arguments
    CLIARGS = parse_arguments()
    
    ###Authenticate
    SDK = authenticate(CLIARGS)
    
    ###Run Code
    go(SDK, CLIARGS)

    ###Exit Program
    logout(SDK)
