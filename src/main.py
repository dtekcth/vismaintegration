import toml
import requests
import time
import argparse
from termcolor import colored

import visma
import sheets 

config = toml.load("./config.toml")


def createInvoicesData(s, start, stop):
    drivers = sheets.parseDrivers()
    drives = sheets.parseKorjournal(start,stop)
    kunder = visma.getKunder(s)

    invoices_to_send = {'committee': [], 'member': [], 'outsider': [], 'dbus': []}

    for drive in drives:
        invoice_rows = visma.InvoiceRow(drive.distance, drive.rented_hours, drive.timestamp, drive.drove_as)
        invoiceIndex = sheets.invoiceStarted(drive, invoices_to_send) # if -1 then no invoice is started

        if invoiceIndex == -1: 
            invoices_to_send[drive.drove_as].append(sheets.startInvoice(drive, invoice_rows, drivers, kunder))
        else:
            invoices_to_send[drive.drove_as][invoiceIndex]['rows'].append(invoice_rows)
            invoices_to_send[drive.drove_as][invoiceIndex]['drives'].append(drive)
    return invoices_to_send

def checkInvoicesData(invoices_data):
    for k, v in invoices_data.items():
        if k == 'committee':
            continue
        for invoice in v:
            print(colored(f'Paying as {k}', 'blue'))
            print(colored('Drives', 'cyan'))
            for drive in invoice['drives']:
                print(drive)
            print()

            print(colored('Invoiced for', 'cyan'))
            for drive_rows in invoice['rows']:
                print(drive_rows)
            print()

            print(colored('Kund Info', 'cyan'))
            print(invoice['kundId'])

            print()
            print('Does this seem right? y/N')
            user_input = input('Does this seem right? y/N:')

            if user_input.lower() == 'n' or user_input == '':
                print("Exiting, fix the data befgain")
                return False 
    return True

def checkKundStatus(invoices_data):
    print("Checking customer status for each invoice")
    for k,invoices in invoices_data.items():
        if k == 'committee':
            continue 

        for invoice in invoices:
            if invoice['kundId'] == False:
                print(colored('Drives', 'cyan'))
                for drive in invoice['drives']:
                    print(drive)
                if invoice['driver'] == False:
                    print(colored("This person/organisation doesn't match any driver contact information", 'red'))
                    print(invoice['name'])
                else:
                    print(colored("This person/organisation haven't been registered in Visma", 'red'))
                    print(invoice['kundId'])

                user_input = input('Go to next problem? y/N: ')

                if user_input.lower() == 'n' or user_input == '':
                    print("Exiting, fix the data before trying again")
                    return False 

    user_input = input('Do you want to create invoices in Visma? (those invoices without a driver registered in visma will be discarded) y/N')

    if user_input.lower() == 'n' or user_input == '':
        print("Exiting, run again")
        return False 

    return True



def main(start, stop, committees):
    with requests.Session() as s:
        s.headers.update({'Authorization': 'Bearer {}'.format(config['visma']['token']) })

        s.post(config['visma']['api_url'] + '/companysettings', data={'BankgiroNumberPrint': '5207-8417'})

        invoices_data = createInvoicesData(s, start, stop) 

        if not(checkInvoicesData(invoices_data)):
            return False
        print(colored('All invoices checked!', 'green'))    
        if not(checkKundStatus(invoices_data)):
            return False
        print(colored('All Drivers checked!', 'green'))    


        if committees:
            for k,v in invoices_data.items():
                if k != 'committee':
                    continue 

                for invoice in v:
                    if invoice['kundId'] != False:
                        visma.createInvoice(s, invoice['kundId'], invoice['rows'])

                print("Invoices created")


        for k,v in invoices_data.items():
            if k == 'committee':
                continue 

            for invoice in v:
                if invoice['kundId'] != False:
                    visma.createInvoice(s, invoice['kundId'], invoice['rows'])

            print("Invoices created")
