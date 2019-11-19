import psycopg2
from dbconnect import connection
from flask import *
import datetime
import csv

def stock_data():
    c, conn = connection()
    d = c.execute("Select * from nse_stocks order by (company)")
    data = c.fetchall()
    return data

def company_data(companyid):
    c, conn = connection()
    c.execute(("Select * from nse_stocks where company_id = {0}").format("'" + companyid + "'"))
    data = c.fetchall()
    return data

def company_timeSeries(companyid):
    c, conn = connection()
    c.execute(("Select * from timeseries_stocks where company_id = {0}").format("'" + companyid + "'"))
    data = c.fetchall()
    return data

def sectors():
    c, conn = connection()
    c.execute("select distinct(sector) from nse_stocks")
    sectors = c.fetchall()
    return sectors

def filter_data(sectorFilter, costFilter):
    c, conn = connection()
    if len(sectorFilter) > 0 and costFilter > 0:
        c.execute(("((Select * from nse_stocks where sector = '{0}') intersect (Select * from nse_stocks where close > {1})) order by(company)").format(sectorFilter, costFilter))
        data = c.fetchall()
        return data
    if len(sectorFilter) > 0 and costFilter == 0:
        c.execute(("Select * from nse_stocks where sector = '{0}'").format(sectorFilter))
        data = c.fetchall()
        return data
    if len(sectorFilter) == 0 and costFilter > 0:
        c.execute(("Select * from nse_stocks where close > {0}").format(costFilter))
        data = c.fetchall()
        return data

def time_format(timeSeries):
    timeList = list()
    for time in timeSeries:
        d = time[2].strftime('%Y/%m/%d')
        timeList.append(d)
    return timeList

def price_format(timeSeries):
    priceList = list()
    for price in timeSeries:
        priceList.append(price[1])
    return priceList

def mutualFunds_data():
    c, conn = connection()
    d = c.execute("Select * from mutual_funds order by (fund_name)")
    data = c.fetchall()
    return data

def mutualFundFilter(price):
    c, conn = connection()
    c.execute(("Select * from mutual_funds where price > {0} order by(fund_name)").format(price))
    data = c.fetchall()
    return data

def fund_data(fundcode):
    c, conn = connection()
    c.execute(("Select * from mutual_funds where fund_code = {0}").format("'" + fundcode + "'"))
    data = c.fetchall()
    return data

def fund_timeSeries(fundcode):
    c, conn = connection()
    c.execute(("Select * from timeseries_mutual_fund where fund_code = {0}").format("'" + fundcode + "'"))
    data = c.fetchall()
    return data

def forex_table_generator():
    forex = {}
    with open('currcodes.csv') as csvfile:
        readCSV = csv.reader(csvfile,delimiter = ',')
        codes = []
        countries = []
        for row in readCSV:
            code = row[0]
            country = row[1]
            codes.append(code)
            countries.append(country)
    forex = dict(zip(codes, countries))
    forex.pop('Code')
    return forex
