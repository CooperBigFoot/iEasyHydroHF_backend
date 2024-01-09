"""The MIT License (MIT)

Copyright (c) 2014 Hydrosolutions GmbH

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
from imomo.models import Units
from imomo.utils.basic_data import connect
from sqlalchemy import func, update


@connect
def trim_units(imomo_init):
    statement = update(Units).values(UnitsName=func.trim(Units.units_name))
    conn = imomo_init._engine.connect()
    trans = conn.begin()
    try:
        conn.execute(statement)
        trans.commit()
    except:
        trans.rollback()
        raise


@connect
def update_methods_seq(imomo_init):
    statement = "ALTER SEQUENCE methodid_methods_seq RESTART WITH 103"
    conn = imomo_init._engine.connect()
    trans = conn.begin()
    try:
        conn.execute(statement)
        trans.commit()
    except:
        trans.rollback()
        raise
