from twisted.application import service
from twbus.app import BusApp

application = service.Application('highscore')
ba = BusApp('127.0.0.1', 31337)
ba.setServiceParent(application)
