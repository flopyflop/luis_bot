from datetime import datetime

import requests
import json
from datatypes_date_time.timex import Timex

from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult
from botbuilder.dialogs.prompts import ConfirmPrompt, TextPrompt, PromptOptions
from botbuilder.core import MessageFactory
from botbuilder.schema import InputHints
from .cancel_and_help_dialog import CancelAndHelpDialog
from .capacity_resolver_dialog import CapcacityResolverDialog
from .user_id_resolver_dialog import UserIDResolverDialog
from .date_resolver_dialog import DateResolverDialog


class EditBookingDialog(CancelAndHelpDialog):
    def __init__(self, dialog_id: str = None):
        super(EditBookingDialog, self).__init__(dialog_id or EditBookingDialog.__name__)

        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))
        self.add_dialog(DateResolverDialog(DateResolverDialog.__name__)),
        self.add_dialog(UserIDResolverDialog(UserIDResolverDialog.__name__)),
        self.add_dialog(CapcacityResolverDialog(CapcacityResolverDialog.__name__)),
        self.add_dialog(
            WaterfallDialog(
                WaterfallDialog.__name__,
                [
                    self.user_id_step,
                    self.destination_step,
                    self.travel_date_step,
                    self.capacity_step,
                    self.confirm_step,
                    self.final_step,
                ],
            )
        )

        self.initial_dialog_id = WaterfallDialog.__name__

    async def user_id_step(
                self, step_context: WaterfallStepContext
        ) -> DialogTurnResult:
            """
            If a travel date has not been provided, prompt for one.
            This will use the DATE_RESOLVER_DIALOG.
            :param step_context:
            :return DialogTurnResult:
            """
            edit_booking_details = step_context.options

            if not edit_booking_details.user_id == 0:
                message_text = "Please enter your user ID"

                return await step_context.begin_dialog(
                    UserIDResolverDialog.__name__, edit_booking_details.user_id
                )
            return await step_context.next(edit_booking_details.user_id)

    async def destination_step(
                self, step_context: WaterfallStepContext
        ) -> DialogTurnResult:
            """
            If a destination city has not been provided, prompt for one.
            :param step_context:
            :return DialogTurnResult:
            """
            edit_booking_details = step_context.options

            # Capture the response to the previous step's prompt
            edit_booking_details.user_id = step_context.result

            if edit_booking_details.destination is None:
                message_text = "Where are you traveling to?"
                prompt_message = MessageFactory.text(
                    message_text, message_text, InputHints.expecting_input
                )
                return await step_context.prompt(
                    TextPrompt.__name__, PromptOptions(prompt=prompt_message)
                )
            return await step_context.next(edit_booking_details.destination)

    async def travel_date_step(
                self, step_context: WaterfallStepContext
        ) -> DialogTurnResult:
            """
            If a travel date has not been provided, prompt for one.
            This will use the DATE_RESOLVER_DIALOG.
            :param step_context:
            :return DialogTurnResult:
            """
            edit_booking_details = step_context.options

            # Capture the results of the previous step
            edit_booking_details.destination = step_context.result
            if not edit_booking_details.travel_date or self.is_ambiguous(
                    edit_booking_details.travel_date
            ):
                return await step_context.begin_dialog(
                    DateResolverDialog.__name__, edit_booking_details.travel_date
                )
            return await step_context.next(edit_booking_details.travel_date)

    async def capacity_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        edit_booking_details = step_context.options
        # Capture the results of the previous step
        edit_booking_details.travel_date = step_context.result
        if not edit_booking_details.capacity <= 0:
            edit_booking_details.capacity = None
            return await step_context.begin_dialog(
                CapcacityResolverDialog.__name__, edit_booking_details.capacity
            )
        return await step_context.next(edit_booking_details.capacity)


    async def confirm_step(
                self, step_context: WaterfallStepContext
        ) -> DialogTurnResult:
            """
            Confirm the information the user has provided.
            :param step_context:
            :return DialogTurnResult:
            """
            edit_booking_details = step_context.options

            # Capture the results of the previous step
            edit_booking_details.capacity = step_context.result
            message_text = (
                f"Please confirm, User ID: {edit_booking_details.user_id}, booking {edit_booking_details.capacity} "
                f"seats on flight to {edit_booking_details.destination} on: {edit_booking_details.travel_date}"
            )
            prompt_message = MessageFactory.text(
                message_text, message_text, InputHints.expecting_input
            )

            # Offer a YES/NO prompt.
            return await step_context.prompt(
                ConfirmPrompt.__name__, PromptOptions(prompt=prompt_message)
            )

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """
        Complete the interaction and end the dialog.
        :param step_context:
        :return DialogTurnResult:
        """
        if step_context.result:
            edit_booking_details = step_context.options

            response = requests.get("http://localhost:5000/v1/get_reservations")

            the_reservation = None

            reservations = json.loads(response.text)["reservations"]

            for reservation in reservations:
                destination = reservation["to"]
                departure = reservation["departure"]
                reservation_id = reservation["id"]
                user_id = reservation["user_id"]

                if destination.lower() != edit_booking_details.destination.lower():
                    continue

                departure_date_object = datetime.strptime(departure, '%d/%m/%y %H:%M:%S')
                departure_date = str(departure_date_object.year) + "-" + str(departure_date_object.month) + "-" + str(
                    departure_date_object.day)
                if departure_date != edit_booking_details.travel_date:
                    continue

                the_reservation = reservation
                break

            if the_reservation is None:
                return await step_context.end_dialog(None)

            reservation_id = the_reservation["id"]

            url = "http://localhost:5000/v1/modify_reservation"

            data = {'reservation_id': str(reservation_id)}
            headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
            r = requests.post(url, data=json.dumps(data), headers=headers)

            return await step_context.end_dialog(edit_booking_details)

        return await step_context.end_dialog()

    def is_ambiguous(self, timex: str) -> bool:
            timex_property = Timex(timex)
            return "definite" not in timex_property.types