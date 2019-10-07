#!/usr/bin/env python3

import requests
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import argparse
import configparser


def parse_args():

    config = configparser.ConfigParser()
    config.read('config.ini')
    defaults = config['default']
    defaults = dict(defaults)

    to_email = config['to_email']
    defaults['to_email'] = [ v for v in to_email.values() ]

    parser = argparse.ArgumentParser(description='Check fantasticosur disponibility')
    valid_date = lambda d: datetime.strptime(d, '%Y-%m-%d')
    parser.add_argument('--to-email', type=str,
                        help='recipient email address')
    parser.add_argument('--from-email', type=str,
                        help='from email address')
    parser.add_argument('--mailgun-url', type=str,
                        help='mailgun url')
    parser.add_argument('--mailgun-api', type=str,
                        help='mailgun api')
    parser.add_argument('--check-in', type=valid_date,
                        help='Check-in date in format YYYY-MM-DD',
                        default=defaults['check_in'])
    parser.add_argument('--check-out', type=valid_date,
                        help='Check-out date in format YYYY-MM-DD',
                        default=defaults['check_out'])
    args = vars(parser.parse_args())

    defaults.update({k: v for k, v in args.items() if v is not None})

    return defaults


def make_msg(args, disponibility):
    subject = "Fantasticosur: disponibility available"
    n_nights = int((args['check_out'] - args['check_in']).total_seconds() / (24*60*60))
    body ='''
    Brace yourself,

    The fantasticosur hotel has availability for the requested dates:

    check-in: {check_in}, check-out: {check_out} ({nights} nights)

    disponibility: {dispo}

    Cheers,
    The magic script
    '''.format(check_in=args['check_in'].strftime('%d/%m/%Y'),
               check_out=args['check_out'].strftime('%d/%m/%Y'),
               nights=n_nights,
               dispo=disponibility)
    return subject, body

def send_mail(args, subject, body):
    return requests.post(
        args['mailgun_url'],
        auth=("api", args['mailgun_api']),
        data={"from": args['from_email'],
              "to": args['to_email'],
              "subject": subject,
              "text": body
        })

def check_availability(args):
    query_url = 'http://int.fantasticosur.com/en/online/lugares/{type}/disponibilidad?fecha_in={date_in}&fecha_out={date_out}'

    types = [9, 29, 30]
    check_in = args['check_in'].strftime('%Y-%m-%d')
    check_out = args['check_out'].strftime('%Y-%m-%d')
    print('Query for dates: {} - {}'.format(check_in, check_out))

    query_data = {
        'type': None,
        'date_in': check_in,
        'date_out': check_out
    }

    disponibility = 0

    for t in types:
        query_data['type'] = str(t)
        resp = requests.get(query_url.format(**query_data))
        disponibility += resp.json()['disponibilidad']

    if disponibility > 0:
        print('{} availabilities were found'.format(disponibility))
    else:
        print('no availability were found')

    return disponibility

def main():
    args = parse_args()
    disponibility = check_availability(args)
    if disponibility > 0:
        subject, body = make_msg(args, disponibility)
        send_mail(args, subject, body)

main()
