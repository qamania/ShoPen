from shopen.models.models import User, Session, Transaction, Pen


async def setup_reset():
    await Session.all().delete()
    await Transaction.all().delete()
    await User.all().delete()
    await Pen.all().delete()


async def set_default_users():
    await User.create(name='admin',
                      password='admin',
                      role='admin',
                      is_superuser=True)


async def set_default_stock():
    await Pen.create(brand='Pilot', price=15, stock=100, color='blue', length=15)
    await Pen.create(brand='Pilot', price=16, stock=100, color='red', length=13)
    await Pen.create(brand='Pilot', price=15, stock=100, color='black', length=20)
    await Pen.create(brand='Parker', price=125, stock=50, color='green', length=17)
    await Pen.create(brand='Parker', price=25, stock=60, color='red', length=17)
    await Pen.create(brand='Bic', price=3, stock=300, color='blue', length=19)


async def is_db_empty() -> bool:
    users = await User.all().count() == 0
    pens = await Pen.all().count() == 0
    return users and pens
