from shopen.models.models import User, Session, Transaction, Pen


async def setup_reset():
    await Session.all().delete()
    await Transaction.all().delete()
    await User.all().delete()
    await Pen.all().delete()

    await User.create(name='admin',
                      password='admin',
                      role='admin',
                      is_superuser=True)
