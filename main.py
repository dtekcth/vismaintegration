import toml
import json
import requests
import webbrowser
import csv
import time
from termcolor import colored
import os
from base64 import standard_b64encode

os.system('color')
config = toml.load("config.toml")

url_base = config['visma']['api_url']


def authenticate():
    __browser = webbrowser.get(config['other']['browser'])
    
    __browser.open(config['visma']['identity_url'] + '/connect/authorize?client_id={}&redirect_uri={}&scope={}&state={}&response_type=code&prompt=login'.format(config['visma']['client_ID'], config['visma']['redirect_uri'], config['visma']['scope'], 'pythonCLI'))
    print("enter \"code\" argument from url")
    code = input()

    credentials = (config['visma']['client_ID'], config['visma']['client_secret'])

    data = f'grant_type=authorization_code&code={code}&redirect_uri={config["visma"]["redirect_uri"]}'

    r = requests.post(config['visma']['identity_url'] + '/connect/token', data, auth=credentials).json()
    
    print(json.dumps(r))
    return r

def getOrCreateKund(s, pnr, email):
    kund = getKundByPnr(s, pnr)

    if kund == []:
        return createKund(s, pnr, email)
    else:
        return kund


def createKund(s, pnr, email, kund_info={}):
    def searchKund(s, pnr):
        payload = {'who': pnr, 'countryCode':'SE','usesCompanyCredits':'false','useOptiway':'false'}
        r = s.get(url_base + '/addresses', params=payload)
    
        return r.json()[0]

    if kund_info == {}:
        kund_info = searchKund(s, pnr)
    
    print(kund_info)
    payload = {
            'IsPrivatePerson': str(kund_info['type'] == 'privatperson'), 
            'CorporateIdentityNumber': pnr,
            'InvoiceCity': kund_info['city'],
            'InvoicePostalCode': kund_info['postalCode'],
            'InvoiceAddress1': kund_info['address'],
            'Name': kund_info['name'],
            'IsActive': 'true',
            'EmailAddress': email,
            'TermsOfPaymentId': "8f9a8f7b-5ea9-44c6-9725-9b8a1addb036"
            }

    r = s.post(url_base + '/customers', data=payload)
    return r.json() 

def getKunder(s):
    r = s.get(url_base + '/customers', params="")
    return r.json()['Data']

def getKundByPnr(s, pnr):
    params = {'filter': 'CorporateIdentityNumber eq ' + pnr }

    r = s.get(url_base + f'/customers?$filter=CorporateIdentityNumber eq \'{pnr}\'')
    
    if r.json()['Data'] == []:
        return False
    else:
        return r.json()['Data'][0]



def createInvoice(s, kundId, rows):
    data = {'CustomerId': kundId['Id'], 'RotReducedInvoicingType': '0', 'Rows': rows, 'EuThirdParty': True}
    
    r = s.post(url_base + "/customerinvoicedrafts", json=data)
    print(json.dumps(r.json()))

def createInvoiceRows(distance, hours, date, drove_as):
    day = time.strftime('%Y-%m-%d', date)

    if drove_as == 'member':
        rows = [
            {'ArticleId': config['price']['medlem_tid_id'], 'IsTextRow': "false", 'Text': f'Hour price for Booking as member, {day}', 'UnitPrice': config['price']['medlem_tid_price'], 'Quantity': hours, 'ReversedConstructionServicesVatFree': False},
            {'ArticleId': config['price']['medlem_distans_id'], 'IsTextRow': "false", 'Text': f'Kilometer price for Booking as member, {day}', 'UnitPrice': config['price']['medlem_distans_price'], 'Quantity': distance, 'ReversedConstructionServicesVatFree': False}
            ]
    elif drove_as == 'dbus':
        rows = [
            {'ArticleId': config['price']['dbus_tid_id'], 'IsTextRow': "false", 'Text': f'Hour price for Booking as DBus, {day}', 'UnitPrice': config['price']['dbus_tid_price'], 'Quantity': hours, 'ReversedConstructionServicesVatFree': False},
            {'ArticleId': config['price']['dbus_distans_id'], 'IsTextRow': "false", 'Text': f'Kilometer price for Booking as DBus, {day}', 'UnitPrice': config['price']['dbus_distans_price'], 'Quantity': distance, 'ReversedConstructionServicesVatFree': False}
            ]
    elif drove_as == 'outsider':
        rows = [
            {'ArticleId': config['price']['icke_medlem_tid_id'], 'IsTextRow': "false", 'Text': f'Hour price for Booking as outsider, {day}', 'UnitPrice': config['price']['icke_medlem_tid_price'], 'Quantity': hours, 'ReversedConstructionServicesVatFree': False},
            {'ArticleId': config['price']['icke_medlem_distans_id'], 'IsTextRow': "false", 'Text': f'Kilometer price for Booking as outsider, {day}', 'UnitPrice': config['price']['icke_medlem_distans_price'], 'Quantity': distance, 'ReversedConstructionServicesVatFree': False}
            ]
    elif drove_as == 'committee':
        rows = [
            {'ArticleId': config['price']['medlem_tid_id'], 'IsTextRow': "false", 'Text': f'Hour price for Booking as committee, {day}', 'UnitPrice': config['price']['medlem_tid_price'], 'Quantity': hours, 'ReversedConstructionServicesVatFree': False},
            {'ArticleId': config['price']['medlem_distans_id'], 'IsTextRow': "false", 'Text': f'Kilometer price for Booking as committee, {day}', 'UnitPrice': config['price']['medlem_distans_price'], 'Quantity': distance, 'ReversedConstructionServicesVatFree': False}
            ]

    return rows
        
    


def parseKorjournal(start,stop):
    valid_rows = []
    with open(config['sheets']['korjournal']) as file:
        rows = list(csv.DictReader(file))

         
        for i in range(len(rows)):
            row_time = time.strptime(rows[i]['Tidstämpel'], '%Y-%m-%d %H.%M.%S' ) 

            if start <= row_time and row_time <= stop:
                if rows[i]['Drove as...'] == 'Committé under the computer division':
                    drove_as = 'committee'
                elif rows[i]['Drove as...'] == 'Member of the computer division':
                    drove_as = 'member'
                elif rows[i]['Drove as...'] == 'DBus Patet':
                    drove_as = 'dbus'
                elif rows[i]['Drove as...'] == 'outsider':
                    drove_as = 'outsider'
                else:
                    drove_as = 'INVALID'
               
                # Will fail if i == 0
                distance = str(int(rows[i]['Meter indication']) - int(rows[i-1]['Meter indication']))


                new_row = {
                        'timestamp': row_time,
                        'email': rows[i]['E-postadress'],
                        'distance': distance,
                        'rented_hours': rows[i]['Number of rented hours'],
                        'name': rows[i]['Booker'],
                        'drove_as': drove_as 
                        }


                valid_rows.append(new_row)

    return sorted(valid_rows, key=lambda r: r['email'])

def parseDrivers():
    valid_rows = []
    with open(config['sheets']['drivers']) as file:
        rows = list(csv.DictReader(file))
         
        for row in rows:
            if row['Skrivit kontrakt? (använd \'x\')'] == 'x':
                new_row = {
                    'time': row['Tidstämpel'],
                    'email': row['E-postadress'],
                    'name': row['First name'] + ' ' + row['Last name'],
                    'pnr': row['National identification number(Personnummer)'],
                    'member': row['I am a member of the student division of computer science and engineering'],
                    'other_org': row['I belong to an organization outside of the student division of computer science and engineering'],
                    'org_name': row['Name'],
                    'org_number': row['Corporate Identity Number(Organisationsnummer)'],
                    'invoice_email': row['E-Mail for invoice']}
                valid_rows.append(new_row)

    return sorted(valid_rows, key=lambda r: r['email'])


def invoiceStarted(drive, invoices_data):
    for i,invoice in enumerate(invoices_data[drive['drove_as']]):
        if drive['drove_as'] == 'committee':
            if invoice['name'] == drive['name']:
                return i
        else:
            if invoice['name'] == drive['email']:
                return i
    return -1 


def startInvoice(drive, invoice_rows, drivers, kunder):

    if drive['drove_as'] == 'committee':
        invoice_name = drive['name']
        kundId = False
        matching_drivers = [] 
    else:
        invoice_name = drive['email']
        matching_drivers = list(filter(lambda d: d['email'] == drive['email'], drivers))

        if len(matching_drivers) == 1:
            if drive['drove_as'] == 'outsider' and drive['other_org'] == 'Yes':
                matching_kunder = list(filter(lambda k: k['CorporateIdentityNumber'] == matching_drivers[0]['org_number'], kunder))
            else:
                matching_kunder = list(filter(lambda k: k['CorporateIdentityNumber'] == matching_drivers[0]['pnr'], kunder))

            if len(matching_kunder) == 1:
                kundId = matching_kunder[0]
            else:
                kundId = False
        else:
            kundId = False

    return {
        'name': invoice_name,
        'drives': [drive],
        'kundId': kundId,
        'driver': matching_drivers[0] if len(matching_drivers) == 1 else False,
        'rows': invoice_rows
        }
def createInvoicesData(s, start, stop):
    drivers = parseDrivers()
    kunder = getKunder(s)
    invoices_to_send = {'committee': [], 'member': [], 'outsider': [], 'dbus': []}

    for drive in parseKorjournal(start,stop):
        invoice_rows = createInvoiceRows(drive['distance'], drive['rented_hours'], drive['timestamp'], drive['drove_as'])
        invoiceIndex = invoiceStarted(drive, invoices_to_send)
        if invoiceIndex == -1:
            invoices_to_send[drive['drove_as']].append(startInvoice(drive, invoice_rows, drivers, kunder))
        else:
            invoices_to_send[drive['drove_as']][invoiceIndex]['rows'] += invoice_rows
            invoices_to_send[drive['drove_as']][invoiceIndex]['drives'].append(drive)
    return invoices_to_send

def checkInvoicesData(invoices_data):
    for k, v in invoices_data.items():
        for invoice in v:
            print(colored(f'Paying as {k}', 'blue'))
            print(colored('Drives', 'cyan'))
            for drive in invoice['drives']:
                print(
                    'Date: ' + time.strftime('%Y-%m-%d', drive['timestamp']), 
                    '| Email: ' + drive['email'], 
                    '| Dist: ' + drive['distance'].rjust(3, ' ') + 'km', 
                    '| Time: ' + drive['rented_hours'].rjust(2,' ') + 'h',
                    '| Booker: ' + drive['name'],
                )
            print()
            print(colored('Invoiced for', 'cyan'))
            for row in invoice['rows']:
                print(
                    row['UnitPrice'] + ' kr/item |',
                    row['Quantity'].rjust(3,' ') + ' items |',
                    row['Text']
                )
            print()
            print(colored('Kund Info', 'cyan'))
            if type(invoice['kundId']) == dict:
                print('Name: ' + invoice['kundId']['Name'] + ' | Personnummer', invoice['kundId']['CorporateIdentityNumber'])
                print('Adress: ', invoice['kundId']['InvoiceAddress1'], ',', invoice['kundId']['InvoicePostalCode'], invoice['kundId']['InvoiceCity'])
            else:
                print(invoice['kundId'])
            print()
            print('Does this seem right? y/N')
            user_input = input()

            if user_input.lower() == 'n' or user_input == '':
                print("Exiting, fix the data before trying again")
                return False 
    return True
        
def checkKundStatus(invoices_data):
    print("Checking customer status for each invoice")
    for k,invoices in invoices_data.items():
        if k == 'committee':
           continue 
        
        for invoice in invoices:
            if invoice['kundId'] == False:
                if invoice['driver'] == False:
                    print(colored("This person/organisation doesn't match any driver contact information", 'red'))
                    
                else:
                    print(colored("This person/organisation haven't been registered in Visma", 'red'))

                    print('Name: ', invoice['driver']['name'],
                        '| Email: ', invoice['driver']['email'],
                        '| Personnummer: ', invoice['driver']['pnr'],
                        '| Other org.: ', invoice['driver']['other_org'],
                        '| Org. number: ', invoice['driver']['org_number'])

                print('Go to next problem? y/N')
                user_input = input()

                if user_input.lower() == 'n' or user_input == '':
                    print("Exiting, fix the data before trying again")
                    return False 

    print('Do you want to create invoices in Visma? (those invoices without a driver registered in visma will be discarded) y/N')
    user_input = input()

    if user_input.lower() == 'n' or user_input == '':
        print("Exiting, run again")
        return False 

    return True


def main():
    if config['visma']['token'] != "":
        token_info = {'access_token': config['visma']['token']}
    else:
        token_info = authenticate()

    with requests.Session() as s:
        
        s.headers.update({'Authorization': 'Bearer {}'.format(token_info['access_token']) })
        (start,stop) = time.strptime('2021-09-28', '%Y-%m-%d'),time.strptime('2021-11-01', '%Y-%m-%d')
        
        invoices_data = createInvoicesData(s, start, stop) 

        if not(checkInvoicesData(invoices_data)):
            return False
        print(colored('All invoices checked!', 'green'))    
        if not(checkKundStatus(invoices_data)):
            return False
        print(colored('All Drivers checked!', 'green'))    


        for k,v in invoices_data.items():
            if k == 'committee':
               continue 
            
            for invoice in v:
                if invoice['kundId'] != False:
                    print("Creating invoice")
                    createInvoice(s, invoice['kundId'], invoice['rows'])

                    




                #rows = createInvoiceRows('34', '4', '2021-10-12')
        #createInvoice(s, "aed5ff22-ad01-4549-8850-1f0d7e4f046a", rows)

#parseDrivers()
#parseKorjournal(time.strptime('2021-09-01', '%Y-%m-%d'),time.strptime('2021-11-01', '%Y-%m-%d'))

main()
