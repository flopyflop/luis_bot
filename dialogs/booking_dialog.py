# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
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


class BookingDialog(CancelAndHelpDialog):
    def __init__(self, dialog_id: str = None):
        super(BookingDialog, self).__init__(dialog_id or BookingDialog.__name__)

        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))
        self.add_dialog(DateResolverDialog(DateResolverDialog.__name__)),
        self.add_dialog(CapcacityResolverDialog(CapcacityResolverDialog.__name__)),
        self.add_dialog(UserIDResolverDialog(UserIDResolverDialog.__name__)),
        self.add_dialog(
            WaterfallDialog(
                WaterfallDialog.__name__,
                [
                    self.user_id_step,
                    self.destination_step,
                    self.origin_step,
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
        booking_details = step_context.options

        if not booking_details.user_id == 0:
            return await step_context.begin_dialog(
                UserIDResolverDialog.__name__, booking_details.user_id
            )
        return await step_context.next(booking_details.user_id)

    async def destination_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """
        If a destination city has not been provided, prompt for one.
        :param step_context:
        :return DialogTurnResult:
        """
        booking_details = step_context.options

        # Capture the response to the previous step's prompt
        booking_details.user_id = step_context.result

        if booking_details.destination is None:
            message_text = "Where would you like to travel to?"
            prompt_message = MessageFactory.text(
                message_text, message_text, InputHints.expecting_input
            )
            return await step_context.prompt(
                TextPrompt.__name__, PromptOptions(prompt=prompt_message)
            )
        return await step_context.next(booking_details.destination)

    async def origin_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """
        If an origin city has not been provided, prompt for one.
        :param step_context:
        :return DialogTurnResult:
        """
        booking_details = step_context.options

        # Capture the response to the previous step's prompt
        booking_details.destination = step_context.result
        if booking_details.origin is None:
            message_text = "From what city will you be travelling?"
            prompt_message = MessageFactory.text(
                message_text, message_text, InputHints.expecting_input
            )
            return await step_context.prompt(
                TextPrompt.__name__, PromptOptions(prompt=prompt_message)
            )
        return await step_context.next(booking_details.origin)

    async def travel_date_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """
        If a travel date has not been provided, prompt for one.
        This will use the DATE_RESOLVER_DIALOG.
        :param step_context:
        :return DialogTurnResult:
        """
        booking_details = step_context.options

        # Capture the results of the previous step
        booking_details.origin = step_context.result
        if not booking_details.travel_date or self.is_ambiguous(
            booking_details.travel_date
        ):
            return await step_context.begin_dialog(
                DateResolverDialog.__name__, booking_details.travel_date
            )
        return await step_context.next(booking_details.travel_date)

    async def capacity_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """
        If a travel date has not been provided, prompt for one.
        This will use the DATE_RESOLVER_DIALOG.
        :param step_context:
        :return DialogTurnResult:
        """
        booking_details = step_context.options

        # Capture the results of the previous step
        booking_details.travel_date = step_context.result
        if booking_details.capacity <= 0:
            booking_details.capacity = None
            return await step_context.begin_dialog(
                CapcacityResolverDialog.__name__, booking_details.capacity
            )
        return await step_context.next(booking_details.capacity)

    async def confirm_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """
        Confirm the information the user has provided.
        :param step_context:
        :return DialogTurnResult:
        """
        booking_details = step_context.options

        # Capture the results of the previous step
        booking_details.capacity = step_context.result
        message_text = (
            f"Please confirm, User ID: {booking_details.user_id} I have you traveling to {booking_details.destination} "
            f"from {booking_details.origin} on: {booking_details.travel_date} for {booking_details.capacity} travelers."
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
            booking_details = step_context.options

            response = requests.get("http://localhost:5000/v1/get_flights")

            the_flight = None

            json_obj = json.loads(response.text)
            flights = json_obj["flights"]
            for flight in flights:
                source = flight["from"]
                destination = flight["to"]
                capacity = flight["capacity"]
                departure = flight["departure"]
                landing = flight["landing"]
                flight_id = flight["id"]

                if source.lower() != booking_details.origin.lower():
                    continue

                if destination.lower() != booking_details.destination.lower():
                    continue

                if capacity < int(booking_details.capacity):
                    continue

                departue_date_object = datetime.strptime(departure ,'%d/%m/%y %H:%M:%S')
                depature_date = str(departue_date_object.year)+ "-"+ str(departue_date_object.month) + "-" + str(departue_date_object.day)
                if depature_date != booking_details.travel_date:
                    continue

                the_flight = flight
                break

            if the_flight is None:
                return await step_context.end_dialog(None)

            flight_id = the_flight["id"]
            seats = booking_details.capacity
            user_id = booking_details.user_id

            url = "http://localhost:5000/v1/make_reservation"
            data = {'flight_id': str(flight_id), 'number_of_seats': int(seats), 'user_id': str(user_id)}
            headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
            r = requests.post(url, data=json.dumps(data), headers=headers)

            return await step_context.end_dialog(booking_details)
        return await step_context.end_dialog()

    def is_ambiguous(self, timex: str) -> bool:
        timex_property = Timex(timex)
        return "definite" not in timex_property.types
