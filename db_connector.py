import psycopg2

import settings


class DbCon(object):

    def __init__(self):
        self.con = psycopg2.connect(host=settings.DATABASE['HOST'], database=settings.DATABASE['NAME'],
                                    user=settings.DATABASE['USERNAME'],
                                    password=settings.DATABASE['PASSWORD'])

    def create_transactions_table(self):
        cur = self.con.cursor()
        cur.execute('DROP TABLE IF EXISTS transactions')
        self.con.commit()
        cur.execute('CREATE TABLE transactions ('
                    'id SERIAL PRIMARY KEY NOT NULL,'
                    'symbol VARCHAR(60) NOT NULL,'
                    'instrument INTEGER NOT NULL,'
                    'instrument_type VARCHAR(60) NOT NULL,'
                    'tick_size DOUBLE PRECISION,'
                    'name VARCHAR(200) NOT NULL,'
                    'exchange VARCHAR(60) NOT NULL'
                    ')')
        self.con.commit()

    def create_orders_table(self):
        cur = self.con.cursor()
        cur.execute('DROP TABLE IF EXISTS orders')
        self.con.commit()
        cur.execute('CREATE TABLE orders ('
                    'id SERIAL PRIMARY KEY NOT NULL,'
                    'symbol VARCHAR(60) NOT NULL,'
                    'instrument INTEGER NOT NULL,'
                    'order_id INTEGER NOT NULL,'
                    'order_type VARCHAR(50) NOT NULL,'
                    'price DOUBLE PRECISION NOT NULL,'
                    'quantity INTEGER NOT NULL,'
                    'trigger_price DOUBLE PRECISION NOT NULL,'
                    'created_at TIMESTAMP NOT NULL DEFAULT NOW(),'
                    'order_status VARCHAR(50) NOT NULL,'
                    'stop_loss DOUBLE PRECISION NOT NULL'
                    ')')
        self.con.commit()

    def create_tokens_table(self):
        cur = self.con.cursor()
        cur.execute('DROP TABLE IF EXISTS tokens')
        self.con.commit()
        cur.execute('CREATE TABLE tokens ('
                    'id SERIAL PRIMARY KEY NOT NULL,'
                    'access_token VARCHAR(500) NOT NULL'
                    ')')
        self.con.commit()

    def create_margins_table(self):
        cur = self.con.cursor()
        cur.execute('DROP TABLE IF EXISTS margins')
        self.con.commit()
        cur.execute('CREATE TABLE margins ('
                    'id SERIAL PRIMARY KEY NOT NULL,'
                    'margin DOUBLE PRECISION NOT NULL,'
                    'co_lower DOUBLE PRECISION NOT NULL,'
                    'co_upper DOUBLE PRECISION NOT NULL,'
                    'mis_multiplier DOUBLE PRECISION NOT NULL,'
                    'nrml_margin DOUBLE PRECISION NOT NULL,'
                    'mis_margin DOUBLE PRECISION NOT NULL,'
                    'tradingsymbol VARCHAR(100) NOT NULL,'
                    'segment VARCHAR(100) NOT NULL'
                    ')')
        self.con.commit()

    def insert_order(self, symbol, instrument, order_id, order_type, price, quantity, trigger_price, created_at,
                     stop_loss, order_status='pending'):
        cur = self.con.cursor()
        cur.execute('INSERT INTO orders(symbol, instrument, order_id, '
                    'order_type, price, quantity, trigger_price, created_at, order_status, stop_loss) '
                    'VALUES ({},{},{},{},{},{},{},{},{},{})'.format(symbol, instrument, order_id, order_type, price,
                                                                    quantity, trigger_price, created_at, order_status,
                                                                    stop_loss))
        self.con.commit()

    def get_token_if_exists(self):
        cur = self.con.cursor()
        cur.execute('SELECT access_token FROM tokens LIMIT 1')
        result = cur.fetchone()
        if result:
            return result[0]
        return None

    def set_token(self, token):
        cur = self.con.cursor()
        cur.execute('DELETE FROM tokens;')
        cur.execute('INSERT INTO tokens (access_token) VALUES (%s);', [token])
        self.con.commit()

    def create_table_instrument(self):
        cur = self.con.cursor()
        cur.execute('DROP TABLE IF EXISTS instrument')
        self.con.commit()
        cur.execute('CREATE TABLE instrument ('
                    'id SERIAL PRIMARY KEY NOT NULL,'
                    'symbol VARCHAR(60) NOT NULL,'
                    'instrument INTEGER NOT NULL,'
                    'instrument_type VARCHAR(60) NOT NULL,'
                    'tick_size DOUBLE PRECISION,'
                    'name VARCHAR(200) NOT NULL,'
                    'exchange VARCHAR(60) NOT NULL'
                    ')')
        self.con.commit()

    def push_instruments_to_database(self):
        cur = self.con.cursor()
        instruments = self.kite_connect.instruments(exchange='NSE')
        for instrument in instruments:
            self.create_table()
            cur.execute('INSERT INTO instrument (symbol, instrument, instrument_type, tick_size, name, exchange) '
                        'VALUES(\'{}\',{},\'{}\',{},\'{}\',\'{}\')'.format(instrument['tradingsymbol'],
                                                                           instrument['instrument_token'],
                                                                           instrument['instrument_type'],
                                                                           instrument['tick_size'],
                                                                           instrument['name'].replace('\'', ''),
                                                                           instrument['exchange']))
        self.con.commit()
