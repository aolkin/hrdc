from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.test import Client, TransactionTestCase, override_settings

from dramaorg.models import Show, User
from finance.models import BudgetExpense, FinanceInfo
from hrdc.routing import websocket_application

IN_MEMORY_LAYER = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}


@override_settings(CHANNEL_LAYERS=IN_MEMORY_LAYER)
class BudgetSocketTests(TransactionTestCase):
    def setUp(self):
        self.show = Show.objects.create(
            title="Test", creator_credit="Someone", slug="test")
        self.finance = FinanceInfo.objects.create(show=self.show)
        self.expense = BudgetExpense.objects.create(
            show=self.finance, name="Lights")
        self.staff = self.make_user("staff@example.com")
        self.show.staff.add(self.staff)
        self.outsider = self.make_user("outsider@example.com")

    def make_user(self, email):
        return User.objects.create_user(
            email, "pw", first_name="A", last_name="B")

    def session_cookie(self, user):
        client = Client()
        client.force_login(user)
        return "sessionid={}".format(client.cookies["sessionid"].value)

    async def communicator(self, user):
        cookie = await database_sync_to_async(self.session_cookie)(user)
        return WebsocketCommunicator(
            websocket_application,
            "/finance/show/{}/budget/ws/".format(self.finance.pk),
            headers=[(b"cookie", cookie.encode())])

    async def test_non_staff_connection_is_refused(self):
        communicator = await self.communicator(self.outsider)
        connected, _ = await communicator.connect()
        self.assertFalse(connected)

    async def test_staff_receives_saved_changes(self):
        communicator = await self.communicator(self.staff)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        self.expense.notes = "Rented"
        await database_sync_to_async(self.expense.save)()

        message = await communicator.receive_json_from()
        self.assertEqual(message["stream"], "budgetexpense")
        self.assertEqual(message["payload"]["action"], "update")
        self.assertEqual(message["payload"]["pk"], self.expense.pk)
        self.assertEqual(message["payload"]["data"]["notes"], "Rented")
        await communicator.disconnect()

    async def test_staff_edit_is_saved_and_rebroadcast(self):
        communicator = await self.communicator(self.staff)
        await communicator.connect()

        await communicator.send_json_to({
            "stream": "budgetexpense",
            "payload": {"action": "update", "pk": self.expense.pk,
                        "data": {"estimate": "12.50", "actual": "99"}},
        })

        message = await communicator.receive_json_from()
        self.assertEqual(message["payload"]["data"]["estimate"], "12.50")
        await database_sync_to_async(self.expense.refresh_from_db)()
        self.assertEqual(str(self.expense.estimate), "12.50")
        self.assertEqual(self.expense.actual, 0)
        await communicator.disconnect()
