import argparse
import visma
import time
from main import main

parser = argparse.ArgumentParser(description='Creates invoices in Visma according to data from the DBus booking system')

parser.add_argument('start', metavar='start', type=str, help="The first date to accumulate drives from")
parser.add_argument('stop', metavar='stop', type=str, help="The last date to accumulate drives from")

parser.add_argument('--committee', action='store_true', help='Output the data for only committees during the period (ignored in normal run)')
parser.add_argument('--authenticate', action='store_true', help='Authenticates the user and updates the token in config.toml')

args = parser.parse_args()

if args.authenticate:
    visma.authenticate()
print(time.strptime(args.start, '%Y-%m-%d'))
print(time.strptime(args.stop, '%Y-%m-%d'))
main(time.strptime(args.start, '%Y-%m-%d'), time.strptime(args.stop, '%Y-%m-%d'), args.committee)


