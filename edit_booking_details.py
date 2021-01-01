# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
class EditBookingDetails:
    def __init__(
        self,
        destination: str = None,
        travel_date: str = None,
        unsupported_airports=None,
        capacity=0,
        user_id=-1
    ):
        if unsupported_airports is None:
            unsupported_airports = []
        self.destination = destination
        self.travel_date = travel_date
        self.unsupported_airports = unsupported_airports
        self.capacity = capacity
        self.user_id = user_id